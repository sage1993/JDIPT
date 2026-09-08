from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.inject_registry_runtime import (
    CANONICAL_TOOL_NAME,
    handle_pre_tool_use,
    is_valid_plugin_data_path,
    resolve_plugin_data,
)
from scripts.jdipt_activation import handle_user_prompt_submit
from scripts.jdipt_runtime_mcp import dispatch_json_rpc
from scripts.synthesis_runtime_state import load_runtime_state


ROOT = Path(__file__).resolve().parents[1]


def _event() -> dict[str, object]:
    return {
        "tool_name": CANONICAL_TOOL_NAME,
        "session_id": "session-r2",
        "turn_id": "turn-r2",
        "tool_input": {
            "proposition_id": "P1",
            "status": "CLOSED",
            "materiality": "MATERIAL",
        },
    }


def _tool_call(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "register_material_proposition",
            "arguments": arguments,
        },
    }


def _clear_plugin_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CLAUDE_PLUGIN_ROOT",
        "CLAUDE_PLUGIN_DATA",
        "PLUGIN_ROOT",
        "PLUGIN_DATA",
    ):
        monkeypatch.delenv(name, raising=False)


def test_d01_missing_root_and_data_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_plugin_environment(monkeypatch)

    result = handle_pre_tool_use(_event())

    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_d02_root_only_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(ROOT))

    result = handle_pre_tool_use(_event())

    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_d03_data_only_is_not_a_complete_hook_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))

    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    windows_commands = [
        item["commandWindows"]
        for groups in hooks["hooks"].values()
        for group in groups
        for item in group["hooks"]
    ]
    assert all("CLAUDE_PLUGIN_ROOT" in command for command in windows_commands)


@pytest.mark.parametrize(
    "name",
    ["CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA", "PLUGIN_ROOT", "PLUGIN_DATA"],
)
def test_d04_and_d05_empty_reserved_values_are_not_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    name: str,
) -> None:
    _clear_plugin_environment(monkeypatch)
    if name == "CLAUDE_PLUGIN_ROOT":
        monkeypatch.setenv(name, "")
        monkeypatch.setenv("PLUGIN_ROOT", str(ROOT))
    elif name == "CLAUDE_PLUGIN_DATA":
        monkeypatch.setenv(name, "")
        monkeypatch.setenv("PLUGIN_DATA", str(tmp_path))
    elif name == "PLUGIN_ROOT":
        monkeypatch.setenv(name, "")
    else:
        monkeypatch.setenv(name, "")

    if name in {"CLAUDE_PLUGIN_DATA", "PLUGIN_DATA"}:
        result = handle_pre_tool_use(_event())
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    else:
        assert resolve_plugin_data() is None


def test_d06_valid_data_path_is_accepted(tmp_path: Path) -> None:
    assert is_valid_plugin_data_path(tmp_path)
    assert resolve_plugin_data(tmp_path) == tmp_path


def test_d07_reserved_data_is_consumed_without_bare_variables(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))

    result = handle_pre_tool_use(_event())

    updated = result["hookSpecificOutput"]["updatedInput"]
    assert updated["_runtime_plugin_data"] == str(tmp_path)


def test_d08_bare_data_is_explicit_compatibility_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path))

    result = handle_pre_tool_use(_event())

    updated = result["hookSpecificOutput"]["updatedInput"]
    assert updated["_runtime_plugin_data"] == str(tmp_path)


def test_reserved_data_wins_and_empty_reserved_data_denies_bare_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "")
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path))

    result = handle_pre_tool_use(_event())

    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_d09_invalid_plugin_data_path_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "relative/plugin-data")

    result = handle_pre_tool_use(_event())

    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert not is_valid_plugin_data_path("relative/plugin-data")


def test_d10_valid_bridge_injects_exact_authoritative_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
    event = _event()
    event["tool_input"] = {
        "session_id": "forged",
        "turn_id": "forged",
        "_runtime_plugin_data": "forged",
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "MATERIAL",
    }

    result = handle_pre_tool_use(event)
    updated = result["hookSpecificOutput"]["updatedInput"]

    assert updated["session_id"] == "session-r2"
    assert updated["turn_id"] == "turn-r2"
    assert updated["_runtime_plugin_data"] == str(tmp_path)


def test_pretool_script_bootstraps_package_root_when_run_by_absolute_path(
    tmp_path: Path,
) -> None:
    environment = os.environ.copy()
    environment["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    environment["CLAUDE_PLUGIN_DATA"] = str(tmp_path)
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "inject_registry_runtime.py")],
        input=json.dumps(_event()),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    updated = payload["hookSpecificOutput"]["updatedInput"]
    assert updated["_runtime_plugin_data"] == str(tmp_path)


@pytest.mark.parametrize(
    "arguments",
    [
        {"_runtime_plugin_data": ""},
        {"_runtime_plugin_data": "relative/plugin-data"},
        {},
    ],
)
def test_d11_and_d12_malformed_or_missing_injection_fails_closed(
    arguments: dict[str, object],
) -> None:
    arguments = {
        "session_id": "session-r2",
        "turn_id": "turn-r2",
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "MATERIAL",
        **arguments,
    }

    response = dispatch_json_rpc(_tool_call(arguments))

    assert response["error"]["code"] == -32602
    assert "error" in response


def test_activation_uses_reserved_plugin_data_for_pending_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_plugin_environment(monkeypatch)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))

    result = handle_user_prompt_submit(
        {
            "session_id": "session-r2",
            "turn_id": "turn-r2",
            "prompt": "$law-interpretation-request\n검토",
        }
    )

    assert result == {}
    state = load_runtime_state("session-r2", "turn-r2", tmp_path)
    assert state is not None
    assert state.activation_state == "PENDING"


def test_windows_hook_commands_use_reserved_root_and_no_legacy_root_token() -> None:
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    windows_commands = [
        item["commandWindows"]
        for groups in hooks["hooks"].values()
        for group in groups
        for item in group["hooks"]
    ]

    assert len(windows_commands) == 3
    assert all("${CLAUDE_PLUGIN_ROOT}" in command for command in windows_commands)
    assert all("%PLUGIN_ROOT%" not in command for command in windows_commands)
    assert all('"' not in command for command in windows_commands)
