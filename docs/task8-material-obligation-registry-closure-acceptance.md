# JDIPT Task 8 — Material Obligation Ledger and Registry Closure

## Acceptance snapshot

- Task title: Material Obligation Ledger and Registry Closure
- Date/time: 2026-09-07T15:48:00+09:00 (Asia/Seoul)
- Base SHA: `b308d46930d355bd6169f67414bdf1b02e9aa639`
- Final candidate SHA (runtime implementation): `bb8fb9c`
- Candidate branch: `codex/task8-material-obligation-closure`
- Candidate worktree: `F:\2026-PJ\JDIPT\.worktrees\task8-material-obligation-closure`
- Working tree at code snapshot: clean after scoped commits
- Acceptance-document commit: recorded in the final report after this document is committed

## Architecture objective

The candidate makes material-obligation completeness independent of the model's
registered proposition list. A generic material-obligation ledger is supplied at
the legal-issue-mapping boundary, verified source evidence is bound explicitly,
and the closure gate compares all three sets:

```text
required material obligations
        -> verified source evidence
        -> canonical LegalProposition registry
        -> deterministic Registry Closure Gate
```

The existing `LegalProposition` model remains canonical. `RegistryService` remains
the sole registry writer and the canonical production read boundary.

## Implemented contract

### Material Obligation Ledger

- `MaterialObligation` is a typed, immutable issue record with stable obligation
  identity, issue type, source-resolution status, evidence-source links, and
  proposition links.
- `MaterialObligationLedger` is the independent required-obligation set plus the
  explicit verified `EvidenceRef` set. It rejects missing top-level fields,
  duplicate identities, unknown fields, and malformed evidence.
- No ASH-specific issue names, numbers, or marker strings were added to the
  Task 8 production implementation.

### Source Resolution Status

`ObligationSourceStatus` is a strict enum with exactly:

- `SOURCE_CONFIRMED`
- `SOURCE_UNRESOLVED`
- `NOT_APPLICABLE`

Unknown and malformed values fail closed. `SOURCE_UNRESOLVED` may remain linked
to an `OPEN` proposition, but cannot promote a proposition to `CLOSED`.

### Evidence Binding and Closure Gate

`evaluate_registry_closure` / `validate_registry_closure` compare the required
obligations, explicit resolved evidence set, and canonical registered
propositions. A confirmed obligation must link to an exact verified `EvidenceRef`
and a canonical material `CLOSED` proposition. Authority and temporal checks reuse
the existing source-closure semantics. The explicit activation path enables the
Task 8 ledger requirement; registration without the ledger remains pending and
fails closed.

## Closure matrix

| Scenario | Expected | Actual |
|---|---:|---:|
| `SOURCE_CONFIRMED` + evidence + proposition | PASS | PASS |
| `SOURCE_CONFIRMED` + no proposition | FAIL | FAIL (`CONFIRMED_OBLIGATION_WITHOUT_PROPOSITION`) |
| `CLOSED` proposition + no required evidence | FAIL | FAIL (`PROPOSITION_WITHOUT_REQUIRED_EVIDENCE`) |
| `SOURCE_UNRESOLVED` + `CLOSED` proposition | FAIL | FAIL (`UNRESOLVED_SOURCE_PROMOTED_TO_CLOSED`) |
| `SOURCE_UNRESOLVED` + `OPEN` proposition | VALID | PASS / structurally valid |
| temporal evidence/conclusion conflict | FAIL | FAIL (`TEMPORAL_CONTRADICTION`) |
| required source type conflict | FAIL | FAIL (`INSUFFICIENT_AUTHORITY`) |
| required exception omitted while base only is registered | FAIL | FAIL |
| explicit activation + registration without ledger | FAIL CLOSED | FAIL CLOSED; state remains `PENDING` |

## Verification evidence

All results below were executed against the candidate implementation snapshot
`bb8fb9c` in the isolated candidate worktree.

| Gate | Command / scope | Result |
|---|---|---:|
| Task 8 focused | `python -m pytest -q tests/test_task8_material_obligation_registry_closure.py` | 38 passed |
| Task 6/7/8 integration | registry service, authority, Stop, runtime state, registry, validator, Task 8 suites | 115 passed |
| Task 1R–5 regression | Task 1R, Task 5, proposition, semantic, authority, and temporal suites | 159 passed |
| Full repository pytest | `python -m pytest -q` | 454 passed |
| Compile | `python -m compileall -q scripts tests` | PASS |
| Repository validator | `python scripts/validate_repo.py` | PASS |
| Authority/temporal validator | `python scripts/validate_authority_temporal_contract.py` | PASS |
| npm audit | `npm audit` | PASS; 0 vulnerabilities |
| MCP smoke | `npm run mcp -- --help` | PASS |
| Candidate plugin integrity | `python scripts/plugin_integrity.py --installed-root <isolated candidate mirror>` | PASS; `mismatches=[]` |
| Diff whitespace | `git diff --check` | PASS |

The candidate mirror was refreshed from the candidate runtime and was used for
the parity result. The installed `sage1993` binding was not changed.

## Authority and review

- Task 6 single RegistryService writer: PASS
- Task 7 RegistryService canonical reader: PASS
- Direct-reader AST guard: PASS
- Shadow authority: rejected / ignored
- Fallback authority: unchanged and fail closed
- Stale state: rejected by existing CAS/fingerprint contract
- Malformed state: rejected by runtime validation
- Critical findings: 0
- Important findings: 0

The final independent review of `bb8fb9c` reported Critical 0, Important 0, and
Readiness READY. Earlier review findings about activation, unactivated ingress,
and ledger lifecycle were fixed and re-reviewed before this close.

## Changed files

- `scripts/material_obligation_ledger.py`: typed ledger, source statuses, and
  deterministic closure validator.
- `scripts/material_obligation_ingress.py`: trusted issue-mapping ledger ingress.
- `scripts/proposition_registry.py`: canonical ledger persistence and lifecycle
  guards.
- `scripts/proposition_obligation_closure.py`: canonical compatibility export.
- `scripts/proposition_source_closure.py`: reused authority/temporal semantics.
- `scripts/synthesis_runtime_state.py`: canonical serialization, fingerprint, and
  fail-closed ledger state validation.
- `scripts/stop_synthesis_gate.py`: Registry Closure Gate integration.
- `scripts/jdipt_activation.py`: Task 8 activation and trusted ledger wiring.
- `scripts/plugin_integrity.py`, `scripts/validate_repo.py`: runtime bundle and
  repository validation coverage.
- `tests/test_task8_material_obligation_registry_closure.py`: focused Task 8
  model, closure, lifecycle, and authority regressions.
- `tests/test_task1r_registry_parity.py`, `tests/test_task6_registry_service.py`,
  `tests/test_registry_runtime_bridge.py`, `tests/test_proposition_registry.py`,
  `tests/test_typed_semantic_controls.py`, `tests/test_jdipt_runtime_mcp.py`:
  compatibility fixtures updated to supply the explicit lifecycle boundary.
- `tests/test_plugin_integrity_runtime_bundle.py`: candidate bundle parity
  coverage.
- `docs/superpowers/specs/2026-09-07-task8-material-obligation-registry-closure-design.md`:
  approved Task 8 design record.
- `docs/superpowers/plans/2026-09-07-task8-material-obligation-registry-closure.md`:
  implementation plan and TDD sequence.
- `docs/task8-material-obligation-registry-closure-acceptance.md`: this acceptance
  record.

## Root and installed-state preservation

- Root worktree `F:\2026-PJ\JDIPT` was not used for candidate edits; its pre-existing
  dirty changes and untracked files were preserved.
- The installed `sage1993` production binding and installation cache were not
  modified. Candidate parity used an isolated temporary runtime mirror.
- No main merge, PR creation, Task 9 implementation, or installed binding update
  was performed.

## Final verdict

Final verdict for the candidate implementation is:

```text
Task 8: PASS
Task 9 readiness: READY
Overall: PASS
```
