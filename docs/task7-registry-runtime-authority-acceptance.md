# Task 7 — Registry Runtime Authority Acceptance

## A. Final Verdict

```text
Task 7: PASS
Task 8 readiness: READY
Overall: PASS
Blocker: NONE
```

Task 7 makes `RegistryService` the production runtime read boundary for the
exact session/turn registry snapshot. The low-level persistence module remains a
storage implementation, while activation, synthesis orchestration,
reconciliation, semantic soundness, source/obligation closure, and Stop consume
the same service-backed snapshot. The existing `sage1993` binding was not
changed.

## B. Baseline

```text
base SHA: 34271c35f8ff70f86f8d87ecfda05b3b22a3b85d
base branch: codex/task5-source-obligation-closure
Task 7 branch: codex/task7-registry-runtime-authority
Task 6 acceptance: 34271c3
working tree at start: clean isolated worktree
root repository: pre-existing dirty changes preserved
```

The Task 7 branch was created in a separate linked worktree from the integrated
Task 6 branch. No root dirty file, existing Task 6 worktree, or installed
marketplace binding was used as a write target.

## C. Root Cause

Task 6 consolidated lifecycle writes but left the persistence reader publicly
reachable from consumer code. `stop_synthesis_gate.py` imported and called
`load_runtime_state()` directly, so the Stop path selected its state outside the
service boundary even though lifecycle mutations used `RegistryService`. This
left a structural path for a future shadow/fallback reader to diverge from the
canonical registry authority.

## D. Before Architecture

```text
RegistryService ── lifecycle writes ──► synthesis-runtime/<S>/<T>.json
       │
       └── load_runtime_state()

Stop gate ── direct load_runtime_state() ──► same JSON
       │
       └── reconciliation / soundness / source / obligation / Stop decision
```

The file itself was exact-turn and fail-closed, but the read authority was not
expressed as one service interface. Derived evidence was stored in the same
state object, while the Stop gate selected the object through the persistence
module rather than through the registry service.

## E. Registry Authority Contract

`RegistryService` now exposes:

```text
read_state(session_id, turn_id) -> RuntimeTurnState | None
begin_pending(session_id, turn_id) -> RuntimeTurnState
register(...) -> RegistrationResult
mark_enforcement(...) -> RuntimeTurnState
record_disposition(...) -> RuntimeTurnState
```

`read_state()` delegates only to the existing exact-turn persistence
implementation. It has no legacy path, environment-status override, shadow
cache, or fallback truth source. Missing state returns `None`; malformed,
mismatched, or invalid state raises `RuntimeStateError` and is handled
fail-closed by the Stop adapter.

The persistence module may perform low-level atomic storage reads for service
implementation and CAS operations. It is not a runtime consumer authority. The
validator rejects `load_runtime_state` and `runtime_state_path` imports/calls in
all other production modules.

## F. Consumer Inventory

| Runtime consumer | Before Task 7 | After Task 7 | Direct FS read | Registry authority |
|---|---|---|---:|---:|
| Activation | Service write, no canonical read API | `RegistryService` exact-turn boundary | 0 | YES |
| Synthesis orchestration | Stop-owned state object | Service snapshot passed through Stop | 0 | YES |
| Reconciliation | State object selected by Stop reader | Service snapshot propositions | 0 | YES |
| Soundness | State object selected by Stop reader | Service snapshot propositions | 0 | YES |
| Source closure | State object selected by Stop reader | Service snapshot propositions | 0 | YES |
| Obligation closure | State object selected by Stop reader | Service snapshot propositions | 0 | YES |
| Stop gate | Direct `load_runtime_state()` | `RegistryService.read_state()` | 0 | YES |
| Validators/integrity | Source and manifest inspection | Architecture guard plus manifest inspection | 0 | YES |

Production inventory after migration:

```text
RegistryService: canonical service read and lifecycle paths
synthesis_runtime_state.py: low-level persistence implementation only
all other production consumers: no runtime registry reader imports/calls
direct consumer filesystem readers: 0
```

## G. Shadow State Removal

No authoritative shadow JSON, in-memory cache, legacy fallback, or environment
state override remains. `first_reconciliation`, `second_reconciliation`,
`repair_count`, and `stop_disposition` remain derived exact-turn evidence and
are protected by the existing persistence CAS fingerprint; they cannot assert
registry activation, replace propositions, or authorize a Stop decision.

The negative tests cover:

```text
missing registry + legacy artifact             FAIL CLOSED
registry PENDING + shadow ACTIVE               PENDING / enforcement block
registry inactive + environment location       explicit registry wins
previous-turn state                             exact-turn miss
malformed ACTIVE/PENDING                       RuntimeStateError
registry proposition + shadow proposition       registry snapshot only
stale source-closure artifact                  new turn is not authorized
```

## H. Direct Reader Removal

`stop_synthesis_gate.py` no longer imports or calls `load_runtime_state()`.
It constructs one `RegistryService(plugin_data)`, reads the canonical snapshot,
and uses that same service for enforcement and disposition transitions. The
architecture validator statically rejects direct persistence-reader imports and
calls from other production modules and requires `read_state` in the service
contract.

## I. Exact-Turn Enforcement

The service receives the same `session_id`, `turn_id`, and `PLUGIN_DATA` binding
used by activation/MCP/Stop. `read_state()` computes the exact existing path
through the existing identifier validation. A previous turn returns no state;
a malformed or mismatched file raises; a stale derived artifact is ignored.
Task 6's bounded transition lock and CAS fingerprint remain unchanged.

## J. Fail-Closed Behavior

```text
missing state on non-JDIPT output       no-op
missing state on JDIPT-shaped output    ACTIVATION_BYPASS / block
malformed state                         fail closed
PENDING without completed registry      enforcement block
shadow completion                       ignored
stale turn                              not reused
environment location conflict           explicit service location wins
```

## K. Regression

```text
Task 7 focused: 13 passed
Task 6/Task 7 integration + architecture group: 75 passed
Task 1R–5 regression group: 165 passed
runtime / Stop / reconciliation subset: 38 passed (included above)
full pytest: 416 passed
```

The Task 6 registry service, runtime bridge, MCP, Stop, Task 1R parity,
validator, bundle, and architecture tests were included in the 75-test group.
The 165-test regression group covered Task 5 source/obligation closure, Task 4
soundness, Task 3 typed semantics, Task 2 authority/temporal behavior, Task 1R
relation/parity, reconciliation, rendering, runtime state, and registry
compatibility.

## L. Verification

```text
compileall: PASS (elevated rerun required by existing Windows __pycache__ ACL)
validate_repo.py: PASS
validate_authority_temporal_contract.py: PASS
plugin integrity / candidate parity: PASS
npm ci: PASS
npm audit: PASS (0 vulnerabilities)
MCP smoke (`npm run mcp -- --help`): PASS (exit 0)
git diff --check: PASS
```

The first non-elevated `compileall` attempt failed only while writing existing
ACL-protected `scripts/__pycache__` and `tests/__pycache__` files. The identical
command was rerun elevated and exited 0. No test oracle or production fallback
was weakened.

## M. Installed Candidate State

```text
candidate path: F:\2026-PJ\JDIPT\.worktrees\task7-registry-runtime-authority-candidate
repository manifest digest: aca3fabc98e7b5c3f44fae038033b1d40c3c2b6c0e5dae6cce46522dcef0054f
candidate manifest digest:  aca3fabc98e7b5c3f44fae038033b1d40c3c2b6c0e5dae6cce46522dcef0054f
mismatches: []
SAGE1993_BINDING: UNCHANGED
```

The candidate was isolated from the existing Task 6 candidate and synchronized
from the Task 7 worktree. The pre-existing `sage1993` marketplace path was not
refreshed or overwritten.

## N. Independent Review

```text
Critical findings: 0
Important findings: 0
```

The post-implementation inventory was rerun. Runtime reader references remain
inside `proposition_registry.py`, the persistence implementation, and the
validator only. No production consumer retains a direct runtime-state reader,
legacy fallback, environment status override, stale-turn cache, or Stop bypass.
`RegistryService` remains a boundary/service object; semantic classification
continues to live in reconciliation, soundness, source, and obligation modules.

## O. Residual Risks

- The persistence module still contains the low-level filesystem reader required
  by service/CAS implementation; it is intentionally not a consumer authority.
- Windows ACL behavior around pre-existing pytest/compile caches may require the
  same elevated verification on this host.
- Live host invocation, external legal-source query correctness, ASH-06 x3/x10,
  and final release acceptance remain outside Task 7's static/runtime suite.

## P. Next Action

```text
NEXT = Task 8 — Enforce Registry Closure and Explicit Registry Completion
```
