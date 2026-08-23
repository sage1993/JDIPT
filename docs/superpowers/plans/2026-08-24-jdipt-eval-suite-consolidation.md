# JDIPT Evaluation Suite Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** JDIPT의 실제 LLM 회귀 실행을 Core 14건 / Full active 26건으로 축소하면서 기존 E1~E42 계약과 추적성을 보존한다.

**Architecture:** E1~E46은 catalog로 보존하고 `suite-manifest.json`이 실제 실행군을 결정한다. Runner와 release gate는 manifest를 읽어 실행하며, 신규 v0.2.3 behavior는 E43~E46 네 건으로 통합한다. 기존 `validate_repo.py`의 E1~E42 registry 계약은 유지하고 E43~E46은 별도 oracle extension과 authority/temporal validator로 검증한다.

**Tech Stack:** Python 3, pytest, Markdown eval fixtures, JSON suite/oracle manifests, Codex CLI regression runner.

**Spec:** `docs/superpowers/specs/2026-08-24-jdipt-eval-suite-consolidation-design.md`

## Global Constraints

- E1~E42 기존 fixture를 삭제하지 않는다.
- 기본 출력 4단 및 법제처 1~3 계약을 변경하지 않는다.
- `allow_implicit_invocation: false`를 유지한다.
- `korean-law-mcp@4.12.1`을 유지한다.
- package/plugin version bump는 이번 PR 범위에 포함하지 않는다.
- 기존 v0.2.2 fail-closed 계약을 약화하지 않는다.

---

### Task 1: Suite manifest와 deterministic 검증

**Files:**
- Create: `skills/law-interpretation-request/evals/suite-manifest.json`
- Create: `scripts/eval_suite.py`
- Create: `tests/test_eval_suite.py`

- [x] Core 14, Full 26, Legacy 20, Catalog E1~E46 계약을 정의한다.
- [x] Core가 Full의 부분집합인지 검증한다.
- [x] Full과 Legacy가 Catalog를 정확히 분할하는지 검증한다.
- [x] Legacy 각 case가 active 대표 case에 연결되는지 coverage mapping을 검증한다.

### Task 2: v0.2.3 E43~E46 통합

**Files:**
- Modify/Create: `skills/law-interpretation-request/evals/v0.2.3-authority-temporal-evidence.md`
- Create: `skills/law-interpretation-request/evals/v0.2.3-machine-oracles.json`
- Modify: `scripts/validate_authority_temporal_contract.py`
- Modify: `tests/test_authority_temporal_evidence_contract.py`

- [x] E43 과거 허가 + 개정법 + 변경허가를 Temporal lifecycle 하나로 통합한다.
- [x] E44 material date 미확인 fail-closed를 독립 유지한다.
- [x] E45 법제처/대법원 authority와 precedent versioning을 통합한다.
- [x] E46 Source Claim / Analytical Inference를 독립 유지한다.
- [x] 기존 E47/E48 별도 실행을 제거한다.

### Task 3: Oracle catalog 호환 구조

**Files:**
- Preserve/Modify: `skills/law-interpretation-request/evals/machine-oracles.json`
- Create: `skills/law-interpretation-request/evals/v0.2.3-machine-oracles.json`
- Modify: `scripts/regression_oracles.py`
- Modify: `tests/test_regression_oracles.py`

- [x] 기존 `validate_repo.py`가 요구하는 E01~E42 base registry를 보존한다.
- [x] E43~E46 oracle을 extension 파일로 분리한다.
- [x] runtime loader에서는 base + extension을 합쳐 E1~E46 catalog로 검증한다.
- [x] combined `release_critical` case가 Core 14와 정확히 일치하도록 한다.
- [x] temporal/authority/evidence semantic guard checks를 추가한다.

### Task 4: Manifest 기반 live runner

**Files:**
- Create: `scripts/run_eval_suite.py`
- Test: `tests/test_eval_suite.py`

- [x] 기존 E1~E42 runner의 안정화된 Codex CLI 해석·plugin integrity·case execution 로직을 재사용한다.
- [x] E1~E46 catalog를 세 eval 문서에서 로딩한다.
- [x] `--suite core|full|legacy|all`을 제공한다.
- [x] 기본 suite는 Full active 26으로 한다.
- [x] `--from-case/--to-case` 지정 시 suite보다 targeted range를 우선한다.
- [x] summary에 suite와 selected case ID를 기록한다.

### Task 5: Release Gate Core/Full 분리

**Files:**
- Modify: `scripts/run_release_gate.py`
- Modify: `tests/test_release_gate.py`

- [x] `CRITICAL_CASES`를 manifest Core 14로 교체한다.
- [x] Gate B를 Core stability로 정의한다.
- [x] E37만 2회 반복하여 실제 Core 호출은 15회로 제한한다.
- [x] Gate C를 Full active 26으로 정의한다.
- [x] Full acceptance 산술을 manifest case 수에서 계산한다.
- [x] Full H1 기대치는 E2/E3 특수형식을 제외한 24/26으로 계산한다.

### Task 6: Repo validator 경계 유지

초기 계획의 `validate_repo.py` 직접 확장은 구현 과정에서 조정했다.

**결정:** 기존 `validate_repo.py`의 E1~E42 static registry 계약을 변경하지 않는다. 대신:

- `scripts/validate_authority_temporal_contract.py`가 E43~E46, suite manifest, oracle extension을 fail-closed 검증한다.
- `scripts/run_release_gate.py`의 Gate A가 기존 validator와 신규 validator를 모두 실행한다.

이 방식은 기존 검증기를 대규모로 변경하지 않으면서 v0.2.3 계약을 추가한다.

### Task 7: 문서 동기화

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/plugin-packaging.md`
- Create: `docs/evaluation-suites.md`
- Update: v0.2.3 spec/plan

- [x] Core/Full/Legacy/Catalog 구조를 문서화한다.
- [x] v0.2.2 42/42는 historical validation으로 남긴다.
- [x] candidate의 기본 live full은 26건임을 구분한다.
- [x] Legacy case가 삭제가 아니라 재현·진단용으로 보존됨을 설명한다.

### Task 8: Fresh verification

최종 PASS는 실제 PR 브랜치 checkout과 설치된 runtime이 일치하는 사용자 환경에서 실행한 결과만 인정한다.

- [ ] `python scripts/validate_repo.py`
- [ ] `python scripts/validate_authority_temporal_contract.py`
- [ ] `python -m pytest -q`
- [ ] `python scripts/plugin_integrity.py`
- [ ] `python scripts/run_eval_suite.py --suite core`
- [ ] `python scripts/run_eval_suite.py --suite full`
- [ ] 필요시 `python scripts/run_release_gate.py --full`

현재 assistant 실행환경에서는 저장소 전체 checkout 기반 검증을 실행할 수 없으므로 이 항목은 완료 표시하지 않는다.
