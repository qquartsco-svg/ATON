"""
KEMET 입출력 계약 (Contract)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEMET이 다른 엔진으로부터 받고, 다른 엔진에 내보내는 공식 인터페이스.
10개 부처 전체 상태를 외부에 노출하지 않고,
"엔진 간 흐름"에 필요한 신호만 추출·정규화한다.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────
# KEMET → 외부  (다른 엔진이 KEMET에서 받는 신호)
# ─────────────────────────────────────────────────────────────────

@dataclass
class KemetOutput:
    """KEMET → PROMETHEUS / 70_TRIBES / EDEN 신호 묶음."""

    t: float = 0.0  # 시뮬레이션 시간 (yr)

    # ── PROMETHEUS로 가는 신호 ────────────────────────────────────
    energy_investment_budget: float = 0.0  # 에너지 투자 예산 (절대값)
    education_budget:         float = 0.0  # 교육 예산 → 기술 학습 가속
    gdp:                      float = 100.0
    foreign_openness:         float = 0.5  # 외교 동맹 → 기술 이전
    solar_reform_active:      bool  = False  # 파라오 칙령 "solar_reform"

    # ── EDEN Euphrates(유브라데)강으로 가는 신호 ──────────────────
    # 유브라데 = 종합·질서 흐름 (KEMET 전체 건전성)
    maat_score:               float = 0.5  # Ma'at 질서 지수 [0,1]
    social_tension:           float = 0.2  # 사회 긴장도 [0,1]
    law_compliance:           float = 0.8  # 법 준수율 [0,1]

    # ── EDEN Gihon(기혼)강으로 가는 신호 ─────────────────────────
    # 기혼강 = 생명/사회 흐름
    population:               float = 1000.0  # 인구 (천 명)
    health_index:             float = 0.7     # 건강 지수 [0,1]
    food_security:            float = 0.8     # 식량 안보 지수 [0,1]

    # ── Dan Engine으로 가는 신호 ─────────────────────────────────
    justice_budget:           float = 0.0   # 사법 예산
    jubilee_decree_active:    bool  = False  # 희년 칙령 발동 여부

    # ── Levi Engine으로 가는 신호 ────────────────────────────────
    education_budget_signal:  float = 0.0   # 교육 예산 신호

    # ── 경보 플래그 ──────────────────────────────────────────────
    flags: Dict[str, bool] = field(default_factory=lambda: {
        "treasury_crisis":     False,  # 국고 마이너스
        "food_crisis":         False,  # 식량 안보 < 0.3
        "social_unrest":       False,  # 사회 긴장 > 0.7
        "minsky_ponzi":        False,  # 민스키 폰지 단계
        "war_mode":            False,  # 전쟁 중
        "epidemic":            False,  # 전염병
    })

    def needs_energy_reform(self) -> bool:
        """에너지 개혁 필요 여부 — 국고 위기 + 석유 의존."""
        return self.flags.get("treasury_crisis", False)

    def is_stable(self) -> bool:
        return (
            not self.flags.get("food_crisis", False)
            and not self.flags.get("social_unrest", False)
            and not self.flags.get("treasury_crisis", False)
        )


# ─────────────────────────────────────────────────────────────────
# 외부 → KEMET  (KEMET이 받는 신호)
# ─────────────────────────────────────────────────────────────────

@dataclass
class KemetInput:
    """PROMETHEUS / 70_TRIBES / EDEN → KEMET 신호 묶음."""

    # ── PROMETHEUS에서 오는 신호 (에너지 충격) ────────────────────
    oil_price_multiplier:   float = 1.0    # 에너지 비용 배수
    energy_independence:    float = 0.0    # EII → 재무부 비용 절감
    solar_lcoe:             float = 40.0   # 건설부 그리드 투자 신호
    carbon_intensity:       float = 1.0    # 농업부 비료 에너지 비용
    oil_shock_active:       bool  = False  # 충격 경보
    tipping_point:          bool  = False  # 재생에너지 티핑 포인트 도달

    # ── Asher(아셀) Engine에서 오는 신호 ─────────────────────────
    grain_stock:            float = 10000.0  # 곡식 비축량
    food_security:          float = 0.8      # 식량 안보 지수
    nile_phase:             str   = "평년"    # 나일 위상

    # ── Zebulun(스불론) Engine에서 오는 신호 ──────────────────────
    fish_revenue:           float = 0.0   # 어업 수익
    maritime_gdp:           float = 0.0   # 해상 GDP 기여
    fleet_signal:           str   = "MAINTAIN"  # 함대 신호

    # ── Dan(단) Engine에서 오는 신호 ─────────────────────────────
    wealth_concentration:   float = 0.35  # c — 부의 집중도
    jubilee_triggered:      bool  = False  # 희년 자동 발동 여부
    social_tension_signal:  float = 0.2   # Dan이 계산한 사회 긴장도
    minsky_stage:           str   = "hedge"  # 민스키 단계

    # ── Levi(레위) Engine에서 오는 신호 ──────────────────────────
    knowledge_stock:        float = 50.0  # 지식 자본 K
    productivity_bonus:     float = 0.0   # 생산성 향상 보너스
    network_output:         float = 0.0   # 48노드 네트워크 출력

    # ── 외부 충격 (테스트/시나리오용) ────────────────────────────
    external_threat:        float = 0.0   # 외부 군사 위협 [0,1]
    epidemic_signal:        bool  = False  # 전염병 발생 신호


def extract_kemet_output(kstate: object, maat_fn=None) -> KemetOutput:
    """
    kemet_core.KemetMutable → KemetOutput 추출.

    maat_fn: Ma'at 점수 계산 함수 (없으면 0.5 기본값)
    """
    g = lambda attr, default: getattr(kstate, attr, default)

    maat = maat_fn(kstate) if maat_fn else 0.5

    return KemetOutput(
        t=g("t", 0.0),
        energy_investment_budget=g("treasury_balance", 0.0) * 0.05,  # 5% 에너지 할당
        education_budget=g("education_budget", 0.0),
        gdp=g("gdp", 100.0),
        foreign_openness=g("alliance_strength", 0.5),
        solar_reform_active=g("solar_reform_active", False),
        maat_score=maat,
        social_tension=g("social_tension", 0.2),
        law_compliance=g("law_compliance", 0.8),
        population=g("population", 1000.0),
        health_index=g("health_index", 0.7),
        food_security=g("food_security", 0.8),
        justice_budget=g("justice_budget", 0.0),
        jubilee_decree_active=g("jubilee_decree_active", False),
        education_budget_signal=g("education_budget", 0.0),
        flags={
            "treasury_crisis":  g("treasury_balance", 1.0) < 0,
            "food_crisis":      g("food_security", 1.0) < 0.3,
            "social_unrest":    g("social_tension", 0.0) > 0.7,
            "minsky_ponzi":     g("minsky_stage", "hedge") == "ponzi",
            "war_mode":         g("war_mode", False),
            "epidemic":         g("health_index", 1.0) < 0.4,
        },
    )
