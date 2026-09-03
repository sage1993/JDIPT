# JDIPT ASH-06 Synthesis Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every material CLOSED source-specific legal effect survive synthesis as an independently rendered, semantically equivalent proposition sentence before explanatory free-form text is generated.

**Architecture:** Add a small deterministic synthesis-integrity module that models the Material Proposition Schema, renders mandatory legal-effect sentences using the source/effect anchor first, reconciles draft coverage, and repairs mismatches by restoring the mandatory sentence. Keep the production Skill generic: its authoritative synthesis block will require the same ledger → mandatory slots → explanation → reconciliation → bounded repair sequence. The existing ASH-06 oracle remains unchanged.

**Tech Stack:** Python 3.13, dataclasses, pytest, Markdown Skill/reference contracts, existing repository validators.

**Spec:** User-provided `JDIPT ASH-06 Synthesis Stability 수정 작업지시서`.

## Global Constraints

- Do not hard-code ASH-06, 안심주택, 250m, 350m, 400%, or 사업대상지 into generic production code or Skill contracts.
- Preserve source-specific designation, approval, recognition, permission, exclusion, counting, and non-application effects; a number, range, threshold, benefit, or generic relaxation is not coverage.
- CLOSED material propositions get independent mandatory sentence slots; base and exception propositions cannot be merged into one range sentence.
- OPEN propositions remain 확인 필요 or neutral conditional and cannot be promoted to confirmed legal effects.
- Repair priority is `mandatory_render_clause` → `source_proposition` → `evidence_span` → close paraphrase; do not invent a missing effect.
- Preserve all existing tracked and untracked user files; do not reset, clean, checkout, restore, commit, or push.
- Keep the existing ASH-06 oracle and its critical-negative criteria unchanged.

---

### Task 1: Add generic behavioral regression tests first

**Files:**
- Create: `tests/test_synthesis_integrity_behavior.py`
- Modify: `tests/test_synthesis_integrity_contract.py`

**Interfaces:**
- Tests will import `MaterialProposition`, `render_mandatory_proposition_sentence`, `render_mandatory_slots`, `reconcile_proposition`, `reconcile_draft`, and `repair_draft` from `scripts.synthesis_integrity`.
- A proposition uses `legal_actor`, `condition`, `procedure`, `modality`, `legal_action`, `legal_object`, `resulting_status_or_effect`, `polarity`, `relation_to_base_or_exception`, `source_proposition`, `evidence_span`, `closure_status`, and optional `operative_verb_lexeme`/`mandatory_render_clause`.

- [ ] **Step 1: Write a generic CLOSED designation fixture and positive test.**

```python
def designation_fixture() -> MaterialProposition:
    return MaterialProposition(
        proposition_id="EXCEPTION_X",
        materiality="material",
        legal_actor="A",
        condition="C",
        procedure="P",
        modality="may",
        legal_action="designate",
        legal_object="O",
        resulting_status_or_effect="Z",
        polarity="positive",
        relation_to_base_or_exception="exception",
        source_proposition="C를 충족하고 P를 거치면 O를 Z로 지정할 수 있다.",
        evidence_span="C를 충족하고 P를 거치면 O를 Z로 지정할 수 있다.",
        closure_status="CLOSED",
        operative_verb_lexeme="지정",
    )

def test_closed_designation_is_rendered_as_a_mandatory_legal_effect_sentence():
    proposition = designation_fixture()
    sentence = render_mandatory_proposition_sentence(proposition)
    result = reconcile_proposition(proposition, sentence)
    assert result.covered
    assert "C" in sentence and "P" in sentence and "O" in sentence
    assert "지정" in sentence and "Z" in sentence
```

- [ ] **Step 2: Add negative tests for effect deletion, procedure deletion, action degradation, and range-only paraphrase.**

```python
@pytest.mark.parametrize(
    ("draft", "missing"),
    [
        ("C를 충족하면 기준이 완화될 수 있다.", {"procedure", "legal_action", "legal_object", "resulting_status_or_effect"}),
        ("C를 충족하면 O를 Z로 지정할 수 있다.", {"procedure"}),
        ("C를 충족하고 P를 거치면 O에 혜택을 적용할 수 있다.", {"legal_action"}),
        ("P를 거치면 기준이 350까지 완화된다.", {"condition", "legal_action", "legal_object", "resulting_status_or_effect"}),
    ],
)
def test_reconciliation_rejects_degraded_closed_relation(draft, missing):
    result = reconcile_proposition(designation_fixture(), draft)
    assert not result.covered
    assert set(result.missing_fields) >= missing
```

- [ ] **Step 3: Add base/exception slot and OPEN safety tests.**

```python
def test_base_and_exception_get_independent_mandatory_slots():
    base = replace(designation_fixture(), proposition_id="BASE_X", relation_to_base_or_exception="base", source_proposition="기본 기준은 B이다.")
    exception = designation_fixture()
    slots = render_mandatory_slots([base, exception])
    assert len(slots) == 2
    assert "B" in slots[0]
    assert "C" in slots[1] and "P" in slots[1] and "지정" in slots[1]

def test_open_proposition_cannot_be_promoted_to_confirmed_effect():
    proposition = replace(designation_fixture(), closure_status="OPEN")
    result = reconcile_draft([proposition], "C를 충족하고 P를 거치면 O를 Z로 지정할 수 있다.")
    assert not result.covered
    assert "OPEN" in result.failures
```

- [ ] **Step 4: Run the new tests and verify they fail because the module/API is missing.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_integrity_behavior.py`

Expected: collection failure for the missing `scripts.synthesis_integrity` module, not a passing test.

---

### Task 2: Implement mandatory sentence rendering and semantic reconciliation

**Files:**
- Create: `scripts/synthesis_integrity.py`

**Interfaces:**
- `MaterialProposition` is a frozen dataclass with the fields used in Task 1 and optional `operative_verb_lexeme: str | None = None`, `mandatory_render_clause: str | None = None`.
- `render_mandatory_proposition_sentence(proposition: MaterialProposition) -> str` returns the source/effect-first sentence for a material CLOSED proposition, or an explicit unresolved sentence for OPEN/non-material input.
- `render_mandatory_slots(propositions: Sequence[MaterialProposition]) -> tuple[str, ...]` emits one slot per material proposition and preserves base/exception order without merging.
- `reconcile_proposition(proposition: MaterialProposition, draft: str) -> ReconciliationResult` checks every material relation component and rejects generic action substitution/range-only coverage.
- `reconcile_draft(propositions: Sequence[MaterialProposition], draft: str) -> DraftReconciliationResult` fails OPEN promotion and any uncovered CLOSED proposition.
- `repair_draft(draft: str, propositions: Sequence[MaterialProposition]) -> str` appends only the priority fallback sentence for each unresolved CLOSED proposition and an unresolved marker for OPEN propositions.

- [ ] **Step 1: Implement normalization and field/anchor matching.**

Use whitespace-normalized text matching. For `operative_verb_lexeme`, require that lexeme; otherwise map only the known generic action families (`designate`→`지정`, `approve`→`승인`, `recognize`→`인정`, `permit`→`허가`, `exclude`→`제외`, `count`→`산입`, `non-application`→`적용하지 아니`). Treat generic terms such as `완화`, `혜택`, and `가능` as insufficient for these fields.

- [ ] **Step 2: Implement exact-effect-first candidate selection.**

Select the first non-empty `mandatory_render_clause`, then `source_proposition`, then `evidence_span`; only if all are absent construct a sentence from the structured relation fields. For OPEN propositions, never return a confirmed assertion; append `확인 필요` and use a neutral conditional form.

- [ ] **Step 3: Implement independent slots and bounded repair.**

Render every material proposition separately. Prefix exception slots with a neutral exception relation cue when needed, but never collapse them into a numeric/range summary. `repair_draft` must not call a free paraphraser or synthesize a missing field.

- [ ] **Step 4: Run the behavioral tests and make them pass.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_integrity_behavior.py`

Expected: all generic positive/negative, base+exception, and OPEN safety cases PASS.

---

### Task 3: Make the Skill execution path authoritative and remove duplicate contract wording

**Files:**
- Modify: `skills/law-interpretation-request/SKILL.md`
- Modify: `skills/law-interpretation-request/references/legal-issue-mapping.md`
- Modify: `skills/law-interpretation-request/references/source-policy.md`
- Modify: `skills/law-interpretation-request/references/logic-validation.md`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_synthesis_integrity_contract.py`

**Interfaces:**
- The authoritative Skill block must state the executable sequence: `Material Proposition Ledger → mandatory proposition sentence construction → mandatory slots in draft → explanatory synthesis → proposition-to-draft reconciliation → one targeted repair → one bounded re-check → final rendering`.
- The schema must expose `operative_verb_lexeme` and `mandatory_render_clause` as optional surface anchors and preserve the existing fields.
- Reference docs contain detailed matching/repair rules; ASCII execution contract contains only hard stops and ordering needed at runtime.

- [ ] **Step 1: Replace the duplicated synthesis bullets with one authoritative block.**

Keep existing marker phrases required by structural tests, but make the mandatory sentence construction the first synthesis action after the ledger closes. State that legal effect is rendered before numbers/ranges/practical explanation, and that a dedicated base and exception sentence is required.

- [ ] **Step 2: Add generic operative anchor and repair priority language.**

Document `operative_verb_lexeme` and `mandatory_render_clause`; require the source-specific action/effect to remain recoverable and reject `완화`, `혜택`, `적용`, or `가능` as substitutes when they erase designation/approval/recognition/permission/exclusion relations.

- [ ] **Step 3: Keep OPEN fail-safe and reconciliation hard stop explicit.**

An OPEN proposition remains `확인 필요` or neutral conditional. A mismatch blocks rendering, repairs from the mandatory/source/evidence clause, then re-checks once. Do not add case-specific strings.

- [ ] **Step 4: Narrow validator names to structural contract presence.**

Rename or label synthesis marker groups as `structural_synthesis_contract`/equivalent in `scripts/validate_repo.py`; do not claim marker presence is behavioral semantic verification. Add a separate check that the behavioral regression module exists and is part of the documented focused validation path.

- [ ] **Step 5: Update contract tests to assert ordering/anchors rather than accumulating duplicate marker bullets.**

Retain marker-presence coverage, add checks for `mandatory proposition sentence`, `operative_verb_lexeme`, `mandatory_render_clause`, `legal effect first`, `one slot`, and the exact sequence. Confirm production docs contain none of the ASH-06 case tokens.

- [ ] **Step 6: Run focused contract tests.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_integrity_contract.py tests/test_structural_behavior_contract.py`

Expected: PASS with no case-specific hard-code failures.

---

### Task 4: Run complete validation and preserve live evidence honestly

**Files:**
- Modify only validation/report files if needed; do not modify the ASH-06 oracle.

- [ ] **Step 1: Run focused synthesis and semantic/oracle tests.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_integrity_behavior.py tests/test_synthesis_integrity_contract.py tests/test_ansim_housing_oracle.py tests/test_ansim_semantic_proposition_matcher.py tests/test_structural_behavior_contract.py`

- [ ] **Step 2: Run all required static checks.**

Run each command separately: `py -3.13 -m pytest -q`, `py -3.13 scripts/validate_repo.py`, `py -3.13 scripts/validate_authority_temporal_contract.py`, `py -3.13 scripts/plugin_integrity.py`, and `git diff --check`.

- [ ] **Step 3: Verify resolved installed Skill integrity before behavioral claims.**

Use the repository's existing integrity tooling and confirm the resolved installed Skill matches the repository source before any live run is considered valid.

- [ ] **Step 4: Run ASH-06 three times only if the existing runner/model environment is available.**

Use model `gpt-5.6-luna`, plugin version `0.2.4`, the existing oracle, and three independent runs. Record Process, Oracle, Critical missing, Base, Exception condition, Procedure, Specific legal effect, Current status, and base–exception relation per run. If the environment cannot run the live model, report that limitation and do not convert old artifacts into new live evidence.

- [ ] **Step 5: Run `git diff --check` and report branch, HEAD, origin HEAD, working tree, changed files, test results, live results, and final decision without commit/push.**

---
