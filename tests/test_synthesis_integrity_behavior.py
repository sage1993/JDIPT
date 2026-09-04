from dataclasses import replace

import pytest

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import RuntimeTurnState, save_runtime_state


def _evidence(source_id: str = "law-001") -> EvidenceRef:
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/조문",
        evidence_span="확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="2026-09-04 현재 시행 중인 기준이다.",
    )


def designation_fixture() -> LegalProposition:
    return LegalProposition(
        proposition_id="EXCEPTION_X",
        status="CLOSED",
        materiality="material",
        subject="A",
        condition="C",
        procedure="P",
        modality="may",
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="O",
        legal_effect="Z",
        polarity="positive",
        relation_type="exception to BASE_X",
        base_proposition_id="BASE_X",
        exception_proposition_id=None,
        evidence=_evidence(),
    )


def test_closed_designation_contract_is_reconciled_as_effect_and_temporal_slots():
    proposition = designation_fixture()
    contract = build_render_contract(proposition)
    draft = "\n\n".join(slot.text for slot in contract.slots)

    result = reconcile_render_contracts([contract], draft)

    assert result.covered
    assert "C" in contract.slots[0].text
    assert "P" in contract.slots[0].text
    assert "O" in contract.slots[0].text
    assert "지정" in contract.slots[0].text
    assert "Z" in contract.slots[0].text


@pytest.mark.parametrize(
    ("legal_action", "operative_verb_lexeme", "source_action"),
    [
        ("designate", "지정", "지정"),
        ("approve", "승인", "승인"),
        ("exclude", "제외", "제외"),
    ],
)
def test_source_specific_legal_actions_survive_deterministic_rendering(
    legal_action: str,
    operative_verb_lexeme: str,
    source_action: str,
):
    proposition = replace(
        designation_fixture(),
        legal_action=legal_action,
        operative_verb_lexeme=operative_verb_lexeme,
    )

    contract = build_render_contract(proposition)

    assert source_action in contract.slots[0].text
    assert reconcile_render_contracts(
        [contract],
        "\n\n".join(slot.text for slot in contract.slots),
    ).covered


def test_reconciliation_rejects_degraded_closed_relation():
    proposition = designation_fixture()
    contract = build_render_contract(proposition)

    result = reconcile_render_contracts(
        [contract],
        "C를 충족하면 기준이 완화될 수 있다.",
    )

    assert not result.covered
    assert {slot.kind for slot in result.missing_slots} == {"effect", "temporal"}


def test_base_and_exception_get_independent_render_contracts():
    base = LegalProposition(
        proposition_id="BASE_X",
        status="CLOSED",
        materiality="material",
        subject="A",
        condition="기본 요건",
        procedure="기본 절차",
        modality="must",
        legal_action="apply",
        operative_verb_lexeme="적용",
        legal_object="O",
        legal_effect="B",
        polarity="positive",
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id="EXCEPTION_X",
        evidence=_evidence("law-002"),
    )
    exception = designation_fixture()
    contracts = [build_render_contract(base), build_render_contract(exception)]

    assert len(contracts) == 2
    assert "B" in contracts[0].slots[0].text
    assert "적용" in contracts[0].slots[0].text
    assert "C" in contracts[1].slots[0].text
    assert "지정" in contracts[1].slots[0].text


def test_mandatory_effect_slot_precedes_optional_explanatory_text():
    contract = build_render_contract(designation_fixture())
    output = "\n\n".join(slot.text for slot in contract.slots)
    output += "\n\n실무상 범위가 확대될 수 있는지는 별도 검토한다."

    assert output.index("지정") < output.index("범위가 확대")


def test_stop_gate_requests_slots_instead_of_rewriting_the_draft(tmp_path):
    proposition = designation_fixture()
    state = RuntimeTurnState(
        schema_version=2,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=True,
        repair_count=0,
        propositions=[proposition],
    )
    save_runtime_state(state, tmp_path)

    result = handle_stop_event(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "last_assistant_message": "C를 충족하면 기준이 완화될 수 있다.",
        },
        tmp_path,
    )

    assert result["decision"] == "block"
    assert "지정" in result["reason"]
    assert "범위가 확대" not in result["reason"]


def test_open_proposition_cannot_be_promoted_to_confirmed_effect():
    proposition = replace(designation_fixture(), status="OPEN", evidence=None)
    contract = build_render_contract(proposition)

    confirmed = reconcile_render_contracts([contract], contract.slots[0].text.replace("확인 필요: ", ""))
    neutral = reconcile_render_contracts([contract], contract.slots[0].text)

    assert not confirmed.covered
    assert neutral.covered
