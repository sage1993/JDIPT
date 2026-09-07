# Task 3 report — Deterministic semantic soundness core

## Fix round 5 — final allowed round, current result

Base: `d505c3fd83c1f598e947def089258b9022af6e66`. All task work ran in `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`. Read the current Task 10 plan, Task 3 brief/report, both soundness/rendering modules, and the entire permanent Task 10 test file before editing. This section supersedes earlier counts and descriptions where they differ.

Changed only `scripts/proposition_soundness.py`, `tests/test_task10_semantic_soundness.py`, and this report. All previous 110 Task 10 cases remain unchanged; 35 permanent cases were appended. No registry, source, obligation, Task 9 coverage, rendering/reconciliation, ASH, root-checkout, or installed-binding files were edited. The existing typed authority snapshots and validation remain intact.

### Permanent RED before production

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py --tb=short
```

RED: **16 failed, 129 passed in 0.52s**, exit 1, no collection/setup errors. The 35 new cases cover:

| Reproduction / control | New cases | RED failures | Final GREEN |
| --- | ---: | ---: | ---: |
| Repeated suffix/prefix punctuation, earlier duplicate, adjacent CRLF | 6 | 4 | 6 |
| Field-local unmet condition, omitted/negated procedure, substituted effect; original and renamed typed values | 8 | 2 | 8 |
| Unique final legal anaphora, CLOSED polarity and OPEN status in both directions | 4 | 2 | 4 |
| No fallback selection between multiple authorities | 2 | 0 | 2 |
| OPEN definitive MAY_NOT, both `하지 않을 수 있다` and `하지 않아도 된다` | 2 | 2 | 2 |
| Unrelated two-field index/download prose, including action/effect mentions, and ownerless predicate controls | 10 | 6 | 10 |
| CRLF fences: shorter/wrong-character false closers, equal/longer true closers, numbered code headings and original offsets | 3 | 0 | 3 |

The prefix repetition, `충족하지 못해도`, `거치지 아니하고`, and `대신` cases were already fixed at this base and remain explicit preservation controls. The procedure omission failed for both original and renamed typed values. Ten RED failures were false passes; six unrelated-prose controls were false rejections. Expected structured violations and final spans are asserted through the public evaluator, with exact render coverage still passing where applicable. No tests were removed or weakened.

### Minimal production changes and review

- Immediate suffix wrapper grammar now accepts repeated punctuation before `이 명제는 거짓이다`. It still permits at most one adjacent newline, cannot cross an intervening assertion or blank paragraph, and checks each occurrence before exact-slot consumption. Earlier correct duplicates cannot cancel the contradiction. The existing repeated-prefix implementation is retained.
- Added `생략하면` only to the grammar directly adjoining the typed procedure value. Existing unmet-condition, negated-procedure, and alternate-effect grammar remains. Structured `LEGAL_RELATION_DEGRADATION` identifies the single affected field; the renamed-value matrix verifies that matching is not tied to fixture strings.
- Extended the existing full-assertion legal-anaphora grammar with `금지된다`. It is considered only in a final conclusion with one canonical authority. The already-supported allowed case remains covered. A bare definitive sentence, report operations, and non-unique anaphora do not trigger fallback assignment.
- Typed modality-marker detection now precedes the OPEN return. An observed MAY_NOT produces `OPEN_PROMOTED_TO_CLOSED` even though it lacks the earlier generic definitive markers. No uncertainty marker can erase that definitive relation predicate.
- Residual claim ownership requires at least two canonical fields and grammar directly attached to the canonical action or effect: an action conjugation or an effect-role particle. An object alone cannot establish legal identity; even nominal action/effect index mentions cannot borrow the report-download predicate. Effect-role identity preserves the existing missing-action regression. OPEN neutral adoption still independently requires uncertainty and at least two distinct anchors in the same explicit assertion; exact OPEN adoption remains supported.
- Reviewed the diff and the full regression result for field/region locality, typed authority freshness, raw assertion boundaries, and public classifier compatibility. The fence scanner itself was not changed; its CRLF, matching-character, closing-length, masked-heading, and offset behavior is verified by the new controls and all prior fence cases.

Scope review: no keyword-only/document-wide semantic inference, automatic repair/injection/rewrite, enum string fallback, compatibility table, source bypass, latest-state fallback, ASH constants, or Task 9 exact-render changes were introduced. Production changed by 21 added / 9 removed lines; test changes are append-only. This remains a deterministic bounded grammar gate, not unrestricted natural-language equivalence or external source-freshness verification.

### GREEN, focused integration, and full suite

```powershell
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py --tb=short
```

Soundness GREEN: **161 passed in 0.32s**, exit 0 (**145 Task 10 + 16 existing soundness**).

The first focused integration run used worktree-local `.pytest-task3-fix5-focused` and produced **231 passed, 71 setup errors in 1.66s**, exit 1. All setup errors were the reproduced Windows sandbox `PermissionError` creating that directory. The approved rerun used a fresh worktree-local path:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-fix5-focused-approved'
python -m pytest -q tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py tests/test_proposition_rendering.py tests/test_proposition_reconciliation.py tests/test_proposition_render_coverage.py tests/test_task9_deterministic_render_coverage.py tests/test_task5_source_obligation_closure.py tests/test_task8_material_obligation_registry_closure.py tests/test_typed_semantic_controls.py --tb=short
```

Focused integration: **1 failed, 301 passed in 0.99s**, exit 1, no setup errors.

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-fix5-full'
python -m pytest -q --tb=short
```

Full suite with approved worktree-local temporary writes: **1 failed, 614 passed in 6.17s**, exit 1, no setup errors. Both runs have the same sole pre-existing failure: `tests/test_task5_source_obligation_closure.py::test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot`, line 425, expects soundness PASS for canonical MUST rendered as MAY. Task 10 requires rejecting that weakening. The stop decision still blocks. Neither the protected Task 5 expectation nor the required soundness rejection was weakened; the full suite is not entirely green.

Required checks: `python scripts/validate_repo.py` **PASS**; `python scripts/validate_authority_temporal_contract.py` **PASS**; `python scripts/plugin_integrity.py` **FAIL**, exit 1, with the same **18 installed mismatches**. These are repository regression results, not installed-runtime parity evidence. `git diff --check` **PASS** with Git LF-to-CRLF notices only. The protected-path diff listing is empty.

Commit subject: `feat: add deterministic semantic soundness gate`. The pre-existing untracked Task 10 plan is excluded. Only production, permanent tests, and this report are included.

## Fix round 4 — current result

Base: `14763230f493cd5abeb86beb91f237d8438b6c74`. Worktree: `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`. Read the Task 10 plan, Task 3 brief/report, current production/tests, round 3 review package, and the independent reviewer's five Important findings. This section supersedes previous counts and implementation descriptions where they differ.

Changed only `scripts/proposition_soundness.py`, `tests/test_task10_semantic_soundness.py`, and this report. Registry, source, obligation, Task 9 coverage/rendering/reconciliation, ASH, and installed files were not edited. Typed semantic identity freshness and fail-closed authority validation remain intact. No repair, injection, rewrite, NLP, embeddings, LLM, or document-wide semantic inference was added.

### RED before production

Added 34 permanent cases covering the five findings and local positive controls; all previous 71 Task 10 cases remain. The actual MUST-to-MAY test still includes all canonical fields, explicit `지정할 수 있다`, and the singleton `MUST_DEGRADED_TO_MAY` expectation.

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py --tb=short
```

Initial RED: **21 failed, 84 passed in 0.46s**, exit 1, no setup errors. Each of the five issue families reproduced. Six label-only fence variants failed classification, three field-local conflicts and four repeated-prefix variants falsely passed, three unrelated OPEN-clause variants falsely adopted, and five unrelated-prose controls incorrectly failed. Six numbered-H1 fence variants already passed and remain permanent controls; the independent review's label-only variant exposed the masked-blank defect.

Self-review then identified real blank paragraphs after fences and wrapper line/paragraph locality as unresolved boundaries. Added five more permanent tests before their fixes:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py -k 'round4_real_blank or round4_false_wrapper_cannot_cross_blank or round4_false_wrapper_after_unpunctuated' --tb=short
```

Additional RED: **5 failed, 105 deselected in 0.19s**, exit 1. Total addition: **39 cases**; final Task 10 suite: **110 cases**.

### Minimal fixes and self-review

- Label paragraph scanning checks the actual blank-line position against fence intervals. Masked code headings/empty code lines cannot terminate a conclusion, while real blank paragraphs outside the fence still terminate labels. The existing scanner continues to handle LF/CRLF/CR, matching fence characters, and closing lengths at least the opener length. Public spans preserve original text and offsets.
- Extended canonical-field-adjacent prerequisite predicates to `못` and `아니하`, and effect substitution to `대신`. Structured violations identify the altered field and the bounded final claim. Correct exact rendering elsewhere cannot conceal those conflicts.
- Wrapper matching preserves raw line boundaries before presentation normalization, accepts repeated punctuation and an adjacent gap of at most one newline, and runs before exact-slot consumption. Prefix assertions require a sentence/line boundary; a suffix rejection cannot be reinterpreted as a prefix for the next temporal slot. Intervening assertions and blank paragraphs do not borrow wrappers. Earlier adoption cannot cancel a final wrapped contradiction.
- OPEN paraphrase adoption requires a full explicit canonical relation-list/uncertainty construction with at least two distinct anchors. Merely mentioning the relation before uncertainty about a report date is insufficient, even without a comma. Exact OPEN slots and the existing neutral OPEN case remain valid; punctuation/CR/newline isolation remains green.
- Residual field mentions need a definitive predicate and at least two canonical relation fields including action, object, or effect before legal claim evaluation. Removed assignment of every ownerless final predicate to all authorities. A small full-assertion legal-anaphora grammar with a unique authority retains the existing `이 행위는 허용된다` promotion and generic legal-relaxation regressions. Report download prose and nonassertive index mentions remain unrelated. This is a bounded deterministic gate, not unrestricted prose equivalence.
- Reviewed the diff for scope, public classifier compatibility, raw boundary handling, test isolation, and typed freshness preservation. Existing tests were not removed or weakened.

### GREEN and regressions

```powershell
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py --tb=short
```

Final focused GREEN: **126 passed in 0.24s**, exit 0 (**110 Task 10 + 16 existing soundness**).

The initial sandbox full run failed to create its fresh worktree-local pytest temporary directory: **420 passed, 155 setup errors in 3.55s**. Approved execution with a new worktree-local directory resolved that environment issue. After the final boundary fixes:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-fix4-final'
python -m pytest -q --tb=short
```

Final full suite: **1 failed, 579 passed in 5.91s**, exit 1, no setup errors. This includes rendering/reconciliation, Task 9 coverage, typed controls, source, obligation, registry, and stop regressions. The sole failure remains `tests/test_task5_source_obligation_closure.py::test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot`, line 425: it expects soundness PASS for a canonical MUST rendered as MAY. That previously documented expectation conflicts with Task 10 SS-06; neither that protected test nor the required rejection was weakened. The full suite is not entirely green.

Required checks: `python scripts/validate_repo.py` **PASS**; `python scripts/validate_authority_temporal_contract.py` **PASS**; `python scripts/plugin_integrity.py` **FAIL** with the same **18 installed mismatches**; `git diff --check` **PASS** (Git LF-to-CRLF notices only). These are repository regression results; installed-runtime parity is not claimed. Commit subject: `feat: add deterministic semantic soundness gate`. The pre-existing untracked Task 10 plan is excluded from the commit.

## Fix round 3 — current result

This section supersedes earlier round counts and fence/OPEN implementation notes. Base commit: `0ec9890b664ed947c5fdbbfeffac609648c4c049`. Worktree: `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`.

Changed paths: `scripts/proposition_soundness.py`, `tests/test_task10_semantic_soundness.py`, and this report. Typed `semantic_identity` validation, exact render contract equality, Task 9 coverage, source/registry/ledger ownership, and installed files remain unchanged.

### Permanent RED before production

Added 18 cases before production changes: four longer-fence/CRLF/CR variants, two fenced structural-marker cases, four local absence/not-effect cases, two exclamation-wrapper variants, four no-space punctuation/standalone-CR isolation cases, one insufficient-anchor OPEN paraphrase, and one exact OPEN adoption positive control. All previous 69 focused cases were retained, including P06 neutral OPEN acceptance, suffix-wrapper rejection, and the strengthened all-fields actual `지정할 수 있다` MUST-to-MAY regression with exact singleton `MUST_DEGRADED_TO_MAY` assertion.

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py --tb=short
```

RED: **17 failed, 54 passed in 0.37s**, exit 1. Sixteen new failures returned an incorrect soundness PASS. One fenced rejected-marker case already failed, but incorrectly returned unavailable authority while hiding the final OPEN promotion. The exact OPEN positive control passed. No collection/setup errors.

### Minimal fixes and self-review

- Replaced whole-document fence regex handling with one deterministic raw-line scanner. A closing fence must use the opener's character, have length at least the opener length, and contain only trailing whitespace. CR, LF, and CRLF are handled by the existing line-range helper; a three-backtick opener can close with four backticks. Unterminated fences remain code through EOF.
- The scanner produces code intervals once. An offset-preserving masked view excludes fenced content when deriving section, example, rejected-alternative, quotation, and uncertainty intervals. Numbered headings, example markers, and rejection text in code cannot affect the surrounding final conclusion. Original text/offsets remain in public spans; non-fenced structural behavior and the Task 9 coverage algorithm are preserved.
- Extended only the existing canonical-field-adjacent grammar for `없어도` and `아니라`. Conditions/procedures and explicit alternate effects produce `LEGAL_RELATION_DEGRADATION` identifying the affected field. Previous `충족되지 않아도`, `없이`, and `거치지 않아도` cases remain covered.
- Expanded the bounded false-wrapper prefix punctuation to include `!`/`?`; immediate suffix detection and occurrence-by-occurrence checks before exact slot consumption remain. Earlier correct occurrences cannot cancel the final contradiction.
- Raw sentence splitting now occurs at punctuation regardless of following whitespace and at CR/CRLF/LF. OPEN paraphrases require uncertainty plus two distinct canonical relation values in that same sentence. Exact adopted OPEN slots are accepted independently of the two-anchor paraphrase rule. The existing P06 neutral case and the new exact-slot positive case pass.
- Reviewed the production diff for scanner state transitions, shared offset preservation, owner/anchor checks, typed freshness, and protected-path scope. No broad NLP/document keyword inference, source/registry changes, repair, injection, rewrite, fixture-specific constants, LLM, or embedding were added. No requested reproduction was skipped.

### GREEN and full verification

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py --tb=short
```

GREEN: **87 passed in 0.20s**, exit 0 (71 Task 10 cases plus 16 existing soundness cases).

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-fix3-full'
python -m pytest -q
```

Full result: **1 failed, 540 passed in 5.79s**, exit 1; no setup errors. This approved worktree-local temporary-file run includes existing soundness, coverage, rendering, reconciliation, source, obligation, registry, and stop tests. The sole failure remains `tests/test_task5_source_obligation_closure.py::test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot`, line 425. It expects soundness PASS for MUST rendered as MAY, which is stale under SS-06. Neither that test nor production was weakened.

```powershell
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py
git diff --check
git diff --name-only -- scripts/proposition_rendering.py scripts/proposition_reconciliation.py scripts/proposition_render_coverage.py scripts/proposition_registry.py scripts/proposition_source_closure.py
```

Results: both validators **PASS**; installed integrity **FAIL** with the existing 18 mismatches; whitespace check clean apart from Git LF-to-CRLF notices; protected-path diff listing empty. No installed-runtime parity is claimed. Commit subject: `feat: add deterministic semantic soundness gate`.

## Fix round 2 — current result

This section supersedes earlier round counts and implementation notes where they differ. Base commit: `917e565889f351cf7c1032f853edbd38d028b320`. All work ran in `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`.

Changed paths: `scripts/proposition_soundness.py`, `tests/test_task10_semantic_soundness.py`, and `.superpowers/sdd/task10-semantic-soundness-closure/task-3-report.md`. No rendering, reconciliation, Task 9 coverage, registry, ledger, or source ownership changes. The typed `semantic_identity` snapshot and its fail-closed validation from round 1 remain intact.

### Regressions before production

Added 16 permanent cases before touching production: two fence variants containing a numbered heading; seven canonical-field-local absence/alternate-effect forms; four prefix-period/suffix false-wrapper cases with and without earlier adoption; and three raw sentence/LF/CRLF assertion-boundary cases. The existing neutral OPEN pass case remains. The original MUST-to-MAY case was strengthened to include all canonical fields and the actual bounded `지정할 수 있다` predicate, preserving its exact singleton `MUST_DEGRADED_TO_MAY` expectation. It no longer relies on an omitted action or missing modality marker.

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py --tb=short
```

RED result: **15 failed, 38 passed in 0.29s**, exit 1. All 15 failures were reproduced false-greens, not fixture/collection errors. The sentence-isolation case already passed; both raw newline variants failed. The strengthened actual-MAY regression also passed before these fixes. All prior 37 Task 10 cases were retained.

### Minimal implementation and self-review

- Section boundaries ignore numbered headings and conclusion labels inside the existing fenced-code ranges. A fenced `# 3. 검토이유` cannot end the enclosing final conclusion; both new fence cases assert coverage PASS followed by soundness FAIL.
- Extended the existing canonical-field-local relation helper to recognize adjacent `충족하지/충족되지 ... 않`, prerequisite `없이`, and effect `가 아닌/아닌/변경된` forms. Prefix `변경된` is also bound immediately to the canonical effect. The helper reports the specific altered field in `LEGAL_RELATION_DEGRADATION`; it does not scan unrelated document keywords.
- Exact slot occurrences inspect their immediately adjoining context before consumption. Prefix false assertions accept colon or period, and suffix `이 명제는 거짓이다.` is rejected. Earlier correct occurrences cannot cancel a final contradiction or make the wrapped occurrence adopted.
- OPEN adoption splits raw punctuation/newline boundaries before normalization. Residual claim analysis also preserves original line boundaries while allowing exact canonical slots to wrap across lines. Supplemental rule checks reuse the bounded sentence helper.
- Reviewed the production diff for shared helper use, typed freshness preservation, and changes outside the requested ownership boundaries. Slot text/IDs/equality and the Task 9 algorithm are unchanged. No broad NLP/keyword inference, repair, injection, rewriting, fixture-specific constants, LLM, or embedding was added.

### GREEN and full regression evidence

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py --tb=short
```

GREEN result: **69 passed in 0.16s**, exit 0 (53 Task 10 cases plus 16 existing soundness cases).

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-fix2-full'
python -m pytest -q
```

Full result: **1 failed, 522 passed in 5.82s**, exit 1, no setup errors. This approved worktree-local temporary-directory run includes all requested rendering/reconciliation/source/obligation and related regressions. The only failure is still `tests/test_task5_source_obligation_closure.py::test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot`, line 425: it expects soundness PASS for MUST rendered as MAY. That assertion is stale under SS-06 and was left unchanged, as instructed. Production continues to reject the weakening.

```powershell
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py
git diff --check
git diff --name-only -- scripts/proposition_rendering.py scripts/proposition_reconciliation.py scripts/proposition_render_coverage.py scripts/proposition_registry.py scripts/proposition_source_closure.py
```

Results: both validators **PASS**; installed integrity **FAIL** with the existing 18 mismatches; whitespace check clean (Git LF-to-CRLF notices only); the protected-path diff listing is empty. No installed files were modified and no installed-runtime parity is claimed. Commit subject: `feat: add deterministic semantic soundness gate`.

## Fix round 1 — current result

This section supersedes the original implementation's scope, freshness limitation, and test counts below; the earlier evidence is retained as history. Starting commit: `1335c7d5dc5b976b00bd7c72582d34400340bde7`. Work remained confined to `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`.

Changed paths in this fix commit:

- `scripts/proposition_soundness.py`
- `scripts/proposition_rendering.py`
- `tests/test_task10_semantic_soundness.py`
- `.superpowers/sdd/task10-semantic-soundness-closure/task-3-report.md`

### Permanent RED first

Added 13 parametrized regression cases before production edits: one subordinate-heading OPEN promotion, three negated condition/procedure variants, two false-wrapper variants with/without earlier adoption, four stale polarity/modality directions with identical slots, one render-only contract lacking semantic metadata, and two unrelated-uncertainty sentence separators. The original 24 required cases and their assertions were preserved.

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py --tb=short
```

Result against the previous production implementation: **13 failed, 24 passed in 0.23s**, exit 1. Every new case reproduced an actual false-green (`soundness_passed=True`); no fixture, import, or collection errors.

### Minimal production fixes and self-review

1. Restored the original numbered H1 `_HEADING_RE` behavior. Subordinate `##` headings remain inside `# 2. 검토결론`; the next numbered H1 still bounds the conclusion. Public span fields and adoption flags were not changed.
2. Added prerequisite-negation checks anchored directly to the canonical condition/procedure lexeme and its adjacent predicate (`충족하지 않`, `거치지 않`). Violations identify the specific degraded relation fields. No document-wide negation inference was added.
3. Exact slot matching now inspects each occurrence's enclosing false assertion before slot consumption. A `다음 명제는 거짓이다:` wrapper makes that occurrence non-adopted and produces a final contradiction. An earlier correct occurrence cannot hide the contradictory wrapper. This classification stays internal to soundness, preserving the public classifier for source/obligation callers.
4. Added the smallest typed metadata extension: `PropositionRenderContract.semantic_identity`, an optional frozen `LegalProposition` snapshot copied when building the contract. This is necessary because polarity changes and MUST_NOT/MAY_NOT changes can have identical rendered slots. Soundness revalidates and compares the typed snapshot explicitly; absent metadata fails unavailable, malformed metadata fails malformed, and stale typed values fail stale. `compare=False` keeps existing render-contract equality unchanged. Slot IDs, kinds, text, and Task 9 coverage/reconciliation code remain unchanged. The three-argument API is preserved; a manually constructed render-only contract is now insufficient semantic authority.
5. OPEN adoption now requires an uncertainty marker and the proposition's own canonical anchor in the same bounded sentence. Uncertainty about a report date cannot adopt the preceding legal proposition.

Self-review checked all five independent-review paths, constructor compatibility, typed enum validation without string fallback, occurrence handling before exact-text consumption, and shared helper reuse. No registry, ledger, source ownership, repair, injection, rewrite, fixture-specific constants, LLM, or embedding changes. Typed metadata proves correspondence to the supplied proposition snapshot; it does not independently establish external registry epoch or source freshness.

### GREEN and relevant regression results

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py tests/test_proposition_soundness.py --tb=short
```

Result: **53 passed in 0.13s**, exit 0: the original focused 40 cases plus all 13 new cases.

The full suite includes the relevant soundness, coverage, rendering/reconciliation, source, obligation, registry, and stop tests. It used approved worktree-local temporary writes to avoid the previously reproduced sandbox setup errors:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=F:/2026-PJ/JDIPT/.worktrees/task10-semantic-soundness-closure/.pytest-task3-fix1-full'
python -m pytest -q
```

Result: **1 failed, 506 passed in 5.46s**, exit 1, no setup errors. The sole failure remains `tests/test_task5_source_obligation_closure.py::test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot`, line 425. Its expectation of `soundness_passed=True` for MUST rendered as MAY is stale under Task 10 SS-06, as explicitly confirmed by the user. Neither production nor that assertion was weakened. All other full-suite tests passed.

```powershell
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py
git diff --check
git diff --name-only -- scripts/proposition_render_coverage.py scripts/proposition_reconciliation.py scripts/proposition_registry.py scripts/proposition_source_closure.py scripts/material_obligation_ledger.py
```

Results: both validators **PASS**; installed integrity **FAIL** with the existing 18 mismatches and no installed-file changes; whitespace check clean (only Git LF-to-CRLF notices); the ownership/coverage diff listing is empty. No installed-runtime parity is claimed. Commit subject remains `feat: add deterministic semantic soundness gate`.

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
