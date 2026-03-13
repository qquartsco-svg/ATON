"""
석유 충격 라우터 (Oil Shock Router)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROMETHEUS가 감지한 석유 충격을
KEMET 각 부처와 70_TRIBES 엔진들로 자동 라우팅한다.

설계:
  "충격은 물처럼 흐른다. 막으려 하지 말고 흐름을 설계하라."

  OWE(t-1) vs OWE(t) 비교 → 급등 감지 → 각 엔진별 대응 신호 생성

충격 전파 경로:
  OIL_SHOCK ──→ 재무부: 비용 상승 → 예산 재배분
              ──→ 농업부: 연료 비용 상승 → 효율 하락
              ──→ 건설부: 건설 비용 상승 → 인프라 투자 감속
              ──→ 해양수산부: 어선 연료 비용 → 수익 하락
              ──→ 국방부: 에너지 확보 비용
              ──→ 파라오: 경보 플래그 → 칙령 검토
              ──→ Dan Engine: 부의 집중도 상승 압력
              ──→ Zebulun Engine: 어업 비용 상승
              ──→ EDEN Pishon강: 충격 이벤트 기록
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class OilShockEvent:
    """
    단일 석유 충격 이벤트.
    PROMETHEUS가 감지 → OilShockRouter가 생성 → 각 엔진에 전달.
    """
    t:              float          # 발생 시점 (yr)
    owe_before:     float          # 충격 전 OWE
    owe_after:      float          # 충격 후 OWE
    delta_owe:      float          # 변화량 (양수 = 악화)
    severity:       str            # "minor"|"moderate"|"severe"|"catastrophic"
    origin:         str = "oil"    # "oil"|"petrodollar"|"opec_cutoff"

    # 각 부처별 충격 계수 (0=무영향, 1=최대)
    treasury_impact:     float = 0.0
    agriculture_impact:  float = 0.0
    construction_impact: float = 0.0
    maritime_impact:     float = 0.0
    defense_impact:      float = 0.0

    def is_severe(self) -> bool:
        return self.severity in ("severe", "catastrophic")

    @classmethod
    def classify(cls, delta_owe: float) -> str:
        if delta_owe < 0.05:  return "minor"
        if delta_owe < 0.15:  return "moderate"
        if delta_owe < 0.30:  return "severe"
        return "catastrophic"


class OilShockRouter:
    """
    석유 충격 탐지 및 라우팅 엔진.

    사용법:
      router = OilShockRouter()
      # 매 스텝마다:
      event = router.detect(t=1.0, owe_before=0.5, owe_after=0.7)
      if event:
          kemet_adj  = router.kemet_adjustments(event)
          tribes_adj = router.tribes_adjustments(event)
    """

    # 충격 감지 임계값
    SHOCK_THRESHOLD:        float = 0.05   # dOWE > 5% → 충격 감지
    SEVERE_THRESHOLD:       float = 0.20   # dOWE > 20% → 심각
    CATASTROPHIC_THRESHOLD: float = 0.35   # dOWE > 35% → 재앙

    def __init__(self):
        self.history: List[OilShockEvent] = []
        self._prev_owe: Optional[float] = None

    def detect(
        self,
        t: float,
        owe_before: float,
        owe_after: float,
    ) -> Optional[OilShockEvent]:
        """
        OWE 변화 감지 → 충격 이벤트 생성.
        delta_owe > SHOCK_THRESHOLD 이면 이벤트 반환, 아니면 None.
        """
        delta = owe_after - owe_before

        if delta < self.SHOCK_THRESHOLD:
            return None  # 충격 없음

        severity = OilShockEvent.classify(delta)

        event = OilShockEvent(
            t=t,
            owe_before=owe_before,
            owe_after=owe_after,
            delta_owe=delta,
            severity=severity,
            treasury_impact=min(1.0, delta * 3.0),
            agriculture_impact=min(1.0, delta * 2.0),
            construction_impact=min(1.0, delta * 1.5),
            maritime_impact=min(1.0, delta * 2.5),
            defense_impact=min(1.0, delta * 1.0),
        )
        self.history.append(event)
        return event

    def kemet_adjustments(self, event: OilShockEvent) -> Dict[str, float]:
        """
        OilShockEvent → KEMET 각 부처별 조정 계수.

        반환값: {"부처": 조정 계수, ...}
        조정 계수 < 1.0 → 예산 효율 하락 (비용 상승)
        조정 계수 > 1.0 → 효율 상승 (충격이 역설적으로 개혁 촉진)
        """
        d = event.delta_owe

        return {
            # 충격 크기에 비례해 효율 저하
            "treasury_efficiency":    max(0.5, 1.0 - event.treasury_impact * 0.3),
            "agriculture_efficiency": max(0.6, 1.0 - event.agriculture_impact * 0.25),
            "construction_efficiency":max(0.7, 1.0 - event.construction_impact * 0.2),
            "maritime_efficiency":    max(0.5, 1.0 - event.maritime_impact * 0.3),
            "defense_priority":       min(1.5, 1.0 + event.defense_impact * 0.5),  # 국방 예산 우선↑
            # 역설: 충격이 에너지 개혁 압력을 높임
            "energy_reform_pressure": min(1.0, d * 2.0),
            # 파라오 경보 강도
            "pharaoh_alert_level":   event.delta_owe,
        }

    def tribes_adjustments(self, event: OilShockEvent) -> Dict[str, float]:
        """
        OilShockEvent → 70_TRIBES 각 엔진별 조정 계수.
        """
        return {
            # Zebulun: 어선 연료 비용 상승 → 수익 하락
            "zebulun_fuel_cost_multiplier": 1.0 + event.maritime_impact * 0.5,
            # Dan: 에너지 가격 상승 → 부의 집중도 악화 압력
            "dan_concentration_pressure": event.treasury_impact * 0.3,
            # Asher: 농업 연료 비용 → 효율 하락
            "asher_efficiency_penalty": event.agriculture_impact * 0.2,
            # Levi: 에너지 비용 → 교육 예산 압박 (간접)
            "levi_budget_pressure": event.treasury_impact * 0.15,
        }

    def eden_record(self, event: OilShockEvent) -> Dict[str, float]:
        """
        OilShockEvent → EDEN Pishon강 기록.
        석유 충격은 자원 흐름의 단절이므로 Pishon강에 기록한다.
        """
        return {
            "pishon_disruption":  event.delta_owe,  # 흐름 교란 강도
            "pishon_oil_shock_t": event.t,           # 충격 발생 시점
            "severity_code":      ["minor","moderate","severe","catastrophic"]
                                  .index(event.severity),
        }

    def total_shocks(self) -> int:
        return len(self.history)

    def cumulative_impact(self) -> float:
        """누적 충격량 (모든 이벤트의 delta_owe 합계)."""
        return sum(e.delta_owe for e in self.history)

    def recovery_signal(self, current_owe: float) -> float:
        """
        현재 OWE가 마지막 충격 이후 회복된 비율 [0,1].
        0 = 여전히 충격 상태
        1 = 완전 회복
        """
        if not self.history:
            return 1.0  # 충격 없음 = 완전 정상
        last = self.history[-1]
        if current_owe >= last.owe_after:
            return 0.0  # 아직 최악 또는 더 악화
        if current_owe <= last.owe_before:
            return 1.0  # 완전 회복
        # 선형 보간
        return 1.0 - (current_owe - last.owe_before) / (last.owe_after - last.owe_before)
