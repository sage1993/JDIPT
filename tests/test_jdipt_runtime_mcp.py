import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.jdipt_runtime_mcp import dispatch_json_rpc, tool_definitions


ROOT = Path(__file__).resolve().parents[1]


def _fields() -> dict[str, str]:
    return {
        "session_id": "session-a",
        "turn_id": "turn-1",
        "proposition_id": "P1",
        "status": "CLOSED",
        "subject": "A",
        "condition": "C",
        "procedure": "P",
        "operative_verb_lexeme": "지정",
        "legal_object": "O",
        "legal_effect": "Z",
        "source_clause": "원문",
        "relation_type": "base",
    }


def test_registry_tool_exposes_structure_but_not_free_render_clause():
    definitions = tool_definitions()
    assert [item["name"] for item in definitions] == ["register_material_proposition"]
    properties = definitions[0]["inputSchema"]["properties"]
    assert "mandatory_render_clause" not in properties
    assert "proposition_id" in properties
    assert "status" in properties


def test_tools_call_registers_and_returns_deterministic_clause(tmp_path):
    response = dispatch_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "register_material_proposition",
                "arguments": _fields(),
            },
        },
        tmp_path,
    )

    assert response["id"] == 1
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["jdipt_active"] is True
    assert payload["mandatory_render_clause"].startswith("기본 기준으로")
    assert payload["repair_count"] == 0


def test_initialize_and_tools_list_are_json_rpc_compatible():
    initialized = dispatch_json_rpc(
        {"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {}},
    )
    listed = dispatch_json_rpc(
        {"jsonrpc": "2.0", "id": "list", "method": "tools/list", "params": {}},
    )

    assert initialized["result"]["capabilities"]["tools"] == {}
    assert listed["result"]["tools"][0]["name"] == "register_material_proposition"


def test_unknown_tool_returns_json_rpc_error():
    response = dispatch_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "not-the-registry", "arguments": {}},
        },
    )

    assert response["id"] == 2
    assert response["error"]["code"] == -32601


def test_model_authored_mandatory_clause_is_rejected(tmp_path):
    arguments = _fields()
    arguments["mandatory_render_clause"] = "모델이 임의로 만든 절"

    response = dispatch_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "register_material_proposition", "arguments": arguments},
        },
        tmp_path,
    )

    assert response["error"]["code"] == -32602
    assert "mandatory_render_clause" in response["error"]["message"]


def test_stdio_entrypoint_completes_initialize_when_called_by_path(tmp_path):
    env = os.environ.copy()
    env["PLUGIN_ROOT"] = str(ROOT)
    env["PLUGIN_DATA"] = str(tmp_path)
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "jdipt_runtime_mcp.py")],
        input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n',
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )

    assert process.returncode == 0
    assert json.loads(process.stdout)["result"]["serverInfo"]["name"] == "jdipt-runtime"
