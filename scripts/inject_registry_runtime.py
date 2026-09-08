"""Bind authoritative Codex hook context to JDIPT registry tool calls."""
from __future__ import annotations

from collections.abc import Mapping
import json
import os
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.plugin_runtime_context import (
    is_valid_plugin_data_path,
    resolve_plugin_data,
)

CANONICAL_TOOL_NAME = "mcp__jdipt_runtime__register_material_proposition"
RUNTIME_PLUGIN_DATA_FIELD = "_runtime_plugin_data"


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def handle_pre_tool_use(
    event: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Overwrite model-controlled runtime identity with authoritative hook context."""
    if not isinstance(event, Mapping):
        return _deny("JDIPT registry runtime binding failed; invalid PreToolUse input.")
    if event.get("tool_name") != CANONICAL_TOOL_NAME:
        return {}

    session_id = event.get("session_id")
    turn_id = event.get("turn_id")
    tool_input = event.get("tool_input")
    if not isinstance(session_id, str) or not session_id:
        return _deny("JDIPT registry runtime binding failed; session_id is unavailable.")
    if not isinstance(turn_id, str) or not turn_id:
        return _deny("JDIPT registry runtime binding failed; turn_id is unavailable.")
    if not isinstance(tool_input, Mapping):
        return _deny("JDIPT registry runtime binding failed; tool_input is invalid.")

    root = resolve_plugin_data(plugin_data)
    if root is None:
        return _deny("JDIPT registry runtime binding failed; PLUGIN_DATA is unavailable.")
    if not is_valid_plugin_data_path(root):
        return _deny("JDIPT registry runtime binding failed; PLUGIN_DATA is invalid.")
    root_text = os.fspath(root)

    updated = dict(tool_input)
    updated["session_id"] = session_id
    updated["turn_id"] = turn_id
    updated[RUNTIME_PLUGIN_DATA_FIELD] = root_text
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated,
        }
    }


def _configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def _main() -> int:
    _configure_stdio()
    try:
        event = json.load(sys.stdin)
        response = handle_pre_tool_use(event)
    except (OSError, UnicodeError, json.JSONDecodeError):
        response = _deny("JDIPT registry runtime binding failed; invalid PreToolUse input.")
    json.dump(response, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
