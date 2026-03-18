"""
ATON Nexus — 통합 시뮬레이션 오케스트레이터
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

모든 엔진을 올바른 순서로 step()하고
신호를 라우팅하는 최상위 조율자(Conductor).

실행 순서 (매 타임스텝):
  1. 70_TRIBES 엔진들 step()  → TribesSignal 생성
  2. PROMETHEUS step()        → PrometheusOutput 생성
  3. 브릿지 변환              → KemetInput 조합
  4. KEMET step()             → KemetOutput 생성
  5. EDEN 집계                → EdenSignal 생성
  6. NexusState 갱신          → 스냅샷 저장
  7. 충격 감지 & 라우팅

설계:
  각 엔진이 없어도(None) 다른 엔진은 기본값으로 정상 동작.
  → "에어 조던 원칙": 각 엔진은 혼자서도 달릴 수 있다.

v1에서 실제 엔진(kemet_core.simulate 등)을 직접 호출하는 대신
인터페이스를 통해 통신한다.
실제 엔진 연결은 각 `adapter` 함수를 통해 이루어진다.
"""

from __future__ import annotations

import math
import sys
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

from .aton_core import (
    NexusState, NexusConfig,
    tribes_to_kemet_input, all_to_eden_signal,
)
from .interfaces import (
    KemetInput, KemetOutput,
    PrometheusInput, PrometheusOutput,
    TribesSignal, EdenSignal,
)
from .interfaces.tribes_io import (
    LeviSignal, DanSignal, AsherSignal, ZebulunSignal,
)
from .bridges import (
    OilShockRouter, OilShockEvent,
    EnergyMinistry, EnergyMinistryParams,
    MonetaBridge,
    make_kemet_adapter,
    make_tribes_adapter,
)


# ─────────────────────────────────────────────────────────────────
# 엔진 어댑터 타입 정의
# ─────────────────────────────────────────────────────────────────
# 어댑터 = 실제 엔진 step() 함수를 래핑하는 콜백.
# 없으면(None) → 기본값 신호 사용.
#
# KemetAdapter:      (KemetInput, dt) → KemetOutput
# PrometheusAdapter: (PrometheusInput, dt) → PrometheusOutput
# TribesAdapter:     (prev_tribes, dt, external) → TribesSignal

KemetAdapter      = Optional[Callable[[KemetInput, float], KemetOutput]]
PrometheusAdapter = Optional[Callable[[PrometheusInput, float], PrometheusOutput]]
TribesAdapter     = Optional[Callable[[TribesSignal, float, Dict], TribesSignal]]


# ─────────────────────────────────────────────────────────────────
# 기본 어댑터 (실제 엔진 없을 때 사용하는 단순 추정 모델)
# ─────────────────────────────────────────────────────────────────

def _default_prometheus_adapter(inp: PrometheusInput, dt: float) -> PrometheusOutput:
    """
    실제 PROMETHEUS 없을 때의 기본 에너지 전환 추정기.

    단순 선형 전환: D → 0, R → 1 (정책 강도에 비례)
    (실제 ODE보다 단순하지만 시스템 연결 테스트에 충분)
    """
    # 정책 가속 반영
    transition_rate = 0.02 + inp.policy_push * 0.03  # 2~5%/yr
    budget_factor   = min(2.0, inp.energy_budget / max(1.0, inp.gdp_level) * 20.0)

    return PrometheusOutput(
        oil_dependency=max(0.0, 1.0 - transition_rate * dt * budget_factor),
        renewable_share=min(1.0, transition_rate * dt * budget_factor),
        oil_weapon_effect=max(0.0, 1.0 - transition_rate * dt * budget_factor),
        energy_independence=min(1.0, transition_rate * dt * budget_factor * 0.8),
        solar_lcoe=max(10.0, 40.0 - inp.energy_budget * 0.1),
        oil_price_multiplier=1.0 + (inp.wealth_concentration - 0.3) * 0.5,
    )


def _default_tribes_adapter(
    prev: TribesSignal,
    dt: float,
    external: Dict,
) -> TribesSignal:
    """
    실제 70_TRIBES 엔진 없을 때의 기본 추정기.
    이전 상태에서 소폭 변동.
    """
    from copy import deepcopy
    tribes = deepcopy(prev)

    # Levi: 지식 축적 (간단한 ODE)
    budget_edu = external.get("education_budget", 0.0)
    dk = (budget_edu * 0.06 - tribes.levi.knowledge_stock * 0.01) * dt
    tribes.levi.knowledge_stock  = max(0.0, min(500.0, tribes.levi.knowledge_stock + dk))
    tribes.levi.productivity_bonus = 0.04 * math.log(1 + tribes.levi.knowledge_stock / 50.0)

    # Dan: 집중도 (로지스틱)
    c = tribes.dan.wealth_concentration
    dc = (0.025 * c * (1 - c)) * dt
    tribes.dan.wealth_concentration = max(0.0, min(1.0, c + dc))
    tribes.dan.jubilee_triggered = tribes.dan.wealth_concentration >= 0.65
    tribes.dan.social_tension = (
        1.0 / (1.0 + math.exp(-(c - 0.5))) * (1.0 - tribes.dan.law_compliance)
    )

    # Asher: 곡식 (나일 주기)
    t = external.get("t", 0.0)
    nile_flux = 100.0 * (1 + 0.40 * math.sin(2 * math.pi * t / 7.0))
    dg = (nile_flux * 0.5 - 0.05 * 1000.0 - 0.01 * tribes.asher.grain_stock) * dt
    tribes.asher.grain_stock = max(0.0, min(99000.0, tribes.asher.grain_stock + dg))
    fsi = tribes.asher.grain_stock / (0.05 * 1000.0 * 12.0)
    tribes.asher.food_security = min(1.0, fsi / 1.0)
    tribes.asher.pishon_grain_flux = max(0.0, dg / dt)

    # Zebulun: 어족 (Schaefer)
    r, K, q = 0.20, 100.0, 0.10
    S = tribes.zebulun.fish_stock
    F_effort = min(20.0, 10.0 + tribes.zebulun.fish_revenue * 0.01)
    harvest = q * F_effort * S
    ds = (r * S * (1 - S / K) - harvest) * dt
    tribes.zebulun.fish_stock = max(1.0, min(K, S + ds))
    tribes.zebulun.fish_revenue = harvest * 2.0

    msy = r * K / 4.0
    if S < msy * 0.3:
        tribes.zebulun.fleet_signal = "EMERGENCY"
    elif S < msy * 0.7:
        tribes.zebulun.fleet_signal = "REDUCE"
    elif S > msy * 1.2:
        tribes.zebulun.fleet_signal = "EXPAND"
    else:
        tribes.zebulun.fleet_signal = "MAINTAIN"

    return tribes


def _default_kemet_adapter(inp: KemetInput, dt: float) -> KemetOutput:
    """
    실제 KEMET 엔진 없을 때의 기본 추정기.
    입력 신호에서 단순 집계.
    """
    maat = (
        0.3 * inp.food_security
        + 0.25 * (1.0 - inp.social_tension_signal)
        + 0.2 * inp.productivity_bonus * 10.0
        + 0.25 * (1.0 - (1.0 if inp.minsky_stage == "ponzi" else 0.3))
    )
    return KemetOutput(
        maat_score=min(1.0, max(0.0, maat)),
        social_tension=inp.social_tension_signal,
        law_compliance=inp.knowledge_stock / max(1.0, inp.knowledge_stock + 50.0),
        population=1000.0,
        health_index=min(1.0, inp.food_security * 0.8 + 0.2),
        food_security=inp.food_security,
        gdp=100.0 * (1.0 + inp.productivity_bonus),
        energy_investment_budget=5.0,
        education_budget=8.0,
        flags={
            "food_crisis":     inp.food_security < 0.3,
            "social_unrest":   inp.social_tension_signal > 0.7,
            "minsky_ponzi":    inp.minsky_stage == "ponzi",
            "jubilee_decree":  inp.jubilee_triggered,
            "treasury_crisis": False,
            "war_mode":        False,
            "epidemic":        False,
        },
    )


# ─────────────────────────────────────────────────────────────────
# Nexus — 메인 오케스트레이터
# ─────────────────────────────────────────────────────────────────

class Nexus:
    """
    ATON 통합 오케스트레이터.

    모든 엔진을 조율하고, 신호를 라우팅하고,
    매 타임스텝마다 NexusState 스냅샷을 생성한다.

    사용법:
      nexus = Nexus(config=NexusConfig())
      history = nexus.simulate(years=50)
      nexus.report(history[-1])
    """

    def __init__(
        self,
        config: Optional[NexusConfig] = None,
        kemet_adapter:      KemetAdapter      = None,
        prometheus_adapter: PrometheusAdapter = None,
        tribes_adapter:     TribesAdapter     = None,
    ):
        self.config = config or NexusConfig()

        # 어댑터 (None이면 기본 추정기 사용)
        self._kemet_fn      = kemet_adapter      or _default_kemet_adapter
        self._prometheus_fn = prometheus_adapter or _default_prometheus_adapter
        self._tribes_fn     = tribes_adapter     or _default_tribes_adapter

        # 브릿지
        self.oil_shock_router = OilShockRouter()
        self.energy_ministry  = EnergyMinistry()
        self.moneta_bridge    = MonetaBridge()

        # 초기 상태
        self._tribes_state = TribesSignal()
        self._prev_owe     = 1.0   # 이전 스텝 OWE (충격 감지용)
        self._planet_context: Optional[Dict] = None  # EdenOS→ATON 브릿지: 행성 컨텍스트 유지

    def step(self, t: float, dt: float, external: Optional[Dict] = None) -> NexusState:
        """
        1 타임스텝 전체 시스템 진행.

        Args:
            t:        현재 시뮬레이션 시간 (yr)
            dt:       타임스텝 크기 (yr)
            external: 외부 충격 / 파라오 칙령 {"oil_shock": True, "jubilee": True, ...}
        """
        ext = external or {}
        cfg = self.config

        nexus = NexusState(t=t)

        # ── 1. 70_TRIBES step ──────────────────────────────────────
        # KEMET 출력 반영 전 교육 예산 기본값
        prev_edu_budget = (
            self._tribes_state.levi.knowledge_stock * 0.01 + 8.0
        )
        tribes_external = {
            "t": t,
            "education_budget": prev_edu_budget,
        }
        if cfg.use_tribes:
            self._tribes_state = self._tribes_fn(
                self._tribes_state, dt, tribes_external
            )
        nexus.tribes = self._tribes_state

        # ── 2. PROMETHEUS step ─────────────────────────────────────
        if cfg.use_prometheus:
            p_input = PrometheusInput(
                energy_budget=self.energy_ministry.state.budget,
                gdp_level=100.0,
                knowledge_stock=self._tribes_state.levi.knowledge_stock,
                levi_spillover=self._tribes_state.levi.productivity_bonus,
                wealth_concentration=self._tribes_state.dan.wealth_concentration,
                solar_reform_decree=ext.get("solar_reform", False),
                policy_push=ext.get("policy_push", 0.0),
            )
            p_out = self._prometheus_fn(p_input, dt)
            nexus.prometheus = p_out

            # ── 충격 감지 ──────────────────────────────────────────
            shock = self.oil_shock_router.detect(
                t=t,
                owe_before=self._prev_owe,
                owe_after=p_out.oil_weapon_effect,
            )
            if shock:
                nexus.shock_events.append(shock)
            self._prev_owe = p_out.oil_weapon_effect
        else:
            p_out = None

        # ── 3. 에너지부 step ────────────────────────────────────────
        if cfg.use_energy_ministry:
            self.energy_ministry.step(
                dt=dt,
                treasury_budget=100.0,  # 기본값 (KEMET 출력 반영 전)
                prometheus_out=p_out,
                solar_reform_active=ext.get("solar_reform", False),
            )
        nexus.energy_ministry = self.energy_ministry.state

        # ── 4. KEMET step ───────────────────────────────────────────
        if cfg.use_kemet:
            k_input = tribes_to_kemet_input(self._tribes_state)
            # PROMETHEUS 신호 오버레이
            if p_out is not None and cfg.prometheus_to_kemet:
                k_input.oil_price_multiplier = p_out.oil_price_multiplier
                k_input.oil_shock_active     = p_out.is_oil_shock()
                k_input.tipping_point        = p_out.flags.get("tipping_point_crossed", False)
            # 외부 충격
            k_input.external_threat = ext.get("external_threat", 0.0)
            k_input.epidemic_signal = ext.get("epidemic", False)

            k_out = self._kemet_fn(k_input, dt)
            nexus.kemet = k_out
        else:
            k_out = None

        # ── 5. EDEN 집계 ─────────────────────────────────────────────
        if cfg.use_eden and cfg.all_to_eden:
            nexus.eden = all_to_eden_signal(k_out, p_out, self._tribes_state, t=t)

        # ── 6. 상태 갱신 ─────────────────────────────────────────────
        # 에너지부 상태는 참조가 아닌 스냅샷으로 저장
        from copy import copy
        nexus.energy_ministry = copy(self.energy_ministry.state)
        # 행성 트윈 브릿지: external에서 planet_context 주입 시 유지
        if "planet_context" in ext:
            self._planet_context = ext["planet_context"]
        nexus.planet_context = self._planet_context
        nexus.update_flags()

        return nexus

    def simulate(
        self,
        years: Optional[float] = None,
        external_sequence: Optional[Dict[float, Dict]] = None,
    ) -> List[NexusState]:
        """
        전체 시뮬레이션 실행.

        Args:
            years:              시뮬레이션 기간 (기본값: config.t_end)
            external_sequence:  {시점: 외부 충격 딕셔너리} 매핑

        Returns:
            NexusState 스냅샷 리스트 (매 스텝)
        """
        cfg = self.config
        t_end = years if years is not None else cfg.t_end
        dt    = cfg.dt
        ext_seq = external_sequence or {}

        history: List[NexusState] = []
        t = cfg.t_start

        while t <= t_end + dt * 0.01:  # 부동소수점 오차 허용
            # 현재 시점의 외부 신호 수집
            ext = {}
            for t_key, v in ext_seq.items():
                if abs(t - t_key) < dt * 0.5:
                    ext.update(v)

            state = self.step(t=t, dt=dt, external=ext)
            history.append(state)
            t = round(t + dt, 6)

        return history

    def report(self, state: NexusState) -> None:
        """NexusState 요약 출력 (파라오 대시보드)."""
        print(state.summary())
        if state.prometheus:
            p = state.prometheus
            print(f"\n  에너지 전환 세부:")
            print(f"    D={p.oil_dependency:.3f}  R={p.renewable_share:.3f}  "
                  f"LCOE={p.solar_lcoe:.1f}$/MWh")
            print(f"    OWE={p.oil_weapon_effect:.3f}  EII={p.energy_independence:.3f}")
        if state.tribes:
            t = state.tribes
            print(f"\n  지파 세부:")
            print(f"    Levi K={t.levi.knowledge_stock:.1f}  "
                  f"Dan c={t.dan.wealth_concentration:.3f}({t.dan.minsky_stage})")
            print(f"    Asher G={t.asher.grain_stock:.0f}  "
                  f"Zebulun S={t.zebulun.fish_stock:.1f}({t.zebulun.fleet_signal})")
        em = state.energy_ministry
        if em:
            print(f"\n  에너지부:")
            print(f"    그리드={em.grid_capacity:.3f}  보조금={em.subsidy_level:.3f}  "
                  f"정책압력={em.policy_signal:.3f}")
        if state.shock_events:
            print(f"\n  충격 이벤트: {len(state.shock_events)}건")
        print()


# ─────────────────────────────────────────────────────────────────
# 팩토리 함수 — 실제 엔진 연결 Nexus 생성
# ─────────────────────────────────────────────────────────────────

def make_real_nexus(
    config:             Optional[NexusConfig] = None,
    kemet_params:       object = None,  # KemetParams | None
    tribes_params:      object = None,  # TribeCouncilParams | None
    use_real_kemet:     bool = True,
    use_real_tribes:    bool = True,
    prometheus_adapter: Optional[Callable] = None,
) -> "Nexus":
    """
    실제 엔진이 연결된 ATON Nexus 인스턴스 생성.

    기본 스텁 어댑터(_default_*) 대신
    실제 KEMET ODE + 실제 12지파 TribeCouncil을 사용한다.

    Parameters
    ----------
    config : NexusConfig | None
        시뮬레이션 설정 (기본값 사용 가능)
    kemet_params : KemetParams | None
        KEMET 엔진 파라미터 (None = 기본값)
    tribes_params : TribeCouncilParams | None
        12지파 파라미터 (None = 기본값)
    use_real_kemet : bool
        True → 실제 KemetEngineAdapter 사용 (False → 기본 스텁)
    use_real_tribes : bool
        True → 실제 TribesEngineAdapter 사용 (False → 기본 스텁)
    prometheus_adapter : Callable | None
        PROMETHEUS 어댑터 (None → 기본 스텁)

    Returns
    -------
    Nexus
        실제 엔진이 주입된 ATON Nexus 오케스트레이터

    Example
    -------
    ::
        nexus = make_real_nexus()
        history = nexus.simulate(years=50)
        nexus.report(history[-1])
    """
    kemet_fn  = make_kemet_adapter(params=kemet_params)   if use_real_kemet  else None
    tribes_fn = make_tribes_adapter(params=tribes_params) if use_real_tribes else None

    return Nexus(
        config             = config,
        kemet_adapter      = kemet_fn,
        prometheus_adapter = prometheus_adapter,
        tribes_adapter     = tribes_fn,
    )
