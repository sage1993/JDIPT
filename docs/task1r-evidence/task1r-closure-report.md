# Task 1R — R2 L1 Invariant Parity Closure Report

**Run evidence:** `staged-run-01`
**R2 worktree:** `C:/Users/KSH/.codex/visualizations/2026/09/06/01a0769a-1b77-7a83-990e-e8f32ba44634/jdipt-correctness-stabilization`
**Branch:** `codex-jdipt-correctness-stabilization`
**HEAD:** `1acf04472b071282959f4f9f3dbace35c3fcdaec`
**Run/session/turn:** `task1r-r2-staged-run-01` / `task1r-session-01` / `task1r-turn-01`

## A. Final Verdict

```text
Task 1R: HOLD
Task 1: BLOCKED
Task 2 readiness: NOT STARTED
Overall: HOLD
```

All four invariant checks are `PASS` in the same staged R2 run. The overall Task 1R gate remains `HOLD` because installed-bundle parity is still `FAIL`, the exact default pytest/compileall commands are blocked by host ACL paths, and no active installed runtime identity was observed. No Task 2 implementation was started.

## B. Exact Root Cause

```text
registry_required:
  R2 previously had no explicit activation producer or required-state field.
  The fix adds UserPromptSubmit -> PENDING exact-turn state creation.

registry_completed:
  R2 previously exposed registry_active but had no separate completion bit or
  completion transition. The canonical registry writer now atomically persists
  registry_completed=true only after a validated registry write.

enforcement_count:
  R2 previously bounded repair_count only; it had no registry enforcement
  counter. The Stop gate now owns one exact 0->1 registry-enforcement transition,
  separate from repair_count, then fails closed on an incomplete continuation.

range-exception relation:
  R2 previously had only generic render slots and no structured relation graph.
  The fix adds explicit base/exception rule fields, a source-linked relation
  object, ordered range checks, same-span legal-field checks, and persisted
  relation reconciliation evidence.
```

## C. Repository / Runtime State

```text
worktree:
  isolated R2 worktree above; the user's F:/2026-PJ/JDIPT worktree was not modified
branch:
  codex-jdipt-correctness-stabilization
HEAD:
  1acf04472b071282959f4f9f3dbace35c3fcdaec
working tree:
  dirty only in the isolated worktree with Task 1R implementation/tests/evidence
installed plugin:
  C:/Users/KSH/.codex/plugins/cache/sage1993/jdipt/0.2.4/skills/law-interpretation-request
runtime source:
  staged R2 repository scripts executed by C:/Program Files/Python313/python.exe
active runtime:
  staged-probe-process only; no active installed Codex plugin/MCP identity observed
repository source manifest digest:
  e078540a742940c3836050a5bae39d1bf9549ce7e00f362666b654ef7d5cd072
installed manifest digest:
  8ec8d1d238f2bb533d306a31bf7b76583be9827f7de304dedfb1afd1db56d382
digest parity:
  FAIL — installed manifest differs and lacks canonical R2 runtime files
```

The full staged-run identity, final state, relation object, and digest metadata are in [`acceptance.json`](staged-run-01/acceptance.json), [`registry-state.json`](staged-run-01/registry-state.json), and [`reconciliation.json`](staged-run-01/reconciliation.json).

## D. Environment Findings

```text
plugin_integrity:
  FAIL, exit 1 — category A for installed/live R2 parity
  16 mismatches: digest differences in Skill/hooks/bridge/activation/MCP/Stop/state
  and references, plus missing installed R2 canonical files including
  legal_proposition.py, proposition_registry.py, proposition_relations.py,
  proposition_rendering.py, and proposition_reconciliation.py.
  No installed bundle was mutated.

pytest:
  exact `python -m pytest -q`: FAIL, exit 1 — category C host/environment-only
  deviation; collection is blocked by permission-denied generated directories
  pytest-cache-files-d_ie3gmn and pytest-cache-files-wmok1bp6.
  Historical baseline 213 passed / 47 setup errors is retained as the same ACL
  cluster. With an isolated basetemp, the complete suite is PASS: 272 passed.
  If the exact default command is a required acceptance command, its unresolved
  status is also category B repository-acceptance impact.

Windows cache/ACL:
  category C host/environment-only deviation. Plain compileall also failed on
  scripts/__pycache__ and tests/__pycache__; compileall with a separate isolated
  bytecode cache passed.

static validators:
  validate_repo.py PASS, exit 0
  validate_authority_temporal_contract.py PASS, exit 0
  isolated compileall PASS, exit 0
  isolated full pytest PASS, exit 0
  git diff --check PASS, exit 0
```

## E. Production Changes

- `scripts/jdipt_activation.py`: explicit line-start activation and pending exact-turn state producer.
- `hooks/hooks.json`: UserPromptSubmit hook with POSIX and Windows commands.
- `scripts/synthesis_runtime_state.py`: schema v3, independent required/completed/enforcement fields, strict load, lifecycle validation, atomic persistence, and compact reconciliation evidence.
- `scripts/proposition_registry.py` and `scripts/jdipt_runtime_mcp.py`: canonical registry completion transition, invocation count, relation-rule fields, and invariant fields in MCP output.
- `scripts/legal_proposition.py`: optional bounded `base_rule` and `exception_rule` fields.
- `scripts/proposition_relations.py`: structured source-linked range/exception relation builder and same-span reconciler.
- `scripts/stop_synthesis_gate.py`: exact registry enforcement before render reconciliation, persisted first/second relation evidence, and fail-closed exhaustion.
- `scripts/proposition_rendering.py`: preserves the existing L1 materiality aliases needed for relation propositions.
- `scripts/plugin_integrity.py` and `scripts/validate_repo.py`: authoritative producer/module presence checks and static markers.

No oracle condition, expected value, required marker, run count, or gate assertion was relaxed. No fallback/default was used while loading the new persisted state, and no ASH-specific literal was added to the new parity modules or changed invariant logic.

## F. Regression Tests

RED evidence was recorded before the implementation: the new focused collection failed because `scripts.jdipt_activation` and `scripts.proposition_relations` did not yet exist.

GREEN evidence:

- Task 1R focused lifecycle/relation suite: `12 passed`.
- Full R2 pytest suite with isolated basetemp: `272 passed`.
- `python -m compileall -q scripts tests` with isolated `PYTHONPYCACHEPREFIX`: exit 0.
- The default compileall failure is preserved as an ACL finding, not hidden.

The added tests cover pending activation, exact completion, missing-field fail-closed loading, exact one-time enforcement, session/turn isolation, same-span relation preservation, separated-span rejection, reversed-range rejection, generic-relaxation rejection, and full registry-to-Stop persisted evidence.

## G. R2 Parity Matrix

| Invariant | R1 Expected | R2 Actual | Same scope? | Same semantics? | Evidence | Verdict |
|---|---|---|---|---|---|---|
| registry_required | Explicit activation sets `registry_required=true` in a PENDING exact-turn state before registry completion. | `UserPromptSubmit` persisted `activation_state=PENDING`, `registry_required=true`, `registry_completed=false`, invocation `0`, enforcement `0`. | yes — `task1r-session-01` / `task1r-turn-01` | yes — activation precedes completion and is independent of `registry_completed`. | staged state + `test_explicit_activation_persists_pending_registry_contract` | PASS |
| registry_completed | A successful validated canonical registry write is the only completion transition; pending remains incomplete. | MCP registry results and persisted state show `registry_completed=true`, `activation_state=ACTIVE`, `registry_active=true`, invocation `2` only after the two successful same-turn writes. | yes — exact session/turn path | yes — no object-existence or required-bit shortcut completes the state. | staged MCP payloads + final state + `test_successful_registry_write_is_the_only_completion_transition` | PASS |
| enforcement_count | Bounded registry enforcement is exactly `0 -> 1`; exhaustion does not increment to `2`; it is separate from repair count. | First incomplete Stop returned `REGISTRY_ENFORCEMENT` and persisted `1`; second incomplete Stop returned `REGISTRY_ENFORCEMENT_EXHAUSTED`; final persisted value remained exactly `1`, while `repair_count=0`. | yes — same run/session/turn | yes — exact counter and separate lifecycle | staged two Stop results + final state + `test_registry_enforcement_is_exactly_one_and_separate_from_repair` | PASS |
| range-exception relation | Source-linked `RangeExceptionRelation` preserves base rule, range direction, exception trigger/procedure, legal act/subject/object/effect, proposition IDs, and same-span meaning. | Canonical relation preserved `100m -> 150m`, `BASE_RANGE -> EXCEPTION_RANGE`, source `law-001`, locator/evidence, condition, procedure, actor, action, object, effect, modality, and polarity; same-span reconciliation passed, separated-span control failed. | yes — same run/session/turn and persisted source path | yes — graph/field/order/same-span checks, not keyword co-occurrence | staged relation object + positive/negative reconciliation + persisted summary | PASS |

The matrix is a staged R2 result. It is not substituted for installed/live parity.

## H. Acceptance Evidence

The single staged run used:

```text
run_id     = task1r-r2-staged-run-01
session_id = task1r-session-01
turn_id    = task1r-turn-01
state path = PLUGIN_DATA/synthesis-runtime/task1r-session-01/task1r-turn-01.json
```

Observed sequence, all under that identity:

1. Explicit prompt created `PENDING / required=true / completed=false`.
2. First incomplete Stop returned a block with `REGISTRY_ENFORCEMENT` and persisted enforcement `1`.
3. Second incomplete Stop returned `continue=false` with `REGISTRY_ENFORCEMENT_EXHAUSTED`; the counter stayed `1`.
4. Canonical registry writes for `BASE_RANGE` and `EXCEPTION_RANGE` returned the same session/turn and promoted the state to `ACTIVE / required=true / completed=true`, with invocation count `2`.
5. The negative control containing range/exception tokens in separate spans returned `covered=false` with `relation_span` missing.
6. The final same-span relation plus all canonical render slots returned an empty Stop response and persisted `overall_covered=true`, relation `covered=true`, and `stop_disposition=COMPLETED`.

The staged probe did not execute a case semantic oracle; its oracle record is explicitly `NOT_RUN` because this is a generic parity probe, not an ASH case acceptance run. No oracle PASS is inferred.

The hook chain was reconstructed as:

```text
prompt input
  -> jdipt_activation.handle_user_prompt_submit
  -> create_pending_runtime_state
  -> PreToolUse inject_registry_runtime.handle_pre_tool_use
  -> jdipt_runtime_mcp.dispatch_json_rpc
  -> proposition_registry.register_material_proposition
  -> synthesis_runtime_state.save_runtime_state (atomic os.replace)
  -> stop_synthesis_gate.handle_stop_event
  -> relation + render-slot reconciliation
  -> persisted first/second summary and stop disposition
```

The staged probe exercised the Python boundaries directly with the same injected `PLUGIN_DATA`; the actual installed hook/MCP process was not observed. That distinction is preserved in the runtime identity and is part of the remaining hold.

## I. Residual Risks

- Installed plugin/runtime remains byte- and file-incomplete relative to the R2 repository; live installed acceptance is not proven.
- No active installed runtime attestation was collected.
- The exact default pytest and compileall commands remain blocked by Windows ACL/cache paths; controlled isolated-cache verification passes.
- The generic staged probe does not prove the full case semantic oracle or source-provider correctness; those are outside this Task 1R parity closure.

## J. Next Action

```text
NEXT = HOLD — continue Task 1R
```

Task 2 remains not started. The installed bundle/runtime must be refreshed or otherwise independently reconciled and the required live acceptance identity must be observed before Task 1 can move from `BLOCKED` to `PASS`.
