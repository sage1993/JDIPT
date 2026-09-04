"""Ephemeral PLUGIN_DATA persistence for one JDIPT session and turn."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    PropositionValidationError,
)


STATE_DIRECTORY = "synthesis-runtime"
RUNTIME_STATE_SCHEMA_VERSION = 2
_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


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


def _validate_identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value or not _ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be a safe non-empty identifier")
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
    return asdict(state)


def _from_json(payload: Any, session_id: str, turn_id: str) -> RuntimeTurnState:
    if not isinstance(payload, dict):
        raise RuntimeStateError("runtime state must be a JSON object")
    if payload.get("session_id") != session_id or payload.get("turn_id") != turn_id:
        raise RuntimeStateError("runtime state session/turn mismatch")
    if payload.get("schema_version") != RUNTIME_STATE_SCHEMA_VERSION:
        raise RuntimeStateError("unsupported runtime state schema version")

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
