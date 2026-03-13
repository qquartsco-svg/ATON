# _ATON_LAYER — ENGINE_HUB 통합 거버넌스 레이어

> **아톤(Aton/Aten, 𓇳)** — 이집트 태양신.
> 파라오 아크나톤이 "모든 에너지는 하나의 원천으로 귀결된다"고 선포한 혁명.
>
> → 모든 ENGINE_HUB 레이어를 하나의 동역학 흐름으로 통합한다.
>
> **현재 상태**: v2.0.0 ✅ — KEMET + 12지파 실제 엔진 연결 완성, 141 테스트 통과
>
> **레이어 이름 `_ATON`**: `_` prefix = ENGINE_HUB 내 **수평 통합 레이어** 네이밍 컨벤션.
> 숫자 prefix(00~70)는 전문화 독립 엔진, 언더스코어(`_`)는 레이어 간 통합을 담당하는
> 거버넌스 레이어(`_ATON`, `_PROMETHEUS`, `_EDEN`)를 의미한다.

---

## 레이어 위치

```
ENGINE_HUB/                        ← 루트
├── _ATON_LAYER/                   ← 통합 거버넌스 (이 레이어)
├── _PROMETHEUS_LAYER/             ← 에너지 전환 ODE
├── _EDEN_LAYER/                   ← 4대강 데이터 흐름
├── 60_APPLIED_LAYER/kemet_engine/ ← 중앙정부 10부처
└── 70_TRIBES_LAYER/               ← 12지파 독립 엔진
```

---

## 설계 철학

```
"각 엔진은 혼자서도 달릴 수 있다. (Air Jordan 원칙)
 ATON은 그들이 함께 달리게 한다."

엔진 A → [인터페이스 계약] → ATON → [인터페이스 계약] → 엔진 B

엔진들은 서로를 직접 참조하지 않는다.
오직 ATON을 통해 신호를 주고받는다.
```

---

## 아키텍처

```
_ATON_LAYER/
├── __init__.py              # 공개 API
├── aton_core.py             # NexusState, NexusConfig, 변환 유틸
├── nexus.py                 # Nexus 오케스트레이터 (step, simulate)
├── run_aton.py              # CLI 실행기
│
├── interfaces/              # 엔진 간 입출력 계약 (Contract)
│   ├── prometheus_io.py     # PrometheusInput / PrometheusOutput
│   ├── kemet_io.py          # KemetInput / KemetOutput
│   ├── tribes_io.py         # TribesSignal (Tier 1~3 슬롯)
│   └── eden_io.py           # EdenSignal (4대강 집약)
│
├── bridges/                 # 엔진 간 변환·라우팅 로직
│   ├── oil_shock.py         # 석유 충격 감지 & 자동 라우팅
│   ├── energy_ministry.py   # KEMET 11번째 부처 (에너지부)
│   └── moneta_bridge.py     # 에너지 ↔ 화폐/인플레이션
│
└── tests/
    └── test_aton.py         # 69개 테스트 ✅
```

---

## 핵심 개념

### 1. NexusState — 통합 스냅샷

```python
@dataclass
class NexusState:
    t:              float             # 시뮬레이션 시간 (yr)
    kemet:          KemetOutput       # KEMET Ma'at, 사회 안정, GDP
    prometheus:     PrometheusOutput  # D, R, OWE, EII
    tribes:         TribesSignal      # 지식(K), 집중도(c), 식량, 어족
    eden:           EdenSignal        # 4대강 Ω 지수
    energy_ministry: EnergyMinistryState  # 11번째 부처
    nexus_coherence: float            # Ω_nexus ∈ [0,1]
    system_flags:   Dict[str, bool]   # 파라오 대시보드
```

**Nexus 정합성 (Coherence) 공식:**
```
Ω_nexus = 0.25×Ma'at + 0.20×EII + 0.20×(1-ST) + 0.20×FSI + 0.15×법준수
```

### 2. 인터페이스 계약 (Contract)

```
엔진 내부 구현 변경 → 인터페이스 파일만 수정
                   → 다른 엔진은 영향 없음

PrometheusOutput: D, R, OWE, EII, oil_price_multiplier, solar_lcoe, ...
KemetOutput:      Ma'at, social_tension, food_security, gdp, flags, ...
TribesSignal:     levi(K), dan(c), asher(grain), zebulun(fish), + 8개 Tier2 슬롯
EdenSignal:       4대강 flux + Ω 계산
```

### 3. 브릿지 (Bridge)

**석유 충격 라우터:**
```
PROMETHEUS OWE 급등 감지 (dOWE > 5%)
    ↓
OilShockEvent 생성 (severity: minor/moderate/severe/catastrophic)
    ↓
KEMET 재무부: treasury_efficiency ↓
KEMET 농업부: agriculture_efficiency ↓
70_TRIBES Zebulun: fuel_cost_multiplier ↑
70_TRIBES Dan: concentration_pressure ↑
EDEN Pishon강: disruption 기록
```

**에너지부 (11번째 부처) ODE:**
```
dG_grid/dt = grid_build_rate × budget × policy_boost × lcoe_factor − decay × G
policy_boost = 2.0 (solar_reform_decree=True)
             × 1.5 (tipping_point_crossed=True)
lcoe_factor  = 40.0 / solar_lcoe    (LCOE 낮을수록 효율↑)
```

**모네타 브릿지:**
```
에너지 인플레이션 채널:
  π_energy = Δoil_price × D × β_passthrough × 100
  (오일쇼크 + 높은 의존도 → 인플레이션)

녹색 디플레이션 채널:
  π_green = -(40 - LCOE)/40 × R × 0.5
  (LCOE 하락 + 재생에너지 확대 → 장기 디플레이션)

Taylor Rule 에너지 항 추가:
  r = r* + α(π-π*) + β(Y-Y*) + γ×energy_pressure
```

### 4. Nexus 실행 순서

```
매 타임스텝:
  1. 70_TRIBES step()  →  TribesSignal
  2. PROMETHEUS step() →  PrometheusOutput
  3. 충격 감지         →  OilShockEvent? (OWE 급등 시)
  4. 에너지부 step()   →  EnergyMinistryState
  5. KEMET step()      →  KemetOutput  (PROMETHEUS + TRIBES 신호 반영)
  6. EDEN 집계         →  EdenSignal
  7. NexusState 갱신   →  스냅샷 저장 + 플래그 갱신
```

---

## 흐름 맵

```
70_TRIBES_LAYER
  Levi  → knowledge_stock → PROMETHEUS(학습 가속), KEMET 교육부
  Dan   → wealth_conc    → Asher 효율, KEMET 사법부, PROMETHEUS 에너지 민주화
  Asher → grain_stock    → KEMET 농업부, EDEN Pishon강
  Zebulun → fish_revenue → KEMET 해양수산부, EDEN Pishon강

_PROMETHEUS_LAYER
  → oil_price_multiplier → KEMET 재무부 비용
  → solar_lcoe           → 에너지부 그리드 투자 효율
  → energy_independence  → KEMET 외교부 동맹 재설정
  → carbon_intensity     → KEMET 농업부 비료 비용

에너지부 (11번째 부처)
  ← PROMETHEUS (lcoe, oil_dep, tipping_point)
  ← KEMET treasury_balance
  ← 파라오 칙령 (solar_reform_decree)
  → PROMETHEUS (policy_push, energy_budget)
  → KEMET 건설부 (grid_investment_signal)

MonetaBridge
  PROMETHEUS → KEMET 재무부 인플레이션 조정
  PROMETHEUS → KEMET GDP 성장 조정

_EDEN_LAYER (4대강 최종 집약)
  Pishon  ← Asher(곡식) + Zebulun(어업) + PROMETHEUS(에너지)
  Gihon   ← Dan(사회안정) + KEMET 보건부
  Hiddekel← Levi(지식) + KEMET 교육부/사법부
  Euphrates← KEMET Ma'at + PROMETHEUS EII
```

---

## Tier 확장 구조

```
TribesSignal v2.0 슬롯 (12지파 전체 완성 ✅):
  Tier 1 (완성):  levi(02), dan(04), asher(07), zebulun(09)     — 4개
  Tier 2 (완성):  reuben(01), simeon(03), issachar(06)          — 3개
  Tier 3 (완성):  gad(05), judah(08), naphtali(10),
                  joseph(11), benjamin(12)                       — 5개

TribesEngineAdapter → TribeCouncil 실제 연결 (v2.0)
None인 슬롯 → 시스템은 기본값으로 정상 동작 (하위 호환)
새 엔진 추가 → tribes_io.py에 슬롯만 채우면 됨 (플러그인 구조 유지)
```

---

## 빠른 시작

```bash
cd ENGINE_HUB

# 기본 50년 시뮬레이션
python _ATON_LAYER/run_aton.py

# 에덴 달성 시나리오 (적극 전환)
python _ATON_LAYER/run_aton.py --scenario eden --years 100 --report

# 석유 충격 시나리오
python _ATON_LAYER/run_aton.py --scenario shock --report

# Nexus 정합성 궤적
python _ATON_LAYER/run_aton.py --coherence

# 테스트 전체 (141/141 ✅)
python -m pytest _ATON_LAYER/tests/ -v

# 테스트 분리 실행
python -m pytest _ATON_LAYER/tests/test_aton.py    -v  # v1.0 기본 (69)
python -m pytest _ATON_LAYER/tests/test_aton_v2.py -v  # v2.0 실제 연결 (72)
```

### Python API

```python
from _ATON_LAYER import Nexus, NexusConfig, make_real_nexus

# ── stub 모드 (기본값, 테스트·프로토타이핑용) ──────────────────────
nexus = Nexus()                      # 내부 어댑터 = 더미 함수
history = nexus.simulate(years=50)

# ── real 모드 (v2.0 실제 엔진 연결) ───────────────────────────────
nexus = make_real_nexus()            # KemetEngineAdapter + TribesEngineAdapter 주입
                                     # → 실제 _rk4_step ODE + TribeCouncil(12지파) 실행
history = nexus.simulate(years=50)

# real 모드 커스텀 파라미터
from kemet_engine.kemet_core import KemetParams
nexus = make_real_nexus(
    kemet_params=KemetParams(population=5_000_000),
    use_real_kemet=True,
    use_real_tribes=True,
)

# 파라오 칙령 포함
history = nexus.simulate(
    years=50,
    external_sequence={
        10.0: {"solar_reform": True, "policy_push": 0.8},
        25.0: {"jubilee": True},
    }
)

# 최종 상태 출력
nexus.report(history[-1])
print(f"Ω_nexus = {history[-1].nexus_coherence:.3f}")
```

---

## 파라오 대시보드 플래그 (12개)

| 플래그 | 조건 | 의미 |
|--------|------|------|
| `energy_transition_active` | R > 5% | 에너지 전환 진행 중 |
| `oil_shock_active` | OWE 급등 | 현재 석유 충격 |
| `energy_tipping_point` | R > 35% | 투자 폭발 시작 |
| `energy_independent` | EII > 75% | 에너지 독립 달성 |
| `petrodollar_risk` | D < 25% | 페트로달러 체계 위기 |
| `social_crisis` | ST > 0.7 | 사회 불안 |
| `food_crisis` | FSI < 0.3 | 식량 위기 |
| `minsky_ponzi` | 폰지 단계 | 금융 불안정 |
| `overfishing_emergency` | fleet="EMERGENCY" | 어족 붕괴 위기 |
| `jubilee_triggered` | c ≥ 0.65 | 희년 자동 발동 |
| `maat_healthy` | Ma'at > 0.6 | 사회 질서 건전 |
| `eden_state` | Ω > 0.75 | 에덴 상태 달성 |

---

## 알고리즘 계보

```
창세기 2:10-14 (4대강 흐름)
아크나톤 태양 개혁 (BC 1353)
        ↓
_PROMETHEUS_LAYER (Wright's Law + Minsky Tipping)
KEMET Engine (10부처 결합 ODE)
70_TRIBES_LAYER (12지파 독립 엔진)
_EDEN_LAYER (Shannon 엔트로피 + 가역적 이벤트 소싱)
        ↓
_ATON_LAYER v2.0.0
인터페이스 계약 + 브릿지 + Nexus 오케스트레이터
(KEMET 실제 연결 + 12지파 TribeCouncil 실제 연결)
```

---

## 버전 정보

| 버전 | 상태 | 내용 |
|------|------|------|
| v1.0.0 | ✅ 완료 | Nexus 오케스트레이터 + stub 어댑터 · 69 테스트 |
| v2.0.0 | ✅ 완료 | KEMET ODE 실제 연결 + 12지파 TribeCouncil 실제 연결 · 141 테스트 |
| v3.0.0 | 🔲 예정 | PROMETHEUS 실제 연결 + EDEN 실제 연결 |
| v4.0.0 | 🔲 예정 | AI 파라오 연동 (자율 칙령 시스템) |

---

*v2.0.0 — ENGINE_HUB/_ATON_LAYER*
*테스트: 141/141 ✅ | 인터페이스: 4개 | 브릿지: 3개 + KemetAdapter + TribesAdapter | 12지파 전체 연결*
