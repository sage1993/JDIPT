from __future__ import annotations

import pytest

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract
from scripts.proposition_soundness import evaluate_soundness


def _evidence(source_id: str = "closure-law-001") -> EvidenceRef:
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title="Task 10 closure fixture",
        source_locator=f"https://example.test/{source_id}",
        evidence_span="요건을 충족하고 절차를 거치면 행정청은 대상에 법적 효과를 지정할 수 있다.",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="현행 기준에 따른다.",
    )


def _proposition(
    *,
    proposition_id: str = "P1",
    status: PropositionStatus = PropositionStatus.CLOSED,
    condition: str = "요건",
    procedure: str = "절차",
    legal_action: str = "지정",
    legal_object: str = "대상",
    legal_effect: str = "350m",
    modality: Modality = Modality.MAY,
    polarity: Polarity = Polarity.POSITIVE,
) -> LegalProposition:
    return LegalProposition(
        proposition_id=proposition_id,
        status=status,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition=condition,
        procedure=procedure,
        modality=modality,
        legal_action=legal_action,
        operative_verb_lexeme=legal_action,
        legal_object=legal_object,
        legal_effect=legal_effect,
        polarity=polarity,
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=_evidence(proposition_id),
    )


def _contract(proposition: LegalProposition):
    return build_render_contract(proposition)


def _rendered(proposition: LegalProposition) -> str:
    return "\n".join(slot.text for slot in _contract(proposition).slots)


def _soundness(proposition: LegalProposition, draft: str):
    return evaluate_soundness([proposition], [_contract(proposition)], draft)


def _soundness_many(propositions: list[LegalProposition], draft: str):
    return evaluate_soundness(
        propositions,
        [_contract(proposition) for proposition in propositions],
        draft,
    )


def _codes(result) -> set[str]:
    return {violation.code for violation in result.violations}


def _covered(proposition: LegalProposition, draft: str) -> bool:
    return reconcile_render_contracts([_contract(proposition)], draft).covered


@pytest.mark.parametrize(
    "test_name, wrapper",
    [
        ("contradiction_normal_period", "다음 명제는 거짓이다. {slot}"),
        ("contradiction_spaced_period", "다음 명제는 거짓이다 . {slot}"),
        ("contradiction_repeated_period", "다음 명제는 거짓이다.. {slot}"),
        ("contradiction_repeated_exclamation", "다음 명제는 거짓이다!! {slot}"),
        ("contradiction_unicode_ellipsis", "다음 명제는 거짓이다 … {slot}"),
        ("contradiction_unicode_full_stop", "다음 명제는 거짓이다 。 {slot}"),
    ],
    ids=lambda value: value if isinstance(value, str) and value.startswith("contradiction_") else None,
)
def test_contradiction_wrapper_punctuation_is_not_adopted(test_name, wrapper):
    del test_name
    proposition = _proposition()
    contract = _contract(proposition)
    draft = "# 2. 검토결론\n" + wrapper.format(slot=contract.slots[0].text)
    draft += "\n" + contract.slots[1].text

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)


@pytest.mark.parametrize(
    "conclusion",
    [
        "적용된다. 그러나 적용되지 않는다.",
        "적용된다 . 그러나 적용되지 않는다 .",
        "적용된다.. 그러나 적용되지 않는다!!",
        "적용된다 … 그러나 적용되지 않는다.",
        "적용된다 。 그러나 적용되지 않는다 。",
    ],
    ids=[
        "contradiction_normal_boundary",
        "contradiction_spaced_boundary",
        "contradiction_repeated_boundary",
        "contradiction_unicode_ellipsis_boundary",
        "contradiction_unicode_full_stop_boundary",
    ],
)
def test_contradictory_predicates_share_one_boundary_contract(conclusion):
    proposition = _proposition()
    draft = f"# 2. 검토결론\n{conclusion}\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)


@pytest.mark.parametrize(
    "field, claim",
    [
        ("condition", "추가 요건을 충족하고 절차를 거치면 행정청은 대상을 350m로 지정할 수 있다."),
        ("procedure", "요건을 충족하고 별도 절차를 거치면 행정청은 대상을 350m로 지정할 수 있다."),
        ("legal_object", "요건을 충족하고 절차를 거치면 행정청은 다른 대상을 350m로 지정할 수 있다."),
        ("legal_effect", "요건을 충족하고 절차를 거치면 행정청은 대상을 350m 이상으로 지정할 수 있다."),
    ],
    ids=["condition_substituted", "procedure_substituted", "object_substituted", "effect_substituted"],
)
def test_relation_substitution_is_not_proved_by_substring_presence(field, claim):
    proposition = _proposition()
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(item for item in result.violations if item.code == "LEGAL_RELATION_DEGRADATION")
    assert field in violation.relation_fields


@pytest.mark.parametrize(
    "field, claim",
    [
        ("condition", "절차를 거치면 행정청은 대상을 350m로 지정할 수 있다."),
        ("procedure", "요건을 충족하면 행정청은 대상을 350m로 지정할 수 있다."),
        ("legal_object", "요건을 충족하고 절차를 거치면 행정청은 350m로 지정할 수 있다."),
        ("legal_effect", "요건을 충족하고 절차를 거치면 행정청은 대상을 지정할 수 있다."),
    ],
    ids=["condition_omitted", "procedure_omitted", "object_omitted", "effect_omitted"],
)
def test_relation_omission_is_not_proved_by_remaining_fields(field, claim):
    proposition = _proposition()
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(item for item in result.violations if item.code == "LEGAL_RELATION_DEGRADATION")
    assert field in violation.relation_fields


def test_multiple_relation_slots_degraded_fails_closed():
    proposition = _proposition()
    claim = "추가 요건을 충족하고 별도 절차를 거치면 행정청은 다른 대상을 350m 이상으로 지정할 수 있다."
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(item for item in result.violations if item.code == "LEGAL_RELATION_DEGRADATION")
    assert set(violation.relation_fields) >= {"condition", "procedure", "legal_object", "legal_effect"}


@pytest.mark.parametrize(
    "field, value",
    [
        ("condition", "요건"),
        ("procedure", "절차"),
        ("legal_object", "대상"),
        ("legal_effect", "350m"),
    ],
    ids=["condition_preserved", "procedure_preserved", "object_preserved", "effect_preserved"],
)
def test_relation_slot_exact_value_is_preserved(field, value):
    proposition = _proposition()
    assert getattr(proposition, field) == value
    draft = f"# 2. 검토결론\n{_rendered(proposition)}"

    result = _soundness(proposition, draft)

    assert result.soundness_passed is True


def test_unrelated_neighbor_sentence_does_not_borrow_legal_ownership():
    proposition = _proposition()
    unrelated = "요건을 충족하고 절차를 거치면 보고서는 대상을 350m로 표시할 수 있다."
    draft = f"# 2. 검토결론\n{_rendered(proposition)}\n{unrelated}"

    result = _soundness(proposition, draft)

    assert result.soundness_passed is True
    assert result.violations == ()


def test_explicit_legal_predicate_without_owner_keyword_is_bound():
    proposition = _proposition(polarity=Polarity.POSITIVE)
    draft = f"# 2. 검토결론\n그러므로 금지된다.\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)


def test_ambiguous_multi_owner_claim_fails_closed():
    first = _proposition(proposition_id="P1", legal_effect="지위 Z")
    second = _proposition(proposition_id="P2", legal_effect="지위 Y")
    claim = "요건을 충족하고 절차를 거치면 행정청은 대상을 법적 상태로 지정할 수 있다."
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(first)}\n{_rendered(second)}"

    result = _soundness_many([first, second], draft)

    assert result.soundness_passed is False
    assert "AMBIGUOUS_ADOPTED_IDENTITY" in _codes(result)


@pytest.mark.parametrize(
    "predicate",
    ["그러므로 적용되지 않는다.", "그러므로 허용되지 않는다."],
    ids=["open_anaphoric_negative_promotion", "open_anaphoric_negative_permission_promotion"],
)
def test_open_anaphoric_negative_promotion_fails(predicate):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = f"# 2. 검토결론\n{predicate}\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)


def test_open_anaphoric_positive_promotion_fails():
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = f"# 2. 검토결론\n그러므로 허용된다.\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)


@pytest.mark.parametrize(
    "predicate",
    ["따라서 이 행위는 허용된다.", "따라서 이 행위는 허용되지 않는다."],
    ids=["open_explicit_subject_positive_promotion", "open_explicit_subject_negative_promotion"],
)
def test_open_explicit_subject_promotion_fails(predicate):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = f"# 2. 검토결론\n{predicate}\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)


def test_closed_anaphoric_negative_is_valid_for_negative_proposition():
    proposition = _proposition(polarity=Polarity.NEGATIVE)
    draft = f"# 2. 검토결론\n그러므로 적용되지 않는다.\n# 3. 검토이유\n{_rendered(proposition)}"

    assert _covered(proposition, draft) is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is True
    assert result.violations == ()


def test_open_ambiguous_anaphora_fails_closed():
    first = _proposition(proposition_id="P1", status=PropositionStatus.OPEN)
    second = _proposition(proposition_id="P2", status=PropositionStatus.OPEN, condition="다른 요건")
    draft = f"# 2. 검토결론\n그러므로 적용되지 않는다.\n# 3. 검토이유\n{_rendered(first)}\n{_rendered(second)}"

    result = _soundness_many([first, second], draft)

    assert result.soundness_passed is False
    assert "AMBIGUOUS_ADOPTED_IDENTITY" in _codes(result)


@pytest.mark.parametrize(
    "region",
    [
        "> 요건을 충족하고 절차를 거치면 행정청은 대상을 350m로 지정할 수 있다.",
        "```\n요건을 충족하고 절차를 거치면 행정청은 대상을 350m로 지정할 수 있다.\n```",
        "예시:\n요건을 충족하고 절차를 거치면 행정청은 대상을 350m로 지정할 수 있다.",
    ],
    ids=[
        "non_contradiction_inside_rejected_quote",
        "non_contradiction_inside_code",
        "non_contradiction_inside_example",
    ],
)
def test_excluded_regions_do_not_create_claim_ownership(region):
    proposition = _proposition()
    draft = f"# 2. 검토결론\n{region}\n# 3. 검토이유\n{_rendered(proposition)}"

    result = _soundness(proposition, draft)

    assert result.soundness_passed is True
