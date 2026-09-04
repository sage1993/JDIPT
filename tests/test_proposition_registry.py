import pytest

from scripts.legal_proposition import PropositionValidationError
from scripts.proposition_registry import register_material_proposition
from scripts.synthesis_runtime_state import (
    RuntimeStateError,
    load_runtime_state,
)


def _closed_fields(**overrides):
    data = {
        "session_id": "session-a",
        "turn_id": "turn-1",
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "material",
        "subject": "행정청",
        "condition": "요건 C",
        "procedure": "절차 P",
        "modality": "may",
        "legal_action": "designate",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상 O",
        "legal_effect": "지위 Z",
        "polarity": "positive",
        "relation_type": "base",
        "base_proposition_id": None,
        "exception_proposition_id": None,
        "source_id": "law-001",
        "authority_kind": "statute",
        "source_title": "검증 법령",
        "source_locator": "법령 식별자/조문",
        "evidence_span": "확인된 원문",
        "temporal_status": "CURRENT_CONFIRMED",
        "temporal_render_text": "2026-09-04 현재 시행 중인 기준이다.",
    }
    data.update(overrides)
    return data


def test_closed_registration_requires_source_id():
    fields = _closed_fields(source_id=None)

    with pytest.raises((PropositionValidationError, RuntimeStateError, ValueError)):
        register_material_proposition(fields)


def test_closed_registration_requires_evidence_span():
    fields = _closed_fields(evidence_span=None)

    with pytest.raises((PropositionValidationError, RuntimeStateError, ValueError)):
        register_material_proposition(fields)


def test_closed_registration_requires_temporal_status():
    fields = _closed_fields(temporal_status=None)

    with pytest.raises((PropositionValidationError, RuntimeStateError, ValueError)):
        register_material_proposition(fields)


def test_unknown_argument_is_rejected():
    fields = _closed_fields(unknown_argument="not allowed")

    with pytest.raises((PropositionValidationError, RuntimeStateError, ValueError)):
        register_material_proposition(fields)


def test_surrogate_is_rejected_before_state_write(tmp_path):
    fields = _closed_fields(condition="bad\ud800text")

    with pytest.raises((PropositionValidationError, RuntimeStateError, ValueError)):
        register_material_proposition(fields, tmp_path)

    assert load_runtime_state("session-a", "turn-1", tmp_path) is None


def test_same_proposition_id_replaces_exact_turn_entry(tmp_path):
    first = register_material_proposition(_closed_fields(), tmp_path)
    second = register_material_proposition(
        _closed_fields(condition="요건 변경"),
        tmp_path,
    )

    assert len(first.state.propositions) == 1
    assert len(second.state.propositions) == 1
    assert second.state.propositions[0].condition == "요건 변경"


def test_different_proposition_id_appends_in_same_turn(tmp_path):
    first = register_material_proposition(_closed_fields(), tmp_path)
    second = register_material_proposition(
        _closed_fields(proposition_id="P2", condition="요건 2"),
        tmp_path,
    )

    assert [item.proposition_id for item in second.state.propositions] == [
        "P1",
        "P2",
    ]
    assert len(first.state.propositions) == 1


def test_cross_session_state_is_not_reused(tmp_path):
    register_material_proposition(_closed_fields(), tmp_path)
    result = register_material_proposition(
        _closed_fields(session_id="session-b"),
        tmp_path,
    )

    assert result.state.session_id == "session-b"
    assert [item.proposition_id for item in result.state.propositions] == ["P1"]


def test_registry_returns_canonical_proposition_and_derived_contract(tmp_path):
    result = register_material_proposition(_closed_fields(), tmp_path)

    assert result.state.registry_active is True
    assert result.proposition is result.state.propositions[0]
    assert result.render_contract.proposition_id == "P1"
    assert [slot.kind for slot in result.render_contract.slots] == [
        "effect",
        "temporal",
    ]
    assert all(slot.proposition_id == "P1" for slot in result.render_contract.slots)


def test_caller_cannot_supply_a_final_render_slot(tmp_path):
    fields = _closed_fields(mandatory_render_clause="모델이 임의로 만든 절")

    with pytest.raises((PropositionValidationError, RuntimeStateError, ValueError)):
        register_material_proposition(fields, tmp_path)

    assert load_runtime_state("session-a", "turn-1", tmp_path) is None
