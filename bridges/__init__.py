"""
_ATON_LAYER / bridges
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
엔진 간 실제 연결 로직.

interfaces/   → "무엇이 흐르는가" (계약, 타입 정의)
bridges/      → "어떻게 흐르는가" (변환, 증폭, 라우팅)

모듈:
  oil_shock.py        — 석유 충격 → 엔진 자동 대응 라우터
  energy_ministry.py  — KEMET 11번째 부처 (에너지부) 골격
  moneta_bridge.py    — 에너지 가격 ↔ 화폐/인플레이션 연결
  kemet_adapter.py    — 실제 KEMET 엔진 어댑터 (v2.0 — 실제 ODE 연결)
  tribes_adapter.py   — 실제 12지파 어댑터 (v2.0 — TribeCouncil 연결)
"""

from .oil_shock import OilShockRouter, OilShockEvent
from .energy_ministry import EnergyMinistry, EnergyMinistryState, EnergyMinistryParams
from .moneta_bridge import MonetaBridge, EnergyMonetaSignal
from .kemet_adapter import KemetEngineAdapter, make_kemet_adapter
from .tribes_adapter import TribesEngineAdapter, make_tribes_adapter

__all__ = [
    "OilShockRouter", "OilShockEvent",
    "EnergyMinistry", "EnergyMinistryState", "EnergyMinistryParams",
    "MonetaBridge", "EnergyMonetaSignal",
    "KemetEngineAdapter", "make_kemet_adapter",
    "TribesEngineAdapter", "make_tribes_adapter",
]
