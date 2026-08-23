# JDIPT Evaluation Suite Consolidation Design

## 1. 목적

JDIPT의 E1~E42 회귀군과 v0.2.3 신규 E43~E48 후보를 그대로 누적하면 실제 Codex/LLM 실행 수가 기능 추가에 비례해 계속 증가한다. 평가 속성 자체는 유지하되, 매 실행마다 모든 역사적 fixture를 독립 호출하는 구조를 중단한다.

핵심 원칙은 **계약 수와 실행 케이스 수를 분리**하는 것이다.

- 계약·oracle은 유지하거나 강화한다.
- 하나의 대표 시나리오에서 여러 계약을 동시에 검증한다.
- 과거 케이스는 삭제하지 않고 legacy catalog로 보존한다.
- PR용 Core와 릴리스용 Full active를 명시적으로 분리한다.

## 2. 목표 구조

### Core suite — 14 cases

모든 기능 PR에서 깨지면 안 되는 fail-closed 계약만 실행한다.

`E02, E03, E09, E13, E18, E31, E36, E37, E39, E41, E43, E44, E45, E46`

검증 범위:

- 법제처 적합성 보정
- 정보 부족 처리
- 누락 전제
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

릴리스 전 실제 LLM 회귀에서 실행한다.

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

기존 행동의 역사적 추적성을 위해 fixture와 oracle 정의는 유지하지만 기본 Core/Full 실행에서는 제외한다.

`E07, E10, E16, E17, E19, E20, E21, E22, E23, E24, E26, E27, E28, E29, E30, E32, E33, E34, E40, E42`

각 legacy case는 active case 또는 deterministic test로 커버된다. 필요하면 `--suite legacy` 또는 명시적 `--from-case/--to-case`로 재실행할 수 있다.

## 3. 신규 v0.2.3 케이스 통합

기존 후보 E43~E48 여섯 건을 네 건으로 통합한다.

### E43 Temporal lifecycle

기존 E43(과거 허가) + E44(개정법/변경허가)를 통합한다.

- 최초 허가 시점
- 개정법 공포/시행
- 경과조치
- 후속 변경허가
- 현재법과 과거법의 역할 구분

### E44 Temporal unknown fail-closed

기존 E48을 유지한다.

- 허가일/시행일/변경신청일 미확인
- 날짜 추정 금지
- 조건부 결론 또는 확인 필요

### E45 Authority + precedent versioning

기존 E45(법제처 vs 대법원) + E46(구법 판례 vs 현행 개정법)을 통합한다.

- 정부유권해석과 사법판단의 기능 구분
- 단순 최신자료 우선 금지
- 판례 당시 조문과 현행 조문 비교
- 핵심 문언 개정 시 결론 자동 이전 금지

### E46 Claim-level evidence

기존 E47을 유지한다.

- Source Claim
- Analytical Inference
- 사용자 사실 포섭
- 판례가 사용자 사안을 직접 판단한 것처럼 표현하는 오류 금지

## 4. Coverage mapping

Legacy case는 다음 active case로 대표 실행한다.

| Legacy | 대표 Active | 이유 |
|---|---|---|
| E07, E22 | E01 | 법제처 1~3 출력 구조 |
| E10, E19, E21, E23, E33 | E04 | 정상 조건논증 + 4단 Answer-first/Markdown/hygiene |
| E16 | E31 | 미확인 사실의 조건부 결론 |
| E17 | E06 | 비정형 규정관계 자연어 해석 |
| E20 | E15 | 필요조건/충분조건 오류 수정 |
| E24, E26 | E08 | 공식자료·URL·명시호출 runtime 검증 |
| E27, E28, E32, E34 | E36 | 정의→분류→본칙→예외→문제발생지점→연속논증 |
| E29 | E37 | 동일 사항 중복규율 |
| E30 | E38 | 규율공백·일반법 보충 |
| E40 | E39 | 부재 논증 + 별지서식 Counterevidence |
| E42 | E41 | unresolved referenced source + final rendering |

E11, E12, E14, E15는 서로 다른 추론 오류라 Full active에 독립 유지한다.

## 5. 구현

### `evals/suite-manifest.json`

Core/Full/Legacy ID와 coverage mapping의 단일 원본이다.

### `run_jdipt_full_regression_v4.py`

- 모든 fixture는 E1~E46 catalog로 로딩한다.
- 기본 실행은 `full` suite 26건이다.
- `--suite core|full|legacy|all`을 제공한다.
- `--from-case/--to-case`가 주어지면 suite 선택보다 우선하여 targeted 실행한다.

### `scripts/run_release_gate.py`

- Gate B는 manifest의 Core 14건을 실행한다.
- Gate C는 Full active 26건만 실행한다.
- E37만 2회 실행하여 기존 안정성 반복검증의 취지를 일부 유지한다.

### `machine-oracles.json`

- 기존 E1~E42 정의를 history/catalog로 유지한다.
- E43~E46만 추가한다.
- registry 전체 크기와 실제 실행 suite 크기를 분리한다.

## 6. 성공 기준

- 기본 live full regression 호출 수: 42 → 26 이하
- PR critical case 수: 14
- 신규 v0.2.3 후보: 6 → 4
- 기존 E1~E42 fixture 삭제 없음
- 기존 deterministic contract 약화 없음
- Core/Full/Legacy 분류가 manifest 한 곳에서 관리됨
- runner와 release gate가 하드코딩된 42/42 산술에 의존하지 않음
