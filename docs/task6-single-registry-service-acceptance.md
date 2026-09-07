# Task 6 — Single Registry Service Acceptance

## A. Final Verdict

```text
Task 6: PASS
Task 7 readiness: READY
Overall: PASS
Blocker: NONE
```

Task 6 establishes one authoritative registry service and one canonical lifecycle
write path. The repository and isolated candidate bundle are verified against the
same final runtime manifest. The existing `sage1993` marketplace binding was not
changed.

## B. Baseline

```text
Task 5 HEAD: 9932d37386ed24ee5ce6b052f114b3df92c7fbbe
Task 5 implementation: 6ca5b06
Task 5 acceptance/docs: 9932d37
Task 6 branch: codex/task6-single-registry-service
Task 6 implementation commits:
  4331303 Create single registry service and remove duplicate writer
  8229db0 Harden registry disposition ownership and stale checks
  4dc53fd Protect registry state from stale persistence writers
  1f14154 Enforce active registry lifecycle and CAS ownership
working tree: clean after acceptance documentation commit
```

The original dirty worktree and the accepted Task 5 worktree were preserved.

## C. Root Cause

Task 5 already had a canonical proposition writer, but registry lifecycle state was
still written through several paths: activation created PENDING state in the
persistence module, proposition registration activated the state, Stop separately
incremented enforcement and wrote dispositions, and persistence helpers could save
whole snapshots without checking whether their input was stale. This allowed a
PENDING snapshot to overwrite a newer ACTIVE state and allowed split ownership of
the registry lifecycle.

## D. Architecture

```text
UserPromptSubmit
    ↓
RegistryService.begin_pending
    ↓
PENDING exact-turn state
    ↓
MCP register_material_proposition
    ↓
RegistryService.register
    ↓
complete ACTIVE exact-turn state
    ↓
coverage / relation closure
    ↓
semantic soundness
    ↓
source / authority / temporal closure
    ↓
obligation / dependency / final-conclusion closure
    ↓
bounded repair and persistence-only evidence CAS
    ↓
PASS or fail-closed Stop
```

`scripts/proposition_registry.py` owns `RegistryService.begin_pending`,
`register`, `mark_enforcement`, and `record_disposition`. Activation, MCP, and
Stop delegate to this service. `scripts/synthesis_runtime_state.py` is
persistence-only: it validates, serializes, loads exact-turn state, and applies
compare-and-swap updates to repair/reconciliation evidence.

## E. Single Writer Contract

- Exactly one `RegistryService` definition exists in the production runtime.
- The proposition registration compatibility function delegates to that service.
- The former `create_pending_runtime_state`,
  `update_registry_enforcement_count`, and `record_stop_disposition` writers were
  removed from persistence.
- AST architecture checks reject duplicate lifecycle writers and stale integration
  paths.
- The runtime bundle still includes the authoritative registry, persistence,
  activation, MCP, bridge, and Stop modules.

## F. Atomicity and Exact-Turn Closure

All registry transitions and persistence-only snapshot updates use the shared
bounded exact-turn lock. State writes retain the existing
`mkstemp → flush → fsync → os.replace` atomic replacement. A service transition
constructs a complete `RuntimeTurnState` before saving it, so PENDING → ACTIVE is
never partially persisted.

`runtime_state_fingerprint` canonicalizes JSON-compatible state before stale
comparison, avoiding false stale failures from tuple/list round-trips in evidence
metadata. A stale snapshot, held lock, malformed state, or cross-session/turn
identity mismatch fails closed. A missing file remains permitted only for the
initial persistence-only evidence write; an existing mismatching file is rejected.

## G. Lifecycle Invariants

```text
ONE authoritative registry service       PASS
ONE canonical write path                 PASS
NO duplicate state writer                PASS
NO direct registry lifecycle mutation    PASS
NO split-brain registry state            PASS
NO partial PENDING → ACTIVE transition  PASS
NO stale cross-turn state reuse          PASS
```

An `INACTIVE` state cannot claim a required or completed registry. Existing
registry-optional ACTIVE semantic fixtures remain valid so Task 1R–5 behavior is
not redefined; registry-owned ACTIVE states always carry the required completion
contract.

## H. Regression Matrix

| Scenario | Result |
|---|---|
| Service owns PENDING and ACTIVE transitions | PASS |
| Same proposition replaces; new proposition appends | PASS |
| Cross-session/turn registration is rejected | PASS |
| Stale enforcement transition is rejected | PASS |
| Held lock fails closed without partial state | PASS |
| Stale repair snapshot cannot overwrite ACTIVE | PASS |
| Stale reconciliation snapshot cannot overwrite ACTIVE | PASS |
| INACTIVE completed registry state is rejected | PASS |
| Active completed state cannot be downgraded | PASS |
| Stop enforcement is one bounded service transition | PASS |
| Stop dispositions route through the service | PASS |
| Task 1R–5 semantic behavior remains unchanged | PASS |

## I. Verification Results

```text
Task 6 focused: 14 passed
Task 6 integration/architecture: 57 passed
Task 4 soundness/runtime: 31 passed (Task 5 baseline)
Task 3 typed semantic: 66 passed (Task 5 baseline)
Task 2 authority/temporal: 10 passed (Task 5 baseline)
Task 1R proposition/dependency: 16 passed (Task 5 baseline)
reconciliation/render/runtime: 21 passed (Task 5 baseline)
full pytest: 402 passed
compileall: PASS
validate_repo.py: PASS
validate_authority_temporal_contract.py: PASS
npm ci: PASS
npm audit: PASS (0 vulnerabilities)
MCP smoke (`npm run mcp -- --help`): PASS (exit 0)
git diff --check: PASS
```

The Windows pytest temporary-directory ACL issue was handled by rerunning the
same commands with approved elevated execution. No test oracle or production
fallback was weakened.

## J. Installed Candidate State

```text
repository runtime digest: registry module `ffcb884ee48b253da549a674185e9e0b0cd8472962af51cfc6ea2bfe633129d5`; state module `76a3372933c8335207183e004eb5295f3648484fb582829954e29fdc6ac0c028`
installed candidate: F:\2026-PJ\JDIPT\.worktrees\task6-single-registry-service-candidate
installed candidate runtime digest: exact match
mismatches: []
candidate plugin integrity: PASS
existing sage1993 binding: unchanged
```

The unqualified integrity path may resolve the pre-existing `sage1993` bundle;
that installation is intentionally not refreshed or mutated. Task 6 acceptance
uses the isolated candidate above.

## K. Independent Review

```text
Critical findings at acceptance: 0
Important findings at acceptance: 0
```

Review identified four important risks during implementation: persistence
writers could overwrite newer registry snapshots, missing-state CAS could
resurrect stale state, generic persistence CAS could mutate registry fields,
and malformed lifecycle states were accepted. Each code finding was reproduced
with a failing test and fixed through shared lock/CAS persistence, protected
registry fingerprints, and strict lifecycle validation. The explicit Task 6
candidate was refreshed and independently rechecked with `mismatches=[]`.
The older marketplace/automatic install path was not used as candidate evidence
and remains intentionally unchanged. No remaining Critical or Important finding
remains.

## L. Residual Risks

- The marketplace `sage1993` binding remains unchanged and may be stale until a
  separately authorized installation refresh.
- The bounded lock uses a short fixed acquisition deadline; contention fails
  closed rather than attempting an unlocked write.
- The runtime still uses deterministic bounded semantic/source/obligation
  classifiers; it is not a general legal theorem prover.
- ASH-06 x3/x10, global live acceptance, and final release acceptance were not
  claimed as Task 6 gates.

## M. Next Action

```text
NEXT = Task 7 — Add a Source-Observed Material Obligation Ledger
```
