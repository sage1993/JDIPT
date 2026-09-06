# Task 1R — R2 L1 Invariant Parity Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port and independently prove the four L1 runtime invariants in the R2 canonical path without changing any oracle gate or using L1/live evidence as R2 evidence.

**Architecture:** R2 remains authoritative for `LegalProposition`, registry persistence, exact-turn state, and Stop orchestration. Explicit activation creates a pending exact-turn state; the canonical registry writer atomically promotes that same state to completed/active; a separate relation module validates a source-linked base→range→exception proposition graph in one sentence span. Evidence is emitted only from the same staged run identity.

**Tech Stack:** Python 3.13, pytest, stdlib dataclasses/enum/json/pathlib/tempfile, existing Codex hook/MCP JSON contracts, SHA-256 manifests.

**Spec:** `docs/superpowers/specs/2026-09-06-jdipt-correctness-stabilization-design.md` and the user-provided Task 1R acceptance contract.

## Global Constraints

- Preserve `F:\2026-PJ\JDIPT` byte-for-byte; all edits remain in the isolated worktree.
- Keep R2 `LegalProposition` and `proposition_registry.py` as the only production domain model/writer.
- Do not copy `runtime_registry_state.py` or `synthesis_integrity.py` into the R2 runtime path.
- Do not weaken oracle conditions, exact counters, relation structure, fail-closed behavior, or required run counts.
- Missing runtime fields are not converted to false/default evidence; the new state schema rejects old incomplete payloads.
- Do not mutate or refresh the installed plugin during this closure; installed mismatch remains a separate acceptance finding.
- Do not enter main-plan Task 2 after this plan; readiness is reported only after the four-invariant matrix and all gates are independently verified.

---

### Task 1: Reconstruct and freeze the evidence chain

**Files:**
- Create: `docs/task1r-evidence/phase-a-chain.md`
- Create: `docs/task1r-evidence/environment-findings.md`
- Create: `docs/task1r-evidence/baseline-commands.txt`

**Interfaces:**
- Consumes: R1 `69dda97106cf094d93d7abb26753a76ed33ea773`, R2 `afa4003ca700f15794dc346e8239c6dda79492e2`, isolated HEAD `1acf04472b071282959f4f9f3dbace35c3fcdaec`, and read-only L1 dirty-tree evidence.
- Produces: a phase-specific producer/consumer/persistence/scope/lifecycle map and explicit classifications for plugin integrity, pytest setup errors, and Windows ACL/cache failures.

- [x] **Step 1: Record exact repository and installed identities**

Run from the isolated worktree:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --branch
python scripts/plugin_integrity.py
```

Record all exit codes and the complete manifest mismatch list. Do not treat the installed cache as R2 evidence while it lacks the R2 files or digests.

- [x] **Step 2: Reproduce the prescribed static environment commands**

```powershell
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python -m pytest -q
```

Record the exact permission-denied paths. Classify their root cause as `C. host/environment-only deviation`; if the approved full-suite gate requires zero setup errors, record the resulting acceptance impact separately as `B. repository acceptance blocker`.

- [x] **Step 3: Write the chain map before production edits**

The map must name these exact R2 boundaries: prompt input → `jdipt_activation.handle_user_prompt_submit` → `create_pending_runtime_state` → PreToolUse `inject_registry_runtime.handle_pre_tool_use` → `jdipt_runtime_mcp.dispatch_json_rpc` → `proposition_registry.register_material_proposition` → `synthesis_runtime_state.save_runtime_state` → `stop_synthesis_gate.handle_stop_event` → relation/slot reconciliation → persisted first/second summary. For every boundary record producer, mutation, consumer, persistence path, identity key, lifecycle state, and failure behavior.

- [ ] **Step 4: Commit only the evidence documents at this boundary**

Proposed message: `docs(task1r): reconstruct R2 parity evidence chain`.

---

### Task 2: Add RED tests for exact-turn registry lifecycle and enforcement

**Files:**
- Create: `tests/test_task1r_registry_parity.py`
- Modify: `tests/test_synthesis_runtime_state.py`
- Modify: `tests/test_proposition_registry.py`
- Modify: `tests/test_jdipt_runtime_mcp.py`
- Modify: `tests/test_stop_synthesis_gate.py`

**Interfaces:**
- Consumes: the existing R2 `LegalProposition`, `RuntimeTurnState`, MCP dispatcher, and Stop hook APIs.
- Produces: failing tests that require explicit pending activation, exact completion transition, exact `registry_enforcement_count` `{0,1}`, same-turn isolation, persisted reconciliation evidence, and no default-substitution for missing new fields.

- [x] **Step 1: Write the pending-state test**

```python
def test_explicit_activation_persists_pending_registry_contract(tmp_path):
    assert handle_user_prompt_submit(_prompt_event(), tmp_path) == {}
    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "PENDING"
    assert state.registry_required is True
    assert state.registry_completed is False
    assert state.registry_enforcement_count == 0
```

- [x] **Step 2: Run the new test and verify the expected RED failure**

Run: `python -m pytest -q tests/test_task1r_registry_parity.py::test_explicit_activation_persists_pending_registry_contract`

Expected: collection/import failure because the R2 activation producer and required state fields do not yet exist.

- [x] **Step 3: Add tests for exact completion and no conflation**

Require the successful canonical registry call to persist `registry_required=True`, `registry_completed=True`, `registry_invocation_count=1`, and `activation_state="ACTIVE"`; require a pending state to remain incomplete until that successful write; reject a payload that omits the new fields; and prove a completed state in `(session-a, turn-a)` cannot satisfy `(session-a, turn-b)`.

- [x] **Step 4: Add tests for exact enforcement count**

Require the first incomplete active Stop to return one block with `registry_enforcement_count=1`, require the next incomplete Stop to fail closed without incrementing to 2, and require an already completed registry to leave the counter at 0 even when render reconciliation later requests a separate bounded repair.

- [x] **Step 5: Run the focused tests and preserve RED output**

Run: `python -m pytest -q tests/test_task1r_registry_parity.py tests/test_synthesis_runtime_state.py tests/test_proposition_registry.py tests/test_jdipt_runtime_mcp.py tests/test_stop_synthesis_gate.py`

Do not edit production code until the new failure is attributable to the absent R2 invariant contract rather than a malformed test.

---

### Task 3: Add RED tests for a structured range-exception relation

**Files:**
- Create: `tests/test_task1r_range_exception_relation.py`
- Create: `scripts/proposition_relations.py` only after the RED test is recorded

**Interfaces:**
- Consumes: R2 `LegalProposition` and `EvidenceRef`.
- Produces: `RangeExceptionRelation`, `build_range_exception_relation`, `render_range_exception_relation`, and `reconcile_range_exception_relation` with source proposition IDs and evidence identity.

- [x] **Step 1: Write positive and negative relation tests**

Construct a base proposition and an exception proposition with explicit `base_rule`, `exception_rule`, `base_proposition_id`, `relation_type`, and one source evidence reference. Require the relation object to preserve base rule, range values, exception trigger, legal act, subject, object, effect, relation type, source ID, and both proposition IDs. Require one contiguous span containing all fields and ordered base→exception direction to pass; separated token co-occurrence, reversed range direction, missing trigger/procedure, and generic “relaxation” effect to fail.

- [x] **Step 2: Run the relation tests and verify RED**

Run: `python -m pytest -q tests/test_task1r_range_exception_relation.py`

Expected: import failure for the new canonical relation module and missing `base_rule`/`exception_rule` proposition fields.

- [x] **Step 3: Keep the test independent of ASH-06 literals**

Use generic distance values in the fixture and assert structure/meaning, not a hard-coded production marker or the presence of unrelated strings elsewhere in the draft.

---

### Task 4: Implement the minimum R2 parity contract

**Files:**
- Create: `scripts/jdipt_activation.py`
- Create: `scripts/proposition_relations.py`
- Modify: `scripts/legal_proposition.py`
- Modify: `scripts/synthesis_runtime_state.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/jdipt_runtime_mcp.py`
- Modify: `scripts/inject_registry_runtime.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `hooks/hooks.json`
- Modify: `scripts/plugin_integrity.py`

**Interfaces:**
- Consumes: the RED tests and existing R2 canonical modules.
- Produces: one exact-turn state lifecycle and one canonical relation gate; no legacy runtime imports.

- [x] **Step 1: Extend the canonical proposition schema**

Add optional structured `base_rule` and `exception_rule` fields to `LegalProposition`, validate them as bounded text, and include them in registry allowlists, MCP schemas, serialization, and deterministic relation rendering. Do not add model-controlled render clauses.

- [x] **Step 2: Version the state schema and add lifecycle fields**

Set the R2 runtime schema to a new version. Add `activation_state`, `registry_required`, `registry_completed`, `registry_required_operations`, `registry_invocation_count`, `registry_enforcement_count`, `first_reconciliation`, `second_reconciliation`, and `stop_disposition`. Require the new keys when loading the new schema so a missing key cannot be read as actual `False` or `0`. Preserve exact `(session_id, turn_id)` pathing and atomic file replacement.

- [x] **Step 3: Add explicit activation**

Implement an explicit line-start `$law-interpretation-request` predicate. On a match, create a PENDING exact-turn state with `registry_required=True`, `registry_completed=False`, and zero counters. Non-explicit prompts remain no-op; missing identity or `PLUGIN_DATA` fails closed. Wire `UserPromptSubmit` in both POSIX and Windows hook commands.

- [x] **Step 4: Promote completion only in the canonical registry writer**

On a successful validated registry write, set `registry_required=True`, `registry_completed=True`, `activation_state="ACTIVE"`, `registry_active=True`, and increment the exact-turn invocation count. On an absent state, create the completed state only as the direct successful registry-call path; never infer completion from object existence. Return the four invariant fields in the MCP result.

- [x] **Step 5: Add bounded registry enforcement before render reconciliation**

In `handle_stop_event`, load only the exact state. For `registry_required=True` and `registry_completed=False`, increment only `registry_enforcement_count` from 0 to 1 and return a block requesting the canonical registry call; on the next incomplete Stop or active continuation, persist `REGISTRY_ENFORCEMENT_EXHAUSTED` and fail closed. A completed registry skips this branch and does not increment the counter.

- [x] **Step 6: Add structured relation reconciliation and evidence persistence**

Run relation reconciliation separately from render-slot coverage. Persist compact first/second summaries with relation ID, source proposition IDs, missing fields, and verdict; persist `COMPLETED`, `REPAIR_REQUESTED`, or `REPAIR_EXHAUSTED` disposition. Require all relation fields in one sentence span with base-before-exception direction. Do not alter the oracle or synthesize a missing source proposition.

- [x] **Step 7: Make installed integrity include the new authoritative producer/module**

Add `scripts/jdipt_activation.py` and `scripts/proposition_relations.py` to the runtime manifest. Do not claim installed parity until an actual installed copy matches these files and all existing R2 runtime files.

- [x] **Step 8: Run the focused RED→GREEN cycle**

Run the exact focused tests from Tasks 2 and 3. Expected: all new tests pass and existing R2 tests remain green. If a test fails, return to root-cause investigation and change one layer at a time.

---

### Task 5: Capture one-run staged evidence and classify all remaining gates

**Files:**
- Create: `docs/task1r-evidence/staged-run-01/registry-state.json`
- Create: `docs/task1r-evidence/staged-run-01/reconciliation.json`
- Create: `docs/task1r-evidence/staged-run-01/acceptance.json`
- Create: `docs/task1r-evidence/task1r-closure-report.md`

**Interfaces:**
- Consumes: fresh R2 repository test output, exact staged run identity, state JSON, relation reconciliation result, oracle result, and repository/install digests.
- Produces: a no-cross-run evidence bundle and the final four-row parity matrix.

- [x] **Step 1: Run the staged acceptance probe**

Use one generated `run_id`, `session_id`, and `turn_id` for a pending→completed registry path, one exact missing-registry enforcement path, one valid relation, one separated-span negative relation, and one final completed reconciliation. Save every JSON result under the same run directory.

- [x] **Step 2: Verify exact evidence linkage**

Assert that every state, MCP result, Stop result, relation result, and final oracle record carries the same session/turn and that the persisted state path is `PLUGIN_DATA/synthesis-runtime/<session_id>/<turn_id>.json`. Reject any evidence with a missing identity, stale timestamp, fallback source, or synthetic default.

- [x] **Step 3: Run the approved static sequence without changing order**

Run and record exit codes for `python scripts/validate_repo.py`, `python scripts/validate_authority_temporal_contract.py`, `python -m pytest -q`, `python -m compileall -q scripts tests`, `python scripts/plugin_integrity.py`, and `git diff --check`. The pytest permission failure and installed mismatch remain explicitly non-PASS until independently resolved.

- [x] **Step 4: Render the closure report**

The report must contain the requested A–J sections, exact root causes, repository/runtime identity, environment classifications, RED→GREEN evidence, and this matrix:

| Invariant | R1 Expected | R2 Actual | Same scope? | Same semantics? | Evidence | Verdict |
|---|---|---|---|---|---|---|
| registry_required | explicit activation creates required pending state | same exact-turn pending state | yes | yes | staged run state + activation test | PASS only if both match |
| registry_completed | successful registry persistence promotes completion | same successful canonical writer transition | yes | yes | MCP result + state transition | PASS only if both match |
| enforcement_count | bounded 0→1 registry enforcement | exact counter 0 or 1 in same turn | yes | yes | two Stop results + final state | PASS only if exact |
| range-exception relation | source-linked ordered base→range→exception relation | same structured relation and same-span reconciliation | yes | yes | relation object + positive/negative tests | PASS only if structural |

Use only `PASS`, `FAIL`, or `NOT_PROVEN` for verdicts. Do not declare Task 1R PASS if any static/environment/installed condition required by the approved acceptance remains unresolved.

- [x] **Step 5: Stop at the Task 1R gate**

If all four invariants and all required acceptance conditions are freshly verified, record `Task 1 final gate: PASS` and `Task 2 readiness: READY` without starting main-plan Task 2. Otherwise record `Task 1R: HOLD`, `Task 1: BLOCKED`, `Task 2: NOT STARTED`, `Overall: HOLD`, and `NEXT = HOLD — continue Task 1R`.

---

## Self-review checklist

- [x] The user's dirty worktree was never modified.
- [x] R1/L1 evidence was never combined with R2 staged evidence.
- [x] Every invariant has expected, actual, source, producer, consumer, persistence, identity, timing, and final observation.
- [x] `registry_required` and `registry_completed` are independent fields and transitions.
- [x] `enforcement_count` is exact and separate from `repair_count`.
- [x] Relation validation is graph/field/span based, not token co-occurrence.
- [x] Installed mismatch and pytest permission errors are reported, not hidden.
- [x] No oracle/gate condition was relaxed.
- [x] Main-plan Task 2 was not started.
