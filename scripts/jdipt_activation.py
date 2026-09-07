"""Create an exact-turn pending state for explicit JDIPT invocation."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.proposition_registry import RegistryService
from scripts.material_obligation_ingress import record_material_obligation_ledger
from scripts.synthesis_runtime_state import RuntimeStateError


EXPLICIT_INVOCATION = "$law-interpretation-request"
_EXPLICIT_PROMPT = re.compile(
    rf"(?m)^\s*{re.escape(EXPLICIT_INVOCATION)}(?=\s|$)"
)


def _fail_closed(reason: str) -> dict[str, Any]:
    return {
        "continue": False,
        "stopReason": "JDIPT activation detection failed",
        "systemMessage": reason,
    }


def _prompt_value(event: Mapping[str, Any]) -> str:
    for key in ("prompt", "user_prompt"):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def is_explicit_jdipt_prompt(prompt: str) -> bool:
    return isinstance(prompt, str) and _EXPLICIT_PROMPT.search(prompt) is not None


def handle_user_prompt_submit(
    event: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Create PENDING state only for an explicit exact-turn invocation."""

    if not isinstance(event, Mapping):
        return _fail_closed(
            "JDIPT activation detection failed; invalid prompt input."
        )
    if not is_explicit_jdipt_prompt(_prompt_value(event)):
        return {}

    session_id = event.get("session_id")
    turn_id = event.get("turn_id")
    if not isinstance(session_id, str) or not session_id:
        return _fail_closed(
            "JDIPT activation detection failed; session_id is unavailable."
        )
    if not isinstance(turn_id, str) or not turn_id:
        return _fail_closed(
            "JDIPT activation detection failed; turn_id is unavailable."
        )
    try:
        service = RegistryService(plugin_data)
        service.begin_pending(
            session_id,
            turn_id,
            material_obligations_required=True,
        )
        if "material_obligation_ledger" in event:
            record_material_obligation_ledger(
                {
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "material_obligation_ledger": event.get(
                        "material_obligation_ledger"
                    ),
                },
                plugin_data,
            )
    except (OSError, RuntimeStateError, TypeError, ValueError) as exc:
        return _fail_closed(
            f"JDIPT activation detection failed; state was not persisted: {exc}"
        )
    return {}


def _main() -> int:
    try:
        event = json.load(sys.stdin)
        response = handle_user_prompt_submit(event)
    except (OSError, UnicodeError, json.JSONDecodeError, RuntimeStateError):
        response = _fail_closed(
            "JDIPT activation detection failed; prompt input was invalid."
        )
    json.dump(response, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
