# JDIPT Evaluation Suite Consolidation Design

## 1. 목적

JDIPT의 E1~E42 회귀군과 v0.2.3 신규 behavior를 단순 누적하면 실제 Codex/LLM 실행 수가 기능 추가에 비례해 계속 증가한다. 평가 속성 자체는 유지하되 모든 역사적 fixture를 매번 독립 호출하는 구조를 중단한다.

핵심 원칙은 **계약 수와 실행 케이스 수를 분리**하는 것이다.

- 계약·oracle은 유지하거나 강화한다.
- 하나의 대표 시나리오에서 여러 계약을 동시에 검증한다.
- 과거 케이스는 삭제하지 않고 legacy catalog로 보존한다.
- PR용 Core와 릴리스용 Full active를 명시적으로 분리한다.

## 2. 목표 구조

### Core suite — 14 cases

`E02, E03, E09, E13, E18, E31, E36, E37, E39, E41, E43, E44, E45, E46`

검증 범위:

- 법제처 적합성 보정
- 정보 부족 처리
- 핵심 누락 전제
- 동일 용어 충돌
- 사실-요건 연결과 조건부 결론
- 핵심 Golden Cases
- Counterevidence
- Referenced Source Resolution
- 적용 기준시점
- 기준시점 미확인 fail-closed
- Authority / precedent versioning
- Source Claim / Analytical Inference

### Full active suite — 26 cases

`E01, E02, E03, E04, E05, E06, E08, E09, E11, E12, E13, E14, E15, E18, E25, E31, E35, E36, E37, E38, E39, E41, E43, E44, E45, E46`

Core에 더해 다음을 보강한다.

- 법제처 제출 형식
- 명확한 문언/예외/법률간 관계
- 공식 source-link
- 전건 부정/후건 긍정/거짓 양자택일/필요충분조건
- 질의요지 사실 최소화
- 복수 독립 쟁점 렌더링
- 규율공백 Golden Case

### Legacy catalog — 20 cases

`E07, E10, E16, E17, E19, E20, E21, E22, E23, E24, E26, E27, E28, E29, E30, E32, E33, E34, E40, E42`

기존 행동의 역사적 추적성을 위해 fixture와 base oracle 정의는 유지하지만 기본 Core/Full 실행에서는 제외한다.

## 3. 신규 v0.2.3 케이스 통합

초기 E43~E48 여섯 건을 네 건으로 통합한다.

- **E43 Temporal lifecycle**: 과거 허가 + 개정법 + 경과조치 + 변경허가
- **E44 Temporal unknown fail-closed**: material date 미확인
- **E45 Authority + precedent versioning**: 법제처 vs 대법원 + 구법/개정법 선례 적합성
- **E46 Claim-level evidence**: Source Claim / Analytical Inference

## 4. Coverage mapping

| Legacy | 대표 Active | 이유 |
|---|---|---|
| E07 | E01 | 법제처 1~3 출력 구조 |
| E10 | E04 | 정상 조건논증 + 기본 출력 |
| E16 | E31 | 미확인 사실의 조건부 결론 |
| E17 | E06 | 비정형 규정관계 자연어 해석 |
| E19 | E04 | 기본 output hygiene |
| E20 | E15 | 필요조건/충분조건 오류 수정 |
| E21 | E04 | Answer-first |
| E22 | E01 | 법제처 1~3 |
| E23 | E04 | Markdown 기본 4단 |
| E24 | E08 | 공식자료·URL |
| E26 | E08 | 실제 source/runtime smoke는 release 검증과 결합 |
| E27 | E36 | 법적 분류 |
| E28 | E36 | 본칙·예외 |
| E29 | E37 | 동일 사항 중복규율 |
| E30 | E38 | 규율공백·일반법 보충 |
| E32 | E36 | 문제 발생 지점 |
| E33 | E04 | Answer-first |
| E34 | E36 | 단일 쟁점 narrative |
| E40 | E39 | 부재 논증 + 별지 Counterevidence |
| E42 | E41 | unresolved referenced source + rendering |

E11, E12, E14, E15는 서로 다른 추론 오류이므로 Full active에서 독립 유지한다.

## 5. 구현 구조

### `evals/suite-manifest.json`

Core/Full/Legacy와 coverage mapping의 단일 원본이다.

### Oracle registry

기존 `machine-oracles.json`은 `validate_repo.py`와의 호환성을 위해 E1~E42 base registry로 유지한다. 신규 E43~E46은 `v0.2.3-machine-oracles.json`에 별도 보관한다.

`regression_oracles.py`는 실행 시 두 registry를 합쳐 E1~E46 전체 catalog를 검증한다.

### `scripts/run_eval_suite.py`

- 모든 fixture를 E1~E46 catalog로 로딩한다.
- 기본 실행은 `full` suite 26건이다.
- `--suite core|full|legacy|all`을 제공한다.
- `--from-case/--to-case`가 있으면 targeted 실행을 우선한다.

### `scripts/run_release_gate.py`

- Gate A: 기존 validator + v0.2.3 validator + pytest + syntax/diff + runtime integrity
- Gate B: Core 14건, E37만 2회
- Gate C: Full active 26건
- Gate D: package/static

## 6. 성공 기준

- 기본 live Full regression 호출 수: 42 → 26
- Core case 수: 14
- Core stability 실제 호출 수: 15(E37 2회 포함)
- 신규 v0.2.3 behavior: 6 → 4
- 기존 E1~E42 fixture 삭제 없음
- 기존 deterministic contract 약화 없음
- Core/Full/Legacy 분류가 manifest 한 곳에서 관리됨
- 과거 42/42 결과는 historical v0.2.2 validation으로 보존됨
