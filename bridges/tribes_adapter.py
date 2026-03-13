"""
tribes_adapter.py — 실제 12지파 엔진 어댑터
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ATON Nexus 어댑터 타입:
  TribesAdapter = Callable[[TribesSignal, float, Dict], TribesSignal]

이 모듈은 kemet_engine.TribeCouncil(12지파 멀티 액터)을
상태 보존 어댑터로 래핑한다.

- TribeCouncil 인스턴스를 스텝 간 유지
- TribesSignal의 외부 신호 + external dict → council.step() 호출
- TribeCouncilState → TribesSignal(v2.0 12지파 완성판) 변환 및 반환

external dict 키:
  "external_threat"  float [0,1]  — 외부 군사 위협 (시므온/갓 입력)
  "diplomacy_budget" float [0,1]  — 납달리 외교 예산
  "project_load"     float [0,1]  — 이사갈 프로젝트 부하
  "disruption"       float [0,1]  — 베냐민 외부 혼란
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, Optional

# ── 경로 주입 ─────────────────────────────────────────────────────
_here  = os.path.dirname(os.path.abspath(__file__))        # bridges/
_aton  = os.path.dirname(_here)                             # _ATON_LAYER/
_hub   = os.path.dirname(_aton)                             # ENGINE_HUB/
_kemet = os.path.join(_hub, "60_APPLIED_LAYER", "kemet_engine")
_tribes_root = os.path.join(_hub, "70_TRIBES_LAYER")

for _sub in [
    "01_reuben_engine", "02_levi_engine", "03_simeon_engine",
    "04_dan_engine",    "05_gad_engine",  "06_issachar_engine",
    "07_asher_engine",  "08_judah_engine", "09_zebulun_engine",
    "10_naphtali_engine", "11_joseph_engine", "12_benjamin_engine",
]:
    _p = os.path.join(_tribes_root, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

for _p in [_kemet, _hub]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tribe_council import (
    TribeCouncil,
    TribeCouncilParams,
    TribeCouncilState,
)

# 각 지파 to_snapshot 함수 (올바른 인수 확인)
from reuben_core   import to_snapshot as r_snap
from levi_core     import to_snapshot as l_snap
from simeon_core   import to_snapshot as si_snap
from dan_core      import to_snapshot as d_snap, social_tension as dan_st
from gad_core      import to_snapshot as g_snap
from issachar_core import to_snapshot as is_snap
from asher_core    import to_snapshot as a_snap
from judah_core    import to_snapshot as ju_snap
from zebulun_core  import to_snapshot as z_snap
from naphtali_core import to_snapshot as n_snap
from joseph_core   import to_state    as jo_snap   # JosephState has inflation; Snapshot does not
from benjamin_core import to_snapshot as b_snap

from _ATON_LAYER.interfaces.tribes_io import (
    TribesSignal,
    LeviSignal,
    DanSignal,
    AsherSignal,
    ZebulunSignal,
    ReubenSignal,
    SimeonSignal,
    IssacharSignal,
    GadSignal,
    JudahSignal,
    NaphtaliSignal,
    JosephSignal,
    BenjaminSignal,
)


# ─────────────────────────────────────────────────────────────────
# 변환 헬퍼
# ─────────────────────────────────────────────────────────────────

def _council_to_tribes(
    cs:               TribeCouncilState,
    council:          TribeCouncil,
    external_threat:  float,
    diplomacy_budget: float,
    project_load:     float,
    disruption:       float,
) -> TribesSignal:
    """TribeCouncilState → TribesSignal(v2.0) 변환.

    TribeCouncilState의 집약 지표 + council 내부 state를 결합해
    12지파 전체 신호를 채운다.
    """
    p   = council.params
    sig = cs.signals

    food  = sig.food_security
    prod  = sig.productivity_bonus
    law   = sig.law_compliance
    st    = sig.social_tension

    # ── Tier 1 스냅샷 ─────────────────────────────────────────────
    conc  = max(0.0, min(1.0, council._dan.wealth_concentration))
    pop   = max(1.0, council._reuben.population)

    a_ss  = a_snap(council._asher,   p.asher,   concentration=conc, population=pop)
    l_ss  = l_snap(council._levi,    p.levi)
    d_ss  = d_snap(council._dan,     p.dan,     food_security=food)
    z_ss  = z_snap(council._zebulun, p.zebulun)

    levi_sig = LeviSignal(
        knowledge_stock    = l_ss.knowledge_stock,
        productivity_bonus = l_ss.productivity_bonus,
        network_output     = l_ss.network_output,
        hiddekel_flux      = l_ss.knowledge_stock * 0.01,
    )
    dan_sig = DanSignal(
        wealth_concentration = d_ss.wealth_concentration,
        law_compliance       = d_ss.law_compliance,
        social_tension       = d_ss.social_tension,
        minsky_stage         = d_ss.minsky_stage,
        jubilee_triggered    = d_ss.jubilee_due,     # DanState.jubilee_due
        gihon_stability      = 1.0 - d_ss.social_tension,
    )
    asher_sig = AsherSignal(
        grain_stock       = a_ss.grain_stock,
        food_security     = a_ss.food_security,
        nile_phase        = a_ss.nile_phase,
        joseph_action     = a_ss.joseph_action,
        pishon_grain_flux = max(0.0, a_ss.dg_dt),   # AsherState.dg_dt
    )
    zeb_sig = ZebulunSignal(
        fish_stock           = z_ss.fish_stock,
        fish_revenue         = z_ss.fish_revenue,
        maritime_gdp         = z_ss.fish_revenue * 0.8,
        fleet_signal         = z_ss.fleet_signal,
        overfishing_risk     = z_ss.stock_ratio < 0.2,  # 파생 계산
        pishon_maritime_flux = z_ss.fish_revenue * 0.5,
    )

    # ── Tier 2 스냅샷 ─────────────────────────────────────────────
    r_ss   = r_snap(council._reuben,    p.reuben,    food_security=food)
    si_ss  = si_snap(council._simeon,   p.simeon,    threat_ext=external_threat)
    is_ss  = is_snap(council._issachar, p.issachar,
                     productivity_bonus=prod, project_load=project_load)

    reu_sig = ReubenSignal(
        population  = r_ss.population,
        birth_rate  = r_ss.birth_rate_eff,   # ReubenState.birth_rate_eff
        death_rate  = r_ss.death_rate_eff,   # ReubenState.death_rate_eff
        growth_rate = r_ss.birth_rate_eff - r_ss.death_rate_eff,
    )
    sim_sig = SimeonSignal(
        military_strength = si_ss.military_strength,
        deterrence        = si_ss.deterrence,
        trade_volume      = 0.0,             # SimeonState에 없음 → 기본값
        threat_ext        = external_threat,
    )
    iss_sig = IssacharSignal(
        labor_efficiency = is_ss.labor_efficiency,
        seasonal_output  = 0.0,              # IssacharState에 없음 → 기본값
        project_load     = project_load,
    )

    # ── Tier 3 스냅샷 ─────────────────────────────────────────────
    eff_threat = max(0.0, external_threat * (1.0 - si_ss.deterrence))
    g_ss  = g_snap(council._gad, p.gad,
                   threat_level=eff_threat, supply_level=food)

    war_for_naphtali  = max(0.0, 1.0 - g_ss.combat_effectiveness)
    budget_naphtali   = min(1.0, diplomacy_budget + min(0.2, z_ss.fish_revenue / 1000.0))

    ju_ss  = ju_snap(council._judah,    p.judah,
                     social_tension=st, law_compliance=law)
    n_ss   = n_snap(council._naphtali,  p.naphtali,
                    war_mode=war_for_naphtali, budget=budget_naphtali)

    network_input = min(1.0, cs.joseph_gdp / max(1.0, p.joseph.gdp_capacity))
    jo_ss  = jo_snap(council._joseph,   p.joseph,
                     grain_supply=food, productivity=prod)
    b_ss   = b_snap(council._benjamin,  p.benjamin,
                    network_input=network_input, disruption=disruption)

    gad_sig = GadSignal(
        troops               = g_ss.troops,
        morale               = g_ss.morale,
        combat_effectiveness = g_ss.combat_effectiveness,
        battle_status        = g_ss.battle_status,
    )
    judah_sig = JudahSignal(
        authority        = ju_ss.authority,
        legitimacy       = ju_ss.legitimacy,
        cohesion         = ju_ss.cohesion,
        leadership_index = ju_ss.leadership_index,
        royal_status     = ju_ss.royal_status,
    )
    nap_sig = NaphtaliSignal(
        alliance          = n_ss.alliance,
        routes            = n_ss.routes,
        influence         = n_ss.influence,
        diplomatic_status = n_ss.diplomatic_status,
    )
    joseph_sig = JosephSignal(
        gdp          = jo_ss.gdp,
        inflation    = jo_ss.inflation,
        debt_ratio   = jo_ss.debt_ratio,
        minsky_stage = jo_ss.minsky_stage,
        money_supply = jo_ss.money,           # JosephState.money (NOT money_supply)
    )
    benjamin_sig = BenjaminSignal(
        information     = b_ss.information,
        connectivity    = b_ss.connectivity,
        signal_fidelity = b_ss.fidelity,       # BenjaminState.fidelity
        amplification   = b_ss.amplification,
    )

    return TribesSignal(
        levi     = levi_sig,
        dan      = dan_sig,
        asher    = asher_sig,
        zebulun  = zeb_sig,
        reuben   = reu_sig,
        simeon   = sim_sig,
        issachar = iss_sig,
        gad      = gad_sig,
        judah    = judah_sig,
        naphtali = nap_sig,
        joseph   = joseph_sig,
        benjamin = benjamin_sig,
    )


# ─────────────────────────────────────────────────────────────────
# TribesEngineAdapter
# ─────────────────────────────────────────────────────────────────

class TribesEngineAdapter:
    """
    상태 보존 12지파 엔진 어댑터 (ATON Nexus용).

    ATON Nexus가 요구하는 TribesAdapter 프로토콜 구현:
      adapter(TribesSignal, dt, external) → TribesSignal

    동작:
      1. external dict에서 외부 파라미터 추출
      2. TribeCouncil.step() 호출 (12지파 동시 진행)
      3. TribeCouncilState → TribesSignal(v2.0) 변환 및 반환
    """

    def __init__(self, params: Optional[TribeCouncilParams] = None):
        self.council = TribeCouncil(params)

    # ── 어댑터 인터페이스 (callable) ─────────────────────────────

    def __call__(
        self,
        prev: TribesSignal,
        dt: float,
        external: Dict[str, Any],
    ) -> TribesSignal:
        """ATON Nexus 호출 인터페이스."""
        ext_threat        = float(external.get("external_threat",  0.20))
        diplomacy_budget  = float(external.get("diplomacy_budget", 0.50))
        project_load      = float(external.get("project_load",     0.50))
        disruption        = float(external.get("disruption",       0.00))

        council_state = self.council.step(
            dt               = dt,
            external_threat  = ext_threat,
            diplomacy_budget = diplomacy_budget,
            project_load     = project_load,
            disruption       = disruption,
        )

        return _council_to_tribes(
            cs               = council_state,
            council          = self.council,
            external_threat  = ext_threat,
            diplomacy_budget = diplomacy_budget,
            project_load     = project_load,
            disruption       = disruption,
        )

    # ── 보조 API ──────────────────────────────────────────────────

    def get_council_state(self) -> TribeCouncilState:
        """최신 TribeCouncilState 반환 (히스토리 마지막)."""
        if self.council.history:
            return self.council.history[-1]
        raise RuntimeError("아직 step()을 호출하지 않았습니다.")


# ─────────────────────────────────────────────────────────────────
# 팩토리 함수
# ─────────────────────────────────────────────────────────────────

def make_tribes_adapter(
    params: Optional[TribeCouncilParams] = None,
) -> TribesEngineAdapter:
    """TribesEngineAdapter 인스턴스 생성 팩토리.

    ATON Nexus에 주입할 실제 12지파 엔진 어댑터를 반환.

    Example::
        from _ATON_LAYER.bridges.tribes_adapter import make_tribes_adapter
        nexus = Nexus(tribes_adapter=make_tribes_adapter())
    """
    return TribesEngineAdapter(params=params)
