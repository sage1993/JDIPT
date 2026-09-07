# Task 5 — Source / Obligation Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic source, authority, temporal, obligation, dependency, and final-conclusion closure to the Task 4 proposition runtime without weakening Task 1R–4 contracts.

**Architecture:** Keep Task 4 coverage and soundness independent, then run two new closure evaluators at the Stop gate. `proposition_source_closure.py` evaluates evidence-span support, source citation, authority compatibility, and temporal validity. `proposition_obligation_closure.py` evaluates modality and legal-relation preservation plus dependency closure. Both return structured forensic results, are persisted beside coverage/soundness, and jointly participate in the existing one-repair/fail-closed state machine.

**Tech Stack:** Python 3, dataclasses, canonical `LegalProposition`/`EvidenceRef`, pytest, existing exact-turn JSON runtime state, plugin integrity and repository validators.

**Spec:** User-provided Task 5 — Source / Obligation Closure requirements in the current request; Task 4 acceptance at `docs/task4-semantic-soundness-acceptance.md`; canonical runtime plan at `docs/JDIPT Legal Proposition Runtime v2 Refactor Implementation Plan.md`.

## Global Constraints

- Preserve Task 1R proposition identity, dependency semantics, OPEN/CLOSED handling, and fail-closed behavior.
- Preserve Task 2 authority and temporal uncertainty; never turn unknown, missing, or outdated evidence into PASS.
- Preserve Task 3 typed enums and normalize aliases only at the existing registry boundary.
- Preserve Task 4 violations and the valid state `coverage=True, soundness=False`.
- Do not use citation presence alone, unrestricted substring presence, ASH-06 literals, or fixture weakening as a closure oracle.
- Keep source closure, obligation closure, soundness, and runtime disposition as independently inspectable results.
- Preserve the existing `sage1993` binding and all unrelated user changes in the original worktree.
- Do not push, create a PR, merge, or alter the marketplace binding.

---

### Task 1: Baseline, canonical extension, and RED evidence

**Files:**
- Create: `tests/test_task5_source_obligation_closure.py`
- Create: `docs/superpowers/plans/2026-09-07-task5-source-obligation-closure.md`
- Modify: `scripts/legal_proposition.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/jdipt_runtime_mcp.py`

**Interfaces:**
- Consumes: Task 4 canonical `LegalProposition`, `EvidenceRef`, typed semantic enums, exact-turn registry.
- Produces: typed authority/temporal requirement fields accepted only at the registry boundary and available to closure evaluators.

- [ ] **Step 1: Record the clean Task 4 baseline and create the Task 5 branch.**

Run:

```powershell
git status --short --branch
git log -1 --oneline
```

Expected: branch `codex/task5-source-obligation-closure`, clean worktree, HEAD `5c0cd31` before the plan file is added.

- [ ] **Step 2: Add failing tests for source and obligation closure behavior before writing closure production code.**

The test module must include real proposition fixtures and assert these exact outcomes: missing source, irrelevant evidence span, lower authority, historical source for a current requirement, unresolved temporal source, missing source citation, MUST dropped, MUST→MAY, MUST_NOT degraded, condition dropped, exception dropped, procedure dropped, dependency missing/open/rejected-only, unsupported final conclusion, and a non-material proposition that passes without source.

- [ ] **Step 3: Run the focused tests and preserve the RED output.**

Run:

```powershell
python -m pytest -q tests/test_task5_source_obligation_closure.py
```

Expected: FAIL because the Task 5 modules and result types do not yet exist. Record the failing test names and first failure in the acceptance evidence; do not change expected outcomes.

- [ ] **Step 4: Add `AuthorityRequirement` and `TemporalRequirement` to the canonical model with conservative defaults.**

Use typed `StrEnum` values `PRIMARY`, `PRECEDENT`, `INTERPRETATION`, `GUIDANCE`, `ANY` for authority and `CURRENT`, `HISTORICAL`, `ANY` for temporal requirement. Keep `EvidenceRef.authority_kind` and `EvidenceRef.temporal_status` unchanged. A CLOSED material proposition defaults to `PRIMARY` and `CURRENT` unless the registry supplies an explicit requirement; OPEN and NON_MATERIAL propositions may remain partial.

- [ ] **Step 5: Extend the registry and MCP schema only at the boundary.**

Accept `required_authority` and `required_temporal_status` in `proposition_registry.py` and `jdipt_runtime_mcp.py`, normalize them into the typed canonical fields, reject unknown values, and preserve `additionalProperties: false`. Do not add model-authored render or closure booleans.

- [ ] **Step 6: Re-run the focused tests to confirm the RED contract is still meaningful.**

Run:

```powershell
python -m pytest -q tests/test_task5_source_obligation_closure.py
```

Expected: the tests fail on missing evaluator behavior, not on malformed enum setup or fixture construction.

### Task 2: Implement source, authority, and temporal closure

**Files:**
- Create: `scripts/proposition_source_closure.py`
- Modify: `tests/test_task5_source_obligation_closure.py`

**Interfaces:**
- Consumes: `Sequence[LegalProposition]`, the final draft, and Task 4 render contracts/answer-region classifier.
- Produces: `SourceClosureViolation`, `SourceClosureResult`, `evaluate_source_closure()`, and `source_closure_result_to_dict()`.

- [ ] **Step 1: Define forensic source result dataclasses.**

Each violation must retain `code`, proposition id, materiality, modality, polarity, status, required source type, actual source type, required authority, actual authority, source id, source span, matched span, required condition, matched condition, required exception, matched exception, required procedure, matched procedure, dependency proposition ids, final-conclusion span, and a reason. Use typed enum values in memory and serialize their string values.

- [ ] **Step 2: Implement conservative source support matching.**

For each MATERIAL proposition, require an evidence reference. Compare the normalized token sequences for subject, legal action/operative verb, legal object, legal effect, condition, and procedure against `evidence_span`; require all non-empty legal relation fields for support. Distinguish no meaningful relation match (`SOURCE_PRESENT_BUT_NOT_SUPPORTING`) from partial/conflicting relation (`SOURCE_PROPOSITION_MISMATCH`). Do not accept only a URL, title, citation marker, or unrelated topic word.

- [ ] **Step 3: Implement citation, authority, and temporal checks.**

Require a final-answer source anchor containing the source id or locator and source title/locator pair where available. Map statute/regulation/ordinance to `PRIMARY`, precedent to `PRECEDENT`, interpretation to `INTERPRETATION`, guidance to `GUIDANCE`; fail with `INSUFFICIENT_AUTHORITY` when the actual kind cannot satisfy the typed requirement. Fail current requirements on `HISTORICAL_CONFIRMED` with `OUTDATED_SOURCE_USED`, and on `CURRENT_UNRESOLVED` with `TEMPORAL_SOURCE_UNRESOLVED`. Preserve actual source/temporal evidence in every violation.

- [ ] **Step 4: Add source-focused tests and run them RED-to-GREEN.**

Run:

```powershell
python -m pytest -q tests/test_task5_source_obligation_closure.py -k "source or authority or temporal or non_material"
```

Expected: all source/authority/temporal cases PASS while obligation/dependency cases remain failing.

### Task 3: Implement obligation, dependency, and final-conclusion closure

**Files:**
- Create: `scripts/proposition_obligation_closure.py`
- Modify: `tests/test_task5_source_obligation_closure.py`

**Interfaces:**
- Consumes: canonical propositions, Task 4 render contracts, final draft, and the existing bounded answer-region classifier.
- Produces: `ObligationClosureViolation`, `ObligationClosureResult`, `evaluate_obligation_closure()`, and `obligation_closure_result_to_dict()`.

- [ ] **Step 1: Define independent obligation/dependency result dataclasses.**

Retain `obligation_closure_passed`, `dependency_closure_passed`, and `final_conclusion_support_passed` separately. Every violation must preserve proposition identity, typed semantics, required/matched condition, exception, procedure, dependency IDs, adopted/rejected matched span, final-conclusion span, and reason.

- [ ] **Step 2: Implement adopted-region obligation checks.**

Use the existing Task 4 region classifier so quotation, example, and code-only text cannot satisfy an obligation. For MUST require a mandatory marker and reject MAY/recommendation-only output as `MUST_DEGRADED_TO_MAY`; for MUST_NOT reject positive or caution-only weakening as `MUST_NOT_DEGRADED`. Require condition, procedure, and exception relation in the adopted final conclusion, emitting `CONDITION_DROPPED`, `PROCEDURAL_PREREQUISITE_DROPPED`, and `EXCEPTION_DROPPED` independently.

- [ ] **Step 3: Implement dependency closure.**

Resolve `base_proposition_id` and `exception_proposition_id` against the exact proposition registry. Emit `DEPENDENCY_OMITTED` for missing ids, `DEPENDENCY_OPEN` for OPEN dependencies supporting a definitive parent, and `DEPENDENCY_OMITTED` when a dependency appears only in rejected/example/code regions. Propagate source closure failure of a dependency without marking it CLOSED.

- [ ] **Step 4: Implement final-conclusion support.**

Require every MATERIAL CLOSED proposition's adopted final conclusion to retain the proposition's legal action/effect and typed modality/polarity. Emit `FINAL_CONCLUSION_UNSUPPORTED` when the conclusion is absent, generic, stronger than the proposition, or opposite in polarity. Keep this result independent from Task 4 `FINAL_CONCLUSION_CONTRADICTION`.

- [ ] **Step 5: Run the full Task 5 focused suite.**

Run:

```powershell
python -m pytest -q tests/test_task5_source_obligation_closure.py
```

Expected: all Task 5 domain tests PASS.

### Task 4: Persist closure evidence and enforce it at Stop

**Files:**
- Modify: `scripts/synthesis_runtime_state.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `tests/test_synthesis_runtime_state.py`
- Modify: `tests/test_stop_synthesis_gate.py`

**Interfaces:**
- Consumes: source and obligation result models from Tasks 2–3.
- Produces: exact-turn persisted `source_closure`, `obligation_closure`, and independent runtime disposition.

- [ ] **Step 1: Extend reconciliation evidence serialization.**

Add optional source and obligation result parameters to `_reconciliation_summary()` and `record_reconciliation()`. Serialize both result objects with their typed forensic fields under the existing first/second reconciliation records; do not combine them into `soundness_passed` or `covered`.

- [ ] **Step 2: Add the failing Stop integration tests.**

Add tests proving a draft with coverage and soundness success still blocks on source failure, obligation failure, dependency failure, or unsupported final conclusion; prove persisted evidence contains both independent results; prove the second attempt fail-closes; prove a different session/turn cannot reuse closure state.

- [ ] **Step 3: Wire the evaluators into `handle_stop_event()`.**

Run source closure and obligation closure after Task 4 soundness. Define runtime PASS only when coverage, Task 1R relation, soundness, source closure, authority closure, temporal closure, obligation closure, dependency closure, and final-conclusion support all pass. Include distinct violation codes in the bounded repair reason. Preserve Task 4 failures even when Task 5 passes.

- [ ] **Step 4: Run runtime-focused tests and existing soundness tests.**

Run:

```powershell
python -m pytest -q tests/test_task5_source_obligation_closure.py tests/test_stop_synthesis_gate.py tests/test_synthesis_runtime_state.py tests/test_proposition_soundness.py
```

Expected: PASS with the first mismatch allowing one repair and the second mismatch returning the existing fail-closed response.

### Task 5: Bundle parity, repository contracts, and documentation

**Files:**
- Modify: `scripts/plugin_integrity.py`
- Modify: `scripts/validate_repo.py`
- Modify: `skills/law-interpretation-request/SKILL.md`
- Modify: `skills/law-interpretation-request/references/source-policy.md`
- Modify: `skills/law-interpretation-request/references/legal-issue-mapping.md`
- Modify: `docs/architecture.md`
- Create: `docs/task5-source-obligation-closure-acceptance.md`
- Modify: `tests/test_plugin_integrity_runtime_bundle.py`
- Modify: structural contract tests as required by the documented owner files

**Interfaces:**
- Consumes: production closure modules and runtime wiring.
- Produces: repository/installed runtime parity and a source-backed acceptance record.

- [ ] **Step 1: Add both modules to the runtime bundle and validators.**

Require both files in the plugin runtime manifest, add generic production markers, and reject ASH-06/fixture-specific literals in the new production modules. Keep `sage1993` marketplace identity unchanged.

- [ ] **Step 2: Update one owner document per policy.**

Document source support, authority/temporal closure, obligation preservation, dependency closure, and fail-closed runtime ordering in the Skill/source-policy/issue-mapping/architecture owners without copying the full policy into unrelated files.

- [ ] **Step 3: Run static contract tests and validators.**

Run:

```powershell
python -m pytest -q tests/test_plugin_integrity_runtime_bundle.py tests/test_validate_repo_contract.py tests/test_proposition_runtime_contract.py
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py
```

Expected: PASS, with repository and installed-candidate parity checked separately after the local implementation is complete.

- [ ] **Step 4: Write the acceptance document from fresh command output.**

Include final verdict, baseline, root cause, actual pipeline, source/authority/temporal/obligation/dependency contracts, violation list, regression counts, verification commands, installed candidate digest state, independent review findings, residual risks, and canonical Task 6 next action. Do not claim unrun live acceptance suites.

### Task 6: Full verification, independent review, and commits

**Files:**
- Modify only files already listed above when verification exposes a scoped defect.

- [ ] **Step 1: Run focused and cross-task regression suites.**

Run the Task 5 suite, Task 4 soundness/runtime tests, Task 3 typed semantic tests, Task 2 authority/temporal tests, Task 1R proposition/dependency tests, reconciliation/render coverage tests, and the complete pytest suite. Record exact counts and failures.

- [ ] **Step 2: Run compile, package, dependency, smoke, and diff verification.**

Run:

```powershell
python -m compileall -q scripts tests
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py
npm ci
npm audit
npm run mcp -- --help
git diff --check
```

Expected: every command exits 0. A live ASH-06 or global release gate is reported as NOT RUN unless actually executed.

- [ ] **Step 3: Perform independent review against the Critical/Important checklist.**

Inspect the diff and tests for source false PASS, authority/temporal bypass, obligation weakening, dependency omission, final-conclusion overclaim, stale cross-turn state, evidence loss, duplicated normalization, unnecessary non-material failures, and runtime-bundle omission. Record `Critical findings` and `Important findings` explicitly.

- [ ] **Step 4: Verify an isolated candidate runtime manifest.**

Use the supported local candidate mechanism or a copied isolated bundle, then compare repository and candidate runtime digests and report `mismatches=[]`. Do not overwrite the existing `sage1993` installation.

- [ ] **Step 5: Commit only Task 5 production/regression changes and acceptance documentation.**

Use separate commits when practical:

```powershell
git add scripts tests skills docs/architecture.md
git commit -m "feat: add source and obligation closure"

git add docs/task5-source-obligation-closure-acceptance.md
git commit -m "docs: record task 5 source obligation closure acceptance"
```

Do not push, open a PR, merge, or include unrelated changes.
