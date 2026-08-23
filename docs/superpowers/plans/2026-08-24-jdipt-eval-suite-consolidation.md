# JDIPT Evaluation Suite Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** JDIPT의 실제 LLM 회귀 실행을 Core 14건 / Full active 26건으로 축소하면서 기존 E1~E42 계약과 추적성을 보존한다.

**Architecture:** E1~E46은 catalog로 보존하고 `suite-manifest.json`이 실제 실행군을 결정한다. Runner와 release gate는 manifest를 읽어 실행하며, 신규 v0.2.3 behavior는 E43~E46 네 건으로 통합한다.

**Tech Stack:** Python 3, pytest, Markdown eval fixtures, JSON suite/oracle manifests, Codex CLI regression runner.

**Spec:** `docs/superpowers/specs/2026-08-24-jdipt-eval-suite-consolidation-design.md`

## Global Constraints

- E1~E42 기존 fixture를 삭제하지 않는다.
- 기본 출력 4단 및 법제처 1~3 계약을 변경하지 않는다.
- `allow_implicit_invocation: false`를 유지한다.
- `korean-law-mcp` 버전을 변경하지 않는다.
- package/plugin version bump는 이번 PR 범위에 포함하지 않는다.
- 기존 v0.2.2 fail-closed 계약을 약화하지 않는다.

---

### Task 1: Suite manifest와 deterministic 검증

**Files:**
- Create: `skills/law-interpretation-request/evals/suite-manifest.json`
- Create: `scripts/eval_suite.py`
- Create/Modify: `tests/test_eval_suite.py`

**Interfaces:**
- Produces: `load_suite_manifest()`, `suite_case_ids(name)`, Core/Full/Legacy ID 집합

- [ ] RED: manifest가 없으면 테스트가 실패하도록 Core=14, Full=26, Legacy=20, union=E1~E46 조건을 작성한다.
- [ ] `suite-manifest.json`에 정확한 케이스 목록과 legacy coverage mapping을 작성한다.
- [ ] `scripts/eval_suite.py`에서 중복·누락·잘못된 case ID를 fail-closed 검증한다.
- [ ] pytest로 manifest contract를 검증한다.

### Task 2: v0.2.3 E43~E46 통합

**Files:**
- Modify: `skills/law-interpretation-request/evals/v0.2.3-authority-temporal-evidence.md`
- Modify: `scripts/validate_authority_temporal_contract.py`
- Modify: `tests/test_authority_temporal_evidence_contract.py`

**Interfaces:**
- Produces: E43 Temporal lifecycle, E44 temporal unknown, E45 authority/versioning, E46 claim/inference

- [ ] 기존 E43~E48 문서를 E43~E46 네 시나리오로 재작성한다.
- [ ] validator/test의 expected range를 E43~E46으로 변경한다.
- [ ] 기존 E48 관련 의미가 E44에 보존되는지 확인한다.

### Task 3: Oracle catalog E1~E46 확장

**Files:**
- Modify: `skills/law-interpretation-request/evals/machine-oracles.json`
- Modify: `scripts/regression_oracles.py`
- Modify: `tests/test_regression_oracles.py`

**Interfaces:**
- Consumes: E1~E46 catalog
- Produces: 기존 checks + v0.2.3 semantic guard checks

- [ ] registry test를 E1~E46 catalog 기준으로 변경한다.
- [ ] E43~E46 oracle 정의를 추가한다.
- [ ] temporal/authority/evidence 최소 semantic guard를 구현한다.
- [ ] 기존 E18/E37 등 강한 oracle 회귀 테스트를 유지한다.

### Task 4: Runner를 manifest 기반 suite 실행으로 변경

**Files:**
- Modify: `run_jdipt_full_regression_v4.py`
- Test: `tests/test_regression_runner.py` 또는 신규 targeted test

**Interfaces:**
- Adds CLI: `--suite core|full|legacy|all`
- Keeps CLI: `--from-case`, `--to-case` targeted selection

- [ ] `load_all_cases()`가 E1~E46 catalog를 로딩하도록 v0.2.3 eval 파일을 포함한다.
- [ ] `--from-case/--to-case` 기본값을 None으로 바꾸고 지정 시 targeted 실행을 우선한다.
- [ ] range 미지정 시 `--suite full`의 26건만 선택한다.
- [ ] summary에 suite name과 selected case IDs를 기록한다.

### Task 5: Release Gate Core/Full 분리

**Files:**
- Modify: `scripts/run_release_gate.py`
- Modify: `tests/test_release_gate.py`

**Interfaces:**
- Gate B: Core 14 cases
- Gate C: Full active 26 cases

- [ ] `CRITICAL_CASES` 하드코딩을 manifest Core로 대체한다.
- [ ] E37만 2회 실행하도록 repeat 정책을 축소한다.
- [ ] Gate C acceptance를 process 26/26, environment 0/26, H1 24/26, hygiene/url/oracle 26/26으로 변경한다.
- [ ] 테스트의 실행 횟수는 하드코딩 숫자가 아니라 suite/repeat에서 계산한다.

### Task 6: Repo validator와 문서 동기화

**Files:**
- Modify: `scripts/validate_repo.py`
- Modify: `docs/architecture.md`
- Modify: `docs/plugin-packaging.md`
- Modify: PR #9 body

- [ ] machine oracle catalog E1~E46 및 suite manifest 존재를 validator가 확인하도록 한다.
- [ ] architecture에 Core/Full/Legacy tier를 기록한다.
- [ ] 과거 v0.2.2 42/42 기록은 historical result로 보존하되 candidate 실행 방식은 14/26으로 설명한다.
- [ ] PR 본문을 새 평가 구조와 검증 명령으로 갱신한다.

### Task 7: Verification

- [ ] `python scripts/validate_repo.py`
- [ ] `python scripts/validate_authority_temporal_contract.py`
- [ ] `python -m pytest -q`
- [ ] `python scripts/run_release_gate.py` — installed runtime sync 후 Gate A 확인
- [ ] `python run_jdipt_full_regression_v4.py --suite core`
- [ ] `python run_jdipt_full_regression_v4.py --suite full`

전체 live 검증은 설치 runtime을 현재 PR branch와 동기화한 환경에서만 PASS로 인정한다.
