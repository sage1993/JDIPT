import json
from dataclasses import replace

import pytest

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.synthesis_runtime_state import (
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    runtime_state_path,
    save_runtime_state,
    update_repair_count,
)


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


def _proposition(*, proposition_id: str = "P1") -> LegalProposition:
    return LegalProposition(
        proposition_id=proposition_id,
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
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=_evidence(),
    )


def _state(*, repair_count: int = 0) -> RuntimeTurnState:
    return RuntimeTurnState(
        schema_version=2,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=True,
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


def test_runtime_state_uses_canonical_proposition_type(tmp_path):
    state = _state()

    save_runtime_state(state, tmp_path)
    loaded = load_runtime_state("session-a", "turn-1", tmp_path)

    assert isinstance(loaded.propositions[0], LegalProposition)
    assert loaded.schema_version == 2
    assert loaded.registry_active is True


def test_old_runtime_schema_fails_closed(tmp_path):
    path = runtime_state_path(tmp_path, "session-a", "turn-1")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": "session-a",
                "turn_id": "turn-1",
                "jdipt_active": True,
                "repair_count": 0,
                "propositions": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeStateError):
        load_runtime_state("session-a", "turn-1", tmp_path)


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
    payload = {
        "schema_version": 2,
        "session_id": "session-a",
        "turn_id": "turn-old",
        "registry_active": True,
        "repair_count": 0,
        "propositions": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        load_runtime_state("session-a", "turn-1", tmp_path)


def test_update_repair_count_is_atomic_and_bounded(tmp_path):
    state = _state()
    save_runtime_state(state, tmp_path)

    updated = update_repair_count(state, 1, tmp_path)

    assert updated.repair_count == 1
    assert load_runtime_state("session-a", "turn-1", tmp_path).repair_count == 1
    with pytest.raises(ValueError):
        update_repair_count(updated, 2, tmp_path)


def test_open_proposition_is_preserved_as_open(tmp_path):
    proposition = replace(_proposition(), status="OPEN", evidence=None)
    state = RuntimeTurnState(
        schema_version=2,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=False,
        repair_count=0,
        propositions=[proposition],
    )

    path = save_runtime_state(state, tmp_path)
    loaded = load_runtime_state("session-a", "turn-1", tmp_path)

    assert path.is_file()
    assert loaded.propositions[0].status == "OPEN"
    assert loaded.registry_active is False
