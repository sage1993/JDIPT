from dataclasses import replace
import json

import pytest

from scripts.synthesis_runtime_state import (
    MaterialProposition,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    register_material_proposition,
    runtime_state_path,
    save_runtime_state,
    update_repair_count,
)


def _proposition(*, proposition_id: str = "P1") -> MaterialProposition:
    return MaterialProposition(
        proposition_id=proposition_id,
        status="CLOSED",
        subject="A",
        condition="C",
        procedure="P",
        operative_verb_lexeme="지정",
        legal_object="O",
        legal_effect="Z",
        source_clause="확인된 원문 문장",
        mandatory_render_clause="C와 P를 충족하면 A는 O를 Z로 지정할 수 있다.",
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        current_status="CURRENT_CONFIRMED",
    )


def _state(*, repair_count: int = 0) -> RuntimeTurnState:
    return RuntimeTurnState(
        session_id="session-a",
        turn_id="turn-1",
        jdipt_active=True,
        repair_count=repair_count,
        propositions=[_proposition()],
    )


def test_round_trip_uses_only_plugin_data_and_exact_session_turn(tmp_path):
    state = _state()

    path = save_runtime_state(state, tmp_path)

    assert path.parent == tmp_path / "synthesis-runtime" / "session-a"
    assert load_runtime_state("session-a", "turn-1", tmp_path) == state
    assert load_runtime_state("session-b", "turn-1", tmp_path) is None
    assert not (tmp_path / "turn-1.json").exists()


def test_runtime_state_path_rejects_path_injection():
    with pytest.raises(ValueError):
        runtime_state_path("plugin-data", "session-a/../outside", "turn-1")
    with pytest.raises(ValueError):
        runtime_state_path("plugin-data", "session-a", "../turn-1")


def test_malformed_state_raises_fail_closed_error(tmp_path):
    path = runtime_state_path(tmp_path, "session-a", "turn-1")
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        load_runtime_state("session-a", "turn-1", tmp_path)


def test_wrong_turn_payload_is_not_reused(tmp_path):
    path = runtime_state_path(tmp_path, "session-a", "turn-1")
    path.parent.mkdir(parents=True)
    payload = json.loads(json.dumps(_state(), default=lambda value: value.__dict__))
    payload["turn_id"] = "turn-old"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        load_runtime_state("session-a", "turn-1", tmp_path)


def test_register_builds_mandatory_clause_deterministically(tmp_path):
    state = register_material_proposition(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "proposition_id": "P1",
            "status": "CLOSED",
            "subject": "A",
            "condition": "C",
            "procedure": "P",
            "operative_verb_lexeme": "지정",
            "legal_object": "O",
            "legal_effect": "Z",
            "source_clause": "확인된 원문 문장",
            "relation_type": "exception",
            "current_status": "CURRENT_CONFIRMED",
        },
        tmp_path,
    )

    proposition = state.propositions[0]
    assert state.jdipt_active is True
    assert proposition.mandatory_render_clause == (
        "다만, 예외로 C을 충족하고 P를 거치면 A는 O를 Z로 지정할 수 있다."
    )
    assert proposition.mandatory_render_clause != "확인된 원문 문장"


def test_register_merges_same_turn_without_cross_session_contamination(tmp_path):
    first = register_material_proposition(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "proposition_id": "P1",
            "status": "CLOSED",
            "subject": "A",
            "condition": "C1",
            "procedure": "P1",
            "operative_verb_lexeme": "승인",
            "legal_object": "O1",
            "legal_effect": "Z1",
            "source_clause": "원문 1",
        },
        tmp_path,
    )
    second = register_material_proposition(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "proposition_id": "P2",
            "status": "OPEN",
            "subject": "A",
            "condition": "C2",
            "procedure": "P2",
            "operative_verb_lexeme": "제외",
            "legal_object": "O2",
            "legal_effect": "Z2",
            "source_clause": "원문 2",
        },
        tmp_path,
    )

    assert len(first.propositions) == 1
    assert [item.proposition_id for item in second.propositions] == [
        item.proposition_id for item in first.propositions
    ] + [second.propositions[-1].proposition_id]
    assert load_runtime_state("session-b", "turn-1", tmp_path) is None


def test_update_repair_count_is_atomic_and_bounded(tmp_path):
    state = _state()
    save_runtime_state(state, tmp_path)

    updated = update_repair_count(state, 1, tmp_path)

    assert updated.repair_count == 1
    assert load_runtime_state("session-a", "turn-1", tmp_path).repair_count == 1
    with pytest.raises(ValueError):
        update_repair_count(updated, 2, tmp_path)


def test_open_proposition_is_preserved_as_open(tmp_path):
    proposition = replace(_proposition(), status="OPEN", mandatory_render_clause=None)
    state = RuntimeTurnState(
        session_id="session-a",
        turn_id="turn-1",
        jdipt_active=False,
        repair_count=0,
        propositions=[proposition],
    )

    path = save_runtime_state(state, tmp_path)
    loaded = load_runtime_state("session-a", "turn-1", tmp_path)

    assert path.is_file()
    assert loaded.propositions[0].status == "OPEN"
    assert loaded.jdipt_active is False


def test_closed_registration_requires_complete_legal_relation(tmp_path):
    with pytest.raises(RuntimeStateError):
        register_material_proposition(
            {
                "session_id": "session-a",
                "turn_id": "turn-1",
                "proposition_id": "P1",
                "status": "CLOSED",
                "subject": "A",
                "condition": "C",
                "procedure": "P",
                "operative_verb_lexeme": "지정",
                "legal_object": "O",
            },
            tmp_path,
        )
