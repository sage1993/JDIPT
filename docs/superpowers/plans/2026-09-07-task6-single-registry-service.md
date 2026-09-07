# Task 6 — Create the Single Registry Service and Remove the Duplicate Writer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one registry service the sole owner of registry lifecycle transitions and proposition writes, with atomic exact-turn transitions and no direct registry mutation in persistence or transport modules.

**Architecture:** Keep `synthesis_runtime_state.py` as serialization, exact-turn loading, and non-registry evidence persistence. Move pending activation, proposition merge/activation, registry-enforcement accounting, and registry disposition writes behind `RegistryService` in `scripts/proposition_registry.py`. The service validates a complete next state and commits it through the existing atomic state-file replacement while holding a bounded per-turn lock.

**Tech Stack:** Python 3.13, stdlib dataclasses/json/pathlib/tempfile/os/time/contextlib, pytest, AST-based repository ownership checks.

**Spec:** User-provided Task 6 registry ownership, atomicity, writer uniqueness, and stale-state invariants; canonical runtime plan section `Task 6: Create the Single Registry Service and Remove the Duplicate Writer`.

## Global Constraints

- Preserve Task 1R proposition/dependency identity and exact-turn semantics.
- Preserve Task 2 authority/temporal fields and Task 3 typed enums.
- Preserve Task 4 soundness and Task 5 source/obligation closure behavior byte-for-byte in meaning.
- Keep one canonical proposition writer: `scripts/proposition_registry.py`.
- Do not allow direct registry lifecycle mutation from `synthesis_runtime_state.py`, MCP transport, activation hook, or Stop gate.
- Keep atomic `mkstemp` → flush → fsync → replace persistence and add bounded per-turn registry transition locking.
- Reject stale expected state and cross-session/cross-turn transitions fail-closed.
- Do not hard-code ASH-06 or any fixture-specific legal fact.
- Preserve the original dirty worktree and the accepted Task 5 branch; do not push, open a PR, or merge.

---

### Task 1: Capture the Current Writer Graph and Write RED Tests

**Files:**
- Create: `tests/test_task6_registry_service.py`
- Modify: `tests/test_synthesis_runtime_state.py`
- Modify: `tests/test_registry_runtime_bridge.py`
- Modify: `tests/test_task1r_registry_parity.py`

**Interfaces:**
- Consumes: current `RuntimeTurnState`, `register_material_proposition`, activation hook, and Stop hook.
- Produces: failing tests for one registry owner, atomic pending/active transitions, stale-state rejection, and cross-turn isolation.

- [x] **Step 1: Write the ownership RED tests.**

Add tests that assert the desired API and ownership boundary:

```python
def test_registry_service_owns_pending_and_active_transitions(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    assert pending.activation_state == "PENDING"
    result = service.register(_fields(), "session-a", "turn-1")
    assert result.state.activation_state == "ACTIVE"
    assert result.state.registry_completed is True


def test_stale_registry_transition_is_rejected(tmp_path):
    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")
    service.register(_fields(), "session-a", "turn-1")
    with pytest.raises(RuntimeStateError):
        service.mark_enforcement(expected, "REGISTRY_ENFORCEMENT")


def test_registry_transition_cannot_cross_session_or_turn(tmp_path):
    service = RegistryService(tmp_path)
    service.begin_pending("session-a", "turn-1")
    with pytest.raises(RuntimeStateError):
        service.register(_fields(session_id="session-b"), "session-a", "turn-1")
    assert load_runtime_state("session-a", "turn-1", tmp_path).activation_state == "PENDING"


def test_registry_lifecycle_writers_are_not_in_persistence_module():
    text = Path("scripts/synthesis_runtime_state.py").read_text(encoding="utf-8")
    assert "def create_pending_runtime_state" not in text
    assert "def update_registry_enforcement_count" not in text
```

- [x] **Step 2: Add transition and lock negative cases.**

Cover an existing completed state, a held registry lock, duplicate proposition replacement, same-turn append, and a malformed/incomplete active state. Assert that no partial `PENDING → ACTIVE` file is left behind after failure.

- [x] **Step 3: Run RED and record the expected failure.**

Run:

```powershell
python -m pytest -q tests/test_task6_registry_service.py tests/test_synthesis_runtime_state.py tests/test_registry_runtime_bridge.py
```

Expected: FAIL because `RegistryService` does not yet own the lifecycle and the persistence module still exposes duplicate registry writers. Do not edit production code before observing this failure.

---

### Task 2: Implement the Single Registry Service and Atomic Transition Lock

**Files:**
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/synthesis_runtime_state.py`
- Test: `tests/test_task6_registry_service.py`

**Interfaces:**
- Consumes: canonical `LegalProposition`, `EvidenceRef`, render contract, `RuntimeTurnState`, and atomic `save_runtime_state`.
- Produces:

```python
class RegistryService:
    def __init__(self, plugin_data: str | os.PathLike[str]): ...
    def begin_pending(self, session_id: str, turn_id: str) -> RuntimeTurnState: ...
    def register(
        self,
        fields: Mapping[str, Any],
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> RegistrationResult: ...
    def mark_enforcement(
        self,
        expected: RuntimeTurnState,
        disposition: str,
    ) -> RuntimeTurnState: ...
    def record_disposition(
        self,
        expected: RuntimeTurnState,
        disposition: str,
    ) -> RuntimeTurnState: ...
```

- [x] **Step 1: Add a bounded per-turn lock helper.**

Use a concrete lock file below the exact session/turn state directory. Acquire with `os.O_CREAT | os.O_EXCL`, retry only until a fixed short deadline, and remove the lock in `finally`. A held or malformed lock raises `RuntimeStateError`; it never falls through to an unlocked write.

- [x] **Step 2: Move pure proposition parsing and merge logic behind `RegistryService`.**

Keep input normalization at the registry boundary. Construct the complete next `RuntimeTurnState` before calling `save_runtime_state`. For a pending state, set `registry_active=True`, `activation_state="ACTIVE"`, `registry_completed=True`, and increment the invocation count in the same state object. For an existing active state, replace the same proposition ID or append a new one without changing session/turn identity.

- [x] **Step 3: Move pending activation and enforcement accounting behind the service.**

`begin_pending` returns an already completed exact-turn state unchanged, returns an existing pending state unchanged, or creates one pending state. `mark_enforcement` reloads the exact state under the lock and compares it with the expected state before applying the single `0 → 1` enforcement transition and disposition in one atomic save.

- [x] **Step 4: Remove registry lifecycle writers from persistence.**

Delete `create_pending_runtime_state` and `update_registry_enforcement_count` from `synthesis_runtime_state.py`. Leave only state serialization/loading, atomic file replacement, repair-count updates, reconciliation evidence, and terminal non-registry metadata updates there.

- [x] **Step 5: Run the focused GREEN suite.**

Run:

```powershell
python -m pytest -q tests/test_task6_registry_service.py tests/test_synthesis_runtime_state.py
```

Expected: all Task 6 transition tests and existing persistence tests pass.

---

### Task 3: Rewire Hooks, MCP, and Stop to the Service

**Files:**
- Modify: `scripts/jdipt_activation.py`
- Modify: `scripts/jdipt_runtime_mcp.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `tests/test_registry_runtime_bridge.py`
- Modify: `tests/test_jdipt_runtime_mcp.py`
- Modify: `tests/test_stop_synthesis_gate.py`

**Interfaces:**
- Consumes: `RegistryService.begin_pending`, `.register`, `.mark_enforcement`, and `.record_disposition`.
- Produces: one production call graph in which every registry lifecycle mutation enters `scripts/proposition_registry.py`.

- [x] **Step 1: Rewire explicit activation.**

Change `jdipt_activation.handle_user_prompt_submit` to call `RegistryService.begin_pending`; it must not import a pending-state writer from `synthesis_runtime_state.py`.

- [x] **Step 2: Keep MCP transport-only.**

Make the MCP wrapper construct the service and delegate the full registration operation. It may serialize the `RegistrationResult`, but it must not construct or mutate `RuntimeTurnState`.

- [x] **Step 3: Rewire Stop enforcement.**

Make `_registry_enforcement_response` call `RegistryService.mark_enforcement` once. The Stop gate continues to call persistence-only reconciliation functions for coverage, soundness, source closure, obligation closure, and repair state.

- [x] **Step 4: Add stale-state and exact-turn integration tests.**

Assert that a stale pending object cannot mark enforcement after registration, a wrong turn cannot reuse a state, and an active completed state cannot be downgraded by a later activation hook.

- [x] **Step 5: Run the integration GREEN suite.**

```powershell
python -m pytest -q tests/test_task6_registry_service.py tests/test_registry_runtime_bridge.py tests/test_jdipt_runtime_mcp.py tests/test_stop_synthesis_gate.py tests/test_task1r_registry_parity.py
```

---

### Task 4: Add Static Writer-Uniqueness and Bundle Contracts

**Files:**
- Modify: `scripts/validate_repo.py`
- Modify: `scripts/plugin_integrity.py`
- Modify: `tests/test_validate_repo_contract.py`
- Modify: `tests/test_plugin_integrity_runtime_bundle.py`
- Modify: `docs/architecture.md`
- Modify: `skills/law-interpretation-request/SKILL.md`

**Interfaces:**
- Consumes: the Task 6 production call graph and service API.
- Produces: fail-closed repository checks that reject duplicate lifecycle writers, stale imports, transport state mutation, and omitted bundle files.

- [x] **Step 1: Add AST/text ownership checks.**

The validator must reject a production `create_pending_runtime_state`, `update_registry_enforcement_count`, or direct registry lifecycle assignment outside `proposition_registry.py`. It must also reject stale `runtime_registry_state` imports and require the service symbols in activation, MCP, and Stop integration.

- [x] **Step 2: Update runtime architecture documentation.**

Document one registry service, one lifecycle writer, atomic exact-turn transitions, and persistence-only state storage. Preserve the Task 1R–5 semantic gate sequence unchanged.

- [x] **Step 3: Verify the bundle.**

Ensure the service changes remain in the candidate runtime manifest and that `mismatches=[]` is still enforced.

---

### Task 5: Full Regression, Review, and Acceptance Evidence

**Files:**
- Create: `docs/task6-single-registry-service-acceptance.md`
- Modify: `docs/superpowers/plans/2026-09-07-task6-single-registry-service.md`

- [x] **Step 1: Run focused and cross-task tests.**

Run Task 6 tests, Task 1R–5 regression suites, reconciliation/render/runtime tests, and the full `python -m pytest -q` suite. Record exact counts.

- [x] **Step 2: Run package and static verification.**

Run:

```powershell
python -m compileall -q scripts tests
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py --repo-root . --installed-root <isolated-candidate>
npm ci
npm audit
npm run mcp -- --help
git diff --check
```

- [x] **Step 3: Perform an independent review.**

Review critical paths for duplicate writers, partial transitions, lock bypass, stale cross-turn state, and semantic regression. Fix every Critical or Important finding before acceptance.

- [x] **Step 4: Write acceptance evidence.**

Record baseline, ownership graph, atomicity proof, violation/transition contract, regression counts, candidate digest, review findings, residual risks, and the canonical next action.

- [x] **Step 5: Commit only Task 6 implementation and acceptance evidence.**

Use separate local commits for production/regression changes and acceptance documentation. Do not push or create a PR.
