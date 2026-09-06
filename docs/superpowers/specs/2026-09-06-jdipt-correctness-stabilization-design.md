# JDIPT Correctness Stabilization Design

**Date:** 2026-09-06  
**Status:** Design approved in principle — written specification for review  
**Scope:** Correctness / runtime / release stabilization only  
**Primary approach:** R2 Canonical Core convergence

---

## 1. Objective

JDIPT의 기존 Skill-first 법령해석 구조를 유지하면서, 감사에서 확인된 correctness·runtime·release false-green 원인을 구조적으로 제거한다.

이번 안정화의 목표는 특정 ASH-06 답안을 하드코딩하여 통과시키는 것이 아니다. 다음 불변식을 일반화하여 고정하는 것이 목표다.

1. 모델이 검사 대상 material proposition 집합까지 임의로 결정하지 못한다.
2. verified source와 proposition 사이의 provenance가 끊기지 않는다.
3. proposition이 답변에 존재하는 것과 최종 결론으로 채택되는 것을 구분한다.
4. runtime state writer 간 갱신이 서로를 덮어쓰지 않는다.
5. release PASS는 필수 suite·hard gate·동일 snapshot evidence를 모두 충족한 경우에만 선언된다.
6. repository, installed bundle, active runtime을 서로 다른 검증 대상으로 취급한다.

---

## 2. Non-Goals

이번 안정화에서 다음은 구현하지 않는다.

- 새 법률 분야 확대
- ChatGPT Web MCP App
- Knowledge Graph
- IFC/BIM 연계
- 새 UI
- 범용 법률 NLP extractor
- 새로운 대규모 orchestration framework
- Skill 역할별 분리
- ASH-06 전용 숫자/문구 하드코딩
- oracle 기준 완화
- 기존 사용자 작업 삭제/정리

---

## 3. Baseline Strategy

현재 프로젝트에는 세 개의 유효한 개발 축이 있다.

### R1
`fix/ansim-structural-behavior-stability`

기존 runtime enforcement와 synthesis integrity가 존재한다.

### R2
`refactor/legal-proposition-core-working2`

다음 canonical 구조가 존재한다.

- `scripts/legal_proposition.py`
- `scripts/proposition_registry.py`
- `scripts/proposition_rendering.py`
- `scripts/proposition_reconciliation.py`
- `scripts/synthesis_runtime_state.py`
- CI workflow

### L1
현재 사용자 로컬 R1 기반 dirty 작업.

Task 14E 계열에서 다음 기능이 추가·수정된 것으로 보고되어 있다.

- registry required/completed
- bounded exact-turn enforcement
- atomic registry completion
- deterministic range-exception relation
- second reconciliation
- runtime/install parity evidence

### Baseline decision

R2를 canonical domain core로 사용한다.

L1에서 R2에 없는 runtime enforcement 기능은 R2로 port한다.

R1 중복 구현은 즉시 삭제하지 않고 먼저 다음 상태로 분류한다.

- KEEP
- PORT_TO_R2
- DELETE_AFTER_PARITY
- UNKNOWN

첫 production 변경 전 반드시 convergence matrix를 작성한다.

---

## 4. Target Architecture

```text
User Question
    ↓
Legal Issue Mapping
    ↓
Material Obligation Ledger
    ↓
Source Acquisition / Verification
    ↓
Canonical LegalProposition Registry
    ↓
Registry Closure Gate
    ↓
Deterministic Render Coverage
    ↓
Semantic Soundness Gate
    ↓
Exact-turn Runtime Enforcement
    ↓
Unified Release / Acceptance Authority
```

각 계층은 하나의 질문만 책임진다.

### 4.1 Material Obligation Ledger

질의에서 검토해야 하는 material legal issue를 표현한다.

예:

```text
O1: BASE_RULE
O2: RANGE_EXCEPTION
O3: TEMPORAL_CURRENT_STATUS
```

각 obligation은 반드시 다음 상태 중 하나다.

```text
SOURCE_CONFIRMED
SOURCE_UNRESOLVED
NOT_APPLICABLE
```

`SOURCE_CONFIRMED`인 material obligation은 최소 하나의 canonical proposition에 연결되어야 한다.

`SOURCE_UNRESOLVED`는 확정 결론으로 승격할 수 없다.

### 4.2 Canonical Legal Proposition

R2 `LegalProposition`을 단일 domain model로 사용한다.

CLOSED proposition은 다음을 요구한다.

- legal relation fields
- evidence reference
- authority
- source locator
- evidence span
- temporal status

OPEN proposition은 source 미확정 또는 적용 미확정 상태를 표현한다.

### 4.3 Registry Closure Gate

Registry가 등록된 proposition의 문법만 검증해서는 안 된다.

다음을 비교한다.

```text
required obligations
vs
resolved source evidence
vs
registered propositions
```

다음은 FAIL이다.

- confirmed obligation인데 proposition 없음
- proposition은 있는데 evidence 없음
- source가 unresolved인데 CLOSED proposition 생성
- evidence temporal status와 proposition conclusion이 충돌

### 4.4 Render Coverage Gate

R2 exact render slot을 유지한다.

역할은 오직:

```text
“필수 proposition이 최종 출력에 존재하는가?”
```

이다.

이 계층은 correctness 최종 판정자가 아니다.

### 4.5 Semantic Soundness Gate

Coverage 후 다음을 검사한다.

- mandatory proposition이 단순 인용/예시/배척 영역에만 있지 않은가
- final conclusion이 proposition과 모순되지 않는가
- OPEN proposition을 CLOSED 결론으로 승격하지 않았는가
- polarity가 역전되지 않았는가
- source-specific legal action/effect가 generic relaxation으로 축약되지 않았는가

Coverage와 Soundness를 분리한다.

### 4.6 Runtime Enforcement

L1의 required/completed exact-turn enforcement를 R2 state model에 통합한다.

권고 상태:

```text
activation_state
registry_required
registry_completed
enforcement_count
repair_count
propositions
revision
```

다음 원칙을 유지한다.

- latest-state fallback 금지
- session/turn exact identity
- bounded enforcement
- repair exhausted 후 fail-closed
- unrelated turn은 no-op

### 4.7 Transactional State Writer

`load → modify → save`를 여러 writer가 독립 수행하지 않는다.

권고 방식:

```text
per-turn lock
+ latest state reload
+ revision check
+ atomic file replacement
```

SQLite 도입은 현재 범위에서 제외한다.

---

## 5. Canonical Semantic Controls

다음 의미 필드는 자유 문자열로 처리하지 않는다.

### Materiality

```text
MATERIAL
NON_MATERIAL
```

### Modality

```text
MAY
MUST
MUST_NOT
MAY_NOT
```

### Polarity

```text
POSITIVE
NEGATIVE
```

### Proposition status

```text
OPEN
CLOSED
```

Unknown 값은 fail closed 한다.

동의어 정규화는 registry domain model 이전의 명시적 adapter에서만 수행한다.

---

## 6. Source Correctness

`korean-law-mcp`는 외부 source provider이다.

JDIPT는 package 설치 성공과 source correctness를 분리한다.

4.12.2 업그레이드 acceptance는 최소 다음을 포함한다.

- MST-only `eflaw` HTML fallback
- `get_law_text`
- `verify_citations`
- historical law wrapper parsing
- article branch number
- paragraph/item body extraction

`npm audit 0` 또는 `--help` 성공은 source correctness PASS로 간주하지 않는다.

---

## 7. Release Authority

하나의 versioned release contract만 최종 PASS를 선언한다.

필수 입력:

```text
repository snapshot
installed snapshot
active runtime identity
static validation
Core suite
Full suite
Ansim suite
critical hard gates
source correctness
runtime host acceptance
```

다음은 무조건 FAIL이다.

- required suite NOT_RUN
- required case missing
- duplicate case로 case count 충족
- any hard gate violation
- critical negative marker
- evidence generated from another snapshot
- active runtime identity mismatch

성공률 threshold로 hard-gate failure를 상쇄하지 않는다.

---

## 8. Workstreams

### WS-0 — Baseline Convergence

산출물:

- R1/R2/L1 feature matrix
- canonical ownership matrix
- port/delete-later 목록
- 통합 기준 SHA/digest

Gate:

production 변경 전 완료.

---

### WS-1 — Unified Release Authority

대상:

- release manifest
- `run_release_gate.py`
- Ansim acceptance aggregation
- test orchestration

Acceptance:

- `--full`이 모든 필수 suite를 실행
- hard-gate 1건도 전체 PASS 불가
- case identity 누락/중복 차단
- snapshot mismatch 차단

---

### WS-2 — Typed Semantic Controls

대상:

- `legal_proposition.py`
- registry adapter/schema
- rendering

Acceptance:

- unknown materiality/modality/polarity reject
- silent non-material downgrade 불가
- `not required` 등 부분문자열 오분류 불가

---

### WS-3 — Semantic Soundness

대상:

- reconciliation 이후 별도 soundness layer

Acceptance:

- rejected quotation false green 차단
- code block/example false green 차단
- OPEN + contradictory final conclusion 차단
- polarity contradiction 차단

---

### WS-4 — Source / Obligation Closure

대상:

- material obligation model
- source resolution status
- registry closure

Acceptance:

```text
confirmed material obligation
→ source evidence
→ proposition
```

연결이 없으면 FAIL.

Source 없는 repair/injection은 금지.

---

### WS-5 — Transactional Runtime State

대상:

- `synthesis_runtime_state.py`
- registry writer
- repair state mutation

Acceptance:

- register/register concurrent update loss 0
- register/repair concurrent update loss 0
- stale revision overwrite 차단
- repair counter monotonic
- atomic serialization 유지

---

### WS-6 — MCP Source Correctness Upgrade

대상:

- `package.json`
- lockfile
- source regression fixtures

Acceptance:

4.12.2 기능 회귀 검증 후 pin update.

---

### WS-7 — Host Runtime Acceptance

검증 계층:

1. repository parity
2. installed bundle completeness/parity
3. active runtime identity

Host tests:

- no registry call
- partial registry
- PLUGIN_DATA missing
- wrong session
- wrong turn
- corrupted state
- exhausted repair
- stale process
- multiple cache versions

---

## 9. Acceptance Sequence

Targeted ASH-06는 구조 수리 이후 실행한다.

### Stage A — Static

```text
pytest
validate_repo
authority/temporal
compileall
npm ci
npm audit
plugin integrity
diff check
```

### Stage B — Host

```text
repository parity
installed parity
active runtime identity
runtime enforcement probes
```

### Stage C — ASH-06 x3

필수:

```text
runtime              3/3
BASE                 3/3
EXCEPTION            3/3
CURRENT_STATUS       3/3
relation             3/3
critical missing       0
critical negative      0
repair exhausted       0
```

한 run 실패 시 즉시 stop.

### Stage D — ASH-06 x10

Stage C PASS 후에만 실행.

```text
runtime             10/10
semantic            10/10
activation bypass      0
registry missing       0
critical missing       0
critical negative      0
repair exhausted       0
```

### Stage E — Global

```text
Core14
Full26
Ansim9
Ansim stability
package
Windows host acceptance
```

ASH-06 PASS만으로 release-ready를 선언하지 않는다.

---

## 10. Pull Request Decomposition

### PR-A — Baseline / Ownership

- convergence matrix
- canonical ownership
- architecture/spec alignment
- no behavior change

### PR-B — Release Authority + Semantic Enums

- unified release manifest
- mandatory suite enforcement
- typed semantic controls

### PR-C — Soundness Gate

- citation/rejection awareness
- contradiction detection
- OPEN promotion guard

### PR-D — Obligation / Source Closure

- obligation ledger
- closure validation
- evidence linkage

### PR-E — Transactional State

- lock/revision model
- concurrent update regression

### PR-F — MCP 4.12.2

- source regressions
- dependency upgrade

### PR-G — Host Attestation

- completeness/parity/active identity
- host runtime negative tests

### PR-H — Acceptance Evidence

- ASH-06 x3
- ASH-06 x10
- Core/Full/Ansim global gate
- final release decision

PR 순서를 생략하거나 병렬 병합하지 않는다.

---

## 11. Regression Requirements

다음 반례는 permanent regression suite에 포함한다.

### Registry completeness

- base only, required exception missing
- exception source missing
- source confirmed but proposition absent
- unresolved source promoted to CLOSED

### Semantic controls

- `critical`
- `important`
- `not required`
- unknown modality
- unknown polarity

### Soundness

- exact required slot inside rejected quote
- exact slot only inside code block
- OPEN uncertainty plus definitive opposite conclusion
- positive proposition followed by negative final conclusion

### State

- register/register race
- register/repair race
- stale revision writer
- process crash during mutation

### Release

- 26/27 + hard gate fail
- missing required suite
- duplicated case ids
- missing case ids
- mixed snapshot evidence

### Runtime identity

- stale cache
- stale active process
- mismatched repo/install
- multiple installation candidates

---

## 12. Documentation and Evidence Rules

PASS/DONE/FIXED는 다음이 같은 snapshot을 가리킬 때만 사용한다.

```text
repo SHA or content digest
installed runtime digest
active runtime identity
oracle version/digest
test result bundle
```

각 evidence 문서에는 최소 다음을 포함한다.

```text
timestamp
repository SHA
working tree state
installed digest
active runtime identity
oracle version
commands
exit codes
result summary
```

Dirty working tree에 대한 acceptance는 SHA만으로 식별하지 않고 changed-file digest manifest를 추가한다.

---

## 13. Migration Principles

- R1 legacy implementation을 먼저 제거하지 않는다.
- R2 canonical implementation으로 parity를 증명한 뒤 delete-later 처리한다.
- L1 Task14E 변경은 file 단위 cherry-pick을 전제로 하지 않는다.
- 기능/불변식 단위로 port한다.
- 기존 사용자 변경은 항상 보존한다.
- reset, clean, restore, rebase 기반 정리 금지.
- oracle 완화 금지.
- production code에 ASH-specific 숫자/명칭 hard coding 금지.

---

## 14. Definition of Stabilization Complete

다음이 모두 충족되어야 한다.

```text
[ ] R1/R2/L1 convergence complete
[ ] one canonical proposition model
[ ] one domain registry writer
[ ] typed semantic controls
[ ] material obligation closure
[ ] verified evidence binding
[ ] coverage/soundness separation
[ ] transactional runtime state
[ ] exact-turn runtime enforcement
[ ] MCP source correctness verified
[ ] repository/install/active identity separated
[ ] unified release authority
[ ] independent false-green regressions PASS
[ ] ASH-06 3/3 PASS
[ ] ASH-06 10/10 PASS
[ ] Core14 PASS
[ ] Full26 PASS
[ ] Ansim9 PASS
[ ] stability gate PASS
[ ] critical negative = 0
[ ] hard-gate violations = 0
```

하나라도 충족되지 않으면:

```text
Overall: HOLD
```

---

## 15. Architectural Decision

JDIPT는 재작성하지 않는다.

**R2 Canonical Core를 기준으로 유지하고, L1 runtime enforcement와 감사에서 확인된 correctness closure를 그 위에 통합한다.**

핵심 설계 원칙은 다음 세 문장으로 고정한다.

1. **The model may propose legal propositions, but it does not define the complete set of obligations that must be checked.**
2. **Coverage is not soundness.**
3. **Only one release authority may declare PASS for one exact runtime snapshot.**

