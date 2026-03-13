"""
모네타 브릿지 (Moneta Bridge)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

에너지 가격 ↔ 화폐/인플레이션 연결.

PROMETHEUS의 에너지 충격이 MONETA/KEMET 재무부의
인플레이션·금리·통화량에 어떻게 전파되는가를 정의한다.

핵심 채널:
  1. 에너지 비용 → 생산자 물가 → 소비자 물가 (Passthrough)
     π_energy = β_pass × Δoil_price / oil_price

  2. 페트로달러 흐름 → 통화량 (Petrodollar Channel)
     ΔM ∝ oil_trade_balance (산유국 달러 recycling)

  3. 에너지 전환 비용 → 재정 압박 → 금리 상승
     r = r_natural + α(π-π*) + β(Y-Y*) + γ×transition_cost   [Taylor Rule 확장]

v1 원칙:
  - 정교한 DSGE가 아니라 "올바른 연결 방향"을 먼저 확립
  - 계수는 단순 선형 추정 (v2에서 실증 데이터로 보정)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EnergyMonetaSignal:
    """
    에너지 ↔ 화폐 신호 묶음.
    PROMETHEUS 출력 → MONETA/KEMET 재무부 입력으로 변환.
    """

    # ── 인플레이션 채널 ──────────────────────────────────────────
    energy_inflation_add:   float = 0.0   # 에너지 비용이 추가하는 인플레이션 (%/yr)
    # (양수 = 인플레이션 압력, 음수 = 에너지 전환으로 디플레이션 압력)

    # ── 통화량 채널 ───────────────────────────────────────────────
    petrodollar_flow:       float = 0.0   # 페트로달러 유입/유출 (GDP 대비 %)
    # (양수 = 유입 = 통화량 확장, 음수 = 페트로달러 체계 약화)

    # ── 금리 채널 ─────────────────────────────────────────────────
    taylor_energy_term:     float = 0.0   # Taylor Rule에 추가되는 에너지 항

    # ── 성장 채널 ─────────────────────────────────────────────────
    gdp_energy_drag:        float = 0.0   # 에너지 비용이 GDP 성장에 미치는 저항 (%/yr)
    gdp_green_bonus:        float = 0.0   # 에너지 전환이 장기 GDP에 주는 보너스 (%/yr)

    # ── 재정 채널 ─────────────────────────────────────────────────
    fiscal_transition_cost: float = 0.0   # 에너지 전환 재정 비용 (GDP 대비 %)
    import_bill_change:     float = 0.0   # 석유 수입 비용 변화 (양수 = 비용 증가)

    # ── 종합 신호 ─────────────────────────────────────────────────
    net_monetary_pressure:  float = 0.0   # 종합 화폐 압력 (양수 = 긴축)

    def is_inflationary_shock(self) -> bool:
        return self.energy_inflation_add > 2.0  # 2%/yr 초과

    def is_deflationary_transition(self) -> bool:
        return self.energy_inflation_add < -1.0  # 에너지 전환이 디플레이션


class MonetaBridge:
    """
    PROMETHEUS ↔ MONETA 연결 브릿지.

    에너지 전환 상태를 화폐·재정 신호로 변환한다.
    """

    # 에너지 가격 → 인플레이션 passthrough 계수
    # (실증: 유가 10% 상승 → 소비자 물가 0.2~0.5% 상승)
    ENERGY_INFLATION_PASSTHROUGH: float = 0.03

    # 페트로달러 재순환: 전 세계 석유 무역의 약 60%가 달러
    PETRODOLLAR_RECYCLE_RATE: float = 0.60

    # 에너지 전환 재정 비용 (GDP 대비, 2030년 NDC 달성 추정)
    TRANSITION_COST_GDP_SHARE: float = 0.025  # 2.5%/yr

    def compute(
        self,
        oil_price_multiplier: float,
        oil_dependency:       float,
        renewable_share:      float,
        energy_independence:  float,
        solar_lcoe:           float,
        gdp:                  float,
        current_inflation:    float = 2.0,
        inflation_target:     float = 2.0,
    ) -> EnergyMonetaSignal:
        """
        에너지 상태 → 화폐 신호 계산.

        Args:
            oil_price_multiplier:  에너지 비용 배수 (1.0=정상)
            oil_dependency:        석유 의존도 D [0,1]
            renewable_share:       재생에너지 비중 R [0,1]
            energy_independence:   에너지 독립지수 EII [0,1]
            solar_lcoe:            태양광 LCOE ($/MWh)
            gdp:                   현재 GDP
            current_inflation:     현재 인플레이션 (%/yr)
            inflation_target:      인플레이션 목표 (%/yr)
        """
        # ── 1. 에너지 인플레이션 채널 ────────────────────────────────
        # 오일쇼크 → 생산 비용 상승 → CPI 상승
        oil_price_change = oil_price_multiplier - 1.0  # 가격 변화율
        inflation_from_energy = (
            oil_price_change
            * oil_dependency          # 의존도 높을수록 충격 크게 받음
            * self.ENERGY_INFLATION_PASSTHROUGH
            * 100.0                   # → %/yr
        )
        # 재생에너지 확대 → 장기 디플레이션 효과 (Wright's Law: LCOE 하락)
        green_deflation = -max(0.0, (40.0 - solar_lcoe) / 40.0) * 0.5 * renewable_share

        energy_inflation_add = inflation_from_energy + green_deflation

        # ── 2. 페트로달러 채널 ────────────────────────────────────────
        # D 감소 → 석유 달러 수요 감소 → 달러 유동성 공급 감소
        # (산유국이 달러를 덜 벌면 글로벌 달러 유동성 수축)
        petrodollar_flow = (
            (oil_dependency - 0.5)     # D=0.5 기준
            * self.PETRODOLLAR_RECYCLE_RATE
            * 5.0                      # 크기 조정
        )

        # ── 3. 재정 채널 ─────────────────────────────────────────────
        # 에너지 전환 투자 → 단기 재정 비용
        transition_phase = max(0.0, renewable_share * (1.0 - renewable_share) * 4.0)
        # (R=0.5일 때 최대, 전환 중간 단계가 가장 비쌈)
        fiscal_cost = transition_phase * self.TRANSITION_COST_GDP_SHARE * 100.0

        # 석유 수입 비용: D × 유가 배수 × GDP 비율
        import_bill = oil_dependency * oil_price_multiplier * 0.05 * gdp  # GDP의 5% 기준
        import_bill_change = import_bill - (oil_dependency * 1.0 * 0.05 * gdp)  # 정상 대비 변화

        # ── 4. GDP 채널 ───────────────────────────────────────────────
        # 단기: 에너지 비용 상승 → GDP 성장 저항
        gdp_drag = -(oil_price_change * oil_dependency * 0.3)  # %/yr
        # 장기: 에너지 독립 달성 → 구조적 성장 보너스
        gdp_green_bonus = energy_independence * 0.5  # 독립 달성 시 최대 +0.5%/yr

        # ── 5. Taylor Rule 에너지 항 ─────────────────────────────────
        # r = r* + α(π-π*) + β(Y-Y*) + γ×energy_pressure
        energy_pressure = oil_price_change * oil_dependency
        taylor_energy = 0.15 * energy_pressure  # γ=0.15

        # ── 6. 종합 ───────────────────────────────────────────────────
        net_pressure = (
            energy_inflation_add * 0.4
            + taylor_energy * 0.3
            + (fiscal_cost / 100.0) * 0.3
        )

        return EnergyMonetaSignal(
            energy_inflation_add=energy_inflation_add,
            petrodollar_flow=petrodollar_flow,
            taylor_energy_term=taylor_energy,
            gdp_energy_drag=gdp_drag,
            gdp_green_bonus=gdp_green_bonus,
            fiscal_transition_cost=fiscal_cost,
            import_bill_change=import_bill_change,
            net_monetary_pressure=net_pressure,
        )

    def apply_to_kemet_treasury(
        self,
        signal: EnergyMonetaSignal,
        current_inflation: float,
        gdp: float,
    ) -> Dict[str, float]:
        """
        EnergyMonetaSignal → KEMET 재무부 조정값.

        반환: {"inflation_adjustment", "gdp_growth_adj", "spending_pressure"}
        """
        return {
            "inflation_adjustment": signal.energy_inflation_add,
            "gdp_growth_adj":       signal.gdp_energy_drag + signal.gdp_green_bonus,
            "spending_pressure":    signal.fiscal_transition_cost / 100.0 * gdp,
            "petrodollar_flow":     signal.petrodollar_flow,
        }
