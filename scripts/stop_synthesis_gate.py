"""Codex Stop-hook adapter for bounded deterministic render-slot enforcement."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract
from scripts.synthesis_runtime_state import (
    RuntimeStateError,
    load_runtime_state,
    update_repair_count,
)


def _fail_closed(system_message: str) -> dict[str, str | bool]:
    return {
        "continue": False,
        "stopReason": "JDIPT synthesis render-slot validation failed",
        "systemMessage": system_message,
    }


def _block(reason: str) -> dict[str, str]:
    return {"decision": "block", "reason": reason}


def _failure_reason(result) -> str:
    grouped: dict[str, list[str]] = {}
    for slot in result.missing_slots:
        grouped.setdefault(slot.proposition_id, []).append(slot.expected_text.strip())
    details = " | ".join(
        f"{proposition_id}: " + " ; ".join(texts)
        for proposition_id, texts in grouped.items()
    )
    if not details:
        details = "material proposition render slots are missing"
    return (
        "JDIPT synthesis mismatch. Insert the missing mandatory legal proposition "
        "render slots without weakening their legal action, modality, temporal "
        "status, or uncertainty. "
        + details
    )


def handle_stop_event(
    event: Mapping[str, Any],
    plugin_data: str | None = None,
) -> dict[str, Any]:
    """Return the documented Stop-hook response for one Codex event."""

    if not isinstance(event, Mapping):
        return _fail_closed(
            "JDIPT synthesis validation failed closed; invalid Stop input."
        )

    session_id = event.get("session_id")
    turn_id = event.get("turn_id")
    if not isinstance(session_id, str) or not isinstance(turn_id, str):
        return {}

    try:
        state = load_runtime_state(session_id, turn_id, plugin_data)
    except (OSError, RuntimeStateError, ValueError):
        return _fail_closed(
            "JDIPT synthesis validation failed closed; runtime state was invalid."
        )
    if state is None or not state.registry_active:
        return {}

    draft = event.get("last_assistant_message")
    if not isinstance(draft, str):
        draft = ""
    contracts = [
        contract
        for proposition in state.propositions
        if (contract := build_render_contract(proposition)).slots
    ]
    result = reconcile_render_contracts(contracts, draft)
    if result.covered:
        return {}

    if state.repair_count != 0 or event.get("stop_hook_active") is True:
        return _fail_closed(
            "JDIPT synthesis validation failed-closed; the bounded repair did not "
            "produce an acceptable final answer."
        )

    try:
        update_repair_count(state, 1, plugin_data)
    except (OSError, RuntimeStateError, ValueError):
        return _fail_closed(
            "JDIPT synthesis validation failed-closed; repair state could not be persisted."
        )
    return _block(_failure_reason(result))


def _main() -> int:
    try:
        event = json.load(sys.stdin)
        response = handle_stop_event(event)
    except (OSError, UnicodeError, json.JSONDecodeError, RuntimeStateError):
        response = _fail_closed(
            "JDIPT synthesis validation failed closed; Stop input was invalid."
        )
    json.dump(response, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
