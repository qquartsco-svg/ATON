"""
_ATON_LAYER / interfaces
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
각 엔진의 입출력 계약(Contract) 정의.

엔진 내부 구현은 여기서 알 필요 없다.
오직 "무엇이 흘러 들어오고, 무엇이 흘러 나가는가"만 정의한다.

흐름 원칙:
  PROMETHEUS → KEMET   (에너지 충격 → 중앙정부 대응)
  KEMET      → PROMETHEUS (예산·정책 → 에너지 투자)
  TRIBES     → KEMET   (곡식/어업/법/지식 → 부처 입력)
  TRIBES     → EDEN    (각 강(江)으로 데이터 공급)
  ALL        → EDEN    (4대강 최종 집계)
"""

from .kemet_io import KemetInput, KemetOutput
from .prometheus_io import PrometheusInput, PrometheusOutput
from .tribes_io import TribesSignal
from .eden_io import EdenSignal

__all__ = [
    "KemetInput", "KemetOutput",
    "PrometheusInput", "PrometheusOutput",
    "TribesSignal",
    "EdenSignal",
]
