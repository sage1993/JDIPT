import json

import pytest

from scripts.jdipt_activation import handle_user_prompt_submit
from scripts.jdipt_runtime_mcp import dispatch_json_rpc
from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    ObligationSourceStatus,
)
from scripts.proposition_rendering import build_render_contract
from scripts.proposition_registry import RegistryService
from scripts.proposition_relations import (
    build_range_exception_relation,
    render_range_exception_relation,
)
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    runtime_state_path,
    save_runtime_state,
)


def _prompt_event(session_id="session-a", turn_id="turn-1"):
    return {
        "hook_event_name": "UserPromptSubmit",
        "session_id": session_id,
        "turn_id": turn_id,
        "prompt": "$law-interpretation-request\n\n법령 쟁점을 검토해줘.",
    }


def _tool_call(arguments):
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "register_material_proposition",
            "arguments": arguments,
        },
    }


def _registry_fields(tmp_path, *, session_id="session-a", turn_id="turn-1"):
    return {
        "session_id": session_id,
        "turn_id": turn_id,
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "material",
        "subject": "행정청",
        "condition": "요건 C",
        "procedure": "절차 P",
        "modality": "may",
        "legal_action": "designate",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상 O",
        "legal_effect": "지위 Z",
        "polarity": "positive",
        "relation_type": "base",
        "base_proposition_id": None,
        "exception_proposition_id": None,
        "source_id": "law-001",
        "authority_kind": "statute",
        "source_title": "검증 법령",
        "source_locator": "법령 식별자/조문",
        "evidence_span": "행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다.",
        "temporal_status": "CURRENT_CONFIRMED",
        "temporal_render_text": "현행 기준에 따른다.",
        "_runtime_plugin_data": str(tmp_path),
    }


def _record_task8_ledger(tmp_path, *proposition_ids, evidence_spans=None):
    default_evidence_span = "행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다."
    spans = evidence_spans or (default_evidence_span,) * len(proposition_ids)
    assert len(spans) == len(proposition_ids)
    sources = [
        {
            "source_id": f"law-00{index + 1}",
            "authority_kind": "statute",
            "source_title": "검증 법령",
            "source_locator": "법령 식별자/조문",
            "evidence_span": spans[index],
            "temporal_status": "CURRENT_CONFIRMED",
            "temporal_render_text": "현행 기준에 따른다.",
        }
        for index in range(len(proposition_ids))
    ]
    ledger = MaterialObligationLedger.from_mapping(
        {
            "obligations": [
                {
                    "obligation_id": f"O_{index}",
                    "issue_type": "BASE_RULE" if index == 0 else "RANGE_EXCEPTION",
                    "source_status": ObligationSourceStatus.SOURCE_CONFIRMED.value,
                    "evidence_source_ids": [sources[index]["source_id"]],
                    "proposition_ids": [proposition_id],
                }
                for index, proposition_id in enumerate(proposition_ids)
            ],
            "verified_source_evidence": sources,
        }
    )
    service = RegistryService(tmp_path)
    state = service.read_state("session-a", "turn-1")
    assert state is not None
    service.record_material_obligation_ledger(state, ledger)


def _stop_event(message, *, session_id="session-a", turn_id="turn-1", active=False):
    return {
        "hook_event_name": "Stop",
        "session_id": session_id,
        "turn_id": turn_id,
        "stop_hook_active": active,
        "last_assistant_message": message,
    }


def test_explicit_activation_persists_pending_registry_contract(tmp_path):
    assert handle_user_prompt_submit(_prompt_event(), tmp_path) == {}

    state = load_runtime_state("session-a", "turn-1", tmp_path)

    assert state is not None
    assert state.activation_state == "PENDING"
    assert state.registry_required is True
    assert state.registry_completed is False
    assert state.registry_enforcement_count == 0


def test_successful_registry_write_is_the_only_completion_transition(tmp_path):
    handle_user_prompt_submit(_prompt_event(), tmp_path)
    _record_task8_ledger(tmp_path, "P1")

    response = dispatch_json_rpc(
        _tool_call(_registry_fields(tmp_path)),
    )

    assert "error" not in response
    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    assert state.activation_state == "ACTIVE"
    assert state.registry_active is True
    assert state.registry_required is True
    assert state.registry_completed is True
    assert state.registry_invocation_count == 1
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["registry_required"] is True
    assert payload["registry_completed"] is True


def test_missing_new_state_fields_fail_closed_instead_of_defaulting(tmp_path):
    path = runtime_state_path(tmp_path, "session-a", "turn-1")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": RUNTIME_STATE_SCHEMA_VERSION,
                "session_id": "session-a",
                "turn_id": "turn-1",
                "registry_active": True,
                "repair_count": 0,
                "propositions": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeStateError):
        load_runtime_state("session-a", "turn-1", tmp_path)


def test_registry_enforcement_is_exactly_one_and_separate_from_repair(tmp_path):
    state = RuntimeTurnState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=False,
        repair_count=0,
        propositions=[],
        activation_state="PENDING",
        registry_required=True,
        registry_completed=False,
        registry_enforcement_count=0,
    )
    save_runtime_state(state, tmp_path)

    first = handle_stop_event(
        _stop_event(
            "# 1. 질의요지\n# 2. 검토결론\n# 3. 검토이유\n# 4. 관련 법령 및 자료"
        ),
        tmp_path,
    )
    second = handle_stop_event(
        _stop_event(
            "# 1. 질의요지\n# 2. 검토결론\n# 3. 검토이유\n# 4. 관련 법령 및 자료",
            active=True,
        ),
        tmp_path,
    )

    assert first["decision"] == "block"
    assert "REGISTRY_ENFORCEMENT" in first["reason"]
    assert second["continue"] is False
    persisted = load_runtime_state("session-a", "turn-1", tmp_path)
    assert persisted is not None
    assert persisted.registry_enforcement_count == 1
    assert persisted.repair_count == 0


def test_completed_registry_does_not_increment_registry_enforcement(tmp_path):
    handle_user_prompt_submit(_prompt_event(), tmp_path)
    _record_task8_ledger(tmp_path, "P1")
    dispatch_json_rpc(_tool_call(_registry_fields(tmp_path)))
    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "요건 C를 충족하고 절차 P를 거치면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
            *(slot.text for slot in build_render_contract(state.propositions[0]).slots),
            "근거: law-001 검증 법령 법령 식별자/조문",
        )
    )

    result = handle_stop_event(
        _stop_event(draft),
        tmp_path,
    )

    assert result == {}
    persisted = load_runtime_state("session-a", "turn-1", tmp_path)
    assert persisted is not None
    assert persisted.registry_completed is True
    assert persisted.registry_enforcement_count == 0


def test_completion_is_isolated_by_exact_session_and_turn(tmp_path):
    handle_user_prompt_submit(_prompt_event("session-a", "turn-a"), tmp_path)
    handle_user_prompt_submit(_prompt_event("session-a", "turn-b"), tmp_path)
    state_a = RegistryService(tmp_path).read_state("session-a", "turn-a")
    assert state_a is not None
    service = RegistryService(tmp_path)
    service.record_material_obligation_ledger(
        state_a,
        MaterialObligationLedger.from_mapping(
            {
                "obligations": [
                    {
                        "obligation_id": "O_BASE",
                        "issue_type": "BASE_RULE",
                        "source_status": "SOURCE_CONFIRMED",
                        "evidence_source_ids": ["law-001"],
                        "proposition_ids": ["P1"],
                    }
                ],
                "verified_source_evidence": [
                    {
                        "source_id": "law-001",
                        "authority_kind": "statute",
                        "source_title": "검증 법령",
                        "source_locator": "법령 식별자/조문",
                        "evidence_span": "행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다.",
                        "temporal_status": "CURRENT_CONFIRMED",
                        "temporal_render_text": "현행 기준에 따른다.",
                    }
                ],
            }
        ),
    )
    dispatch_json_rpc(
        _tool_call(_registry_fields(tmp_path, session_id="session-a", turn_id="turn-a"))
    )

    result = handle_stop_event(
        _stop_event(
            "# 1. 질의요지\n# 2. 검토결론\n# 3. 검토이유\n# 4. 관련 법령 및 자료",
            turn_id="turn-b",
        ),
        tmp_path,
    )

    assert result["decision"] == "block"
    state_a = load_runtime_state("session-a", "turn-a", tmp_path)
    state_b = load_runtime_state("session-a", "turn-b", tmp_path)
    assert state_a is not None and state_a.registry_completed is True
    assert state_b is not None and state_b.registry_completed is False


def test_canonical_registry_to_stop_preserves_relation_and_final_evidence(tmp_path):
    handle_user_prompt_submit(_prompt_event(), tmp_path)
    _record_task8_ledger(
        tmp_path,
        "BASE_RANGE",
        "EXCEPTION_RANGE",
        evidence_spans=(
            "행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다.",
            "행정청은 특정 입지 요건을 충족하는 경우 통합심의를 거치면 사업대상지를 예외 대상 지정할 수 있다.",
        ),
    )
    base = _registry_fields(tmp_path)
    base.update(
        {
            "proposition_id": "BASE_RANGE",
            "relation_type": "base",
            "exception_proposition_id": "EXCEPTION_RANGE",
            "base_rule": "승강장 경계로부터 100m 이내",
            "exception_rule": None,
        }
    )
    exception = _registry_fields(tmp_path)
    exception.update(
        {
            "proposition_id": "EXCEPTION_RANGE",
            "relation_type": "exception to BASE_RANGE",
            "base_proposition_id": "BASE_RANGE",
            "base_rule": "승강장 경계로부터 100m 이내",
            "exception_rule": "승강장 경계로부터 150m 이내",
            "source_id": "law-002",
            "condition": "특정 입지 요건을 충족하는 경우",
            "procedure": "통합심의를 거치면",
            "legal_object": "사업대상지",
            "legal_effect": "예외 대상 지정",
            "operative_verb_lexeme": "지정",
            "evidence_span": "행정청은 특정 입지 요건을 충족하는 경우 통합심의를 거치면 사업대상지를 예외 대상 지정할 수 있다.",
        }
    )
    dispatch_json_rpc(_tool_call(base))
    dispatch_json_rpc(_tool_call(exception))

    state = load_runtime_state("session-a", "turn-1", tmp_path)
    assert state is not None
    relation = build_range_exception_relation(state.propositions)
    assert relation is not None
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "요건 C를 충족하고 절차 P를 거치면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
            "예외: 특정 입지 요건을 충족하는 경우 통합심의를 거치면 행정청은 사업대상지를 예외 대상 지정할 수 있다.",
            *(slot.text for proposition in state.propositions for slot in build_render_contract(proposition).slots),
            render_range_exception_relation(relation),
            "근거: law-001 law-002 검증 법령 법령 식별자/조문",
        )
    )

    result = handle_stop_event(_stop_event(draft), tmp_path)

    assert result == {}
    persisted = load_runtime_state("session-a", "turn-1", tmp_path)
    assert persisted is not None
    assert persisted.registry_required is True
    assert persisted.registry_completed is True
    assert persisted.registry_invocation_count == 2
    assert persisted.registry_enforcement_count == 0
    assert persisted.first_reconciliation is not None
    relation_evidence = persisted.first_reconciliation["range_exception_relation"]
    assert relation_evidence["covered"] is True
    assert relation_evidence["source_proposition_ids"] == [
        "BASE_RANGE",
        "EXCEPTION_RANGE",
    ]
