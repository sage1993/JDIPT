# Task 9 Deterministic Render Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove deterministically that every canonical proposition required by the Task 8 material-obligation closure is present in the final rendered answer.

**Architecture:** Derive the required proposition IDs only from the canonical Task 8 ledger after revalidating the trusted registry closure. Reuse the existing exact normalized render-slot matcher for presence, persist an auditable coverage result through the existing reconciliation evidence path, and fail closed when authority, identity, or deterministic evaluation is unavailable. Semantic soundness remains a separate existing gate.

**Tech Stack:** Python 3, dataclasses, pytest, existing `RegistryService`, `RegistryClosureResult`, `PropositionRenderContract`, and exact render reconciliation primitives.

**Spec:** Task 9 Deterministic Render Coverage requirements supplied in the user request.

## Global Constraints

- Start from Task 8 accepted SHA `c8e2354f2ba5c3156c360e8c2139909399428998`.
- Keep `RegistryService` as the sole canonical writer and `RegistryService.read_state()` as the production reader.
- Derive required propositions from `SOURCE_CONFIRMED` ledger links, verified evidence, and linked canonical propositions; never infer them from the final answer.
- Render Coverage checks deterministic presence/completeness only; Semantic Soundness remains responsible for context, polarity, OPEN/CLOSED promotion, contradiction, and generic-relaxation behavior.
- Do not auto-repair, inject, mutate registry/ledger state, add network/model dependencies, or hard-code ASH-06 values.
- Preserve Task 6–8 activation, trusted ingress, pending restart, stale, shadow, and malformed-state contracts.

---

### Task 1: Add RED coverage and authority tests

**Files:**
- Create: `tests/test_proposition_render_coverage.py`
- Create: `tests/test_task9_deterministic_render_coverage.py`

**Interfaces:**
- Tests will define the desired `RenderCoverageResult`, authoritative required-set derivation, deterministic exact-slot coverage, and stop-gate integration behavior before production code exists.

- [ ] **Step 1: Write focused failing tests**

Cover complete, missing, exception-missing, extra prose, duplicate rendering, registry-only false green, keyword-only false green, malformed identity, normal empty required set, authority-failure empty set, and coverage/soundness separation. Use generic proposition IDs and fixture text rather than domain-specific constants.

- [ ] **Step 2: Run the focused tests and verify the expected RED failure**

Run `python -m pytest -q tests/test_proposition_render_coverage.py tests/test_task9_deterministic_render_coverage.py`. The failure must be caused by the missing Task 9 module/API, not a test collection or fixture error.

- [ ] **Step 3: Commit the RED tests**

Commit only the two new test files with `test: add deterministic render coverage red tests`.

### Task 2: Implement the deterministic coverage primitive

**Files:**
- Create: `scripts/proposition_render_coverage.py`
- Test: `tests/test_proposition_render_coverage.py`

**Interfaces:**
- Produce `RenderCoverageResult` with required IDs, covered IDs, missing IDs, `coverage_passed`, and an auditable failure reason.
- Produce a required-set derivation function that accepts the canonical `MaterialObligationLedger`, trusted `RegistryClosureResult`, and canonical `LegalProposition` sequence.
- Reuse `build_render_contract` and `reconcile_render_contracts`; do not introduce keyword, embedding, or LLM matching.

- [ ] **Step 1: Implement only enough for the focused tests**

Validate the ledger/closure/proposition identity chain, require a passing Task 8 closure before coverage, select only `SOURCE_CONFIRMED` linked proposition IDs, allow a genuinely empty confirmed set, and return failure evidence for malformed or unavailable authority. Compare exact deterministic render slots against the complete final draft and tolerate extra text or duplicate occurrences.

- [ ] **Step 2: Run focused tests and verify GREEN**

Run `python -m pytest -q tests/test_proposition_render_coverage.py`. Confirm all coverage matrix cases pass.

- [ ] **Step 3: Refactor without changing behavior**

Keep identity extraction, required-set validation, and render comparison small and auditable. Re-run the focused tests.

- [ ] **Step 4: Commit the primitive**

Commit the implementation and its tests with `feat: add deterministic render coverage gate`.

### Task 3: Integrate coverage at the canonical stop boundary

**Files:**
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `scripts/synthesis_runtime_state.py`
- Test: `tests/test_task9_deterministic_render_coverage.py`
- Test: `tests/test_task8_material_obligation_registry_closure.py`

**Interfaces:**
- Consume state only through `RegistryService.read_state()` and use its canonical Task 8 ledger/propositions.
- Persist compact coverage evidence alongside existing reconciliation evidence through `record_reconciliation`/`update_runtime_state`; do not add a writer or alternate state reader.
- Include coverage failure in the final release decision while keeping existing soundness and obligation closure evaluations independent.

- [ ] **Step 1: Add failing stop-gate integration tests**

Prove that a passing Task 8 registry closure with an omitted final proposition is blocked, that required exception omission is blocked, and that a proposition present only in quotation/example context still satisfies coverage while the existing soundness gate may block it.

- [ ] **Step 2: Run the integration tests and verify RED**

Run `python -m pytest -q tests/test_task9_deterministic_render_coverage.py`. Confirm the current stop gate does not yet expose or enforce the Task 9 coverage result.

- [ ] **Step 3: Add the minimal integration**

Evaluate coverage after the canonical registry closure, pass the result into the existing reconciliation summary, include it in `overall_covered`, and include missing IDs/authority failures in the failure reason. Preserve legacy non-Task-8 behavior and all existing soundness/obligation calls.

- [ ] **Step 4: Run Task 8/9 and authority-focused suites**

Run `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py tests/test_task9_deterministic_render_coverage.py tests/test_task6_registry_service.py tests/test_task7_registry_runtime_authority.py tests/test_registry_runtime_bridge.py`.

- [ ] **Step 5: Commit the integration**

Commit only the stop/runtime evidence changes and affected tests with `feat: enforce render coverage at stop boundary`.

### Task 4: Document acceptance and run all gates

**Files:**
- Create: `docs/task9-deterministic-render-coverage-acceptance.md`

**Interfaces:**
- Document the actual base/final SHA, branch/worktree state, coverage matrix, authority regressions, focused/integration/regression/full verification output, review findings, changed files, commits, push state, residual risks, and Task 10 readiness.

- [ ] **Step 1: Run repository verification**

Run the repository-required commands and record only fresh output: focused tests, Task 8/9 integration, authority integration, Task 1R–5 regression, full `pytest`, `compileall`, `validate_repo`, authority/temporal validation, `npm audit`, MCP smoke, plugin integrity, candidate parity, and `git diff --check`.

- [ ] **Step 2: Perform independent review against all 14 questions**

Inspect the diff and verify no answer-derived required set, registry-only acceptance, keyword false green, fail-open malformed/empty authority, new writer/reader, shadow/stale bypass, soundness merge, ASH-specific production matcher, or oracle weakening exists.

- [ ] **Step 3: Write the acceptance document and verify it**

Populate actual command results and final verdict. Re-run `git diff --check` and relevant tests after documentation changes.

- [ ] **Step 4: Commit acceptance documentation**

Commit only the Task 9 acceptance document with `docs: record Task 9 deterministic render coverage acceptance`.

- [ ] **Step 5: Push the branch only after PASS**

Run `git push -u origin codex/task9-deterministic-render-coverage` only after every required gate is fresh and green. Do not create a PR or merge to main.
