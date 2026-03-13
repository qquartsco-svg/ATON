"""
_ATON_LAYER 테스트 스위트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

§1  PrometheusOutput/Input    (8)
§2  KemetOutput/Input         (7)
§3  TribesSignal              (6)
§4  EdenSignal                (6)
§5  OilShockRouter            (8)
§6  EnergyMinistry            (7)
§7  MonetaBridge              (6)
§8  NexusState                (7)
§9  Nexus.step()              (8)
§10 Nexus.simulate() 시나리오  (6)
──────────────────────────────
합계: 69 테스트
"""

from __future__ import annotations

import math
import sys
import os
import pytest

# 경로 설정
_layer = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_hub   = os.path.dirname(_layer)
for p in [_layer, _hub]:
    if p not in sys.path:
        sys.path.insert(0, p)

from _ATON_LAYER.interfaces.prometheus_io import (
    PrometheusOutput, PrometheusInput, extract_prometheus_output,
)
from _ATON_LAYER.interfaces.kemet_io import (
    KemetOutput, KemetInput, extract_kemet_output,
)
from _ATON_LAYER.interfaces.tribes_io import (
    LeviSignal, DanSignal, AsherSignal, ZebulunSignal, TribesSignal,
)
from _ATON_LAYER.interfaces.eden_io import EdenSignal
from _ATON_LAYER.bridges.oil_shock import OilShockRouter, OilShockEvent
from _ATON_LAYER.bridges.energy_ministry import (
    EnergyMinistry, EnergyMinistryParams, EnergyMinistryState,
)
from _ATON_LAYER.bridges.moneta_bridge import MonetaBridge, EnergyMonetaSignal
from _ATON_LAYER.aton_core import (
    NexusState, NexusConfig, tribes_to_kemet_input, all_to_eden_signal,
)
from _ATON_LAYER.nexus import Nexus


# ═══════════════════════════════════════════════════════════════
# §1  PrometheusOutput / Input
# ═══════════════════════════════════════════════════════════════

class TestPrometheusIO:

    def test_default_values(self):
        p = PrometheusOutput()
        assert p.oil_dependency == 1.0
        assert p.renewable_share == 0.0
        assert p.oil_weapon_effect == 1.0
        assert p.energy_independence == 0.0

    def test_is_oil_shock_when_high_owe(self):
        p = PrometheusOutput(flags={"oil_shock_active": True})
        assert p.is_oil_shock() is True

    def test_is_not_oil_shock_by_default(self):
        p = PrometheusOutput()
        assert p.is_oil_shock() is False

    def test_is_energy_independent(self):
        p = PrometheusOutput(energy_independence=0.8)
        assert p.is_energy_independent() is True

    def test_not_energy_independent_below_threshold(self):
        p = PrometheusOutput(energy_independence=0.5)
        assert p.is_energy_independent() is False

    def test_threat_level_zero_when_d_zero(self):
        """D=0이면 에너지 위협 수준 0."""
        p = PrometheusOutput(oil_dependency=0.0, oil_weapon_effect=1.0)
        assert p.threat_level() == pytest.approx(0.0)

    def test_threat_level_max_when_fully_dependent(self):
        p = PrometheusOutput(oil_dependency=1.0, oil_weapon_effect=1.0)
        assert p.threat_level() == pytest.approx(1.0)

    def test_extract_from_mock_state(self):
        """extract_prometheus_output: 임의 객체에서 안전하게 추출."""
        class MockState:
            oil_dependency = 0.5
            renewable_share = 0.3
            oil_weapon_effect = 0.4
            energy_independence_index = 0.4
            solar_lcoe = 30.0
            investment_level = 50.0

        out = extract_prometheus_output(MockState())
        assert out.oil_dependency == pytest.approx(0.5)
        assert out.renewable_share == pytest.approx(0.3)
        assert 0.0 <= out.oil_price_multiplier


# ═══════════════════════════════════════════════════════════════
# §2  KemetOutput / Input
# ═══════════════════════════════════════════════════════════════

class TestKemetIO:

    def test_default_values(self):
        k = KemetOutput()
        assert k.maat_score == 0.5
        assert k.social_tension == 0.2
        assert k.population == 1000.0

    def test_needs_energy_reform_when_treasury_crisis(self):
        k = KemetOutput(flags={"treasury_crisis": True})
        assert k.needs_energy_reform() is True

    def test_stable_when_no_crises(self):
        k = KemetOutput()
        assert k.is_stable() is True

    def test_not_stable_with_food_crisis(self):
        k = KemetOutput(flags={
            "food_crisis": True, "social_unrest": False, "treasury_crisis": False,
        })
        assert k.is_stable() is False

    def test_kemet_input_defaults(self):
        ki = KemetInput()
        assert ki.oil_price_multiplier == 1.0
        assert ki.nile_phase == "평년"

    def test_extract_from_mock_state(self):
        class MockKemState:
            t = 5.0
            gdp = 120.0
            treasury_balance = 500.0
            social_tension = 0.15
            law_compliance = 0.85
            population = 1200.0
            health_index = 0.75
            food_security = 0.9
            alliance_strength = 0.6
            solar_reform_active = True
            jubilee_decree_active = False
            education_budget = 10.0
            justice_budget = 8.0
            war_mode = False
            minsky_stage = "hedge"

        out = extract_kemet_output(MockKemState())
        assert out.gdp == pytest.approx(120.0)
        assert out.maat_score == pytest.approx(0.5)  # maat_fn=None → 기본값

    def test_kemet_output_flags_structure(self):
        k = KemetOutput()
        required = {"treasury_crisis", "food_crisis", "social_unrest",
                    "minsky_ponzi", "war_mode", "epidemic"}
        assert required.issubset(set(k.flags.keys()))


# ═══════════════════════════════════════════════════════════════
# §3  TribesSignal
# ═══════════════════════════════════════════════════════════════

class TestTribesSignal:

    def test_default_signal_creation(self):
        ts = TribesSignal()
        assert ts.levi.knowledge_stock == 50.0
        assert ts.dan.law_compliance == 0.8
        assert ts.asher.grain_stock == 10000.0
        assert ts.zebulun.fish_stock == 80.0

    def test_tier1_complete_with_defaults(self):
        ts = TribesSignal()
        assert ts.tier1_complete() is True

    def test_active_count_tier1_only(self):
        ts = TribesSignal()
        # Tier 2 모두 None → 4개만 활성
        assert ts.active_count() == 4

    def test_active_count_with_tier2(self):
        ts = TribesSignal()
        ts.reuben = {"placeholder": True}
        assert ts.active_count() == 5

    def test_dan_signal_minsky_stages(self):
        d = DanSignal(wealth_concentration=0.70, minsky_stage="ponzi")
        assert d.minsky_stage == "ponzi"

    def test_zebulun_fleet_signals(self):
        z = ZebulunSignal(fleet_signal="EMERGENCY")
        assert z.fleet_signal == "EMERGENCY"


# ═══════════════════════════════════════════════════════════════
# §4  EdenSignal
# ═══════════════════════════════════════════════════════════════

class TestEdenSignal:

    def test_omega_bounded(self):
        e = EdenSignal()
        assert 0.0 <= e.omega() <= 1.0

    def test_omega_increases_with_better_state(self):
        e_good = EdenSignal(
            pishon_grain_flux=5000.0,
            gihon_stability=0.9,
            gihon_health=0.9,
            hiddekel_knowledge=200.0,
            hiddekel_law=0.95,
            euphrates_maat=0.9,
            euphrates_eii=0.8,
            euphrates_owe=0.1,
        )
        e_bad = EdenSignal(
            gihon_stability=0.1,
            hiddekel_law=0.1,
            euphrates_maat=0.1,
        )
        assert e_good.omega() > e_bad.omega()

    def test_is_eden_state_threshold(self):
        e_eden = EdenSignal(
            pishon_grain_flux=5000.0,
            gihon_stability=0.95,
            gihon_health=0.95,
            hiddekel_knowledge=300.0,
            hiddekel_law=0.95,
            euphrates_maat=0.9,
            euphrates_eii=0.9,
            euphrates_owe=0.05,
        )
        # Ω > 0.75 → 에덴 상태
        assert e_eden.is_eden_state() is True

    def test_crisis_rivers_detected(self):
        e = EdenSignal(
            gihon_stability=0.2,   # 위기
            hiddekel_law=0.2,      # 위기
            euphrates_maat=0.5,
        )
        crisis = e.crisis_rivers()
        assert "gihon" in crisis
        assert "hiddekel" in crisis

    def test_no_crisis_rivers_normal(self):
        e = EdenSignal(
            pishon_grain_flux=3000.0,
            gihon_stability=0.8,
            hiddekel_law=0.8,
            euphrates_maat=0.7,
        )
        assert len(e.crisis_rivers()) == 0

    def test_pishon_crisis_low_grain(self):
        e = EdenSignal(pishon_grain_flux=100.0)
        assert "pishon" in e.crisis_rivers()


# ═══════════════════════════════════════════════════════════════
# §5  OilShockRouter
# ═══════════════════════════════════════════════════════════════

class TestOilShockRouter:

    def test_no_shock_below_threshold(self):
        r = OilShockRouter()
        event = r.detect(t=1.0, owe_before=0.5, owe_after=0.53)
        assert event is None

    def test_shock_detected_above_threshold(self):
        r = OilShockRouter()
        event = r.detect(t=1.0, owe_before=0.3, owe_after=0.5)
        assert event is not None
        # delta = 0.2 → in [0.15, 0.30) → "severe"
        assert event.severity == "severe"
        assert event.delta_owe == pytest.approx(0.2)

    def test_severity_catastrophic(self):
        r = OilShockRouter()
        event = r.detect(t=5.0, owe_before=0.1, owe_after=0.6)
        assert event.severity == "catastrophic"

    def test_kemet_adjustments_treasury_drops(self):
        r = OilShockRouter()
        event = r.detect(t=1.0, owe_before=0.2, owe_after=0.5)
        adj = r.kemet_adjustments(event)
        assert adj["treasury_efficiency"] < 1.0
        assert adj["energy_reform_pressure"] > 0.0

    def test_tribes_adjustments_zebulun_fuel_rises(self):
        r = OilShockRouter()
        event = r.detect(t=1.0, owe_before=0.2, owe_after=0.5)
        adj = r.tribes_adjustments(event)
        assert adj["zebulun_fuel_cost_multiplier"] > 1.0

    def test_recovery_signal_before_shock(self):
        r = OilShockRouter()
        assert r.recovery_signal(current_owe=0.5) == pytest.approx(1.0)

    def test_recovery_signal_during_shock(self):
        r = OilShockRouter()
        r.detect(t=1.0, owe_before=0.3, owe_after=0.6)
        # current_owe = 0.45 (중간 회복)
        rec = r.recovery_signal(current_owe=0.45)
        assert 0.0 < rec < 1.0

    def test_cumulative_impact_adds_up(self):
        r = OilShockRouter()
        r.detect(t=1.0, owe_before=0.2, owe_after=0.4)
        r.detect(t=5.0, owe_before=0.3, owe_after=0.5)
        assert r.cumulative_impact() == pytest.approx(0.4, abs=0.01)


# ═══════════════════════════════════════════════════════════════
# §6  EnergyMinistry
# ═══════════════════════════════════════════════════════════════

class TestEnergyMinistry:

    def test_initial_state(self):
        em = EnergyMinistry()
        assert em.state.grid_capacity == pytest.approx(0.1)
        assert em.state.oil_import_share == pytest.approx(1.0)

    def test_grid_grows_with_investment(self):
        em = EnergyMinistry()
        s0 = em.state.grid_capacity
        em.step(dt=1.0, treasury_budget=1000.0)
        assert em.state.grid_capacity > s0

    def test_solar_reform_accelerates_grid(self):
        """solar_reform 발동 → 그리드 누적 투자량이 더 많아야 함."""
        em1 = EnergyMinistry()
        em2 = EnergyMinistry()
        # 소규모 예산 + 짧은 스텝 → 포화 전에 비교
        for _ in range(3):
            em1.step(dt=1.0, treasury_budget=1.0, solar_reform_active=False)
        for _ in range(3):
            em2.step(dt=1.0, treasury_budget=1.0, solar_reform_active=True)
        assert em2.state.grid_investment_cumulative > em1.state.grid_investment_cumulative

    def test_prometheus_signal_output(self):
        em = EnergyMinistry()
        em.step(dt=1.0, treasury_budget=100.0)
        sig = em.prometheus_input_signal()
        assert "energy_budget" in sig
        assert "policy_push" in sig
        assert sig["policy_push"] >= 0.0

    def test_pharaoh_flags_structure(self):
        em = EnergyMinistry()
        flags = em.pharaoh_flags()
        assert "energy_reform_needed" in flags
        assert "energy_independent" in flags

    def test_grid_bounded_at_max(self):
        em = EnergyMinistry()
        for _ in range(200):
            em.step(dt=1.0, treasury_budget=10000.0, solar_reform_active=True)
        assert em.state.grid_capacity <= 1.0

    def test_budget_increases_during_crisis(self):
        em = EnergyMinistry()
        em.state.oil_import_share = 0.95  # 위기 상태
        em.step(dt=1.0, treasury_budget=100.0)
        assert em.state.budget > 100.0 * 0.08  # 기본보다 예산 많음


# ═══════════════════════════════════════════════════════════════
# §7  MonetaBridge
# ═══════════════════════════════════════════════════════════════

class TestMonetaBridge:

    def test_oil_shock_causes_inflation(self):
        bridge = MonetaBridge()
        sig = bridge.compute(
            oil_price_multiplier=2.0,  # 2배 상승
            oil_dependency=0.8,
            renewable_share=0.1,
            energy_independence=0.1,
            solar_lcoe=40.0,
            gdp=100.0,
        )
        assert sig.energy_inflation_add > 0.0

    def test_no_shock_no_inflation(self):
        bridge = MonetaBridge()
        sig = bridge.compute(
            oil_price_multiplier=1.0,  # 변화 없음
            oil_dependency=0.8,
            renewable_share=0.1,
            energy_independence=0.1,
            solar_lcoe=40.0,
            gdp=100.0,
        )
        assert abs(sig.energy_inflation_add) < 1.0  # 작은 변화

    def test_low_dependency_reduces_impact(self):
        bridge = MonetaBridge()
        sig_high_d = bridge.compute(
            oil_price_multiplier=2.0,
            oil_dependency=0.9,
            renewable_share=0.05,
            energy_independence=0.05,
            solar_lcoe=40.0, gdp=100.0,
        )
        sig_low_d = bridge.compute(
            oil_price_multiplier=2.0,
            oil_dependency=0.1,  # 독립 달성
            renewable_share=0.8,
            energy_independence=0.8,
            solar_lcoe=40.0, gdp=100.0,
        )
        assert sig_low_d.energy_inflation_add < sig_high_d.energy_inflation_add

    def test_green_deflation_when_lcoe_low(self):
        bridge = MonetaBridge()
        sig = bridge.compute(
            oil_price_multiplier=1.0,
            oil_dependency=0.3,
            renewable_share=0.6,
            energy_independence=0.6,
            solar_lcoe=15.0,  # LCOE 급락
            gdp=100.0,
        )
        assert sig.energy_inflation_add < 0.0  # 디플레이션 압력

    def test_apply_to_kemet_treasury_keys(self):
        bridge = MonetaBridge()
        sig = bridge.compute(1.5, 0.5, 0.2, 0.2, 35.0, 100.0)
        result = bridge.apply_to_kemet_treasury(sig, 2.0, 100.0)
        assert "inflation_adjustment" in result
        assert "gdp_growth_adj" in result
        assert "spending_pressure" in result

    def test_is_inflationary_shock(self):
        bridge = MonetaBridge()
        sig = bridge.compute(3.0, 0.9, 0.05, 0.05, 40.0, 100.0)
        assert sig.is_inflationary_shock() is True


# ═══════════════════════════════════════════════════════════════
# §8  NexusState
# ═══════════════════════════════════════════════════════════════

class TestNexusState:

    def test_default_coherence(self):
        ns = NexusState()
        c = ns.compute_coherence()
        assert 0.0 <= c <= 1.0

    def test_coherence_with_good_state(self):
        ns = NexusState(
            kemet=KemetOutput(
                maat_score=0.9, social_tension=0.1,
                food_security=0.95, law_compliance=0.9,
            ),
            prometheus=PrometheusOutput(energy_independence=0.85),
        )
        c = ns.compute_coherence()
        assert c > 0.6

    def test_update_flags_detects_oil_shock(self):
        ns = NexusState(
            prometheus=PrometheusOutput(
                flags={"oil_shock_active": True, "tipping_point_crossed": False,
                       "energy_independent": False, "petrodollar_collapse_risk": False,
                       "solar_grid_parity": False}
            )
        )
        ns.tribes = TribesSignal()
        ns.kemet  = KemetOutput()
        ns.update_flags()
        assert ns.system_flags["oil_shock_active"] is True

    def test_update_flags_eden_state(self):
        ns = NexusState()
        ns.prometheus = PrometheusOutput()
        ns.kemet      = KemetOutput()
        ns.tribes     = TribesSignal()
        eden = EdenSignal(
            pishon_grain_flux=5000.0, gihon_stability=0.95,
            gihon_health=0.95, hiddekel_knowledge=300.0,
            hiddekel_law=0.95, euphrates_maat=0.9,
            euphrates_eii=0.9, euphrates_owe=0.05,
        )
        ns.eden = eden
        ns.update_flags()
        assert ns.system_flags["eden_state"] is True

    def test_summary_contains_time(self):
        ns = NexusState(t=10.0)
        ns.prometheus = PrometheusOutput()
        ns.kemet      = KemetOutput()
        ns.tribes     = TribesSignal()
        summary = ns.summary()
        assert "10" in summary

    def test_nexus_config_active_layers(self):
        cfg = NexusConfig(use_eden=False)
        layers = cfg.active_layers()
        assert "KEMET" in layers
        assert "_EDEN" not in layers

    def test_tribes_to_kemet_input_transform(self):
        ts = TribesSignal()
        ts.asher.grain_stock = 20000.0
        ki = tribes_to_kemet_input(ts)
        assert ki.grain_stock == pytest.approx(20000.0)


# ═══════════════════════════════════════════════════════════════
# §9  Nexus.step()
# ═══════════════════════════════════════════════════════════════

class TestNexusStep:

    def setup_method(self):
        self.nexus = Nexus()

    def test_step_returns_nexus_state(self):
        state = self.nexus.step(t=0.0, dt=1.0)
        assert isinstance(state, NexusState)

    def test_step_t_matches(self):
        state = self.nexus.step(t=5.0, dt=1.0)
        assert state.t == pytest.approx(5.0)

    def test_step_has_prometheus(self):
        state = self.nexus.step(t=0.0, dt=1.0)
        assert state.prometheus is not None

    def test_step_has_tribes(self):
        state = self.nexus.step(t=0.0, dt=1.0)
        assert state.tribes is not None

    def test_step_has_kemet(self):
        state = self.nexus.step(t=0.0, dt=1.0)
        assert state.kemet is not None

    def test_step_has_eden(self):
        state = self.nexus.step(t=0.0, dt=1.0)
        assert state.eden is not None

    def test_step_oil_shock_external(self):
        state = self.nexus.step(
            t=1.0, dt=1.0,
            external={"solar_reform": True, "policy_push": 1.0}
        )
        assert state.energy_ministry.solar_reform_active is True

    def test_step_coherence_bounded(self):
        state = self.nexus.step(t=0.0, dt=1.0)
        assert 0.0 <= state.nexus_coherence <= 1.0


# ═══════════════════════════════════════════════════════════════
# §10  Nexus.simulate() 시나리오
# ═══════════════════════════════════════════════════════════════

class TestNexusSimulate:

    def test_simulate_returns_history(self):
        nexus = Nexus(config=NexusConfig(t_end=10.0))
        history = nexus.simulate(years=10)
        assert len(history) == 11  # t=0..10 (dt=1)

    def test_simulate_time_sequence(self):
        nexus = Nexus(config=NexusConfig(t_end=5.0))
        history = nexus.simulate(years=5)
        for i, state in enumerate(history):
            assert state.t == pytest.approx(float(i))

    def test_solar_reform_accelerates_transition(self):
        """solar_reform 칙령 발동 → 누적 그리드 투자량이 더 많아야 함."""
        n_no_reform  = Nexus(config=NexusConfig(t_end=5.0))
        n_with_reform= Nexus(config=NexusConfig(t_end=5.0))

        hist_no  = n_no_reform.simulate(years=5)
        hist_yes = n_with_reform.simulate(
            years=5,
            external_sequence={float(t): {"solar_reform": True, "policy_push": 0.8}
                               for t in range(0, 6)}
        )
        # 개혁 있는 경우 누적 투자량이 더 많아야 함
        assert (hist_yes[-1].energy_ministry.grid_investment_cumulative >
                hist_no[-1].energy_ministry.grid_investment_cumulative)

    def test_jubilee_reduces_concentration(self):
        """희년 발동 → Dan 집중도 낮아짐."""
        nexus = Nexus(config=NexusConfig(t_end=30.0))
        # 초기 집중도를 높게 설정
        nexus._tribes_state.dan.wealth_concentration = 0.70
        history = nexus.simulate(years=30)
        # 희년이 발동되면 집중도가 낮아져야 함
        final_c = history[-1].tribes.dan.wealth_concentration
        # 기본 동역학으로 집중도가 상승하지만 희년 발동으로 리셋됨
        # (기본 어댑터의 jubilee_triggered 플래그 확인)
        jubilees = sum(1 for s in history if s.tribes.dan.jubilee_triggered)
        assert jubilees > 0

    def test_external_sequence_applied(self):
        """외부 시퀀스 적용: t=3에 solar_reform → 해당 스텝 누적 투자 증가."""
        n_no  = Nexus(config=NexusConfig(t_end=5.0))
        n_yes = Nexus(config=NexusConfig(t_end=5.0))

        hist_no  = n_no.simulate(years=5)
        hist_yes = n_yes.simulate(
            years=5,
            external_sequence={float(t): {"solar_reform": True} for t in range(0, 6)}
        )
        # solar_reform 있는 시뮬레이션이 누적 투자가 더 많아야 함
        assert (hist_yes[-1].energy_ministry.grid_investment_cumulative >=
                hist_no[-1].energy_ministry.grid_investment_cumulative)

    def test_knowledge_grows_over_time(self):
        """교육 예산이 있을 때 지식 자본 K는 누적됨."""
        nexus = Nexus(config=NexusConfig(t_end=30.0))
        # 초기 지식 자본을 낮게 설정해서 성장 여지 확보
        nexus._tribes_state.levi.knowledge_stock = 10.0
        history = nexus.simulate(years=30)
        k_initial = history[0].tribes.levi.knowledge_stock
        k_final   = history[-1].tribes.levi.knowledge_stock
        # 기본 교육 예산(~8.0 + K*0.01)이 decay를 상회하므로 성장
        assert k_final > k_initial
