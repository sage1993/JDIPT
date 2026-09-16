"""Codex Stop-hook adapter for bounded runtime synthesis enforcement."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.synthesis_integrity import reconcile_draft, render_mandatory_proposition_sentence
from scripts.synthesis_runtime_state import (
    RuntimeStateError,
    load_runtime_state,
    update_repair_count,
)


def _fail_closed(system_message: str) -> dict[str, str | bool]:
    return {
        "continue": False,
        "stopReason": "JDIPT synthesis integrity validation failed",
        "systemMessage": system_message,
    }


def _block(reason: str) -> dict[str, str]:
    return {"decision": "block", "reason": reason}


def _failure_reason(state, result) -> str:
    clauses = []
    for proposition, proposition_result in zip(
        (item.to_integrity_proposition() for item in state.propositions),
        result.proposition_results,
        strict=False,
    ):
        if proposition_result.covered:
            continue
        clause = render_mandatory_proposition_sentence(proposition).strip()
        if clause:
            clauses.append(f"{proposition.proposition_id}: {clause}")
    if not clauses:
        clauses.append("확인된 material proposition을 누락 없이 반영해야 한다.")
    return (
        "JDIPT synthesis integrity mismatch. Add each mandatory legal-effect "
        "proposition before optional explanation, then resubmit. "
        + " | ".join(clauses)
    )


def handle_stop_event(
    event: Mapping[str, Any],
    plugin_data: str | None = None,
) -> dict[str, Any]:
    """Return the documented Stop-hook response for one Codex event."""

    if not isinstance(event, Mapping):
        return _fail_closed("JDIPT synthesis validation failed closed; invalid Stop input.")

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
    if state is None or not state.jdipt_active:
        return {}

    draft = event.get("last_assistant_message")
    if not isinstance(draft, str):
        draft = ""
    result = reconcile_draft(
        [proposition.to_integrity_proposition() for proposition in state.propositions],
        draft,
    )
    if result.covered:
        return {}

    # Codex sets stop_hook_active when a prior Stop hook already requested a
    # continuation.  Refuse another continuation even if stale state says 0.
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
    return _block(_failure_reason(state, result))


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
