# Task 3 report — Deterministic semantic soundness core

## Scope

- Worktree: `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`.
- Starting commit: `91c5323` (Task 2 RED suite).
- Commit subject: `feat: add deterministic semantic soundness gate`.
- Changed paths: `scripts/proposition_soundness.py` and this report only.
- No tests, Task 9 coverage implementation, rendering/reconciliation metadata, registry, ledger, source ownership, installed plugin binding, or root-checkout files changed.

Read the Task 10 plan and Task 3 brief, canonical proposition/rendering/reconciliation/soundness modules, direct soundness consumers, and relevant source/obligation and stop-boundary regressions.

## Implementation and self-review

The three-argument `evaluate_soundness(propositions, contracts, draft)` API and `AnswerSpan` fields remain compatible. Structured violation serialization retains canonical enum values; unavailable or malformed enum metadata is represented by `None`, never converted through a string fallback.

- Validate canonical dataclasses and exact supplied contracts before evaluating adoption. Missing contracts no longer silently skip material propositions. Duplicate identities, colliding effect/open strings, malformed slot identities, and contract text stale relative to the supplied proposition produce structured violations.
- Bound a conclusion label by the next Markdown heading or blank paragraph. A later correct render can no longer supply missing fields to an earlier contradictory conclusion. Fences support backticks, tildes, and unterminated fenced regions.
- Preserve quotation, rejected-alternative, example, and code exclusions. Internally rejoin uncertainty fragments without crossing excluded regions. OPEN quotation-only content does not count as adoption; an uncertainty phrase does not cancel a definitive predicate elsewhere in the sentence.
- Consume exact contract assertions and inspect remaining adopted sentences individually. Exact canonical relation fields identify the proposition; ambiguous identities fail closed. Correct duplicates cannot cancel a contradictory sentence.
- Compare bounded predicate markers to typed modality and polarity. MUST weakening and MUST_NOT weakening return their dedicated structured codes. Final polarity contradictions also report `FINAL_CONCLUSION_CONTRADICTION`.
- Report missing condition, procedure, action, object, effect, and exception relation metadata in `relation_fields`. Supplemental base/exception rule text may appear together in a separate adopted relation sentence, preserving existing canonical range-relation rendering.
- Review corrected false matches between short relation identifiers and ordinary words/source URLs. The existing stop and registry parity acceptance tests pass in the final full-suite run.

Duplication/ownership review: contract generation and presentation normalization reuse their existing owners. No Task 9 required-set calculation was copied. No new persistence, source lookup, repair, injection, rewriting, embedding, LLM evaluation, or fixture-specific constants were added. The existing violation de-duplication helper remains shared; semantic inspection uses bounded candidate sentences rather than a document-wide union of legal keywords.

Authority boundary: freshness is checked against the supplied canonical proposition and exact generated contract. This three-argument API has no independent registry epoch or external freshness token; it does not establish external source freshness or replace upstream registry/source closure. Exact renderer assertions remain the semantic authority. The implementation is a deterministic bounded gate, not a general natural-language equivalence checker.

## TDD and focused verification

All commands below ran in the worktree stated above. After the first RED run, Python output was set to UTF-8 with `$env:PYTHONIOENCODING='utf-8'`.

Before production edits:

```powershell
python -m pytest -q tests/test_task10_semantic_soundness.py -p no:cacheprovider
```

Result: **8 failed, 16 passed in 0.16s**, exit 1. These were assertion failures, not fixture or collection errors. Failures covered MUST weakening, MUST_NOT weakening, final contradiction reporting (including duplicates), removed effect, malformed identity, ambiguous identity, and unavailable authority.

Final focused command:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py --tb=short
```

Result: **40 passed in 0.07s**, exit 0. All 24 permanent Task 10 cases and all 16 existing soundness cases passed. Tests were not changed or weakened.

Additional in-memory probes checked OPEN quotation-only content, OPEN mixed uncertainty/definitive assertion, a contradictory duplicate outside a labeled conclusion, stale effect contracts, missing authority, malformed slots, duplicate contracts, and tilde fences. All eight returned failing structured results. Earlier probes exposed the first two OPEN fail-open paths before they were corrected.

## Relevant and full regression evidence

The first sandboxed relevant run used:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider --basetemp=.pytest-task3-relevant tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py tests/test_proposition_render_coverage.py tests/test_task9_deterministic_render_coverage.py tests/test_task5_source_obligation_closure.py tests/test_task8_material_obligation_registry_closure.py tests/test_synthesis_runtime_state.py tests/test_stop_synthesis_gate.py tests/test_proposition_rendering.py tests/test_proposition_reconciliation.py tests/test_typed_semantic_controls.py --tb=short
```

Result: exit 1, pytest setup `PermissionError: [WinError 5]` creating the worktree-local temporary directory. Tool output was truncated. This was an environment failure, not a clean regression result.

An approved escalation ran the same selection with a fresh worktree-local temporary directory:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-verified tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py tests/test_proposition_render_coverage.py tests/test_task9_deterministic_render_coverage.py tests/test_task5_source_obligation_closure.py tests/test_task8_material_obligation_registry_closure.py tests/test_synthesis_runtime_state.py tests/test_stop_synthesis_gate.py tests/test_proposition_rendering.py tests/test_proposition_reconciliation.py tests/test_typed_semantic_controls.py --tb=short
```

Intermediate result: **3 failed, 202 passed in 1.32s**, exit 1. Two failures were the short-identifier/source-URL matching bug subsequently corrected; the third was the Task 5 compatibility failure below.

First full run, also with approved worktree-local temporary writes:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-full1'
python -m pytest -q
```

Intermediate result: **2 failed, 492 passed in 5.89s**, exit 1. A canonical registry/range-relation acceptance regression was corrected by allowing a separate adopted rule-relation sentence and bounded exception labels.

Final full run:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-full2'
python -m pytest -q
```

Result: **1 failed, 493 passed in 5.45s**, exit 1. No setup errors. This includes the relevant coverage, obligation, source, registry, stop, rendering, reconciliation, and typed-control tests.

### Explicit compatibility failure: Task 5 versus Task 10 SS-06

`tests/test_task5_source_obligation_closure.py::test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot`, line 425, expects `stored.first_reconciliation["soundness"]["soundness_passed"] is True` for a canonical MUST proposition whose final conclusion uses MAY (`지정할 수 있다`).

Task 10 SS-06 requires soundness to reject precisely that weakening. The new result is `False`; the overall stop decision remains blocked. This existing expectation is objectively incompatible with the requested contract, as explicitly confirmed by the user. Production was not weakened to satisfy it, and the test was left unchanged. The full suite is therefore **not entirely green**; this one compatibility failure remains documented for the next task.

## Required repository checks

```powershell
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py
git diff --check
```

- Repository validator: **PASS**.
- Authority/temporal contract validator: **PASS**.
- Installed plugin integrity: **FAIL**, exit 1, with the same 18 installed-file/digest mismatches documented in the Task 2 report. No installed files were changed. These are local regression results, not installed-runtime behavioral parity evidence.
- Diff whitespace check: clean, exit 0; Git emitted only its LF-to-CRLF notice.

The final production diff was reviewed again before reporting and committing. Only the production module and this report are included in the requested commit; the pre-existing untracked Task 10 plan is excluded.
