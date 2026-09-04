from dataclasses import replace

from scripts.synthesis_integrity import (
    MaterialProposition,
    reconcile_draft,
    reconcile_proposition,
)


def _closed_proposition(**overrides):
    values = {
        "proposition_id": "P_EXCEPTION",
        "materiality": "material",
        "legal_actor": "행정청",
        "condition": "거리 350m 요건",
        "procedure": "통합심의",
        "modality": "may",
        "legal_action": "designate",
        "legal_object": "사업대상지",
        "resulting_status_or_effect": "예외 대상",
        "polarity": "positive",
        "relation_to_base_or_exception": "exception",
        "source_proposition": (
            "거리 350m 요건을 충족하고 통합심의를 거치면 "
            "행정청은 사업대상지를 예외 대상으로 지정할 수 있다."
        ),
        "evidence_span": (
            "거리 350m 요건을 충족하고 통합심의를 거치면 "
            "행정청은 사업대상지를 예외 대상으로 지정할 수 있다."
        ),
        "closure_status": "CLOSED",
        "operative_verb_lexeme": "지정",
        "temporal_status": "CURRENT_CONFIRMED",
    }
    values.update(overrides)
    return MaterialProposition(**values)


def test_fields_from_different_sentences_cannot_satisfy_one_proposition():
    draft = (
        "거리 350m 요건은 별도 쟁점이다. "
        "통합심의 절차도 검토한다. "
        "행정청은 다른 용도지역을 지정할 수 있다. "
        "사업대상지는 다음 항목에서 다룬다. "
        "별도의 예외 대상도 존재한다."
    )

    result = reconcile_proposition(_closed_proposition(), draft)

    assert not result.covered


def test_unrelated_negation_does_not_flip_a_valid_positive_proposition():
    draft = (
        "거리 350m 요건을 충족하고 통합심의를 거치면 "
        "행정청은 사업대상지를 예외 대상으로 지정할 수 있다. "
        "다만 다른 인허가 쟁점에서는 허가할 수 없다."
    )

    result = reconcile_proposition(_closed_proposition(), draft)

    assert result.covered


def test_one_generic_neutral_phrase_does_not_cover_multiple_open_propositions():
    first = replace(
        _closed_proposition(),
        proposition_id="P_OPEN_1",
        condition="시행일 확인",
        closure_status="OPEN",
    )
    second = replace(
        _closed_proposition(),
        proposition_id="P_OPEN_2",
        condition="예외요건 확인",
        closure_status="OPEN",
    )

    result = reconcile_draft(
        [first, second],
        "일부 사항은 확인 필요하다.",
    )

    assert not result.covered


def test_current_temporal_status_is_not_satisfied_by_effect_clause_alone():
    proposition = _closed_proposition(
        temporal_status="CURRENT_CONFIRMED",
    )
    draft = (
        "거리 350m 요건을 충족하고 통합심의를 거치면 "
        "행정청은 사업대상지를 예외 대상으로 지정할 수 있다."
    )

    result = reconcile_proposition(proposition, draft)

    assert not result.covered
