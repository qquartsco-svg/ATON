"""
_ATON_LAYER v2.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEMET ↔ PROMETHEUS ↔ 70_TRIBES ↔ _EDEN 통합 레이어.

아톤(Aton/Aten):
  이집트 파라오 아크나톤(Akhenaten)이 선포한 유일신 — 태양 에너지.
  모든 에너지는 하나의 원천으로 귀결된다.
  모든 엔진은 하나의 동역학 흐름으로 통합된다.

v2.0 변경사항:
  - KEMET → ATON 실제 연결 (KemetEngineAdapter)
  - 12지파 → ATON 실제 연결 (TribesEngineAdapter + TribeCouncil)
  - TribesSignal v2.0: 12지파 전체 신호 완성 (Tier 2/3 dataclass)
  - make_real_nexus(): 실제 엔진 주입 Nexus 팩토리

공개 API:
  Nexus          — 통합 시뮬레이션 오케스트레이터
  NexusState     — 전체 시스템 스냅샷
  NexusConfig    — 시뮬레이션 설정
  make_real_nexus — 실제 엔진 연결 Nexus 팩토리 (v2.0)

브릿지:
  OilShockRouter      — 석유 충격 감지 및 라우팅
  EnergyMinistry      — KEMET 11번째 부처 (에너지부)
  MonetaBridge        — 에너지 ↔ 화폐/인플레이션
  KemetEngineAdapter  — 실제 KEMET ODE 어댑터 (v2.0)
  TribesEngineAdapter — 실제 12지파 TribeCouncil 어댑터 (v2.0)

인터페이스:
  KemetInput / KemetOutput
  PrometheusInput / PrometheusOutput
  TribesSignal (v2.0 — 12지파 완성)
  EdenSignal
"""

from .nexus import Nexus, make_real_nexus
from .aton_core import NexusState, NexusConfig
from .bridges import (
    OilShockRouter, EnergyMinistry, MonetaBridge,
    KemetEngineAdapter, make_kemet_adapter,
    TribesEngineAdapter, make_tribes_adapter,
)
from .interfaces import (
    KemetInput, KemetOutput,
    PrometheusInput, PrometheusOutput,
    TribesSignal, EdenSignal,
)

__version__ = "2.0.0"
__codename__ = "KEMET→ATON 실제 연결 + 12지파 완성"

__all__ = [
    # 핵심 오케스트레이터
    "Nexus", "NexusState", "NexusConfig",
    "make_real_nexus",
    # 브릿지
    "OilShockRouter", "EnergyMinistry", "MonetaBridge",
    "KemetEngineAdapter", "make_kemet_adapter",
    "TribesEngineAdapter", "make_tribes_adapter",
    # 인터페이스
    "KemetInput", "KemetOutput",
    "PrometheusInput", "PrometheusOutput",
    "TribesSignal", "EdenSignal",
]
