# JDIPT Task 9 — Deterministic Render Coverage

## A. Acceptance snapshot

- Task title: Deterministic Render Coverage
- Date/time: 2026-09-07T16:24:04+09:00 (Asia/Seoul)
- Base SHA: `c8e2354f2ba5c3156c360e8c2139909399428998`
- Final candidate SHA (runtime implementation): `6003a14ce86e36885d781fc0855b8f170df19a31`
- Candidate branch: `codex/task9-deterministic-render-coverage`
- Candidate worktree: `F:\2026-PJ\JDIPT\.worktrees\task9-deterministic-render-coverage`
- Working tree at runtime snapshot: clean after scoped commits
- Acceptance-document commit: recorded in the final report after this document is committed

## B. Task 9 objective

Task 9 answers one question only:

```text
Does every canonical proposition required by the Task 8 material-obligation
closure occur in the final user-visible answer?
```

The implemented authority chain is:

```text
MaterialObligationLedger
        ↓
Task 8 Registry Closure
        ↓
SOURCE_CONFIRMED verified evidence links
        ↓
linked canonical LegalProposition IDs
        ↓
existing deterministic PropositionRenderContract slots
        ↓
final rendered answer
        ↓
RenderCoverageResult
```

The required proposition set is computed from the canonical ledger and the
canonical closure result. It is never inferred from the final answer, model
importance judgments, keywords, or registry presence alone.

## C. Architecture implemented

- Required proposition authority: `MaterialObligationLedger` plus a passing,
  canonical `RegistryClosureResult`; only `SOURCE_CONFIRMED` obligations and
  their linked canonical proposition IDs enter the required set.
- Render coverage mechanism: `evaluate_render_coverage()` reuses
  `build_render_contract()` and `reconcile_render_contracts()` for exact,
  normalized deterministic slot presence.
- Coverage result model: `RenderCoverageResult` reports required IDs, covered
  IDs, missing IDs, pass/fail, and failure reason.
- Runtime integration: the Stop boundary obtains state through
  `RegistryService.read_state()`, evaluates coverage for Task 8 ledger-required
  states, and persists compact evidence through the existing
  `record_reconciliation()` compare-and-swap path.
- Fail-closed behavior: missing authority, closure mismatch, malformed or
  ambiguous identity, non-string final output, missing slot, and deterministic
  evaluation errors fail closed. No answer repair, proposition injection,
  registry mutation, or ledger mutation is performed by the coverage primitive.

## D. Render Coverage Matrix

| Scenario | Expected | Actual |
|---|---:|---:|
| All required propositions rendered | PASS | PASS |
| One required proposition missing | FAIL | FAIL; missing ID reported |
| Required exception missing | FAIL | FAIL; exception ID reported |
| Registry only, answer missing | FAIL | FAIL |
| Keyword only | FAIL | FAIL |
| Extra prose | PASS | PASS |
| Duplicate render | PASS | PASS |
| Malformed required identity | FAIL CLOSED | FAIL CLOSED |
| Authority failure producing empty set | FAIL CLOSED | FAIL CLOSED |

The Task 8/9 integration test also proves that a passing Task 8 registry
closure does not hide an omitted final proposition.

## E. Coverage / Soundness boundary

```text
Render Coverage:
deterministic presence and completeness of the authoritative required
proposition set in the final rendered text only.

Not evaluated by Task 9:
context correctness, quotation/example-only adoption, contradiction,
polarity, OPEN/CLOSED promotion, modality weakening, generic-relaxation
preservation, or semantic conclusion support.
```

A context/example-only fixture has `coverage_passed=True` while the existing
Semantic Soundness gate reports failure. The two result objects remain
separate and the Stop boundary still requires both gates for release.

## F. False-green regressions blocked

- The final answer cannot determine its own required set.
- Registry presence without final-answer slot presence fails.
- Partial legal terms or numbers do not satisfy an exact canonical slot.
- A base proposition cannot satisfy a separately required exception.
- A malformed required identity and a forged ledger/closure mismatch fail
  closed.
- A missing or unavailable required-set authority cannot be converted to `[]`
  and passed.
- Extra prose and duplicate occurrences do not create false failures for
  presence coverage.

No ASH-06 value, marker, question text, or domain-specific matcher was added
to production code.

## G. Regression / Authority

- Task 6 single `RegistryService` writer: PASS.
- Task 7 `RegistryService.read_state()` canonical reader: PASS.
- Task 8 ledger/closure authority: PASS; coverage revalidates the canonical
  closure and rejects authority mismatch.
- Activation lifecycle: PASS.
- Trusted ledger ingress: PASS.
- Pending restart semantics: PASS.
- Unactivated ingress rejection: PASS.
- Shadow state: rejected/ignored by the existing canonical-state tests.
- Stale state: rejected by the existing exact-turn fingerprint/CAS contract.
- Malformed state: rejected by existing runtime validation.
- Registry and ledger state remain mutation-free during coverage evaluation.

## H. Verification evidence

All results below are fresh results from the isolated Task 9 worktree.

| Gate | Command / scope | Result |
|---|---|---:|
| Task 9 focused | `python -m pytest -q -p no:cacheprovider tests/test_proposition_render_coverage.py tests/test_task9_deterministic_render_coverage.py` | 16 passed |
| Task 8/9 integration | `python -m pytest -q -p no:cacheprovider tests/test_task8_material_obligation_registry_closure.py tests/test_task9_deterministic_render_coverage.py` | 41 passed |
| Task 6/7/8/9 authority integration | Registry service, authority, closure, Stop, runtime state, bridge, and Task 9 suites | 99 passed |
| Task 1R–5 prior regression | Task 1R, Task 5, proposition, semantic, authority, and temporal group | 120 passed |
| Full repository pytest | `python -m pytest -q -p no:cacheprovider` | 470 passed |
| Compile | `python -m compileall -q scripts tests` | PASS; exit 0 |
| Repository validator | `python scripts/validate_repo.py` | PASS |
| Authority/temporal validator | `python scripts/validate_authority_temporal_contract.py` | PASS |
| npm ci | `npm ci` | PASS; 202 packages added, 0 vulnerabilities |
| npm audit | `npm audit` | PASS; 0 vulnerabilities |
| MCP smoke | `npm run mcp -- --help` | PASS; exit 0 |
| Candidate plugin integrity | `python scripts/plugin_integrity.py --repo-root <candidate> --installed-root <isolated candidate mirror>` | PASS; `mismatches=[]` |
| Diff whitespace | `git diff --check` | PASS; no output |

The candidate mirror was created outside the repository from this candidate
runtime solely for parity verification. The installed `sage1993` binding and
installation cache were not modified.

## I. Independent review findings

The 14 requested review questions were checked against the final runtime diff:

- Required set derived from final answer: no.
- Registry-only or keyword-only acceptance: no.
- Missing exception acceptance: no.
- Malformed identity or authority failure fail-open: no.
- Coverage mutation or source-less repair: no.
- Task 6 writer, Task 7 reader, or Task 8 closure bypass: no.
- Shadow/stale state authority: no.
- Coverage and Semantic Soundness merged: no.
- ASH-specific production hard coding: no.
- Oracle/acceptance weakening: no.

```text
Critical findings: 0
Important findings: 0
```

## J. Changed files

- `scripts/proposition_render_coverage.py`: authoritative required-set
  derivation and deterministic coverage result.
- `scripts/stop_synthesis_gate.py`: Task 9 coverage evaluation and release
  decision/evidence integration at the existing Stop boundary.
- `scripts/synthesis_runtime_state.py`: compact render-coverage evidence
  serialization through the existing persistence-only reconciliation path.
- `scripts/plugin_integrity.py`: candidate bundle manifest includes the new
  runtime module.
- `scripts/validate_repo.py`: required runtime/architecture inventory includes
  the coverage module.
- `tests/test_proposition_render_coverage.py`: RCOV matrix, fail-closed,
  authority mismatch, and coverage/soundness separation tests.
- `tests/test_task9_deterministic_render_coverage.py`: Task 8/9 Stop-boundary
  integration tests.
- `tests/test_plugin_integrity_runtime_bundle.py`: candidate runtime bundle
  parity guard.
- `docs/superpowers/plans/2026-09-07-task9-deterministic-render-coverage.md`:
  implementation plan and TDD sequence.
- `docs/task9-deterministic-render-coverage-acceptance.md`: this acceptance
  record.

## K. Commits / Push

```text
Commits:
2133f9b test: add deterministic render coverage red tests
b5054ec feat: add deterministic render coverage gate
4e5c224 feat: enforce render coverage at stop boundary
6003a14 test: add render coverage authority fail-closed guards
Acceptance-document commit: recorded in the final report after this document is committed

Remote branch: origin/codex/task9-deterministic-render-coverage
Remote SHA: recorded in the final report after the acceptance-document push
PUSH: PASS after acceptance-document commit
PR: NOT CREATED
MERGE TO MAIN: NOT RUN
```

## L. Residual risks and scope boundary

Task 9 intentionally does not enter Task 10 or broader Semantic Soundness /
runtime-acceptance work. The existing soundness gate remains responsible for
context, contradiction, polarity, OPEN/CLOSED promotion, modality, and final
conclusion semantics. Those later acceptance questions remain outside this
candidate.

The existing installed `sage1993` binding remains unchanged; candidate parity
was verified against an isolated mirror instead.

## M. Final verdict

```text
Task 9: PASS
Task 10 readiness: READY
Overall: PASS
```
