# JDIPT v0.2.4 ASH-06 Evidence-to-Synthesis Stability Fix Implementation Plan

**Goal:** Preserve generic, source-specific legal effects and temporal closure through synthesis while making the ASH-06 oracle evaluate only local semantic propositions.

**Architecture:** Keep the production Skill contract generic and concise, with a per-issue material proposition ledger that carries condition, procedure, specific legal effect, authority, temporal status, and closure status. Implement the deterministic regression oracle as a local-proposition detector: sentence/clause evidence may satisfy a marker, but unrelated document-wide terms may not. Extend focused tests with generic legal-effect, temporal, and `AUTO_FAR_400` locality fixtures.

**Tech Stack:** Markdown Skill contract, Python 3.13, pytest, deterministic regex-based regression oracle.

**Spec:** User-provided Codex 작업지시서 — JDIPT v0.2.4 ASH-06 Evidence-to-Synthesis Stability Fix.

## Global Constraints

- Do not hardcode ASH-06, 250m, 350m, 400%, 사업대상지, or 안심주택 into the production contract.
- Preserve verified source-specific effects such as designation, approval, permission, exclusion, counting, or non-application; do not replace them with generic relaxation language.
- Keep unresolved material dependencies explicit and conditional after bounded targeted retry; never infer a missing rule.
- Distinguish confirmed current, confirmed historical, and unresolved temporal status; recent date or document title alone does not confirm current applicability.
- Limit `AUTO_FAR_400` detection to the same sentence/clause/local proposition and retain true automatic-application negatives.
- Preserve existing tracked changes and existing untracked files.
- Run focused tests before full validation, then run all required repository checks and `git diff --check`.

---

### Task 1: Add regression coverage for evidence-to-synthesis invariants

**Files:**
- Modify: `tests/test_structural_behavior_contract.py`
- Modify: `tests/test_ansim_housing_oracle.py`
- Modify: `tests/test_ansim_semantic_proposition_matcher.py`

**Interfaces:**
- Tests consume the existing Markdown contract and `scripts.ansim_housing_oracle.detect_ansim_markers` API.
- Tests must describe generic source effects and temporal states, while ASH-06 fixtures may use its concrete numbers only in the evaluator tests.

- [ ] Add failing tests for source-specific effects that reject generic relaxation substitutions.
- [ ] Add failing tests for current-confirmed, historical-confirmed, and current-unresolved wording.
- [ ] Add passing and failing `AUTO_FAR_400` locality fixtures, including separated basic-rate and unrelated-relaxation sentences.
- [ ] Run the focused tests and record the expected failures before changing production code.

### Task 2: Implement local semantic scope in the deterministic oracle

**Files:**
- Modify: `scripts/ansim_housing_oracle.py`

**Interfaces:**
- Preserve `detect_ansim_markers(answer: str) -> set[str]` and all existing marker names and gate mappings.
- Keep true automatic-application phrases failing while separated factual/basic-rate phrases pass.

- [ ] Normalize line-wrapped Markdown without treating every line break as a semantic boundary.
- [ ] Evaluate `AUTO_FAR_400` within a sentence/clause-local proposition rather than document-wide term combinations.
- [ ] Re-run the new focused oracle tests and existing oracle tests.

### Task 3: Refine the generic production contract and reference guidance

**Files:**
- Modify: `skills/law-interpretation-request/SKILL.md`
- Modify: `skills/law-interpretation-request/references/legal-issue-mapping.md`
- Modify: `skills/law-interpretation-request/references/source-policy.md`

**Interfaces:**
- Keep the existing runtime priority contract and source hierarchy intact.
- Add only generic material-proposition ledger requirements and temporal status semantics; do not add ASH-06-specific tokens.

- [ ] Consolidate duplicated closure wording where practical without removing existing structural-contract markers.
- [ ] Define the generic proposition fields and `OPEN`/`CLOSED` behavior, including condition, procedure, specific legal effect, and temporal status.
- [ ] State that unresolved current applicability cannot be rendered as current and that unresolved effects remain explicitly unresolved.
- [ ] Run structural contract tests after documentation changes.

### Task 4: Validate the complete change and report the acceptance gate

**Files:**
- No additional production files unless validation exposes a covered defect.

- [ ] Run focused structural and oracle tests.
- [ ] Run full pytest and distinguish any environment failure from production failures.
- [ ] Run `validate_repo.py`, `validate_authority_temporal_contract.py`, `plugin_integrity.py`, and `git diff --check`.
- [ ] Compare the existing three ASH-06 runs against the fixed oracle and document that live model reruns are only claimable if independently executed.
- [ ] Report repository state, changed files, contract/oracle changes, validation results, live evidence, semantic review, and final verdict.
