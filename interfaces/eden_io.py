"""
_EDEN_LAYER 입출력 계약 (Contract)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

에덴 4대강 = 모든 엔진 데이터의 최종 집약점.
각 엔진은 해당 강에 "신호를 흘려보낸다".

창세기 2:10-14 강 매핑:
  Pishon  (피손):    자원·에너지·식량·해양 흐름
  Gihon   (기혼):    생명·사회·안정 흐름
  Hiddekel(힛데겔):  지식·정보·법 흐름
  Euphrates(유브라데): 종합 질서·거버넌스 흐름
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EdenRiverReading:
    """한 강(江)의 현재 상태 스냅샷."""
    river_name: str              # "pishon"|"gihon"|"hiddekel"|"euphrates"
    flux:       float = 0.0      # 현재 흐름량 (정규화, 0~1)
    order:      float = 0.5      # 질서 지수 (Shannon 역)
    entropy:    float = 0.5      # 정보 엔트로피
    volume:     float = 0.0      # 누적 데이터 볼륨


@dataclass
class EdenSignal:
    """
    모든 엔진 → _EDEN_LAYER 신호 묶음.

    ATON이 각 엔진 출력을 수집해 EDEN에 일괄 전달한다.
    """

    # ── Pishon강 (자원/에너지/식량/해양) ─────────────────────────
    # 공급: Asher(곡식), Zebulun(해양), PROMETHEUS(에너지)
    pishon_grain_flux:    float = 0.0   # 곡식 흐름 (ton/yr)
    pishon_fish_flux:     float = 0.0   # 어족 수확 흐름
    pishon_energy_flux:   float = 0.0   # 재생에너지 플럭스 (GW·yr)
    pishon_oil_flux:      float = 1.0   # 석유 의존 잔류 흐름 (0=독립)

    # ── Gihon강 (생명/사회/안정) ─────────────────────────────────
    # 공급: Dan(사회 긴장), KEMET 보건부/사법부
    gihon_population:     float = 1000.0  # 인구 수
    gihon_health:         float = 0.7     # 건강 지수
    gihon_stability:      float = 0.8     # 사회 안정도 (1-ST)
    gihon_jubilee_events: int   = 0       # 희년 발동 횟수 (누적)

    # ── Hiddekel강 (지식/정보/법) ─────────────────────────────────
    # 공급: Levi(지식 네트워크), KEMET 교육부/사법부
    hiddekel_knowledge:   float = 50.0  # 지식 자본 K
    hiddekel_law:         float = 0.8   # 법 준수율
    hiddekel_network:     float = 0.0   # 48노드 네트워크 출력
    hiddekel_tech_level:  float = 0.0   # 기술 수준 (PROMETHEUS 학습 곡선)

    # ── Euphrates강 (종합 질서/거버넌스) ─────────────────────────
    # 공급: KEMET Ma'at 점수, ATON Nexus 통합 지수
    euphrates_maat:       float = 0.5   # Ma'at 질서 지수
    euphrates_gdp:        float = 100.0 # GDP
    euphrates_eii:        float = 0.0   # 에너지 독립 지수 (PROMETHEUS)
    euphrates_owe:        float = 1.0   # 석유 무기 효과 (PROMETHEUS)

    # ── 메타 ──────────────────────────────────────────────────────
    t:    float = 0.0   # 시뮬레이션 시간 (yr)
    year: int   = 0     # 정수 연도

    def omega(self) -> float:
        """
        에덴 질서 파라미터 Ω ∈ [0,1].
        Ω → 1: 에덴 상태 (완전 정렬)
        Ω → 0: 혼돈 상태

        4강 균형 가중 평균:
          w_pishon   = 0.25 (자원 충분도)
          w_gihon    = 0.30 (사회 안정)
          w_hiddekel = 0.25 (지식·법 질서)
          w_euphrates= 0.20 (거버넌스)
        """
        # Pishon: 식량+어업+에너지 충분도
        pishon_order = min(1.0,
            0.4 * min(1.0, self.pishon_grain_flux / 5000.0)
            + 0.3 * min(1.0, self.pishon_fish_flux / 50.0)
            + 0.3 * min(1.0, self.pishon_energy_flux / 100.0)
        )
        # Gihon: 사회 안정
        gihon_order = self.gihon_stability * 0.7 + self.gihon_health * 0.3

        # Hiddekel: 지식·법 질서
        hiddekel_order = (
            min(1.0, self.hiddekel_knowledge / 200.0) * 0.5
            + self.hiddekel_law * 0.5
        )
        # Euphrates: 거버넌스 질서
        euphrates_order = (
            self.euphrates_maat * 0.4
            + min(1.0, self.euphrates_eii) * 0.3
            + (1.0 - min(1.0, self.euphrates_owe)) * 0.3  # OWE 낮을수록 좋음
        )

        return (
            0.25 * pishon_order
            + 0.30 * gihon_order
            + 0.25 * hiddekel_order
            + 0.20 * euphrates_order
        )

    def is_eden_state(self) -> bool:
        """Ω > 0.75 → 에덴 상태."""
        return self.omega() > 0.75

    def crisis_rivers(self) -> List[str]:
        """질서 지수 < 0.3인 강 목록 (위기 강)."""
        crisis = []
        if self.gihon_stability < 0.3:
            crisis.append("gihon")
        if self.hiddekel_law < 0.3:
            crisis.append("hiddekel")
        if self.euphrates_maat < 0.3:
            crisis.append("euphrates")
        if self.pishon_grain_flux < 500.0:
            crisis.append("pishon")
        return crisis
