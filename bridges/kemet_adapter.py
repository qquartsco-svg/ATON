"""
kemet_adapter.py — 실제 KEMET 엔진 어댑터
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ATON Nexus 어댑터 타입:
  KemetAdapter = Callable[[KemetInput, float], KemetOutput]

이 모듈은 real KEMET ODE 엔진을 상태 보존 어댑터로 래핑한다.
- KemetMutable 상태를 스텝 간 유지
- KemetInput 신호 → 지파 출력을 mutable 상태에 오버레이
- _rk4_step() 실행 → 새 상태 계산
- KemetOutput으로 변환하여 반환

설계 원칙:
  - "지파 권위(Tribe Authority)": 지파 엔진이 담당하는 동역학은
    지파 출력값을 KEMET 상태에 직접 반영 (override).
    → grain_stock, wealth_concentration, knowledge_stock
    → KEMET의 내부 ODE는 그 외 나머지를 처리
  - Jubilee: jubilee_triggered=True → 강제 집중도 리셋
  - War: external_threat > 0.5 → war_mode = 1.0
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, Optional

# ── 경로 주입: kemet_engine ──────────────────────────────────────
_here  = os.path.dirname(os.path.abspath(__file__))       # bridges/
_aton  = os.path.dirname(_here)                            # _ATON_LAYER/
_hub   = os.path.dirname(os.path.dirname(_aton))           # ENGINE_HUB/
_kemet = os.path.join(_hub, "1_operational", "60_APPLIED_LAYER", "kemet_engine")

for _p in [_kemet, _hub]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kemet_core import (
    KemetParams,
    KemetMutable,
    KemetState,
    make_initial_state,
    _rk4_step,
    _derived,
    _flags,
    to_snapshot,
)
from _ATON_LAYER.interfaces.kemet_io import KemetInput, KemetOutput


# ─────────────────────────────────────────────────────────────────
# Ma'at 점수 계산
# ─────────────────────────────────────────────────────────────────

def compute_maat(
    food_security:  float,
    law_compliance: float,
    social_tension: float,
    health_index:   float,
) -> float:
    """Ma'at 질서 지수 [0,1] — 이집트의 우주 질서/정의/진리 지수.

    Ma'at = 0.30×식량안보 + 0.25×법준수율 + 0.25×(1−사회긴장) + 0.20×건강지수
    """
    raw = (
        0.30 * food_security
        + 0.25 * law_compliance
        + 0.25 * (1.0 - social_tension)
        + 0.20 * health_index
    )
    return max(0.0, min(1.0, raw))


# ─────────────────────────────────────────────────────────────────
# KemetEngineAdapter
# ─────────────────────────────────────────────────────────────────

class KemetEngineAdapter:
    """
    상태 보존 KEMET 엔진 어댑터 (ATON Nexus용).

    ATON Nexus가 요구하는 KemetAdapter 프로토콜 구현:
      adapter(KemetInput, dt) → KemetOutput

    동작:
      1. KemetInput 신호를 KemetMutable에 오버레이
      2. _rk4_step() 으로 1 타임스텝 진행
      3. KemetOutput 변환 및 반환
    """

    def __init__(
        self,
        params:           Optional[KemetParams] = None,
        initial_overrides: Optional[Dict[str, Any]] = None,
    ):
        self.params = params or KemetParams()
        overrides = initial_overrides or {}
        self._state: KemetMutable = make_initial_state(self.params, **overrides)

    # ── 어댑터 인터페이스 (callable) ─────────────────────────────

    def __call__(self, inp: KemetInput, dt: float) -> KemetOutput:
        """ATON Nexus 호출 인터페이스."""
        self._apply_input(inp)
        self._state = _rk4_step(self._state, self.params, dt)
        return self._to_output()

    # ── 입력 신호 오버레이 ────────────────────────────────────────

    def _apply_input(self, inp: KemetInput) -> None:
        """KemetInput 신호 → KemetMutable 상태 오버레이.

        "지파 권위" 원칙:
          지파 엔진이 실제로 시뮬레이션하는 동역학은
          해당 지파 출력값이 KEMET 상태를 직접 덮어쓴다.
          KEMET 내부 ODE는 나머지 부처(국방, 건설, 외교 등)를 처리.
        """
        s = self._state

        # ── Asher (농업): grain_stock 권위 ───────────────────────
        if inp.grain_stock > 0:
            s.grain_stock = max(0.0, inp.grain_stock)

        # ── Dan (사법): wealth_concentration 권위 ────────────────
        if 0.0 < inp.wealth_concentration < 1.0:
            s.wealth_concentration = max(0.01, min(0.99, inp.wealth_concentration))

        # ── Levi (교육): knowledge_stock 권위 ────────────────────
        if inp.knowledge_stock > 0:
            s.knowledge_stock = max(0.0, inp.knowledge_stock)

        # ── 희년 칙령: 강제 집중도 리셋 ──────────────────────────
        if inp.jubilee_triggered:
            s.wealth_concentration = max(0.05, s.wealth_concentration * 0.30)
            # 집중도를 30%로 강제 압축 (← _12 희년 리셋 계승)

        # ── 외부 위협: war_mode 설정 ──────────────────────────────
        s.war_mode = 1.0 if inp.external_threat > 0.5 else 0.0

        # ── 전염병 신호: 건강지수 급락 ───────────────────────────
        if inp.epidemic_signal:
            s.health_index = max(0.01, s.health_index - 0.05)

    # ── KemetOutput 변환 ──────────────────────────────────────────

    def _to_output(self) -> KemetOutput:
        """KemetMutable → KemetOutput."""
        s  = self._state
        p  = self.params
        d  = _derived(s, p)

        maat = compute_maat(
            food_security  = d["food_security"],
            law_compliance = s.law_compliance,
            social_tension = d["social_tension"],
            health_index   = s.health_index,
        )

        # 예산 배분 (부처별) — KemetParams v0.6.0 기준 11개 필드
        # bw_treasury=0.00(수입원) 제외, bw_foreign 삭제(→ bw_infocomm으로 교체)
        total_w = (
            p.bw_health + p.bw_education + p.bw_homeland + p.bw_justice
            + p.bw_defense + p.bw_labor + p.bw_agriculture
            + p.bw_maritime + p.bw_construction + p.bw_econplan + p.bw_infocomm
        )  # 기본값 합계 = 1.00
        edu_budget = d["tax_revenue"] * p.bw_education / max(1e-9, total_w)
        jus_budget = d["tax_revenue"] * p.bw_justice   / max(1e-9, total_w)

        return KemetOutput(
            t=s.t,
            energy_investment_budget=max(0.0, s.treasury_balance) * 0.05,
            education_budget=edu_budget,
            education_budget_signal=edu_budget,
            gdp=d["gdp"],
            foreign_openness=s.alliance_strength,
            solar_reform_active=False,   # 파라오 칙령에서만 설정
            maat_score=maat,
            social_tension=d["social_tension"],
            law_compliance=s.law_compliance,
            population=s.population,
            health_index=s.health_index,
            food_security=d["food_security"],
            justice_budget=jus_budget,
            jubilee_decree_active=(s.wealth_concentration > 0.65),
            flags={
                "treasury_crisis":  s.treasury_balance < 0.0,
                "food_crisis":      d["food_security"] < 0.3,
                "social_unrest":    d["social_tension"] > 0.7,
                "minsky_ponzi":     d["minsky_stage"] == "ponzi",
                "war_mode":         bool(s.war_mode > 0.5),
                "epidemic":         s.health_index < 0.4,
            },
        )

    # ── 보조 API ──────────────────────────────────────────────────

    def get_kemet_state(self) -> KemetState:
        """현재 KEMET 내부 상태 스냅샷 (외부 확인용)."""
        return to_snapshot(self._state, self.params)

    def reset(self, **overrides: Any) -> None:
        """내부 상태 초기화."""
        self._state = make_initial_state(self.params, **overrides)


# ─────────────────────────────────────────────────────────────────
# 팩토리 함수
# ─────────────────────────────────────────────────────────────────

def make_kemet_adapter(
    params:            Optional[KemetParams] = None,
    initial_overrides: Optional[Dict[str, Any]] = None,
) -> KemetEngineAdapter:
    """KemetEngineAdapter 인스턴스 생성 팩토리.

    ATON Nexus에 주입할 실제 KEMET 엔진 어댑터를 반환.

    Example::
        from _ATON_LAYER.bridges.kemet_adapter import make_kemet_adapter
        nexus = Nexus(kemet_adapter=make_kemet_adapter())
    """
    return KemetEngineAdapter(params=params, initial_overrides=initial_overrides)
