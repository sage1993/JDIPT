from dataclasses import replace

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.proposition_reconciliation import reconcile_render_contracts
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


def test_cross_sentence_token_stitching_is_rejected():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)

    draft = (
        "요건은 별도로 충족한다. "
        "절차도 거친다. "
        "행정청은 다른 항목을 지정할 수 있다. "
        "대상과 법적 효과는 뒤에서 설명한다."
    )

    result = reconcile_render_contracts([contract], draft)

    assert not result.covered
    assert result.missing_slots[0].proposition_id == proposition.proposition_id


def test_unrelated_negation_does_not_affect_present_exact_slots():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = (
        f"{contract.slots[0].text} {contract.slots[1].text} "
        "다만 다른 인허가 쟁점에서는 허가할 수 없다."
    )

    result = reconcile_render_contracts([contract], draft)

    assert result.covered
    assert result.missing_slots == ()


def test_one_generic_neutral_phrase_does_not_cover_two_open_slots():
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
    contracts = [build_render_contract(first), build_render_contract(second)]

    result = reconcile_render_contracts(contracts, "일부 사항은 확인 필요하다.")

    assert not result.covered
    assert [slot.proposition_id for slot in result.missing_slots] == [
        "P_OPEN_1",
        "P_OPEN_2",
    ]


def test_missing_temporal_slot_fails_even_when_effect_slot_is_present():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)

    result = reconcile_render_contracts([contract], contract.slots[0].text)

    assert not result.covered
    assert [slot.kind for slot in result.missing_slots] == ["temporal"]


def test_unrelated_current_token_does_not_satisfy_temporal_slot():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = f"{contract.slots[0].text} 현행 제도에 관한 일반 설명이다."

    result = reconcile_render_contracts([contract], draft)

    assert not result.covered
    assert result.missing_slots[0].kind == "temporal"


def test_markdown_formatting_and_line_wrapping_are_ignored():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = (
        f"- **{contract.slots[0].text}**\n"
        f"- `{contract.slots[1].text}`"
    )

    result = reconcile_render_contracts([contract], draft)

    assert result.covered


def test_reordered_or_reconstructed_tokens_do_not_satisfy_a_slot():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = (
        "행정청은 대상에 법적 지위를 부여할 수 있다. "
        "요건과 절차를 별도로 설명한다. "
        f"{contract.slots[1].text}"
    )

    result = reconcile_render_contracts([contract], draft)

    assert not result.covered
    assert result.missing_slots[0].kind == "effect"
