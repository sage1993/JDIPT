import json
from pathlib import Path

import pytest

from scripts.jdipt_activation import handle_user_prompt_submit
from scripts.legal_proposition import CANONICAL_PROPOSITION_FIELDS
from scripts.jdipt_runtime_mcp import PROPOSITION_FIELDS, dispatch_json_rpc, tool_definitions
from scripts.proposition_registry import _TYPED_FIELDS
from scripts.proposition_registry import RegistryService
from scripts.runtime_transaction import load_current_transaction


ROOT = Path(__file__).resolve().parents[1]


def _proposition_schema():
    tool = next(
        item
        for item in tool_definitions()
        if item["name"] == "register_material_proposition"
    )
    return tool["inputSchema"]["properties"]["proposition"]


def test_mcp_and_typed_registry_use_one_proposition_field_contract():
    schema_fields = frozenset(_proposition_schema()["properties"])

    assert schema_fields == PROPOSITION_FIELDS
    assert schema_fields == CANONICAL_PROPOSITION_FIELDS
    assert schema_fields == _TYPED_FIELDS


def test_legacy_native_names_are_not_part_of_the_public_contract():
    schema_fields = frozenset(_proposition_schema()["properties"])
    rejected = {
        "closure_status",
        "direct_source",
        "relation_to_base_or_exception",
        "resulting_status_or_effect",
        "mandatory_render_clause",
    }

    assert schema_fields.isdisjoint(rejected)
    assert PROPOSITION_FIELDS.isdisjoint(rejected)


def test_tool_schema_is_closed_to_unsupported_proposition_fields():
    schema = _proposition_schema()
    assert schema["additionalProperties"] is False
    assert json.dumps(schema, ensure_ascii=False).find("closure_status") == -1


def test_native_skill_schema_names_match_canonical_contract():
    skill_text = (ROOT / "skills" / "law-interpretation-request" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    schema_line = next(
        line
        for line in skill_text.splitlines()
        if line.startswith("- Material Proposition Schema:")
    )

    for field in (
        "status",
        "legal_effect",
        "relation_type",
        "source_id",
        "evidence_span",
    ):
        assert f"`{field}`" in schema_line
    for field in (
        "closure_status",
        "direct_source",
        "relation_to_base_or_exception",
        "resulting_status_or_effect",
    ):
        assert field not in schema_line


def test_dispatch_rejects_failed_native_field_before_handler():
    response = dispatch_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "register_material_proposition",
                "arguments": {
                    "turn_capability": "jtc_test",
                    "proposition": {
                        "proposition_id": "P1",
                        "status": "CLOSED",
                        "materiality": "MATERIAL",
                        "closure_status": "CLOSED",
                    },
                },
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "closure_status" in response["error"]["message"]


def _call(name, arguments, request_id=1):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }


def _payload(response):
    return json.loads(response["result"]["content"][0]["text"])


def _evidence():
    return {
        "source_id": "SRC_FIX4",
        "authority_kind": "guidance",
        "source_title": "Fix4 verified source",
        "source_locator": "SRC_FIX4/article-1",
        "evidence_span": "행정청은 조건 C에서 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다.",
        "temporal_status": "CURRENT_CONFIRMED",
        "temporal_render_text": "현행 기준에 따른다.",
    }


def _ledger(evidence):
    return {
        "obligations": [
            {
                "obligation_id": "O_FIX4",
                "issue_type": "RULE",
                "source_status": "SOURCE_CONFIRMED",
                "evidence_source_ids": [evidence["source_id"]],
                "proposition_ids": ["P_FIX4"],
            }
        ],
        "verified_source_evidence": [evidence],
    }


def _canonical_proposition(evidence):
    return {
        "proposition_id": "P_FIX4",
        "status": "CLOSED",
        "materiality": "MATERIAL",
        "subject": "행정청",
        "condition": "조건 C",
        "procedure": "절차 P",
        "modality": "MAY",
        "legal_action": "지정",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상 O",
        "legal_effect": "지위 Z",
        "polarity": "POSITIVE",
        "relation_type": "base",
        "required_authority": "GUIDANCE",
        "required_temporal_status": "CURRENT",
        **evidence,
    }


def _begin_and_record_ledger(tmp_path):
    handle_user_prompt_submit(
        {"hook_event_name": "UserPromptSubmit", "prompt": "Fix4 native-equivalent"},
        tmp_path,
    )
    begun = dispatch_json_rpc(_call("begin_runtime_turn", {}), tmp_path)
    assert "error" not in begun
    capability = _payload(begun)["turn_capability"]
    evidence = _evidence()
    recorded = dispatch_json_rpc(
        _call(
            "submit_material_obligation_ledger",
            {"turn_capability": capability, "ledger": _ledger(evidence)},
        ),
        tmp_path,
    )
    assert "error" not in recorded
    return capability, evidence


def test_native_equivalent_payload_uses_actual_mcp_handler_and_closes(tmp_path):
    capability, evidence = _begin_and_record_ledger(tmp_path)

    registered = dispatch_json_rpc(
        _call(
            "register_material_proposition",
            {
                "turn_capability": capability,
                "proposition": _canonical_proposition(evidence),
            },
        ),
        tmp_path,
    )
    assert "error" not in registered
    assert _payload(registered)["state"] == "ACTIVE"
    assert _payload(registered)["mandatory_render_clause"]

    finalized = dispatch_json_rpc(
        _call("finalize_runtime_turn", {"turn_capability": capability}),
        tmp_path,
    )
    assert "error" not in finalized
    assert _payload(finalized)["state"] == "CLOSED"


@pytest.mark.parametrize(
    "field",
    [
        "closure_status",
        "direct_source",
        "relation_to_base_or_exception",
        "resulting_status_or_effect",
    ],
)
def test_unsupported_native_field_fails_before_registry_mutation(tmp_path, field):
    capability, evidence = _begin_and_record_ledger(tmp_path)
    proposition = _canonical_proposition(evidence)
    proposition[field] = "legacy"

    response = dispatch_json_rpc(
        _call(
            "register_material_proposition",
            {"turn_capability": capability, "proposition": proposition},
        ),
        tmp_path,
    )

    assert response["error"]["code"] == -32602
    assert "INVALID_TOOL_ARGUMENTS" in response["error"]["message"] or "Unsupported" in response["error"]["message"]
    registry = RegistryService(tmp_path).read_canonical_registry()
    assert registry is not None
    assert registry.propositions == ()
    transaction = load_current_transaction(tmp_path)
    assert transaction is not None
    assert transaction.transaction_state == "LEDGER_RECORDED"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("materiality", None),
        ("status", "NOT_CLOSED"),
        ("modality", "MAYBE"),
    ],
)
def test_malformed_or_missing_proposition_field_fails_closed(tmp_path, field, value):
    capability, evidence = _begin_and_record_ledger(tmp_path)
    proposition = _canonical_proposition(evidence)
    if value is None:
        proposition.pop(field)
    else:
        proposition[field] = value

    response = dispatch_json_rpc(
        _call(
            "register_material_proposition",
            {"turn_capability": capability, "proposition": proposition},
        ),
        tmp_path,
    )

    assert response["error"]["code"] == -32602
    registry = RegistryService(tmp_path).read_canonical_registry()
    assert registry is not None
    assert registry.propositions == ()
