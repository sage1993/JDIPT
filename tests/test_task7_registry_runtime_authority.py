import json
from pathlib import Path

import pytest

from scripts.proposition_registry import RegistryService
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeStateError,
    RuntimeTurnState,
    runtime_state_path,
    save_runtime_state,
)


def _event(message: str, *, session_id: str = "session-a", turn_id: str = "turn-1"):
    return {
        "session_id": session_id,
        "turn_id": turn_id,
        "last_assistant_message": message,
    }


def _inactive_state(*, session_id: str = "session-a", turn_id: str = "turn-1"):
    return RuntimeTurnState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        session_id=session_id,
        turn_id=turn_id,
        registry_active=False,
        repair_count=0,
        propositions=[],
    )


def test_registry_service_read_state_returns_exact_turn_snapshot(tmp_path):
    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")

    assert service.read_state("session-a", "turn-1") == expected
    assert service.read_state("session-a", "turn-2") is None


def test_stop_gate_uses_registry_service_read_boundary():
    source = Path("scripts/stop_synthesis_gate.py").read_text(encoding="utf-8")

    assert "load_runtime_state" not in source
    assert ".read_state(" in source


def test_stop_gate_calls_registry_service_read_state(monkeypatch, tmp_path):
    calls = []

    def read_state(self, session_id, turn_id):
        calls.append((session_id, turn_id))
        return None

    monkeypatch.setattr(RegistryService, "read_state", read_state)

    assert handle_stop_event(_event("범위만 설명"), tmp_path) == {}
    assert calls == [("session-a", "turn-1")]


def test_missing_registry_does_not_fallback_to_legacy_shadow_state(tmp_path):
    legacy = tmp_path / "legacy-runtime.json"
    legacy.write_text(
        json.dumps({"activation_state": "ACTIVE", "registry_active": True}),
        encoding="utf-8",
    )

    result = handle_stop_event(
        _event("# 1. 질의요지\n# 2. 검토결론\n# 3. 검토이유\n# 4. 관련 법령 및 자료"),
        tmp_path,
    )

    assert result["continue"] is False
    assert "ACTIVATION_BYPASS" in result["systemMessage"]
    assert RegistryService(tmp_path).read_state(
        "session-a", "turn-1"
    ).activation_state == "PENDING"


def test_registry_state_wins_over_shadow_state(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    shadow = tmp_path / "shadow-state.json"
    shadow.write_text(
        json.dumps({"session_id": "session-a", "turn_id": "turn-1", "activation_state": "ACTIVE"}),
        encoding="utf-8",
    )

    assert service.read_state("session-a", "turn-1") == pending
    assert service.read_state("session-a", "turn-1").activation_state == "PENDING"


def test_explicit_registry_location_wins_over_environment_location(
    monkeypatch, tmp_path
):
    registry_root = tmp_path / "registry"
    environment_root = tmp_path / "environment"
    service = RegistryService(registry_root)
    expected = service.begin_pending("session-a", "turn-1")
    monkeypatch.setenv("PLUGIN_DATA", str(environment_root))

    assert service.read_state("session-a", "turn-1") == expected
    assert not runtime_state_path(environment_root, "session-a", "turn-1").exists()


def test_previous_turn_state_is_not_reused(tmp_path):
    service = RegistryService(tmp_path)
    service.begin_pending("session-a", "turn-1")

    assert service.read_state("session-a", "turn-2") is None


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": 3, "session_id": "session-a", "turn_id": "turn-1"},
        {
            "schema_version": 3,
            "session_id": "session-a",
            "turn_id": "turn-1",
            "registry_active": True,
            "activation_state": "ACTIVE",
            "registry_required": True,
            "registry_completed": False,
            "registry_required_operations": ["register_material_proposition"],
            "registry_invocation_count": 1,
            "registry_enforcement_count": 0,
            "repair_count": 0,
            "propositions": [],
            "first_reconciliation": None,
            "second_reconciliation": None,
            "stop_disposition": None,
        },
    ],
)
def test_malformed_registry_state_fails_closed(tmp_path, payload):
    path = runtime_state_path(tmp_path, "session-a", "turn-1")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        RegistryService(tmp_path).read_state("session-a", "turn-1")


def test_reconciliation_uses_registry_propositions_not_shadow_copy(tmp_path):
    service = RegistryService(tmp_path)
    state = service.begin_pending("session-a", "turn-1")
    shadow = tmp_path / "synthesis-propositions.json"
    shadow.write_text(
        json.dumps({"session_id": "session-a", "turn_id": "turn-1", "propositions": [{"proposition_id": "STALE"}]}),
        encoding="utf-8",
    )

    snapshot = service.read_state(state.session_id, state.turn_id)

    assert snapshot is not None
    assert snapshot.propositions == []


def test_derived_diagnostic_artifact_does_not_become_authority(tmp_path):
    service = RegistryService(tmp_path)
    state = service.begin_pending("session-a", "turn-1")
    diagnostic = tmp_path / "diagnostic-snapshot.json"
    diagnostic.write_text(
        json.dumps({"session_id": "session-a", "turn_id": "turn-1", "activation_state": "ACTIVE"}),
        encoding="utf-8",
    )

    assert service.read_state(state.session_id, state.turn_id).activation_state == "PENDING"


def test_stop_gate_rejects_shadow_completion_when_registry_enforcement_is_incomplete(
    tmp_path,
):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    shadow = tmp_path / "legacy-stop-state.json"
    shadow.write_text(
        json.dumps(
            {
                "session_id": "session-a",
                "turn_id": "turn-1",
                "registry_enforcement_count": 1,
                "stop_disposition": "COMPLETED",
            }
        ),
        encoding="utf-8",
    )

    result = handle_stop_event(_event("범위만 설명"), tmp_path)

    assert result["decision"] == "block"
    assert "REGISTRY_ENFORCEMENT" in result["reason"]
    assert service.read_state("session-a", "turn-1").registry_enforcement_count == 1
    assert pending.registry_enforcement_count == 0


def test_stale_source_closure_artifact_cannot_authorize_a_new_registry_turn(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-2")
    stale = tmp_path / "source-closure-turn-1.json"
    stale.write_text(
        json.dumps(
            {
                "session_id": "session-a",
                "turn_id": "turn-1",
                "source_closure_passed": True,
                "authority_closure_passed": True,
                "temporal_closure_passed": True,
            }
        ),
        encoding="utf-8",
    )

    result = handle_stop_event(
        _event("범위만 설명", turn_id="turn-2"),
        tmp_path,
    )

    assert result["decision"] == "block"
    assert "REGISTRY_ENFORCEMENT" in result["reason"]
    stored = service.read_state("session-a", "turn-2")
    assert stored is not None
    assert stored.session_id == pending.session_id
    assert stored.turn_id == pending.turn_id
    assert stored.registry_enforcement_count == 1
