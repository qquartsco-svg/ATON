"""
_ATON_LAYER — run_aton.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLI 실행기.

사용법:
  python run_aton.py                    # 기본 50년 시뮬레이션
  python run_aton.py --years 100        # 100년 시뮬레이션
  python run_aton.py --scenario eden    # 에덴 달성 시나리오
  python run_aton.py --scenario shock   # 석유 충격 시나리오
  python run_aton.py --scenario jubilee # 희년 + 에너지 전환 시나리오
  python run_aton.py --report           # 최종 상태 상세 리포트
  python run_aton.py --coherence        # Nexus 정합성 그래프
"""

from __future__ import annotations

import argparse
import math
import sys
import os

# 경로 설정
_dir = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_dir)
if _parent not in sys.path:
    sys.path.insert(0, _parent)
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from aton_core import NexusConfig
from nexus import Nexus


# ─────────────────────────────────────────────────────────────────
# 시나리오 정의
# ─────────────────────────────────────────────────────────────────

def scenario_baseline(years: int = 50):
    """기본 시나리오: 자연 동역학."""
    nexus = Nexus(config=NexusConfig(t_end=years))
    return nexus.simulate(years=years)


def scenario_eden(years: int = 50):
    """에덴 시나리오: 적극적 에너지 전환 + 교육 투자."""
    nexus = Nexus(config=NexusConfig(t_end=years))
    # 매 5년마다 solar_reform + policy_push
    ext_seq = {
        float(t): {"solar_reform": True, "policy_push": 0.8}
        for t in range(0, years, 5)
    }
    return nexus.simulate(years=years, external_sequence=ext_seq)


def scenario_oil_shock(years: int = 50):
    """석유 충격 시나리오: 10년에 갑작스러운 OWE 급등."""
    nexus = Nexus(config=NexusConfig(t_end=years))
    ext_seq = {
        10.0: {"oil_shock_multiplier": 3.0, "external_threat": 0.6},
        11.0: {"oil_shock_multiplier": 3.0},
        12.0: {"solar_reform": True, "policy_push": 1.0},  # 충격 → 개혁
    }
    return nexus.simulate(years=years, external_sequence=ext_seq)


def scenario_jubilee(years: int = 50):
    """희년 + 에너지 전환 동시 시나리오."""
    nexus = Nexus(config=NexusConfig(t_end=years))
    ext_seq = {
        0.0:  {"solar_reform": True},
        25.0: {"jubilee": True, "policy_push": 0.7},  # 중간 지점 희년
        50.0: {"jubilee": True},
    }
    return nexus.simulate(years=years, external_sequence=ext_seq)


# ─────────────────────────────────────────────────────────────────
# 출력 함수
# ─────────────────────────────────────────────────────────────────

def print_timeline(history, interval: int = 10):
    """주요 시점의 핵심 지표 출력."""
    print("\n" + "="*70)
    print(" ATON NEXUS — 시뮬레이션 결과")
    print("="*70)
    print(f"{'t':>5}  {'Ω':>6}  {'D':>5}  {'R':>5}  {'OWE':>5}  "
          f"{'Maat':>6}  {'K':>6}  {'c':>5}  플래그")
    print("-"*70)

    for state in history:
        if state.t % interval != 0:
            continue

        p = state.prometheus
        k = state.kemet
        t = state.tribes

        D   = f"{p.oil_dependency:.2f}"   if p else "  -  "
        R   = f"{p.renewable_share:.2f}"  if p else "  -  "
        OWE = f"{p.oil_weapon_effect:.2f}"if p else "  -  "
        maat= f"{k.maat_score:.3f}"       if k else "  -  "
        K   = f"{t.levi.knowledge_stock:.0f}" if t else "  -  "
        c   = f"{t.dan.wealth_concentration:.2f}" if t else "  -  "

        active = [fl for fl, v in state.system_flags.items() if v]
        flag_str = ", ".join(active[:3]) + ("..." if len(active) > 3 else "")

        print(f"{state.t:>5.0f}  {state.nexus_coherence:>6.3f}  "
              f"{D:>5}  {R:>5}  {OWE:>5}  {maat:>6}  {K:>6}  {c:>5}  {flag_str}")

    print("="*70)


def print_detailed_report(final_state):
    """최종 상태 상세 리포트."""
    print("\n" + "="*70)
    print(" ATON NEXUS — 최종 상태 상세 리포트")
    print("="*70)

    nexus = Nexus()
    nexus.report(final_state)

    if final_state.prometheus:
        p = final_state.prometheus
        print("── 에너지 지정학 ──────────────────────────────────────")
        print(f"  석유 의존도(D):      {p.oil_dependency:.4f}")
        print(f"  재생 비중(R):        {p.renewable_share:.4f}")
        print(f"  석유 무기 효과(OWE): {p.oil_weapon_effect:.4f}")
        print(f"  에너지 독립지수(EII):{p.energy_independence:.4f}")
        print(f"  페트로달러 안정도:   {p.petrodollar_stability:.4f}")
        if p.is_energy_independent():
            print("  ✅ 에너지 독립 달성!")
        if p.is_oil_shock():
            print("  ⚠️  석유 충격 진행 중!")

    if final_state.tribes:
        t = final_state.tribes
        print("\n── 70_TRIBES 상태 ─────────────────────────────────────")
        print(f"  [레위] 지식 자본: {t.levi.knowledge_stock:.1f}  "
              f"생산성 보너스: {t.levi.productivity_bonus:.3f}")
        print(f"  [단]   집중도: {t.dan.wealth_concentration:.3f}  "
              f"({t.dan.minsky_stage})  긴장도: {t.dan.social_tension:.3f}")
        print(f"  [아셀] 곡식: {t.asher.grain_stock:.0f}t  "
              f"식량안보: {t.asher.food_security:.3f}")
        print(f"  [스불론] 어족: {t.zebulun.fish_stock:.1f}  "
              f"수익: {t.zebulun.fish_revenue:.1f}  신호: {t.zebulun.fleet_signal}")
        print(f"  활성 지파 엔진: {t.active_count()}/12")

    if final_state.energy_ministry:
        em = final_state.energy_ministry
        print("\n── 에너지부 (11번째 부처) ──────────────────────────────")
        print(f"  그리드 용량:  {em.grid_capacity:.4f}")
        print(f"  보조금 수준:  {em.subsidy_level:.4f}")
        print(f"  석유 비중:    {em.oil_import_share:.4f}")
        print(f"  정책 압력:    {em.policy_signal:.4f}")
        print(f"  누적 투자:    {em.grid_investment_cumulative:.2f}")

    if final_state.eden:
        e = final_state.eden
        print("\n── EDEN 4대강 ─────────────────────────────────────────")
        print(f"  Pishon  (자원): 곡식={e.pishon_grain_flux:.1f}  "
              f"석유잔류={e.pishon_oil_flux:.3f}")
        print(f"  Gihon   (생명): 인구={e.gihon_population:.0f}  "
              f"안정={e.gihon_stability:.3f}")
        print(f"  Hiddekel(지식): K={e.hiddekel_knowledge:.1f}  "
              f"법준수={e.hiddekel_law:.3f}")
        print(f"  Euphrates(질서): Ma'at={e.euphrates_maat:.3f}  "
              f"EII={e.euphrates_eii:.3f}")
        print(f"  Ω (에덴 질서 지수): {e.omega():.4f}")
        if e.is_eden_state():
            print("  ✨ 에덴 상태 달성! (Ω > 0.75)")
        crisis = e.crisis_rivers()
        if crisis:
            print(f"  ⚠️  위기 강: {', '.join(crisis)}")

    print("\n" + "="*70)


def print_coherence_chart(history):
    """Nexus 정합성 Ω 시계열 텍스트 차트."""
    print("\n── Nexus 정합성 Ω 궤적 ──")
    max_width = 40
    for state in history:
        if int(state.t) % 5 != 0:
            continue
        bar_len = int(state.nexus_coherence * max_width)
        bar = "█" * bar_len + "░" * (max_width - bar_len)
        flags = "⚡" if state.system_flags.get("energy_tipping_point") else "  "
        eden  = "🌿" if state.system_flags.get("eden_state") else "  "
        print(f"  {state.t:>4.0f}yr │{bar}│ {state.nexus_coherence:.3f} {flags}{eden}")
    print()


# ─────────────────────────────────────────────────────────────────
# CLI 메인
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="_ATON_LAYER 통합 시뮬레이션 실행기"
    )
    parser.add_argument(
        "--scenario",
        choices=["baseline", "eden", "shock", "jubilee"],
        default="baseline",
        help="시뮬레이션 시나리오",
    )
    parser.add_argument("--years", type=int, default=50, help="시뮬레이션 기간 (yr)")
    parser.add_argument("--report", action="store_true", help="최종 상태 상세 리포트")
    parser.add_argument("--coherence", action="store_true", help="정합성 궤적 출력")
    parser.add_argument("--interval", type=int, default=10, help="출력 간격 (yr)")
    args = parser.parse_args()

    # 시나리오 실행
    scenarios = {
        "baseline": scenario_baseline,
        "eden":     scenario_eden,
        "shock":    scenario_oil_shock,
        "jubilee":  scenario_jubilee,
    }
    print(f"\n▶ 시나리오: {args.scenario} | 기간: {args.years}yr")
    history = scenarios[args.scenario](args.years)

    # 출력
    print_timeline(history, interval=args.interval)

    if args.coherence:
        print_coherence_chart(history)

    if args.report:
        print_detailed_report(history[-1])

    # 요약
    final = history[-1]
    print(f"\n총 {len(history)} 스텝 완료.")
    print(f"최종 Ω = {final.nexus_coherence:.4f}")
    if final.prometheus:
        print(f"최종 D = {final.prometheus.oil_dependency:.4f}  "
              f"R = {final.prometheus.renewable_share:.4f}")


if __name__ == "__main__":
    main()
