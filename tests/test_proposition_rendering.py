from dataclasses import replace

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.proposition_rendering import build_render_contract


def _evidence():
    return EvidenceRef(
        source_id="law-001",
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/조문",
        evidence_span="확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="2026-09-04 현재 시행 중인 기준이다.",
    )


def _closed_proposition(**overrides):
    values = {
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "material",
        "subject": "행정청",
        "condition": "요건",
        "procedure": "절차",
        "modality": "may",
        "legal_action": "designate",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상",
        "legal_effect": "법적 지위",
        "polarity": "positive",
        "relation_type": "exception",
        "base_proposition_id": None,
        "exception_proposition_id": None,
        "evidence": _evidence(),
    }
    values.update(overrides)
    return LegalProposition(**values)


def test_closed_discretionary_proposition_gets_effect_slot():
    contract = build_render_contract(_closed_proposition())

    assert [slot.kind for slot in contract.slots] == ["effect", "temporal"]
    assert "지정할 수 있다" in contract.slots[0].text


def test_mandatory_modality_is_not_weakened():
    proposition = replace(
        _closed_proposition(),
        modality="must",
        operative_verb_lexeme="실시",
        legal_action="conduct",
    )

    text = build_render_contract(proposition).slots[0].text

    assert "하여야" in text
    assert "할 수 있다" not in text


def test_prohibited_modality_is_not_rendered_as_discretionary():
    proposition = replace(
        _closed_proposition(),
        modality="prohibited",
        operative_verb_lexeme="지정",
        legal_action="designate",
    )

    text = build_render_contract(proposition).slots[0].text

    assert "하여서는 안" in text
    assert "할 수 있다" not in text


def test_current_proposition_requires_exact_temporal_slot():
    contract = build_render_contract(_closed_proposition())

    temporal = [slot for slot in contract.slots if slot.kind == "temporal"]

    assert len(temporal) == 1
    assert "2026-09-04 현재 시행 중인 기준이다." in temporal[0].text


def test_open_propositions_get_distinct_neutral_slots_for_their_context():
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

    first_slot = build_render_contract(first).slots[0]
    second_slot = build_render_contract(second).slots[0]

    assert first_slot.kind == "open"
    assert second_slot.kind == "open"
    assert first_slot.text != second_slot.text
    assert "시행일 확인" in first_slot.text
    assert "예외요건 확인" in second_slot.text
