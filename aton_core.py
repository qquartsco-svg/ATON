"""
_ATON_LAYER — aton_core.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ATON = 아톤(Aton/Aten) — 이집트 태양신.
파라오 아크나톤이 기존의 다신교를 버리고
태양 에너지 하나로 통일한 혁명적 전환.

"모든 에너지는 하나의 원천으로 귀결된다."
  → 모든 ENGINE_HUB 레이어를 하나의 동역학 흐름으로 통합.

NexusState:
  모든 엔진 상태의 현재 스냅샷 집합.
  각 엔진이 독립적으로 계산한 결과를 한 곳에서 볼 수 있는 "관제탑".

NexusConfig:
  어떤 엔진들을 활성화할지 설정.
  None인 엔진은 기본값으로 동작 (Air Jordan 원칙 유지).

설계 원칙:
  1. 엔진들은 서로 직접 참조하지 않는다.
     A → 인터페이스 → B  (인터페이스가 변환 담당)
  2. ATON이 오케스트레이터 역할.
     각 엔진을 순서대로 step() 하고 신호를 라우팅.
  3. 상태는 불변(immutable) 스냅샷으로 기록.
     → 어떤 시점의 상태든 재현 가능 (EDEN의 가역성 원칙)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .interfaces import (
    KemetInput, KemetOutput,
    PrometheusInput, PrometheusOutput,
    TribesSignal,
    EdenSignal,
)
from .bridges.energy_ministry import EnergyMinistryState
from .bridges.oil_shock import OilShockEvent


# ─────────────────────────────────────────────────────────────────
# NexusState — 모든 엔진의 통합 스냅샷
# ─────────────────────────────────────────────────────────────────

@dataclass
class NexusState:
    """
    시점 t에서의 전체 시스템 상태 스냅샷.

    "파라오는 이 한 화면을 본다."
    각 엔진의 핵심 출력이 여기 집약된다.
    """
    t: float = 0.0

    # ── 레이어별 출력 신호 ────────────────────────────────────────
    kemet:      Optional[KemetOutput]      = None
    prometheus: Optional[PrometheusOutput] = None
    tribes:     Optional[TribesSignal]     = None
    eden:       Optional[EdenSignal]       = None

    # ── 에너지부 상태 (11번째 부처) ─────────────────────────────
    energy_ministry: Optional[EnergyMinistryState] = None

    # ── 충격 이벤트 기록 ──────────────────────────────────────────
    shock_events: List[OilShockEvent] = field(default_factory=list)

    # ── ATON 통합 지수 ────────────────────────────────────────────
    nexus_coherence:    float = 0.5    # 시스템 전체 정합성 [0,1]
    # Ω_nexus = f(Ma'at, EII, 사회안정, 식량안보, 법준수)

    # ── 시스템 플래그 (Pharaoh Dashboard) ───────────────────────
    system_flags: Dict[str, bool] = field(default_factory=lambda: {
        # 에너지 전환 상태
        "energy_transition_active":     False,  # PROMETHEUS가 진행 중
        "oil_shock_active":             False,  # 현재 석유 충격 진행 중
        "energy_tipping_point":         False,  # R > 35% 돌파
        "energy_independent":           False,  # EII > 75%
        "petrodollar_risk":             False,  # D < 25%
        # 사회 안정
        "social_crisis":               False,  # ST > 0.7
        "food_crisis":                 False,  # FSI < 0.3
        "minsky_ponzi":                False,  # 민스키 폰지 단계
        # 자원
        "overfishing_emergency":        False,  # 어족 붕괴 위기
        "jubilee_triggered":            False,  # 희년 발동
        # 거버넌스
        "maat_healthy":                False,  # Ma'at > 0.6
        "eden_state":                  False,  # Ω > 0.75
    })

    def compute_coherence(self) -> float:
        """
        Nexus 정합성 = 각 레이어의 핵심 지수 종합.

        c = w1×Ma'at + w2×EII + w3×(1-ST) + w4×FSI + w5×법준수
        """
        weights = {
            "maat":          0.25,
            "energy_indep":  0.20,
            "social_stable": 0.20,
            "food_secure":   0.20,
            "law":           0.15,
        }
        scores = {
            "maat":          (self.kemet.maat_score if self.kemet else 0.5),
            "energy_indep":  (self.prometheus.energy_independence if self.prometheus else 0.0),
            "social_stable": (1.0 - (self.kemet.social_tension if self.kemet else 0.5)),
            "food_secure":   (self.kemet.food_security if self.kemet else 0.5),
            "law":           (self.kemet.law_compliance if self.kemet else 0.5),
        }
        return sum(weights[k] * scores[k] for k in weights)

    def update_flags(self) -> None:
        """현재 상태에서 시스템 플래그 갱신."""
        p = self.prometheus
        k = self.kemet
        t = self.tribes
        e = self.eden

        self.system_flags["energy_transition_active"] = (
            p is not None and p.renewable_share > 0.05
        )
        self.system_flags["oil_shock_active"] = (
            p is not None and p.is_oil_shock()
        )
        self.system_flags["energy_tipping_point"] = (
            p is not None and p.flags.get("tipping_point_crossed", False)
        )
        self.system_flags["energy_independent"] = (
            p is not None and p.is_energy_independent()
        )
        self.system_flags["petrodollar_risk"] = (
            p is not None and p.flags.get("petrodollar_collapse_risk", False)
        )
        self.system_flags["social_crisis"] = (
            k is not None and k.flags.get("social_unrest", False)
        )
        self.system_flags["food_crisis"] = (
            k is not None and k.flags.get("food_crisis", False)
        )
        self.system_flags["minsky_ponzi"] = (
            k is not None and k.flags.get("minsky_ponzi", False)
        )
        self.system_flags["overfishing_emergency"] = (
            t is not None and t.zebulun.fleet_signal == "EMERGENCY"
        )
        self.system_flags["jubilee_triggered"] = (
            t is not None and t.dan.jubilee_triggered
        )
        self.system_flags["maat_healthy"] = (
            k is not None and k.maat_score > 0.6
        )
        self.system_flags["eden_state"] = (
            e is not None and e.is_eden_state()
        )

        self.nexus_coherence = self.compute_coherence()

    def summary(self) -> str:
        """한눈에 보는 시스템 요약 (파라오 대시보드)."""
        p = self.prometheus
        k = self.kemet
        t = self.tribes

        lines = [
            f"══ NEXUS STATE  t={self.t:.1f}yr  Ω={self.nexus_coherence:.3f} ══",
            f"  에너지:  D={p.oil_dependency:.2f}  R={p.renewable_share:.2f}  "
            f"OWE={p.oil_weapon_effect:.2f}  EII={p.energy_independence:.2f}"
            if p else "  에너지:  [없음]",
            f"  KEMET:   Ma'at={k.maat_score:.2f}  ST={k.social_tension:.2f}  "
            f"FSI={k.food_security:.2f}  GDP={k.gdp:.1f}"
            if k else "  KEMET:   [없음]",
            f"  지파:    K={t.levi.knowledge_stock:.0f}  c={t.dan.wealth_concentration:.2f}  "
            f"곡식={t.asher.grain_stock:.0f}  어족={t.zebulun.fish_stock:.0f}"
            if t else "  지파:    [없음]",
        ]

        active_flags = [k for k, v in self.system_flags.items() if v]
        if active_flags:
            lines.append(f"  🚨 플래그: {', '.join(active_flags)}")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# NexusConfig — 시뮬레이션 설정
# ─────────────────────────────────────────────────────────────────

@dataclass
class NexusConfig:
    """
    ATON 시뮬레이션 설정.

    어떤 엔진들을 실제로 실행할지,
    각 엔진의 연결을 어떻게 구성할지 설정한다.
    """
    # 활성화 여부
    use_kemet:       bool = True
    use_prometheus:  bool = True
    use_tribes:      bool = True
    use_eden:        bool = True
    use_energy_ministry: bool = True

    # 시뮬레이션 시간 설정
    dt:      float = 1.0    # 타임스텝 (yr)
    t_start: float = 0.0
    t_end:   float = 50.0

    # 브릿지 연결 설정
    prometheus_to_kemet: bool = True  # 에너지 충격 → KEMET 전달
    tribes_to_kemet:     bool = True  # 지파 신호 → KEMET 전달
    tribes_to_prometheus:bool = True  # 지파 지식 → PROMETHEUS 가속
    all_to_eden:         bool = True  # 모든 엔진 → EDEN 4대강

    # 초기 조건 오버라이드 (None = 엔진 기본값)
    kemet_initial:      Optional[Dict] = None
    prometheus_initial: Optional[Dict] = None

    def active_layers(self) -> List[str]:
        layers = []
        if self.use_kemet:      layers.append("KEMET")
        if self.use_prometheus: layers.append("PROMETHEUS")
        if self.use_tribes:     layers.append("70_TRIBES")
        if self.use_eden:       layers.append("_EDEN")
        if self.use_energy_ministry: layers.append("ENERGY_MINISTRY")
        return layers


# ─────────────────────────────────────────────────────────────────
# 신호 변환 유틸리티
# ─────────────────────────────────────────────────────────────────

def tribes_to_kemet_input(tribes: TribesSignal) -> KemetInput:
    """TribesSignal → KemetInput 변환."""
    return KemetInput(
        grain_stock=tribes.asher.grain_stock,
        food_security=tribes.asher.food_security,
        nile_phase=tribes.asher.nile_phase,
        fish_revenue=tribes.zebulun.fish_revenue,
        maritime_gdp=tribes.zebulun.maritime_gdp,
        fleet_signal=tribes.zebulun.fleet_signal,
        wealth_concentration=tribes.dan.wealth_concentration,
        jubilee_triggered=tribes.dan.jubilee_triggered,
        social_tension_signal=tribes.dan.social_tension,
        minsky_stage=tribes.dan.minsky_stage,
        knowledge_stock=tribes.levi.knowledge_stock,
        productivity_bonus=tribes.levi.productivity_bonus,
        network_output=tribes.levi.network_output,
    )


def all_to_eden_signal(
    kemet: Optional[KemetOutput],
    prometheus: Optional[PrometheusOutput],
    tribes: Optional[TribesSignal],
    t: float = 0.0,
) -> EdenSignal:
    """모든 엔진 출력 → EdenSignal 통합."""
    eden = EdenSignal(t=t, year=int(t))

    if tribes:
        eden.pishon_grain_flux    = tribes.asher.pishon_grain_flux
        eden.pishon_fish_flux     = tribes.zebulun.fish_revenue
        eden.gihon_population     = kemet.population if kemet else 1000.0
        eden.gihon_stability      = tribes.dan.gihon_stability
        eden.gihon_health         = kemet.health_index if kemet else 0.7
        eden.hiddekel_knowledge   = tribes.levi.knowledge_stock
        eden.hiddekel_law         = tribes.dan.law_compliance
        eden.hiddekel_network     = tribes.levi.network_output

    if prometheus:
        eden.pishon_energy_flux   = prometheus.pishon_energy_flux
        eden.pishon_oil_flux      = prometheus.oil_dependency
        eden.hiddekel_tech_level  = 1.0 - max(0.0, prometheus.solar_lcoe / 40.0 - 0.5)
        eden.euphrates_eii        = prometheus.energy_independence
        eden.euphrates_owe        = prometheus.oil_weapon_effect

    if kemet:
        eden.euphrates_maat       = kemet.maat_score
        eden.euphrates_gdp        = kemet.gdp
        eden.gihon_jubilee_events += 1 if kemet.jubilee_decree_active else 0

    return eden
