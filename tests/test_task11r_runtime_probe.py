from __future__ import annotations

import json
from pathlib import Path

from scripts.task11r_runtime_probe import (
    capture_context,
    capture_stdin,
    presence_state,
)


def test_presence_state_keeps_absent_empty_and_nonempty_distinct() -> None:
    assert presence_state(None) == "ABSENT"
    assert presence_state("") == "PRESENT_EMPTY"
    assert presence_state("C:/plugin-data") == "PRESENT_NONEMPTY"


def test_capture_context_records_only_named_environment_and_selected_event_fields(
    monkeypatch,
) -> None:
    monkeypatch.delenv("PLUGIN_ROOT", raising=False)
    monkeypatch.setenv("PLUGIN_DATA", "C:/plugin-data")
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__jdipt_runtime__register_material_proposition",
        "session_id": "session-1",
        "turn_id": "turn-1",
        "secret_like_field": "must-not-be-captured",
    }
    record = capture_context("T3", event=event, wrapper_command="cmd /c probe")
    assert record["environment"]["PLUGIN_ROOT"] == {
        "state": "ABSENT",
        "value": None,
    }
    assert record["environment"]["PLUGIN_DATA"] == {
        "state": "PRESENT_NONEMPTY",
        "value": "C:/plugin-data",
    }
    assert record["event"]["hook_event_name"]["value"] == "PreToolUse"
    assert record["event"]["tool_name"]["value"].startswith("mcp__jdipt")
    assert "secret_like_field" not in json.dumps(record)


def test_capture_stdin_records_hash_and_input_contract_without_full_payload(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PLUGIN_ROOT", "C:/plugin-root")
    monkeypatch.setenv("PLUGIN_DATA", "")
    raw = b'{"hook_event_name":"Stop","session_id":"s","turn_id":"t"}'
    record = capture_stdin("T4", raw)
    assert record["stdin"]["received"] is True
    assert record["stdin"]["json_parse_success"] is True
    assert record["environment"]["PLUGIN_DATA"]["state"] == "PRESENT_EMPTY"
    assert "session_id" in record["stdin"]["top_level_keys"]
    assert "hook_event_name" not in record["stdin"]


def test_probe_module_has_no_implicit_full_environment_dump() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "scripts" / "task11r_runtime_probe.py"
    ).read_text(encoding="utf-8")
    assert "os.environ.items()" not in source
    assert "os.environ.copy()" not in source
