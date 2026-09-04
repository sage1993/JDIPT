"""Small stdio MCP transport for the JDIPT proposition registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.proposition_registry import register_material_proposition as _register_material_proposition
from scripts.synthesis_runtime_state import RuntimeStateError


TOOL_NAME = "register_material_proposition"
RUNTIME_PLUGIN_DATA_FIELD = "_runtime_plugin_data"
REGISTRY_FIELDS = frozenset(
    {
        "session_id",
        "turn_id",
        "proposition_id",
        "status",
        "materiality",
        "subject",
        "condition",
        "procedure",
        "modality",
        "legal_action",
        "operative_verb_lexeme",
        "legal_object",
        "legal_effect",
        "polarity",
        "relation_type",
        "base_proposition_id",
        "exception_proposition_id",
        "source_id",
        "authority_kind",
        "source_title",
        "source_locator",
        "evidence_span",
        "temporal_status",
        "temporal_render_text",
        RUNTIME_PLUGIN_DATA_FIELD,
    }
)


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": TOOL_NAME,
            "description": (
                "Register one canonical material legal proposition for the current "
                "session and turn. The runtime hook binds authoritative identity "
                "and the registry returns a deterministic render contract."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["session_id", "turn_id", "proposition_id", "status"],
                "properties": {
                    "session_id": {"type": "string"},
                    "turn_id": {"type": "string"},
                    "proposition_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["OPEN", "CLOSED"]},
                    "materiality": {"type": "string"},
                    "subject": {"type": "string"},
                    "condition": {"type": "string"},
                    "procedure": {"type": "string"},
                    "modality": {"type": "string"},
                    "legal_action": {"type": "string"},
                    "operative_verb_lexeme": {"type": "string"},
                    "legal_object": {"type": "string"},
                    "legal_effect": {"type": "string"},
                    "polarity": {"type": "string"},
                    "relation_type": {"type": "string"},
                    "base_proposition_id": {"type": "string"},
                    "exception_proposition_id": {"type": "string"},
                    "source_id": {"type": "string"},
                    "authority_kind": {"type": "string"},
                    "source_title": {"type": "string"},
                    "source_locator": {"type": "string"},
                    "evidence_span": {"type": "string"},
                    "temporal_status": {"type": "string"},
                    "temporal_render_text": {"type": "string"},
                    RUNTIME_PLUGIN_DATA_FIELD: {
                        "type": "string",
                        "description": (
                            "Runtime-injected by JDIPT PreToolUse; model values are "
                            "overwritten."
                        ),
                    },
                },
            },
        }
    ]


def register_material_proposition(
    arguments: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    runtime_plugin_data = plugin_data
    if runtime_plugin_data is None:
        injected = arguments.get(RUNTIME_PLUGIN_DATA_FIELD)
        if not isinstance(injected, str) or not injected:
            raise RuntimeStateError("authoritative plugin data was not injected")
        runtime_plugin_data = injected
    fields = dict(arguments)
    fields.pop(RUNTIME_PLUGIN_DATA_FIELD, None)
    result = _register_material_proposition(fields, runtime_plugin_data)
    return {
        "session_id": result.state.session_id,
        "turn_id": result.state.turn_id,
        "proposition_id": result.proposition.proposition_id,
        "status": result.proposition.status,
        "registry_active": result.state.registry_active,
        "repair_count": result.state.repair_count,
        "render_contract": {
            "proposition_id": result.render_contract.proposition_id,
            "slots": [asdict(slot) for slot in result.render_contract.slots],
        },
    }


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def dispatch_json_rpc(
    request: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(request, Mapping):
        return _error(None, -32600, "Invalid Request")
    request_id = request.get("id")
    method = request.get("method")
    if not isinstance(method, str):
        return _error(request_id, -32600, "Invalid Request")
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jdipt-runtime", "version": "0.2.4"},
            },
        }
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tool_definitions()},
        }
    if method != "tools/call":
        return _error(request_id, -32601, "Method not found")

    params = request.get("params")
    if not isinstance(params, Mapping) or params.get("name") != TOOL_NAME:
        return _error(request_id, -32601, "Tool not found")
    arguments = params.get("arguments", {})
    if not isinstance(arguments, Mapping):
        return _error(request_id, -32602, "Tool arguments must be an object")
    unknown_fields = sorted(set(arguments) - REGISTRY_FIELDS)
    if unknown_fields:
        return _error(
            request_id,
            -32602,
            "Unsupported tool arguments: " + ", ".join(unknown_fields),
        )
    try:
        result = register_material_proposition(arguments, plugin_data)
    except (RuntimeStateError, OSError, TypeError, ValueError) as exc:
        return _error(request_id, -32602, f"Invalid tool arguments: {exc}")
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
            ]
        },
    }


def _configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def serve() -> None:
    _configure_stdio()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = dispatch_json_rpc(request)
        except (UnicodeError, json.JSONDecodeError):
            response = _error(None, -32700, "Parse error")
        if response is not None:
            json.dump(response, sys.stdout, ensure_ascii=True, separators=(",", ":"))
            sys.stdout.write("\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve()
