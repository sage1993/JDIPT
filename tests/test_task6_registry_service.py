from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.proposition_registry import RegistryService
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    record_reconciliation,
    runtime_state_path,
    update_runtime_state,
    update_repair_count,
)


def _fields(**overrides):
    data = {
        "session_id": "session-a",
        "turn_id": "turn-1",
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "MATERIAL",
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
        "temporal_render_text": "현행 기준이다.",
    }
    data.update(overrides)
    return data


def test_registry_service_owns_pending_and_active_transitions(tmp_path):
    service = RegistryService(tmp_path)

    pending = service.begin_pending("session-a", "turn-1")
    assert pending.activation_state == "PENDING"

    result = service.register(_fields(), "session-a", "turn-1")

    assert result.state.activation_state == "ACTIVE"
    assert result.state.registry_completed is True
    assert result.state.registry_invocation_count == 1
    assert load_runtime_state("session-a", "turn-1", tmp_path) == result.state


def test_stale_registry_transition_is_rejected(tmp_path):
    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")
    service.register(_fields(), "session-a", "turn-1")

    with pytest.raises(RuntimeStateError):
        service.mark_enforcement(expected, "REGISTRY_ENFORCEMENT")


def test_registry_transition_cannot_cross_session_or_turn(tmp_path):
    service = RegistryService(tmp_path)
    service.begin_pending("session-a", "turn-1")

    with pytest.raises(RuntimeStateError):
        service.register(_fields(session_id="session-b"), "session-a", "turn-1")

    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "PENDING"
    assert state.propositions == []


def test_registry_lifecycle_writers_are_not_in_persistence_module():
    text = Path("scripts/synthesis_runtime_state.py").read_text(encoding="utf-8")

    assert "def create_pending_runtime_state" not in text
    assert "def update_registry_enforcement_count" not in text
    assert "def record_stop_disposition" not in text


def test_held_registry_lock_fails_closed_without_partial_transition(tmp_path):
    service = RegistryService(tmp_path)
    service.begin_pending("session-a", "turn-1")
    lock_path = runtime_state_path(tmp_path, "session-a", "turn-1").with_suffix(
        ".lock"
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("held", encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        service.register(_fields(), "session-a", "turn-1")

    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "PENDING"
    assert state.registry_completed is False


def test_enforcement_transition_is_single_atomic_state_update(tmp_path):
    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")

    updated = service.mark_enforcement(expected, "REGISTRY_ENFORCEMENT")

    assert updated.registry_enforcement_count == 1
    assert updated.stop_disposition == "REGISTRY_ENFORCEMENT"
    persisted = load_runtime_state("session-a", "turn-1", tmp_path)
    assert persisted == updated


def test_active_completed_state_cannot_be_downgraded_by_pending_activation(tmp_path):
    service = RegistryService(tmp_path)
    service.begin_pending("session-a", "turn-1")
    service.register(_fields(), "session-a", "turn-1")

    state = service.begin_pending("session-a", "turn-1")

    assert state.activation_state == "ACTIVE"
    assert state.registry_completed is True
    assert state.registry_active is True


def test_failed_registration_leaves_no_active_partial_state(tmp_path):
    service = RegistryService(tmp_path)
    service.begin_pending("session-a", "turn-1")

    with pytest.raises((RuntimeStateError, ValueError)):
        service.register(_fields(evidence_span="bad\ud800text"))

    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "PENDING"
    assert state.registry_active is False


def test_stale_repair_snapshot_cannot_overwrite_newer_active_registry(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    service.register(_fields(), "session-a", "turn-1")

    with pytest.raises(RuntimeStateError):
        update_repair_count(pending, 1, tmp_path)

    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "ACTIVE"
    assert state.registry_completed is True
    assert state.repair_count == 0


def test_stale_reconciliation_snapshot_cannot_overwrite_newer_active_registry(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    service.register(_fields(), "session-a", "turn-1")

    with pytest.raises(RuntimeStateError):
        record_reconciliation(
            pending,
            "first",
            SimpleNamespace(missing_slots=[]),
            tmp_path,
        )

    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "ACTIVE"
    assert state.registry_completed is True
    assert state.first_reconciliation is None


def test_inactive_completed_registry_state_is_rejected():
    with pytest.raises(RuntimeStateError):
        RuntimeTurnState(
            schema_version=RUNTIME_STATE_SCHEMA_VERSION,
            session_id="session-a",
            turn_id="turn-1",
            registry_active=False,
            repair_count=0,
            propositions=[],
            activation_state="INACTIVE",
            registry_required=True,
            registry_completed=True,
            registry_invocation_count=1,
        )


def test_missing_state_cannot_be_resurrected_from_stale_snapshot(tmp_path):
    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")
    runtime_state_path(tmp_path, "session-a", "turn-1").unlink()

    with pytest.raises(RuntimeStateError):
        update_repair_count(expected, 1, tmp_path)

    assert load_runtime_state("session-a", "turn-1", tmp_path) is None


def test_persistence_cas_cannot_mutate_registry_lifecycle_or_propositions(tmp_path):
    from dataclasses import replace

    service = RegistryService(tmp_path)
    expected = service.begin_pending("session-a", "turn-1")
    malicious = replace(
        expected,
        registry_active=True,
        activation_state="ACTIVE",
        registry_completed=True,
        registry_invocation_count=1,
    )

    with pytest.raises(RuntimeStateError):
        update_runtime_state(expected, malicious, tmp_path)

    assert load_runtime_state("session-a", "turn-1", tmp_path) == expected


def test_active_registry_state_requires_registry_completion_contract():
    with pytest.raises(RuntimeStateError):
        RuntimeTurnState(
            schema_version=RUNTIME_STATE_SCHEMA_VERSION,
            session_id="session-a",
            turn_id="turn-1",
            registry_active=True,
            repair_count=0,
            propositions=[],
            activation_state="ACTIVE",
            registry_required=False,
            registry_completed=False,
        )
