"""
에너지부 (Energy Ministry) — KEMET 11번째 부처
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEMET 기존 10부처 + 에너지부(11번째) 골격.

PROMETHEUS가 에너지 전환 ODE를 담당하고,
에너지부는 KEMET ↔ PROMETHEUS 사이의 정책 번역기 역할을 한다.

에너지부 3대 기능:
  1. 그리드 인프라 (Grid Infrastructure)
     → 건설부 + PROMETHEUS solar_lcoe 신호 연동
  2. 에너지 보조금 (Subsidy)
     → 재무부 예산 배분 + 재생에너지 확대
  3. 석유 수입 관리 (Import Management)
     → 외교부 + PROMETHEUS oil_dependency 신호 연동

ODE (v1 골격 — 상세 계수는 v2에서 보정):
  dG_energy/dt = grid_invest × efficiency − grid_decay × G_energy
  dS_renew/dt  = subsidy × R_growth_rate − S_renew × decay
  dI_oil/dt    = demand × (1 − R) − import_reduction × policy

연결 관계:
  IN:  PROMETHEUS(solar_lcoe, oil_dependency, tipping_point)
  IN:  KEMET treasury_balance, construction_budget
  OUT: KEMET 건설부(그리드 투자 신호)
  OUT: KEMET 재무부(에너지 비용 조정)
  OUT: PROMETHEUS(policy_push, energy_budget)
  OUT: EDEN Euphrates강(에너지 독립 진도)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────
# 파라미터
# ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EnergyMinistryParams:
    """에너지부 시스템 상수."""

    # 그리드 인프라
    grid_build_rate:    float = 0.15   # 예산 → 그리드 용량 전환률
    grid_decay:         float = 0.02   # 노후화율 /yr
    grid_capacity_max:  float = 1.0    # 최대 그리드 용량 [0,1]

    # 재생에너지 보조금
    subsidy_efficiency: float = 0.20   # 보조금 → R 성장 가속
    subsidy_decay:      float = 0.05   # 보조금 효과 감소율

    # 석유 수입 관리
    import_reduction_rate: float = 0.10  # 정책 강도 → 수입 감소율
    strategic_reserve:     float = 0.10  # 전략 비축 비율 (GDP 대비)

    # 예산 배분 (재무부 전체 예산 대비 비율)
    budget_share:       float = 0.08   # 에너지부 기본 예산 비율 (8%)
    crisis_budget_mult: float = 2.0    # 석유 충격 시 예산 배수

    # 정책 효과 지연
    policy_lag:         float = 3.0    # 정책 → 효과 지연 (yr)


# ─────────────────────────────────────────────────────────────────
# 상태 벡터
# ─────────────────────────────────────────────────────────────────

@dataclass
class EnergyMinistryState:
    """에너지부 가변 상태."""

    # 그리드 인프라 수준 [0,1]
    grid_capacity:      float = 0.1    # 현재 재생에너지 그리드 용량

    # 재생에너지 보조금 레벨 [0,1]
    subsidy_level:      float = 0.05   # 현재 보조금 강도

    # 석유 수입 의존도 (PROMETHEUS oil_dependency와 연동)
    oil_import_share:   float = 1.0    # 에너지 믹스 중 석유 비중

    # 에너지부 연간 예산 (절대값)
    budget:             float = 0.0

    # 누적 신호
    grid_investment_cumulative: float = 0.0   # 누적 그리드 투자
    policy_signal:      float = 0.0           # 정책 압력 강도

    # 파라오 칙령 반영
    solar_reform_active: bool = False

    t: float = 0.0


# ─────────────────────────────────────────────────────────────────
# 에너지부 동역학 (v1)
# ─────────────────────────────────────────────────────────────────

class EnergyMinistry:
    """
    KEMET 11번째 부처 — 에너지부.

    v1 원칙:
      - 내부 ODE는 단순하게 (1차 선형 수렴)
      - 연결 인터페이스를 풍부하게
      - 상세 계수는 데이터 수집 후 v2에서 보정
    """

    def __init__(self, params: Optional[EnergyMinistryParams] = None):
        self.params = params or EnergyMinistryParams()
        self.state  = EnergyMinistryState()

    def step(
        self,
        dt: float,
        treasury_budget: float,
        prometheus_out: Optional[object] = None,  # PrometheusOutput 또는 None
        solar_reform_active: bool = False,
    ) -> EnergyMinistryState:
        """
        1 타임스텝 진행.

        Args:
            dt:                  시간 간격 (yr)
            treasury_budget:     KEMET 재무부 전체 예산
            prometheus_out:      PROMETHEUS 출력 신호 (없으면 기본값)
            solar_reform_active: 파라오 칙령 발동 여부
        """
        p = self.params
        s = self.state

        # ── 예산 계산 ──────────────────────────────────────────────
        budget_mult = p.crisis_budget_mult if s.oil_import_share > 0.8 else 1.0
        self.state.budget = treasury_budget * p.budget_share * budget_mult
        budget = self.state.budget

        # ── PROMETHEUS 신호 추출 ────────────────────────────────────
        if prometheus_out is not None:
            g = lambda attr, default: getattr(prometheus_out, attr, default)
            solar_lcoe     = g("solar_lcoe", 40.0)
            oil_dep        = g("oil_dependency", 1.0)
            tipping        = g("flags", {}).get("tipping_point_crossed", False)
            energy_indep   = g("energy_independence", 0.0)
        else:
            solar_lcoe  = 40.0
            oil_dep     = 1.0
            tipping     = False
            energy_indep= 0.0

        self.state.oil_import_share = oil_dep  # PROMETHEUS 동기화

        # ── 칙령 반영 ──────────────────────────────────────────────
        self.state.solar_reform_active = solar_reform_active
        policy_boost = 2.0 if solar_reform_active else 1.0
        policy_boost *= 1.5 if tipping else 1.0  # 티핑 포인트 돌파 시 추가 가속

        # ── 그리드 인프라 ODE: dG/dt = rate×budget×policy − decay×G ──
        # 태양광 LCOE 하락 → 비용 효율 개선 계수
        lcoe_factor = max(0.5, 40.0 / max(1.0, solar_lcoe))  # LCOE 낮을수록 효율↑
        dg = (
            p.grid_build_rate * budget * policy_boost * lcoe_factor
            - p.grid_decay * s.grid_capacity
        ) * dt

        new_grid = max(0.0, min(p.grid_capacity_max, s.grid_capacity + dg))
        self.state.grid_capacity = new_grid
        self.state.grid_investment_cumulative += max(0.0, dg)

        # ── 보조금 조정: 그리드 확장 단계 → 보조금 단계적 감소 ────
        # "그리드 자립 → 보조금 불필요" 원칙
        subsidy_target = max(0.0, 0.3 - new_grid * 0.25)
        ds = (subsidy_target - s.subsidy_level) * p.subsidy_decay * dt
        self.state.subsidy_level = max(0.0, s.subsidy_level + ds)

        # ── 정책 신호 강도 ──────────────────────────────────────────
        # 석유 의존도 + 에너지 독립 부족 → 정책 압력
        self.state.policy_signal = min(1.0,
            oil_dep * 0.5
            + (1.0 - energy_indep) * 0.3
            + (1.0 if s.oil_import_share > 0.7 else 0.0) * 0.2
        )

        self.state.t += dt
        return self.state

    def prometheus_input_signal(self) -> Dict[str, float]:
        """
        에너지부 상태 → PROMETHEUS 입력 신호.
        에너지부 예산이 PROMETHEUS의 정책 가속(policy_push)에 반영된다.
        """
        s = self.state
        return {
            "energy_budget":     s.budget,
            "policy_push":       s.policy_signal,
            "solar_reform":      1.0 if s.solar_reform_active else 0.0,
            "grid_capacity":     s.grid_capacity,
        }

    def kemet_output_signal(self) -> Dict[str, float]:
        """
        에너지부 상태 → KEMET 건설부/재무부 신호.
        """
        return {
            "grid_investment_signal":   self.state.grid_capacity,
            "subsidy_level":           self.state.subsidy_level,
            "energy_cost_reduction":   self.state.grid_capacity * 0.3,  # 그리드 확장 → 비용↓
        }

    def pharaoh_flags(self) -> Dict[str, bool]:
        """파라오가 보는 에너지부 플래그."""
        s = self.state
        return {
            "energy_reform_needed":     s.oil_import_share > 0.7 and not s.solar_reform_active,
            "grid_expansion_opportunity": s.grid_capacity < 0.3 and s.policy_signal > 0.5,
            "solar_tipping_imminent":   s.grid_capacity > 0.4,
            "energy_independent":       s.oil_import_share < 0.2,
        }
