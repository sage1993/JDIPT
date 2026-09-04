from dataclasses import replace

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract


def _closed_proposition(**overrides):
    values = {
        "proposition_id": "P_EXCEPTION",
        "status": "CLOSED",
        "materiality": "material",
        "subject": "행정청",
        "condition": "거리 350m 요건",
        "procedure": "통합심의",
        "modality": "may",
        "legal_action": "designate",
        "operative_verb_lexeme": "지정",
        "legal_object": "사업대상지",
        "legal_effect": "예외 대상",
        "polarity": "positive",
        "relation_type": "exception",
        "base_proposition_id": None,
        "exception_proposition_id": None,
        "evidence": EvidenceRef(
            source_id="law-001",
            authority_kind="statute",
            source_title="검증 법령",
            source_locator="법령 식별자/조문",
            evidence_span=(
                "거리 350m 요건을 충족하고 통합심의를 거치면 "
                "행정청은 사업대상지를 예외 대상으로 지정할 수 있다."
            ),
            temporal_status="CURRENT_CONFIRMED",
            temporal_render_text="2026-09-04 현재 시행 중인 기준이다.",
        ),
    }
    values.update(overrides)
    return LegalProposition(**values)


def test_fields_from_different_sentences_cannot_satisfy_one_proposition():
    draft = (
        "거리 350m 요건은 별도 쟁점이다. "
        "통합심의 절차도 검토한다. "
        "행정청은 다른 용도지역을 지정할 수 있다. "
        "사업대상지는 다음 항목에서 다룬다. "
        "별도의 예외 대상도 존재한다."
    )

    proposition = _closed_proposition()
    result = reconcile_render_contracts([build_render_contract(proposition)], draft)

    assert not result.covered


def test_unrelated_negation_does_not_flip_a_valid_positive_proposition():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = (
        f"{contract.slots[0].text} {contract.slots[1].text} "
        "다만 다른 인허가 쟁점에서는 허가할 수 없다."
    )

    result = reconcile_render_contracts([contract], draft)

    assert result.covered


def test_one_generic_neutral_phrase_does_not_cover_multiple_open_propositions():
    first = replace(
        _closed_proposition(),
        proposition_id="P_OPEN_1",
        status="OPEN",
        condition="시행일 확인",
        evidence=None,
    )
    second = replace(
        _closed_proposition(),
        proposition_id="P_OPEN_2",
        status="OPEN",
        condition="예외요건 확인",
        evidence=None,
    )

    result = reconcile_render_contracts(
        [build_render_contract(first), build_render_contract(second)],
        "일부 사항은 확인 필요하다.",
    )

    assert not result.covered


def test_current_temporal_status_is_not_satisfied_by_effect_clause_alone():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    result = reconcile_render_contracts([contract], contract.slots[0].text)

    assert not result.covered
