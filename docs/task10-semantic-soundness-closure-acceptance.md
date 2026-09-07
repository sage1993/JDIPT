# Task 10 — Semantic Soundness Closure Acceptance

## A. Final Verdict

```text
Task 10: PASS
Task 11 readiness: READY
Overall: PASS
```

This acceptance covers the semantic-soundness closure only. Task 11 was not entered.

## B. Repository State

```text
Base SHA: 02156e9b4633da7d6bfc5c308e98d602c4318f86
Branch: codex/task10-semantic-soundness-closure
Final HEAD (implementation acceptance): c6bb0f3ae1b9c4fe1f6c739478f82fa150770e96
Remote SHA: no origin tracking ref; branch was not pushed
Working tree: tracked implementation files clean; pre-existing/untracked scratch evidence retained
Root dirty changes: preserved; root checkout was not modified
sage1993 binding: unchanged
PUSH: NO
PR: NO
MERGE: NO
```

## C. Architecture Boundary

- `scripts/proposition_soundness.py` remains the independent post-coverage semantic layer.
- Typed semantic identity remains authoritative for proposition ownership and relation comparison.
- `scripts/proposition_render_coverage.py` was not modified. Coverage and soundness remain independent results.
- Registry writer/reader boundaries, automatic repair/injection, and ASH-06 production branches were not changed.
- Ambiguous, malformed, unavailable, or unresolved identity remains fail-closed.

The preserved boundary is:

```text
coverage = PASS
soundness = FAIL
final acceptance = FAIL
```

## D. Remediation and TDD Evidence

The permanent regression matrix is in `tests/test_task10_semantic_soundness_closure.py`.

The four required defect families were exercised before the corresponding production closure:

- `PUNCTUATION_CONTRADICTION`: wrapper punctuation variants and direct contradictory predicates. Spaced-period and Unicode-full-stop variants were observed RED before boundary-only normalization.
- `RELATION_DEGRADATION`: condition/procedure/object/effect omission and substitution, plus multi-slot degradation.
- `CLAIM_OWNERSHIP`: unrelated neighboring subjects, ownerless legal predicates, ambiguous multi-owner claims, and excluded regions.
- `OPEN_NEGATIVE_ANAPHORA`: explicit-subject, anaphoric positive/negative, ambiguous anaphora, and a valid CLOSED negative anaphora control.

The final Task 10 focused gate is `272 passed`. The implementation uses deterministic punctuation-boundary normalization, exact typed-field boundaries, bounded claim ownership, and an identity-bound anaphora grammar. No embedding judge, general-purpose coreference engine, automatic repair, or ASH-specific relation special case was added.

## E. Semantic Soundness Matrix

`Actual` records the gate result: `PASS` means the valid case passed; `FAIL` means the invalid case was rejected; `FAIL CLOSED` means ambiguity or unavailable authority was rejected without guessing.

| Scenario | Expected | Actual |
| --- | --- | --- |
| Correct CLOSED adoption | PASS | PASS |
| Rejected quotation only | FAIL | FAIL — `REJECTED_QUOTATION_ONLY` |
| Code block only | FAIL | FAIL — `CODE_BLOCK_OR_EXAMPLE_ONLY` |
| Example only | FAIL | FAIL — `CODE_BLOCK_OR_EXAMPLE_ONLY` |
| OPEN → definitive positive | FAIL | FAIL — `OPEN_PROMOTED_TO_CLOSED` |
| OPEN → definitive negative | FAIL | FAIL — `OPEN_PROMOTED_TO_CLOSED` |
| OPEN → anaphoric definitive negative | FAIL | FAIL — `OPEN_PROMOTED_TO_CLOSED` |
| Polarity inversion | FAIL | FAIL — polarity/final-conclusion contradiction |
| MUST → MAY | FAIL | FAIL — `MUST_DEGRADED_TO_MAY` |
| MUST_NOT → MAY_NOT | FAIL | FAIL — `MUST_NOT_DEGRADED` |
| Contradictory conclusion | FAIL | FAIL — final-conclusion contradiction |
| Spaced-punctuation contradiction | FAIL | FAIL — final-conclusion contradiction |
| Repeated-punctuation contradiction | FAIL | FAIL — final-conclusion contradiction |
| Unicode ellipsis/full-stop contradiction | FAIL | FAIL — final-conclusion contradiction |
| Contradictory duplicate | FAIL | FAIL — contradiction/ambiguous adoption |
| Condition omission | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Condition substitution | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Procedure omission | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Procedure substitution | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Object omission | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Object substitution | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Effect omission | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Effect substitution | FAIL | FAIL — `LEGAL_RELATION_DEGRADATION` |
| Ambiguous claim ownership | FAIL CLOSED | FAIL CLOSED — `AMBIGUOUS_ADOPTED_IDENTITY` |
| Malformed identity | FAIL CLOSED | FAIL CLOSED — `MALFORMED_SEMANTIC_IDENTITY` |
| Unavailable authority | FAIL CLOSED | FAIL CLOSED — `UNAVAILABLE_SEMANTIC_AUTHORITY` |

The excluded quotation, code, and example controls retain coverage while failing soundness. This confirms the required `Coverage PASS + Soundness FAIL` boundary.

## F. Task 5 Contract Reconciliation

```text
SOURCE_REQUIREMENT = docs/task5-source-obligation-closure-acceptance.md records MUST → MAY as MUST_DEGRADED_TO_MAY
OLD_EXPECTATION = test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot expected soundness_passed=True
TASK10_REQUIREMENT = MUST → MAY is modality weakening and therefore UNSOUND
RESOLUTION = RESOLVED_BY_TASK10_SUPERSESSION
```

The old assertion was reconciled to the normative closure contract: the stop result remains blocked, the coverage/effect-slot result remains covered, and both soundness and obligation closure report `MUST_DEGRADED_TO_MAY`. No production behavior was weakened to satisfy the old assertion. The remaining Task 1R–8 regression suite passed unchanged in behavior.

## G. Verification Evidence

```text
Task10 focused: 272 passed
Task9 regression: 28 passed
Task1R–8 regression: 162 passed
Broader integration: 416 passed
Full suite: 652 passed
validate_repo: PASS
authority-temporal: PASS
compileall: PASS
plugin integrity: FAIL — 18 pre-existing installed-cache mismatches
git diff --check: PASS
npm ci: PASS — 202 packages audited, 0 vulnerabilities
npm audit: PASS — 0 vulnerabilities
MCP: PASS — npm run mcp -- --help exit 0; local JSON-RPC smoke 6 passed
```

The full suite was a fresh run in a worktree-local pytest temp directory and completed with zero failures.

## H. Plugin Integrity Classification

```text
BASE_MISMATCH_COUNT = 18
FINAL_MISMATCH_COUNT = 18
TASK10_INTRODUCED_MISMATCH_COUNT = 0
TASK10_REMOVED_MISMATCH_COUNT = 0
PLUGIN_INTEGRITY_REGRESSION = 0
ENVIRONMENTAL_INSTALLED_PARITY_BLOCKER = YES
```

The unqualified integrity check still fails because the installed `sage1993` cache is stale/missing files. The cache and binding were not modified or overwritten. The exact mismatch set is identical at the Task 9 base and Task 10 final implementation.

## I. Scope and Preservation

```text
Task 9 algorithm modified: NO
Task 9 coverage behavior changed: NO — protected file diff is empty; regression is 28 passed
ASH-06 oracle modified: NO — oracle diff is empty
sage1993 binding modified: NO
Root dirty changes preserved: YES
Automatic repair/injection added: NO
Task 11 entered: NO
```

## J. Task 11 Boundary

All Task 10 semantic, regression, static, package, and MCP gates are green. The only non-green command is the pre-existing installed-plugin parity check, with zero Task 10-introduced mismatches and no binding mutation. Therefore:

```text
Task 11 readiness: READY
```

