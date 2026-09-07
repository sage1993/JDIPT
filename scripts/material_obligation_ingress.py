"""Trusted issue-mapping ingress for the canonical material-obligation ledger."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
from typing import Any

from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    ObligationValidationError,
)
from scripts.proposition_registry import RegistryService
from scripts.synthesis_runtime_state import RuntimeStateError, RuntimeTurnState


_INGRESS_FIELDS = frozenset(
    {"session_id", "turn_id", "material_obligation_ledger"}
)


def record_material_obligation_ledger(
    event: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Persist one independently produced ledger before proposition registration.

    This is a trusted integration boundary for Legal Issue Mapping / source
    verification. It is intentionally not exposed as a model-facing MCP tool.
    The canonical RegistryService remains the only state writer.
    """

    if not isinstance(event, Mapping):
        raise RuntimeStateError("material-obligation ingress input must be an object")
    unknown = sorted(set(event) - _INGRESS_FIELDS)
    if unknown:
        raise RuntimeStateError(
            "unsupported material-obligation ingress fields: " + ", ".join(unknown)
        )
    session_id = event.get("session_id")
    turn_id = event.get("turn_id")
    if not isinstance(session_id, str) or not session_id:
        raise RuntimeStateError("material-obligation ingress session_id is required")
    if not isinstance(turn_id, str) or not turn_id:
        raise RuntimeStateError("material-obligation ingress turn_id is required")
    raw_ledger = event.get("material_obligation_ledger")
    try:
        ledger = (
            raw_ledger
            if isinstance(raw_ledger, MaterialObligationLedger)
            else MaterialObligationLedger.from_mapping(raw_ledger)
        )
    except (TypeError, ValueError, ObligationValidationError) as exc:
        raise RuntimeStateError(
            f"material-obligation ingress ledger is invalid: {exc}"
        ) from exc

    service = RegistryService(plugin_data)
    state = service.read_state(session_id, turn_id)
    if state is None:
        raise RuntimeStateError(
            "material-obligation ingress requires an exact pending activation"
        )
    if state.activation_state != "PENDING" or not state.material_obligation_ledger_required:
        raise RuntimeStateError(
            "material-obligation ingress requires a pending Task 8 activation"
        )
    return service.record_material_obligation_ledger(state, ledger)
