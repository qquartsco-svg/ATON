"""
PROMETHEUS 입출력 계약 (Contract)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROMETHEUS가 다른 엔진에 신호를 보내는 공식 인터페이스.
prometheus_core.PrometheusState 전체를 넘기지 않는다.
필요한 신호만 추출·정규화해서 전달한다.

설계 원칙:
  "경계는 구현이 아닌 계약(contract)으로"
  → PROMETHEUS 내부가 바뀌어도 이 파일만 수정하면 된다.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


# ─────────────────────────────────────────────────────────────────
# PROMETHEUS → 외부  (다른 엔진이 받는 신호)
# ─────────────────────────────────────────────────────────────────

@dataclass
class PrometheusOutput:
    """PROMETHEUS → KEMET / 70_TRIBES / EDEN 신호 묶음."""

    # ── 핵심 지수 ───────────────────────────────────────────────
    oil_dependency:         float = 1.0    # D  ∈ [0,1]  (0=완전 독립)
    renewable_share:        float = 0.0    # R  ∈ [0,1]  (재생에너지 비중)
    oil_weapon_effect:      float = 1.0    # OWE ∈ [0,1] (0=석유 무기 무효)
    energy_independence:    float = 0.0    # EII ∈ [0,1] (1=완전 독립)

    # ── KEMET 재무부로 가는 신호 ─────────────────────────────────
    oil_price_multiplier:   float = 1.0    # 에너지 비용 배수 (1.0=정상, 2.0=오일쇼크)
    energy_subsidy_signal:  float = 0.0    # 재생에너지 투자 수익 신호 (GDP% 기준)

    # ── KEMET 건설부로 가는 신호 ─────────────────────────────────
    solar_lcoe:             float = 40.0   # 태양광 균등화 발전비용 ($/MWh)
    grid_investment_signal: float = 0.0    # 그리드 투자 긴급도 [0,1]

    # ── KEMET 농업부로 가는 신호 ─────────────────────────────────
    carbon_intensity:       float = 1.0    # CO₂ 강도 (비료 에너지 비용 배수)
    fuel_cost_index:        float = 1.0    # 농업 연료 비용 지수

    # ── KEMET 외교부로 가는 신호 ─────────────────────────────────
    petrodollar_stability:  float = 1.0    # 페트로달러 안정도 [0,1]
    # (< 0.25 → D < 25% 달성 → 페트로달러 체계 붕괴)

    # ── EDEN 피손(Pishon)강으로 가는 신호 ───────────────────────
    # 피손강 = 자원·에너지 흐름
    pishon_energy_flux:     float = 0.0    # 재생에너지 플럭스 (GW·yr)
    pishon_oil_withdrawal:  float = 0.0    # 석유 의존도 감소 속도

    # ── 경보 플래그 ──────────────────────────────────────────────
    flags: Dict[str, bool] = field(default_factory=lambda: {
        "oil_shock_active":         False,   # OWE 급등 (0.2 이상 점프)
        "tipping_point_crossed":    False,   # R > 35% 돌파
        "energy_independent":       False,   # EII > 75% 달성
        "petrodollar_collapse_risk":False,   # D < 25% 접근
        "solar_grid_parity":        False,   # 태양광 LCOE < 20$/MWh
    })

    def is_oil_shock(self) -> bool:
        return self.flags.get("oil_shock_active", False)

    def is_energy_independent(self) -> bool:
        return self.energy_independence >= 0.75

    def threat_level(self) -> float:
        """에너지 지정학 위협 수준 [0,1] — KEMET 국방부 연동."""
        return self.oil_weapon_effect * self.oil_dependency


# ─────────────────────────────────────────────────────────────────
# 외부 → PROMETHEUS  (PROMETHEUS가 받는 신호)
# ─────────────────────────────────────────────────────────────────

@dataclass
class PrometheusInput:
    """KEMET / 70_TRIBES → PROMETHEUS 신호 묶음."""

    # ── KEMET 재무부에서 오는 신호 ───────────────────────────────
    energy_budget:          float = 0.0    # 에너지 투자 예산 (GDP 대비 비율)
    gdp_level:              float = 100.0  # GDP 수준 (투자 용량 기준)

    # ── KEMET 교육부(레위)에서 오는 신호 ─────────────────────────
    knowledge_stock:        float = 0.0    # 지식 자본 K (학습 가속)
    levi_spillover:         float = 0.0    # 레위 기술 파급 계수

    # ── KEMET 외교부에서 오는 신호 ───────────────────────────────
    trade_openness:         float = 0.5    # 무역 개방도 → 기술 이전

    # ── KEMET 파라오 칙령에서 오는 신호 ─────────────────────────
    solar_reform_decree:    bool  = False  # 태양광 개혁 칙령 발동 여부
    policy_push:            float = 0.0    # 정책 가속도 (0=현상, 1=최대 가속)

    # ── Dan Engine에서 오는 신호 ─────────────────────────────────
    wealth_concentration:   float = 0.35   # c — 부의 집중도 (에너지 민주화 저항)

    # ── Levi Engine에서 오는 신호 ────────────────────────────────
    tech_learning_boost:    float = 0.0    # Levi knowledge → 에너지 학습 가속


def extract_prometheus_output(pstate: object) -> PrometheusOutput:
    """
    prometheus_core.PrometheusState → PrometheusOutput 추출.

    PrometheusState에 접근할 수 없는 경우(독립 실행 등)를 대비해
    getattr로 안전하게 추출한다.
    """
    g = lambda attr, default: getattr(pstate, attr, default)

    D   = g("oil_dependency",      1.0)
    R   = g("renewable_share",     0.0)
    OWE = g("oil_weapon_effect",   1.0)
    EII = g("energy_independence_index", 0.0)

    # 페트로달러 안정도: D > 0.25 → 1.0, D < 0.25 → 선형 감소
    petro_stability = min(1.0, D / 0.25) if D < 0.25 else 1.0

    # 태양광 LCOE
    solar_lcoe = g("solar_lcoe", 40.0)

    return PrometheusOutput(
        oil_dependency=D,
        renewable_share=R,
        oil_weapon_effect=OWE,
        energy_independence=EII,
        oil_price_multiplier=1.0 + max(0.0, (OWE - 0.3) * 3.0),  # OWE 높을수록 비용 ↑
        energy_subsidy_signal=R * 0.05,                            # 재생 비중 → 보조금 신호
        solar_lcoe=solar_lcoe,
        grid_investment_signal=min(1.0, R * 2.0),                  # R 30% → signal 0.6
        carbon_intensity=1.0 - R * 0.7,                            # 재생↑ → 탄소↓
        fuel_cost_index=0.5 + D * 0.5,                             # D 낮을수록 연료 저렴
        petrodollar_stability=petro_stability,
        pishon_energy_flux=R * g("investment_level", 0.0) * 100.0,
        pishon_oil_withdrawal=max(0.0, -g("_last_d_dot", 0.0)),    # dD/dt 음수=감소
        flags={
            "oil_shock_active":          OWE > 0.7,
            "tipping_point_crossed":     R > 0.35,
            "energy_independent":        EII > 0.75,
            "petrodollar_collapse_risk": D < 0.25,
            "solar_grid_parity":         solar_lcoe < 20.0,
        },
    )
