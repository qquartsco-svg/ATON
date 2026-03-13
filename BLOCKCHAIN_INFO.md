# 🔗 PHAM 블록체인 서명 정보

## 📋 개요

이 **ATON (_ATON_LAYER)** 은 **PHAM (Proof of Authorship & Merit) 블록체인 시스템**으로 서명되어 있습니다.

> 아톤(Aton/Aten, 𓇳) — 이집트 태양신.
> 파라오 아크나톤: "모든 에너지는 하나의 원천으로 귀결된다."
> → 모든 ENGINE_HUB 레이어를 하나의 동역학 흐름으로 통합한다.

---

## 🏛️ 레이어 구성

```
_ATON_LAYER v2.0.0
├── nexus.py              — Nexus 오케스트레이터 + make_real_nexus()
├── aton_core.py          — NexusState, NexusConfig
├── interfaces/
│   ├── kemet_io.py       — KemetInput / KemetOutput
│   ├── tribes_io.py      — TribesSignal v2.0 (12지파 완성)
│   ├── prometheus_io.py  — PrometheusInput / PrometheusOutput
│   └── eden_io.py        — EdenSignal
├── bridges/
│   ├── kemet_adapter.py  — 실제 KEMET ODE 어댑터
│   ├── tribes_adapter.py — 실제 12지파 TribeCouncil 어댑터
│   ├── oil_shock.py      — 석유 충격 라우터
│   ├── energy_ministry.py — 에너지부
│   └── moneta_bridge.py  — 에너지↔화폐 브릿지
└── tests/
    ├── test_aton.py       — 69 테스트
    └── test_aton_v2.py    — 72 테스트 (실제 연결)
```

---

## 🔐 4-Signal Scoring 시스템

각 코드 변경은 다음 4가지 신호로 평가됩니다:

| 신호 | 가중치 | 설명 |
|------|--------|------|
| **Byte Signal** | 25% | 바이트 레벨 변경 비율 |
| **Text Signal** | 35% | 텍스트 유사도 (difflib) |
| **AST Signal** | 30% | AST 구조 변경 분석 |
| **Exec Signal** | 10% | 실행 결과 변화 |

**총점 = (Byte × 0.25) + (Text × 0.35) + (AST × 0.30) + (Exec × 0.10)**

---

## 💰 블록체인 기반 기여도 시스템

**라이선스**: MIT License
**사용 제한**: 없음
**로열티 요구**: 없음

### ⚠️ GNJz의 기여도 원칙 (블록체인 기반)

- 상한선: GNJz의 기여도는 블록체인 기반으로 최대 70% 상한
- 검증 가능성: 블록체인으로 검증 가능한 기여도 상한선
- 투명성: 모든 기여도 계산은 블록체인에 기록되어 검증 가능

이 원칙은 코드가 어떻게 상용화되든, 누가 상용화하든 관계없이 블록체인에 영구 기록됩니다.

---

## 📞 문의

- GitHub: https://github.com/qquartsco-svg/ATON
- Issues: https://github.com/qquartsco-svg/ATON/issues

---

**작성일**: 2026-03-14
**버전**: 2.0.0
**작성자**: GNJz (Qquarts)
