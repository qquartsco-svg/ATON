"""
70_TRIBES_LAYER 입출력 계약 (Contract)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

v2.0 — 12지파 전체 신호 완성 (Tier 2/3 실제 dataclass 추가)

Tier 1 (완성):  02_levi, 04_dan, 07_asher, 09_zebulun
Tier 2 (완성):  01_reuben, 03_simeon, 06_issachar
Tier 3 (완성):  05_gad, 08_judah, 10_naphtali, 11_joseph, 12_benjamin

각 엔진의 출력을 KEMET / PROMETHEUS / EDEN으로 라우팅하는 계약.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────
# Tier 1 — 완성 엔진 신호
# ─────────────────────────────────────────────────────────────────

@dataclass
class LeviSignal:
    """02_levi_engine → KEMET 교육부 / EDEN Hiddekel강."""
    knowledge_stock:    float = 50.0   # K — 지식 자본
    productivity_bonus: float = 0.028  # Romer spillover 보너스
    network_output:     float = 0.0    # 48노드 네트워크 출력
    law_knowledge_sync: float = 0.0    # Dan Engine 법 준수율 지원
    # EDEN Hiddekel(힛데겔)강: 지식·정보 흐름
    hiddekel_flux:      float = 0.0    # 지식 흐름량


@dataclass
class DanSignal:
    """04_dan_engine → KEMET 사법부 / EDEN Gihon강."""
    wealth_concentration: float = 0.35  # c — 부의 집중도 [0,1]
    law_compliance:       float = 0.8   # L_c — 법 준수율 [0,1]
    social_tension:       float = 0.2   # ST — 사회 긴장도 [0,1]
    minsky_stage:         str   = "hedge"  # "hedge"|"speculative"|"ponzi"
    jubilee_triggered:    bool  = False    # 희년 자동 발동
    # EDEN Gihon(기혼)강: 사회 안정 흐름
    gihon_stability:      float = 0.8   # 사회 안정 지수


@dataclass
class AsherSignal:
    """07_asher_engine → KEMET 농업부 / EDEN Pishon강."""
    grain_stock:     float = 10000.0  # G — 곡식 비축량 (ton)
    food_security:   float = 0.8      # FSI — 식량 안보 지수 [0,1]
    nile_phase:      str   = "평년"    # 나일 위상
    joseph_action:   str   = "유지"    # "비축"|"방출"|"유지"
    # EDEN Pishon(피손)강: 자원·식량 흐름
    pishon_grain_flux: float = 0.0   # 곡식 흐름량 (ton/yr)


@dataclass
class ZebulunSignal:
    """09_zebulun_engine → KEMET 해양수산부 / EDEN Pishon강."""
    fish_stock:      float = 80.0   # S — 어족 자원
    fish_revenue:    float = 0.0    # 어업 수익
    maritime_gdp:    float = 0.0    # 해상 GDP 기여
    fleet_signal:    str   = "MAINTAIN"  # "EXPAND"|"MAINTAIN"|"REDUCE"|"EMERGENCY"
    overfishing_risk: bool = False   # 과잉 어획 경보
    # EDEN Pishon(피손)강: 해양 자원 흐름
    pishon_maritime_flux: float = 0.0  # 해양 자원 흐름량


# ─────────────────────────────────────────────────────────────────
# Tier 2 — 완성 엔진 신호
# ─────────────────────────────────────────────────────────────────

@dataclass
class ReubenSignal:
    """01_reuben_engine → KEMET 보건/인구부."""
    population:     float = 500_000.0  # 인구 (명)
    birth_rate:     float = 0.035      # 출생률 /yr
    death_rate:     float = 0.020      # 사망률 /yr
    growth_rate:    float = 0.015      # 순 성장률 /yr
    # EDEN Gihon강: 인구 생명 흐름
    gihon_population_flux: float = 0.0


@dataclass
class SimeonSignal:
    """03_simeon_engine → KEMET 국방부 / 갓(05) 위협 입력."""
    military_strength: float = 100.0   # 군사력 (단위 병력)
    deterrence:        float = 0.3     # 억지력 [0,1]
    trade_volume:      float = 0.0     # 교역량
    threat_ext:        float = 0.20    # 외부 위협 수준 [0,1]


@dataclass
class IssacharSignal:
    """06_issachar_engine → KEMET 노동부."""
    labor_efficiency:  float = 0.75    # 노동 효율 [0,1]
    seasonal_output:   float = 0.0     # 계절 농업 출력
    project_load:      float = 0.5     # 프로젝트 부하


# ─────────────────────────────────────────────────────────────────
# Tier 3 — 완성 엔진 신호
# ─────────────────────────────────────────────────────────────────

@dataclass
class GadSignal:
    """05_gad_engine → KEMET 국방부 / 납달리(10) war_mode."""
    troops:                float = 3_000.0  # 병력 수
    morale:                float = 0.70     # 사기 [0,1]
    combat_effectiveness:  float = 0.30     # 전투 효율 [0,1]
    battle_status:         str   = "평화"    # "평화"|"경계"|"전쟁"


@dataclass
class JudahSignal:
    """08_judah_engine → KEMET 거버넌스/사법부."""
    authority:       float = 0.50     # 권위 [0,1]
    legitimacy:      float = 0.50     # 정통성 [0,1]
    cohesion:        float = 0.50     # 결속력 [0,1]
    leadership_index: float = 0.50    # 리더십 지수 [0,1]
    royal_status:    str   = "왕권 불안"  # "왕권 확립"|"왕권 불안"|"왕권 위기"


@dataclass
class NaphtaliSignal:
    """10_naphtali_engine → KEMET 외교통상부."""
    alliance:          float = 0.30    # 동맹 강도 [0,1]
    routes:            float = 2.0     # 무역로 수
    influence:         float = 0.30    # 외교 영향력 [0,1]
    diplomatic_status: str   = "중립"   # "고립"|"중립"|"동맹"|"주도"


@dataclass
class JosephSignal:
    """11_joseph_engine → KEMET 재무부 / 베냐민(12) 정보 입력."""
    gdp:          float = 1_000.0   # GDP (경제 산출량)
    inflation:    float = 2.0       # 인플레이션 (%/yr)
    debt_ratio:   float = 0.30      # 부채 비율
    minsky_stage: str   = "hedge"   # "hedge"|"speculative"|"ponzi"
    money_supply: float = 500.0     # 통화량


@dataclass
class BenjaminSignal:
    """12_benjamin_engine → KEMET 정보/통신 시스템."""
    information:     float = 10.0   # 정보 축적량
    connectivity:    float = 0.50   # 연결성 [0,1]
    signal_fidelity: float = 0.70   # 신호 충실도 [0,1]
    amplification:   float = 1.20   # 증폭 계수


# ─────────────────────────────────────────────────────────────────
# TribesSignal — 12지파 통합 신호 묶음
# ─────────────────────────────────────────────────────────────────

@dataclass
class TribesSignal:
    """
    70_TRIBES_LAYER 전체 신호 묶음 (v2.0 — 12지파 완성).

    Tier 1 (완성):  levi, dan, asher, zebulun
    Tier 2 (완성):  reuben, simeon, issachar
    Tier 3 (완성):  gad, judah, naphtali, joseph, benjamin
    """
    # ── Tier 1 완성 ──────────────────────────────────────────────
    levi:    LeviSignal    = field(default_factory=LeviSignal)
    dan:     DanSignal     = field(default_factory=DanSignal)
    asher:   AsherSignal   = field(default_factory=AsherSignal)
    zebulun: ZebulunSignal = field(default_factory=ZebulunSignal)

    # ── Tier 2 완성 ──────────────────────────────────────────────
    reuben:   Optional[ReubenSignal]   = None
    simeon:   Optional[SimeonSignal]   = None
    issachar: Optional[IssacharSignal] = None

    # ── Tier 3 완성 ──────────────────────────────────────────────
    gad:      Optional[GadSignal]      = None
    judah:    Optional[JudahSignal]    = None
    naphtali: Optional[NaphtaliSignal] = None
    joseph:   Optional[JosephSignal]   = None
    benjamin: Optional[BenjaminSignal] = None

    def tier1_complete(self) -> bool:
        """Tier 1 4개 엔진 모두 기본값 이상인지 확인."""
        return (
            self.levi.knowledge_stock > 0
            and self.dan.law_compliance > 0
            and self.asher.grain_stock > 0
            and self.zebulun.fish_stock > 0
        )

    def active_count(self) -> int:
        """활성화된 지파 엔진 수 (None이 아닌 것 포함, Tier 1 항상 4개)."""
        optional_fields = [
            self.reuben, self.simeon, self.issachar,
            self.gad, self.judah, self.naphtali, self.joseph, self.benjamin,
        ]
        return 4 + sum(1 for f in optional_fields if f is not None)

    def all_active(self) -> bool:
        """12지파 전체 활성화 여부."""
        return self.active_count() == 12
