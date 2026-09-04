import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.inject_registry_runtime import CANONICAL_TOOL_NAME, handle_pre_tool_use
from scripts.jdipt_runtime_mcp import dispatch_json_rpc
from scripts.synthesis_runtime_state import load_runtime_state, runtime_state_path


ROOT = Path(__file__).resolve().parents[1]


def _arguments(**overrides):
    data = {
        "session_id": "current",
        "turn_id": "current",
        "proposition_id": "P1",
        "status": "CLOSED",
        "subject": "행정청",
        "condition": "요건 C",
        "procedure": "절차 P",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상 O",
        "legal_effect": "지위 Z",
        "relation_type": "base",
        "modality": "may",
        "polarity": "positive",
        "source_id": "law-001",
        "authority_kind": "statute",
        "source_title": "검증 법령",
        "source_locator": "법령 식별자/조문",
        "evidence_span": "확인된 원문",
        "temporal_status": "CURRENT_CONFIRMED",
        "temporal_render_text": "2026-09-04 현재 시행 중인 기준이다.",
    }
    data.update(overrides)
    return data


def _event(arguments):
    return {
        "tool_name": CANONICAL_TOOL_NAME,
        "session_id": "actual-session",
        "turn_id": "actual-turn",
        "tool_input": arguments,
    }


def _tool_call(arguments, request_id=1):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": "register_material_proposition",
            "arguments": arguments,
        },
    }


def test_pretool_overwrites_model_identity_and_injects_authoritative_plugin_data(tmp_path):
    result = handle_pre_tool_use(_event(_arguments()), tmp_path)
    updated = result["hookSpecificOutput"]["updatedInput"]

    assert updated["session_id"] == "actual-session"
    assert updated["turn_id"] == "actual-turn"
    assert updated["_runtime_plugin_data"] == str(tmp_path)


def test_bridge_and_mcp_write_exact_stop_hook_state(tmp_path):
    hook_output = handle_pre_tool_use(_event(_arguments()), tmp_path)
    updated = hook_output["hookSpecificOutput"]["updatedInput"]

    response = dispatch_json_rpc(_tool_call(updated))

    assert "error" not in response
    state = load_runtime_state("actual-session", "actual-turn", tmp_path)
    assert state is not None and state.registry_active is True
    assert not runtime_state_path(tmp_path, "current", "current").exists()


def test_missing_plugin_data_denies_registry_call(monkeypatch):
    monkeypatch.delenv("PLUGIN_DATA", raising=False)

    result = handle_pre_tool_use(_event(_arguments()))

    output = result["hookSpecificOutput"]
    assert output["permissionDecision"] == "deny"
    assert "PLUGIN_DATA" in output["permissionDecisionReason"]


def test_mandatory_modality_is_not_weakened_to_discretion(tmp_path):
    args = _arguments(
        modality="mandatory",
        operative_verb_lexeme="shall hold",
        legal_action="hold a hearing",
    )
    hook_output = handle_pre_tool_use(_event(args), tmp_path)
    updated = hook_output["hookSpecificOutput"]["updatedInput"]

    response = dispatch_json_rpc(_tool_call(updated, request_id=2))

    payload = json.loads(response["result"]["content"][0]["text"])
    clause = payload["render_contract"]["slots"][0]["text"]
    assert "할 수 있다" not in clause
    assert "의무적" in clause and "하여야" in clause
    assert "shall hold" in clause


def test_surrogate_is_rejected_before_state_write(tmp_path):
    args = _arguments(condition="bad\ud800text")
    hook_output = handle_pre_tool_use(_event(args), tmp_path)
    updated = hook_output["hookSpecificOutput"]["updatedInput"]

    response = dispatch_json_rpc(_tool_call(updated, request_id=3))

    assert response["error"]["code"] == -32602
    assert "surrogate" in response["error"]["message"]
    path = runtime_state_path(tmp_path, "actual-session", "actual-turn")
    assert not path.exists()


def test_stdio_forces_utf8_even_if_pythonioencoding_is_cp949(tmp_path):
    args = _arguments(
        session_id="actual-session",
        turn_id="actual-turn",
        _runtime_plugin_data=str(tmp_path),
    )
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp949"

    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "jdipt_runtime_mcp.py")],
        input=json.dumps(_tool_call(args, request_id=4), ensure_ascii=False) + "\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )

    assert process.returncode == 0
    response = json.loads(process.stdout)
    payload = json.loads(response["result"]["content"][0]["text"])
    assert "지정" in payload["render_contract"]["slots"][0]["text"]


def test_packaging_wires_exact_registry_pretool_hook_and_no_mcp_env_dependency():
    hooks = json.loads(
        (ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8")
    )
    pretool = hooks["hooks"]["PreToolUse"]
    assert pretool[0]["matcher"] == (
        "^mcp__jdipt_runtime__register_material_proposition$"
    )
    assert "inject_registry_runtime.py" in pretool[0]["hooks"][0]["command"]

    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["jdipt_runtime"]
    assert "env_vars" not in server
