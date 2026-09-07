"""Ephemeral PLUGIN_DATA persistence for one JDIPT session and turn."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
from typing import Literal

from scripts.legal_proposition import (
    normalize_authority_requirement,
    EvidenceRef,
    LegalProposition,
    normalize_materiality,
    normalize_modality,
    normalize_polarity,
    normalize_status,
    normalize_temporal_requirement,
    PropositionValidationError,
)
from scripts.proposition_obligation_closure import obligation_closure_result_to_dict
from scripts.proposition_source_closure import source_closure_result_to_dict
from scripts.proposition_soundness import soundness_result_to_dict


STATE_DIRECTORY = "synthesis-runtime"
RUNTIME_STATE_SCHEMA_VERSION = 3
_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_REQUIRED_STATE_FIELDS = frozenset(
    {
        "schema_version",
        "session_id",
        "turn_id",
        "registry_active",
        "repair_count",
        "propositions",
        "activation_state",
        "registry_required",
        "registry_completed",
        "registry_required_operations",
        "registry_invocation_count",
        "registry_enforcement_count",
        "first_reconciliation",
        "second_reconciliation",
        "stop_disposition",
    }
)


class RuntimeStateError(ValueError):
    """Raised when runtime state cannot be safely loaded or written."""


@dataclass
class RuntimeTurnState:
    """Canonical proposition ledger for one exact session and turn."""

    schema_version: int
    session_id: str
    turn_id: str
    registry_active: bool
    repair_count: int
    propositions: list[LegalProposition]
    activation_state: Literal["INACTIVE", "PENDING", "ACTIVE"] | None = None
    registry_required: bool = False
    registry_completed: bool = False
    registry_required_operations: tuple[str, ...] = (
        "register_material_proposition",
    )
    registry_invocation_count: int = 0
    registry_enforcement_count: int = 0
    first_reconciliation: dict[str, Any] | None = None
    second_reconciliation: dict[str, Any] | None = None
    stop_disposition: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.session_id, "session_id")
        _validate_identifier(self.turn_id, "turn_id")
        if self.schema_version != RUNTIME_STATE_SCHEMA_VERSION:
            raise RuntimeStateError(
                "unsupported runtime state schema version"
            )
        if not isinstance(self.registry_active, bool):
            raise RuntimeStateError("registry_active must be a boolean")
        if self.repair_count not in {0, 1}:
            raise RuntimeStateError("repair_count must be 0 or 1")
        if self.activation_state is None:
            self.activation_state = "ACTIVE" if self.registry_active else "INACTIVE"
        if self.activation_state not in {"INACTIVE", "PENDING", "ACTIVE"}:
            raise RuntimeStateError("activation_state is invalid")
        if self.activation_state == "PENDING" and self.registry_active:
            raise RuntimeStateError("PENDING runtime state cannot be active")
        if self.activation_state == "ACTIVE" and not self.registry_active:
            raise RuntimeStateError("ACTIVE runtime state must be active")
        if not isinstance(self.registry_required, bool):
            raise RuntimeStateError("registry_required must be a boolean")
        if not isinstance(self.registry_completed, bool):
            raise RuntimeStateError("registry_completed must be a boolean")
        if self.registry_completed and not self.registry_required:
            raise RuntimeStateError("registry_completed requires registry_required")
        if self.activation_state == "PENDING" and not self.registry_required:
            raise RuntimeStateError("PENDING runtime state requires registry_required")
        if self.activation_state == "ACTIVE" and self.registry_required and not self.registry_completed:
            raise RuntimeStateError("ACTIVE runtime state requires registry_completed")
        if not isinstance(self.registry_required_operations, tuple):
            raise RuntimeStateError("registry_required_operations must be a tuple")
        if self.registry_required_operations != ("register_material_proposition",):
            raise RuntimeStateError(
                "registry_required_operations must name the canonical registry operation"
            )
        if (
            not isinstance(self.registry_invocation_count, int)
            or isinstance(self.registry_invocation_count, bool)
            or self.registry_invocation_count < 0
        ):
            raise RuntimeStateError(
                "registry_invocation_count must be a non-negative integer"
            )
        if self.registry_completed and self.registry_invocation_count < 1:
            raise RuntimeStateError(
                "registry_completed requires a persisted registry invocation"
            )
        if (
            not isinstance(self.registry_enforcement_count, int)
            or isinstance(self.registry_enforcement_count, bool)
            or self.registry_enforcement_count not in {0, 1}
        ):
            raise RuntimeStateError("registry_enforcement_count must be 0 or 1")
        if not isinstance(self.propositions, list):
            raise RuntimeStateError("propositions must be a list")
        if any(not isinstance(item, LegalProposition) for item in self.propositions):
            raise RuntimeStateError(
                "propositions must contain LegalProposition instances"
            )
        if len({item.proposition_id for item in self.propositions}) != len(
            self.propositions
        ):
            raise RuntimeStateError("duplicate proposition_id in runtime state")
        for name in ("first_reconciliation", "second_reconciliation"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, dict):
                    raise RuntimeStateError(f"{name} must be an object")
                try:
                    encoded = json.dumps(
                        value,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                except (TypeError, ValueError) as exc:
                    raise RuntimeStateError(f"{name} is not JSON serializable") from exc
                if len(encoded) > 131072:
                    raise RuntimeStateError(f"{name} exceeds the evidence metadata limit")
        if self.stop_disposition is not None:
            _validate_text(self.stop_disposition, "stop_disposition")


def _validate_identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value or not _ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be a safe non-empty identifier")
    return value


def _validate_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise RuntimeStateError(f"{field} must be a string")
    if len(value) > 2048:
        raise RuntimeStateError(f"{field} exceeds the runtime metadata limit")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise RuntimeStateError(f"{field} contains an invalid Unicode surrogate")
    if any(ord(char) < 32 and char not in "\t\r\n" for char in value):
        raise RuntimeStateError(f"{field} contains a control character")
    return value


def _plugin_data_root(plugin_data: str | os.PathLike[str] | None) -> Path:
    value = plugin_data if plugin_data is not None else os.environ.get("PLUGIN_DATA")
    if not value:
        raise RuntimeStateError("PLUGIN_DATA is required for runtime state")
    root = Path(value)
    if root.name in {"", ".", ".."}:
        raise RuntimeStateError("PLUGIN_DATA must be a concrete directory")
    return root


def runtime_state_path(
    plugin_data: str | os.PathLike[str] | None,
    session_id: str,
    turn_id: str,
) -> Path:
    """Return the exact plugin-data path for a session/turn pair."""

    _validate_identifier(session_id, "session_id")
    _validate_identifier(turn_id, "turn_id")
    return _plugin_data_root(plugin_data) / STATE_DIRECTORY / session_id / f"{turn_id}.json"


def _as_json(state: RuntimeTurnState) -> dict[str, Any]:
    try:
        state.__post_init__()
    except (ValueError, RuntimeStateError) as exc:
        raise RuntimeStateError(f"invalid runtime state: {exc}") from exc
    payload = asdict(state)
    for item in payload["propositions"]:
        for field in (
            "status",
            "materiality",
            "modality",
            "polarity",
            "required_authority",
            "required_temporal_status",
        ):
            value = item[field]
            item[field] = None if value is None else value.value
    return payload


def _from_json(payload: Any, session_id: str, turn_id: str) -> RuntimeTurnState:
    if not isinstance(payload, dict):
        raise RuntimeStateError("runtime state must be a JSON object")
    if payload.get("session_id") != session_id or payload.get("turn_id") != turn_id:
        raise RuntimeStateError("runtime state session/turn mismatch")
    if payload.get("schema_version") != RUNTIME_STATE_SCHEMA_VERSION:
        raise RuntimeStateError("unsupported runtime state schema version")
    missing_fields = sorted(_REQUIRED_STATE_FIELDS - set(payload))
    if missing_fields:
        raise RuntimeStateError(
            "runtime state is missing required fields: " + ", ".join(missing_fields)
        )

    raw_propositions = payload.get("propositions")
    if not isinstance(raw_propositions, list):
        raise RuntimeStateError("runtime state propositions must be a list")

    propositions: list[LegalProposition] = []
    try:
        for item in raw_propositions:
            if not isinstance(item, dict):
                raise RuntimeStateError(
                    "runtime state contains a non-object proposition"
                )
            raw_evidence = item.get("evidence")
            evidence = (
                None
                if raw_evidence is None
                else EvidenceRef(**raw_evidence)
            )
            proposition_fields = dict(item)
            proposition_fields["evidence"] = evidence
            proposition_fields["status"] = normalize_status(
                proposition_fields.get("status"),
                required=True,
            )
            proposition_fields["materiality"] = normalize_materiality(
                proposition_fields.get("materiality"),
                required=True,
            )
            proposition_fields["modality"] = normalize_modality(
                proposition_fields.get("modality")
            )
            proposition_fields["polarity"] = normalize_polarity(
                proposition_fields.get("polarity")
            )
            proposition_fields["required_authority"] = normalize_authority_requirement(
                proposition_fields.get("required_authority", "PRIMARY")
            )
            proposition_fields["required_temporal_status"] = normalize_temporal_requirement(
                proposition_fields.get("required_temporal_status", "CURRENT")
            )
            propositions.append(LegalProposition(**proposition_fields))
    except (KeyError, TypeError, ValueError, RuntimeStateError, PropositionValidationError) as exc:
        raise RuntimeStateError(f"invalid proposition metadata: {exc}") from exc

    try:
        return RuntimeTurnState(
            schema_version=payload["schema_version"],
            session_id=session_id,
            turn_id=turn_id,
            registry_active=payload["registry_active"],
            repair_count=payload["repair_count"],
            propositions=propositions,
            activation_state=payload["activation_state"],
            registry_required=payload["registry_required"],
            registry_completed=payload["registry_completed"],
            registry_required_operations=tuple(payload["registry_required_operations"]),
            registry_invocation_count=payload["registry_invocation_count"],
            registry_enforcement_count=payload["registry_enforcement_count"],
            first_reconciliation=payload["first_reconciliation"],
            second_reconciliation=payload["second_reconciliation"],
            stop_disposition=payload["stop_disposition"],
        )
    except (KeyError, TypeError, ValueError, RuntimeStateError) as exc:
        raise RuntimeStateError(f"invalid runtime state: {exc}") from exc


def save_runtime_state(
    state: RuntimeTurnState,
    plugin_data: str | os.PathLike[str] | None = None,
) -> Path:
    """Atomically save state under PLUGIN_DATA and return its path."""

    path = runtime_state_path(plugin_data, state.session_id, state.turn_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.dumps(
            _as_json(state),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise RuntimeStateError(f"could not serialize runtime state: {exc}") from exc

    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{state.turn_id}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except OSError as exc:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise RuntimeStateError(f"could not atomically save runtime state: {exc}") from exc
    return path


def load_runtime_state(
    session_id: str,
    turn_id: str,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState | None:
    """Load only the exact session/turn state; missing state is not an error."""

    path = runtime_state_path(plugin_data, session_id, turn_id)
    try:
        exists = path.exists()
    except OSError as exc:
        raise RuntimeStateError(f"could not inspect runtime state: {exc}") from exc
    if not exists:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeStateError(f"could not read runtime state: {exc}") from exc
    return _from_json(payload, session_id, turn_id)


def update_repair_count(
    state: RuntimeTurnState,
    repair_count: int,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Persist the single permitted transition from zero to one repair."""

    if state.repair_count != 0 or repair_count != 1:
        raise ValueError("repair_count can only transition from 0 to 1")
    updated = replace(state, repair_count=repair_count)
    save_runtime_state(updated, plugin_data)
    return updated


def update_registry_enforcement_count(
    state: RuntimeTurnState,
    enforcement_count: int,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Persist the single permitted registry-enforcement continuation."""

    if (
        not state.registry_required
        or state.registry_completed
        or state.registry_enforcement_count != 0
        or enforcement_count != 1
    ):
        raise ValueError(
            "registry enforcement can only transition from 0 to 1 before completion"
        )
    updated = replace(state, registry_enforcement_count=enforcement_count)
    save_runtime_state(updated, plugin_data)
    return updated


def create_pending_runtime_state(
    session_id: str,
    turn_id: str,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Create the exact-turn pending state at the explicit prompt boundary."""

    existing = load_runtime_state(session_id, turn_id, plugin_data)
    if existing is not None and existing.registry_required and existing.registry_completed:
        return existing
    if existing is not None:
        updated = replace(
            existing,
            registry_active=False,
            activation_state="PENDING",
            registry_required=True,
            registry_completed=False,
            registry_required_operations=("register_material_proposition",),
            registry_enforcement_count=0,
            stop_disposition=None,
        )
        save_runtime_state(updated, plugin_data)
        return updated
    state = RuntimeTurnState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        session_id=session_id,
        turn_id=turn_id,
        registry_active=False,
        repair_count=0,
        propositions=[],
        activation_state="PENDING",
        registry_required=True,
        registry_completed=False,
        registry_required_operations=("register_material_proposition",),
        registry_invocation_count=0,
        registry_enforcement_count=0,
    )
    save_runtime_state(state, plugin_data)
    return state


def _reconciliation_summary(
    result: Any,
    relation_result: Any | None = None,
    soundness_result: Any | None = None,
    source_closure_result: Any | None = None,
    obligation_closure_result: Any | None = None,
) -> dict[str, Any]:
    """Serialize compact reconciliation evidence without copying the draft."""

    slots_missing = [
        {
            "proposition_id": getattr(item, "proposition_id", None),
            "slot_id": getattr(item, "slot_id", None),
            "kind": getattr(item, "kind", None),
        }
        for item in getattr(result, "missing_slots", ())
    ]
    summary: dict[str, Any] = {
        "covered": bool(getattr(result, "covered", False)),
        "missing_slots": slots_missing,
    }
    if relation_result is not None:
        summary["range_exception_relation"] = {
            "relation_id": getattr(relation_result, "relation_id", None),
            "relation_type": getattr(relation_result, "relation_type", None),
            "covered": bool(getattr(relation_result, "covered", False)),
            "missing_fields": list(getattr(relation_result, "missing_fields", ())),
            "source_proposition_ids": list(
                getattr(relation_result, "source_proposition_ids", ())
            ),
            "source_id": getattr(relation_result, "source_id", None),
            "failure_reason": getattr(relation_result, "failure_reason", ""),
        }
    if soundness_result is not None:
        summary["soundness"] = soundness_result_to_dict(soundness_result)
    if source_closure_result is not None:
        summary["source_closure"] = source_closure_result_to_dict(source_closure_result)
    if obligation_closure_result is not None:
        summary["obligation_closure"] = obligation_closure_result_to_dict(
            obligation_closure_result
        )
    summary["overall_covered"] = bool(
        summary["covered"]
        and (
            relation_result is None
            or bool(getattr(relation_result, "covered", False))
        )
    )
    return summary


def record_reconciliation(
    state: RuntimeTurnState,
    phase: Literal["first", "second"],
    result: Any,
    plugin_data: str | os.PathLike[str] | None = None,
    *,
    relation_result: Any | None = None,
    soundness_result: Any | None = None,
    source_closure_result: Any | None = None,
    obligation_closure_result: Any | None = None,
    stop_disposition: str | None = None,
) -> RuntimeTurnState:
    """Persist compact first/second reconciliation and relation evidence."""

    if phase not in {"first", "second"}:
        raise ValueError("phase must be first or second")
    updates: dict[str, Any] = {
        "first_reconciliation" if phase == "first" else "second_reconciliation": _reconciliation_summary(
            result,
            relation_result,
            soundness_result,
            source_closure_result,
            obligation_closure_result,
        )
    }
    if stop_disposition is not None:
        updates["stop_disposition"] = stop_disposition
    updated = replace(state, **updates)
    save_runtime_state(updated, plugin_data)
    return updated


def record_stop_disposition(
    state: RuntimeTurnState,
    disposition: str,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Persist a terminal runtime disposition for acceptance evidence."""

    _validate_text(disposition, "stop_disposition")
    updated = replace(state, stop_disposition=disposition)
    save_runtime_state(updated, plugin_data)
    return updated
