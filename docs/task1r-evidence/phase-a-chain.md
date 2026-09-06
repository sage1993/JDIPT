# Task 1R Phase A — R1/R2 Evidence Chain Reconstruction

**Scope:** read-only reconstruction before the Task 1R production change.

**Identity:**

- R1/L1 comparison source: `F:\2026-PJ\JDIPT`, branch `fix/ansim-structural-behavior-stability`, HEAD `69dda97106cf094d93d7abb26753a76ed33ea773`.
- R2 canonical source: `refactor/legal-proposition-core-working2`, baseline `afa4003ca700f15794dc346e8239c6dda79492e2`.
- Task 1R isolated worktree: `C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization`, branch `codex-jdipt-correctness-stabilization`, pre-change HEAD `1acf04472b071282959f4f9f3dbace35c3fcdaec`.
- The user worktree was not edited. Its Task 14D/14E outputs are comparison evidence, not R2 acceptance evidence.

## Reconstructed chain

| Boundary | R1/L1 producer and consumer | R2 before Task 1R | Persistence / scope | Lifecycle and failure behavior |
|---|---|---|---|---|
| input | `scripts/jdipt_activation.py:handle_user_prompt_submit` receives `UserPromptSubmit`; `is_explicit_jdipt_prompt` requires a line-start `$law-interpretation-request` | No `UserPromptSubmit` activation producer or hook | Host event; exact `session_id` + `turn_id` | Non-explicit prompt is no-op; explicit prompt with missing identity/data fails closed |
| activation | `create_pending_runtime_state` creates `PENDING`, `registry_required=True`, `registry_completed=False`, zero enforcement count | No pending activation state or L1 required/completed fields | `PLUGIN_DATA/synthesis-runtime/<session>/<turn>.json` | PENDING is not ACTIVE; no registry completion is inferred |
| registry bridge | PreToolUse `inject_registry_runtime.handle_pre_tool_use` overwrites model identity and injects authoritative plugin data | PreToolUse bridge exists and preserves exact identity, but no pending-state prerequisite | MCP tool input plus exact plugin-data path | Missing identity/data is denied; unrelated tools are unchanged |
| registry writer | L1 `jdipt_runtime_mcp` delegates to legacy `runtime_registry_state.register_material_proposition`; successful write sets `registry_completed=True`, ACTIVE, and invocation count | `jdipt_runtime_mcp` delegates to canonical `proposition_registry.register_material_proposition`; writer only sets `registry_active=True` and `repair_count=0` | `synthesis-runtime/<session>/<turn>.json`; replacement is by exact proposition ID | Validated proposition persists; R2 has no completion transition and therefore cannot prove registry completion |
| runtime state | L1 `RuntimeTurnState` carries activation, completion, invocation, enforcement, reconciliation, and Stop disposition fields | R2 `RuntimeTurnState` carries only schema v2, `registry_active`, `repair_count`, and propositions | Atomic file replacement, exact session/turn load | Exact-turn mismatch and malformed data fail closed; old R2 schema lacks L1 fields |
| enforcement | L1 `stop_synthesis_gate._registry_enforcement_response` increments `registry_enforcement_count` once before completion, then returns `REGISTRY_ENFORCEMENT_EXHAUSTED` | R2 Stop only increments bounded `repair_count` after render-slot mismatch | Same exact state file | R2 cannot distinguish registry enforcement from synthesis repair |
| reconciliation | L1 `synthesis_integrity.reconcile_range_exception_relation` builds a source-linked `RangeExceptionRelation` and records first/second results | R2 `proposition_reconciliation.reconcile_render_contracts` checks independent effect/temporal slots only | Result not persisted in R2 state | R2 has no structural relation gate; token/span parity is unproven |
| synthesis / oracle | L1 Stop writes compact reconciliation/Stop evidence; `runtime_acceptance.py` consumes the exact ledger and the unchanged ASH oracle | No R2 runtime ledger or active host attestation in this task | Separate evidence bundle required per run | L1 final9 stopped after source-linked 350m proposition was absent; no L1 result is promoted to R2 |

## Four invariant source-of-truth decisions

### `registry_required`

The authoritative producer is the explicit activation transition, not the existence of a registry object. The expected lifecycle is `PENDING / required=true / completed=false`, followed only by a successful exact-turn registry write. R2 had no producer or consumer before this closure.

### `registry_completed`

Completion means a validated canonical registry write was persisted for the same exact session and turn and the state was atomically promoted to ACTIVE. It is not equivalent to call attempt, object existence, or `registry_required`. R2 had no completion bit before this closure.

### `enforcement_count`

The authoritative counter is the registry-enforcement continuation counter, distinct from `repair_count`. It has one permitted transition, `0 → 1`, only while required completion is false. R2 had only `repair_count`, so exact parity was not established.

### range-exception relation

The authoritative relation must carry base rule, range values, exception rule/trigger, legal act, subject, object, effect, relation direction, source evidence, and source proposition IDs. A single sentence/span must preserve the ordered base→exception proposition graph. R2 effect/temporal render slots do not establish this relation.

## Phase A conclusion

The R2 pre-change chain stops at canonical proposition persistence and independent render-slot coverage. The four L1 invariants are therefore `NOT_PROVEN`, not PASS. The exact root causes are missing R2 lifecycle fields/producer, missing separate enforcement counter, and missing canonical structured relation model. No oracle or gate condition was changed to reach this conclusion.
