# Task 7 — Make the Registry the Sole Runtime Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make `RegistryService` the only production runtime read boundary for exact session/turn state while preserving Task 1R–6 semantics and fail-closed behavior.

**Architecture:** Keep `synthesis_runtime_state.py` as the low-level atomic persistence implementation, but expose its state to production consumers only through `RegistryService.read_state()`. The Stop gate will obtain one canonical snapshot from the service and pass that snapshot to reconciliation, soundness, source/obligation closure, and disposition transitions. A repository architecture guard will reject direct runtime-state reader imports/calls from consumer modules.

**Tech Stack:** Python 3.13, stdlib dataclasses/json/pathlib/AST, pytest, existing runtime validators and plugin-integrity manifest.

**Spec:** User-provided Task 7 — Make the Registry the Sole Runtime Authority.

## Global Constraints

- Base Task 7 from `34271c3` on branch `codex/task7-registry-runtime-authority`.
- Preserve the root dirty worktree and the existing `sage1993` binding.
- Do not use `git reset --hard`, `git clean`, `git stash`, force checkout, unrelated deletion, push, PR, or merge to main.
- Keep `RegistryService` responsible for canonical read, lifecycle/write validation, exact-turn identity, and persistence boundary; keep reconciliation and semantic/source/obligation classification in their domain modules.
- Do not add ASH-06 or fixture-specific literals to production runtime code.
- Existing Task 1R–6 semantic contracts remain unchanged.

---

### Task 1: Add RED tests for the canonical read boundary

**Files:**
- Create: `tests/test_task7_registry_runtime_authority.py`
- Test existing: `scripts/proposition_registry.py`, `scripts/stop_synthesis_gate.py`

**Interfaces:**
- Consumes: `RegistryService`, `RuntimeTurnState`, Stop hook, and exact-turn state fixtures.
- Produces: failing tests that require a service read API, Stop delegation, exact-turn isolation, and fail-closed conflict/malformed behavior.

- [x] **Step 1: Write tests that require `RegistryService.read_state()` and Stop delegation.**

Add tests for:

```python
def test_registry_service_read_state_returns_exact_turn_snapshot(tmp_path):
    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")
    assert service.read_state("session-a", "turn-1") == expected
    assert service.read_state("session-a", "turn-2") is None


def test_stop_gate_uses_registry_service_read_boundary():
    source = Path("scripts/stop_synthesis_gate.py").read_text(encoding="utf-8")
    assert "load_runtime_state" not in source
    assert ".read_state(" in source
```

Also cover missing registry with a legacy/shadow artifact, registry-vs-environment conflict, stale previous-turn state, malformed `ACTIVE`/`PENDING`, and a reconciliation proposition mismatch. Assertions must require registry state or explicit fail-closed behavior, never legacy fallback.

- [x] **Step 2: Run the new tests and observe the expected RED result.**

Run:

```powershell
python -m pytest -q tests/test_task7_registry_runtime_authority.py
```

Expected RED: `RegistryService.read_state` is absent and the Stop module still contains the direct `load_runtime_state` reader. Any test that already passes because Task 6 already fails closed must be recorded as an existing PASS rather than weakened.

- [x] **Step 3: Commit the RED tests.**

```powershell
git add tests/test_task7_registry_runtime_authority.py
git commit -m "test: define Task 7 registry read authority"
```

### Task 2: Implement the service read boundary and migrate Stop

**Files:**
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Test: `tests/test_task7_registry_runtime_authority.py`

**Interfaces:**
- Consumes: low-level exact-turn persistence read inside `synthesis_runtime_state.py`.
- Produces: `RegistryService.read_state(session_id, turn_id) -> RuntimeTurnState | None` and one service instance used by Stop for read/enforcement/disposition.

- [x] **Step 1: Add the minimal `RegistryService.read_state` wrapper.**

The method must validate the exact identifiers through the existing persistence reader, return `None` only for an absent exact-turn file, and propagate `RuntimeStateError` for malformed or mismatched content. It must not consult a legacy path, environment status flag, cache, or shadow state.

- [x] **Step 2: Replace Stop's direct reader with the service.**

Construct one `RegistryService(plugin_data)` in `handle_stop_event`, call `service.read_state(session_id, turn_id)`, and use that same service for pending activation, enforcement, and disposition transitions. Keep `record_reconciliation` and `update_repair_count` persistence-only derived updates; they must receive the canonical snapshot returned by the service.

- [x] **Step 3: Run the focused GREEN suite.**

Run:

```powershell
python -m pytest -q tests/test_task7_registry_runtime_authority.py tests/test_task6_registry_service.py tests/test_stop_synthesis_gate.py
```

Expected: all focused authority, Task 6 lifecycle, and Stop tests pass.

- [x] **Step 4: Commit the runtime migration.**

```powershell
git add scripts/proposition_registry.py scripts/stop_synthesis_gate.py
git commit -m "feat: route runtime reads through registry service"
```

### Task 3: Add static architecture and runtime-bundle guards

**Files:**
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo_contract.py`
- Modify: `docs/architecture.md`
- Test: `tests/test_task7_registry_runtime_authority.py`

**Interfaces:**
- Consumes: production runtime module map and the service read API.
- Produces: fail-closed detection of direct `load_runtime_state`/`runtime_state_path` consumers and required `read_state` integration.

- [x] **Step 1: Write validator contract tests first.**

Test that a synthetic production module importing or calling `load_runtime_state` is rejected, while `proposition_registry.py` and the persistence implementation remain allowed. Test that the registry service exposes `read_state` and Stop delegates to it.

- [x] **Step 2: Run validator tests RED.**

Run:

```powershell
python -m pytest -q tests/test_validate_repo_contract.py
```

Expected RED until the new architecture guard and service marker are implemented.

- [x] **Step 3: Implement the narrow AST/text guard.**

Limit the guard to production runtime modules under `scripts/`; allow the low-level persistence module and `proposition_registry.py`, reject other imports/calls of `load_runtime_state` or `runtime_state_path`, and require `read_state` in the service method set and Stop integration.

- [x] **Step 4: Document the authority boundary.**

Update `docs/architecture.md` with the before/after graph, the consumer matrix, the distinction between canonical state and derived evidence, and the rule that `PLUGIN_DATA` is location/bootstrap input only.

- [x] **Step 5: Run static GREEN checks and commit.**

```powershell
python -m pytest -q tests/test_validate_repo_contract.py tests/test_task7_registry_runtime_authority.py
python scripts/validate_repo.py
git diff --check
git add scripts/validate_repo.py tests/test_validate_repo_contract.py docs/architecture.md
git commit -m "feat: guard registry runtime read authority"
```

### Task 4: Acceptance evidence and complete verification

**Files:**
- Create: `docs/task7-registry-runtime-authority-acceptance.md`
- Modify: `docs/superpowers/plans/2026-09-07-task7-registry-runtime-authority.md`

**Interfaces:**
- Consumes: forensic inventory, test output, validator output, and isolated candidate parity evidence.
- Produces: Task 7 acceptance report with exact counts and residual risks.

- [x] **Step 1: Run Task 7 focused and Task 6 regression suites.**

Run the new Task 7 suite, Task 6 registry/bridge/Stop tests, Task 5 source/obligation tests, Task 4 soundness/runtime tests, Task 3 typed semantic tests, Task 2 authority/temporal tests, Task 1R relation tests, plugin-integrity tests, and validators. Record actual counts; never substitute expected counts.

- [x] **Step 2: Run full verification in the isolated worktree.**

```powershell
python -m pytest -q
python -m compileall -q scripts tests
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py --repo-root . --installed-root F:\\2026-PJ\\JDIPT\\.worktrees\\task7-registry-runtime-authority-candidate
npm ci
npm audit
npm run mcp -- --help
git diff --check
```

- [x] **Step 3: Verify repository/candidate parity and clean state.**

Confirm the Task 7 branch contains only scoped changes, the isolated candidate runtime manifest has `mismatches=[]`, the Task 6 base branch remains unchanged, and the root dirty status is unchanged. Do not mutate `sage1993`.

- [x] **Step 4: Perform independent review.**

Re-run the inventory searches and inspect every direct runtime-state read, fallback, environment override, exact-turn check, and Stop path. Critical or Important findings block PASS.

- [x] **Step 5: Commit acceptance documentation.**

```powershell
git add docs/task7-registry-runtime-authority-acceptance.md docs/superpowers/plans/2026-09-07-task7-registry-runtime-authority.md
git commit -m "docs: record Task 7 registry authority acceptance"
```
