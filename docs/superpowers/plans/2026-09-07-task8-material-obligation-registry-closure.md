# Material Obligation Registry Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically verify that every independently supplied material obligation closes through verified source evidence into the canonical proposition registry.

**Architecture:** Add a typed material-obligation ledger that references existing `EvidenceRef` and `LegalProposition` objects. Persist the optional ledger inside the existing exact-turn `RuntimeTurnState` through the sole `RegistryService` writer, and make Stop include a registry closure result alongside the existing source and answer closure checks.

**Tech Stack:** Python 3, dataclasses, `StrEnum`, pytest, existing atomic JSON persistence and registry service.

**Spec:** `docs/superpowers/specs/2026-09-07-task8-material-obligation-registry-closure-design.md`

## Global Constraints

- Preserve `RegistryService` as the single production registry writer and `RegistryService.read_state()` as the production read boundary.
- Use existing canonical `EvidenceRef`, authority semantics, temporal semantics, and `LegalProposition` objects.
- Unknown or malformed source statuses fail closed; no silent normalization, source-less repair, fallback, or shadow authority.
- Do not infer required obligations from registered propositions or build a generic NLP extractor.
- Do not add ASH-06-specific production markers or weaken existing test or validator oracles.
- Do not change the installed `sage1993` binding, root dirty worktree, or unrelated files.

---

### Task 1: RED tests for the typed ledger and closure gate

**Files:**
- Create: `tests/test_task8_material_obligation_registry_closure.py`
- Test fixtures: use generic issue types such as `BASE_RULE` and `RANGE_EXCEPTION`, existing `EvidenceRef`, and existing canonical `LegalProposition` fields.

**Interfaces:**
- Tests specify `ObligationSourceStatus`, `MaterialObligation`, `MaterialObligationLedger`, and `evaluate_registry_closure`.
- Tests cover status rejection, confirmed/unresolved/not-applicable states, every required negative closure scenario, valid unresolved state, and the base-plus-exception completeness false-green.

- [ ] **Step 1: Write the failing status and closure tests**

```python
def test_confirmed_obligation_requires_a_linked_proposition():
    result = evaluate_registry_closure(
        (obligation("O_BASE", "BASE_RULE", SOURCE_CONFIRMED, evidence=("law-base",), propositions=("P_BASE",)),),
        (evidence("law-base"),),
        (),
    )
    assert result.registry_closure_passed is False


def test_unresolved_obligation_cannot_promote_an_open_or_closed_proposition():
    result = evaluate_registry_closure(
        (obligation("O_RANGE", "RANGE_EXCEPTION", SOURCE_UNRESOLVED, propositions=("P_RANGE",)),),
        (),
        (closed_proposition("P_RANGE"),),
    )
    assert result.registry_closure_passed is False


def test_required_exception_is_not_hidden_by_a_base_proposition_only():
    ledger = (
        obligation("O_BASE", "BASE_RULE", SOURCE_CONFIRMED, evidence=("law-base",), propositions=("P_BASE",)),
        obligation("O_RANGE", "RANGE_EXCEPTION", SOURCE_CONFIRMED, evidence=("law-range",), propositions=("P_RANGE",)),
    )
    result = evaluate_registry_closure(ledger, (evidence("law-base"),), (closed_proposition("P_BASE"),))
    assert result.registry_closure_passed is False
```

- [ ] **Step 2: Run only the new tests and verify the feature-missing RED**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py`

Expected: collection/test failures because the Task 8 public domain module and APIs do not yet exist. No production implementation is written before this RED result.

### Task 2: Minimal typed obligation domain and deterministic closure

**Files:**
- Create: `scripts/material_obligation_ledger.py`
- Modify: `scripts/proposition_source_closure.py` to expose the existing authority and temporal checks as public reuse points.
- Test: `tests/test_task8_material_obligation_registry_closure.py`

**Interfaces:**
- `ObligationSourceStatus(StrEnum)` has exactly `SOURCE_CONFIRMED`, `SOURCE_UNRESOLVED`, and `NOT_APPLICABLE`.
- `MaterialObligation(obligation_id, issue_type, source_status, evidence_source_ids, proposition_ids)` validates typed status, identifiers, and unique links.
- `MaterialObligationLedger(obligations, verified_source_evidence)` validates typed evidence and unique source IDs.
- `evaluate_registry_closure(required_obligations, resolved_source_evidence, registered_propositions) -> RegistryClosureResult` compares all three explicit sets.
- `validate_registry_closure` delegates to the same deterministic implementation.

- [ ] **Step 1: Implement only the status/value validation needed by the RED tests**

Use exact enum construction and strict `isinstance` checks. Reject raw unknown status strings, non-string IDs, duplicate IDs, malformed evidence, and invalid links; do not strip or guess status values.

- [ ] **Step 2: Run the focused status tests**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py -k status`

Expected: PASS for the typed status tests.

- [ ] **Step 3: Implement closure checks in deterministic input order**

Require confirmed obligations to have resolved evidence and at least one linked proposition. Require every linked proposition to be material, CLOSED, and bound to an exact verified `EvidenceRef`; reuse source-closure authority and temporal checks. Reject unresolved-to-CLOSED, invalid NOT_APPLICABLE linkage, missing required obligations, and any material CLOSED proposition whose evidence is absent from the explicit resolved evidence set.

- [ ] **Step 4: Run all focused closure tests**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py`

Expected: PASS for all status, positive, negative, temporal, and completeness cases.

### Task 3: Integrate ledger persistence through RegistryService

**Files:**
- Modify: `scripts/synthesis_runtime_state.py`
- Modify: `scripts/proposition_registry.py`
- Test: `tests/test_task8_material_obligation_registry_closure.py`

**Interfaces:**
- `RuntimeTurnState.material_obligation_ledger` is optional for legacy compatibility and is serialized/deserialized at the canonical exact-turn state boundary.
- `RegistryService.record_material_obligation_ledger(expected, ledger) -> RuntimeTurnState` is the only ledger persistence transition.

- [ ] **Step 1: Add failing persistence and service-authority tests**

Assert that a ledger survives `RegistryService.record_material_obligation_ledger` and `RegistryService.read_state`, that the ledger participates in stale CAS protection, and that direct persistence helpers are not used as a new consumer writer.

- [ ] **Step 2: Run the persistence tests to verify RED**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py -k persistence`

Expected: FAIL because the runtime state has no ledger field or service transition yet.

- [ ] **Step 3: Implement optional state serialization and the service transition**

Keep the existing schema version and required fields backward-compatible. Treat a malformed present ledger as `RuntimeStateError`; never fall back to an alternate state. Include the ledger in the registry fingerprint so stale snapshots cannot overwrite it.

- [ ] **Step 4: Run focused persistence and prior authority tests**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py tests/test_task6_registry_service.py tests/test_task7_registry_runtime_authority.py`

Expected: PASS.

### Task 4: Wire Registry Closure into Stop evidence and authority regressions

**Files:**
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `scripts/synthesis_runtime_state.py` reconciliation summary plumbing.
- Test: `tests/test_task8_material_obligation_registry_closure.py`

**Interfaces:**
- Stop evaluates the ledger from the `RegistryService` snapshot and records `registry_closure` evidence beside source and obligation closure.
- Any registry-closure failure blocks or fail-closes under the existing bounded repair protocol.

- [ ] **Step 1: Add failing Stop integration and authority regression tests**

Cover valid ledger closure, missing required exception, shadow ledger ignored, malformed canonical ledger fail-closed, and preservation of the direct-reader AST guard.

- [ ] **Step 2: Run the new integration tests to verify RED**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py -k stop`

Expected: FAIL because Stop does not yet evaluate or persist registry closure.

- [ ] **Step 3: Integrate the gate through `RegistryService.read_state()` only**

Do not add a direct runtime file read, shadow state, fallback, proposition derivation, or new lifecycle writer. Include registry closure in the failure reason and all first/second reconciliation persistence calls.

- [ ] **Step 4: Run focused and Task 6/7/8 integration tests**

Run: `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py tests/test_task6_registry_service.py tests/test_task7_registry_runtime_authority.py tests/test_task5_source_obligation_closure.py`

Expected: PASS.

### Task 5: Refactor, review, and complete verification artifacts

**Files:**
- Modify: `tests/test_task8_material_obligation_registry_closure.py` only for test clarity after green.
- Create: `docs/task8-material-obligation-registry-closure-acceptance.md`

- [ ] **Step 1: Refactor only after green**

Remove duplication while keeping all focused tests green; perform the mutation check against missing proposition, missing evidence, unresolved promotion, temporal mismatch, and omitted obligation.

- [ ] **Step 2: Run the independent review checklist**

Review the final candidate for obligation completeness ownership, confirmed/evidence linkage, unresolved promotion, temporal contradiction, source-less repair, single writer/reader authority, shadow/fallback/stale/malformed handling, ASH-specific hard coding, oracle weakening, and unnecessary NLP framework. Critical and Important findings must both be zero.

- [ ] **Step 3: Run every required verification command on the same candidate snapshot**

Run the focused tests, Task 6/7/8 integration tests, Task 1R–5 regression suite, full `python -m pytest -q`, `python -m compileall scripts tests`, `python scripts/validate_repo.py`, `python scripts/validate_authority_temporal_contract.py`, plugin integrity, MCP smoke, candidate parity, `npm audit`, and `git diff --check`. Record actual counts and exit statuses.

- [ ] **Step 4: Write the acceptance document from fresh command output**

Record base SHA, final SHA, branch, remote SHA, working tree state, closure matrix, authority results, actual verification numbers, review findings, changed files, commits, push result, unchanged root dirty state, unchanged `sage1993` binding, residual Task 9 risks, and `Task 9 readiness: READY` only if every required gate passes.

- [ ] **Step 5: Commit scoped Task 8 changes and push the candidate branch**

Stage only Task 8 files, preserve the root worktree, push `codex/task8-material-obligation-closure`, do not create a PR, merge to main, refresh `sage1993`, or begin Task 9.
