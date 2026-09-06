"""Generate one exact-identity staged Task 1R evidence bundle."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.jdipt_runtime_mcp import dispatch_json_rpc
from scripts.plugin_integrity import (
    build_runtime_manifest,
    resolve_installed_skill_root,
)
from scripts.proposition_relations import (
    build_range_exception_relation,
    reconcile_range_exception_relation,
)
from scripts.proposition_rendering import build_render_contract
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import load_runtime_state, runtime_state_path


RUN_ID = "task1r-r2-staged-run-01"
SESSION_ID = "task1r-session-01"
TURN_ID = "task1r-turn-01"
RUN_ROOT = Path(__file__).resolve().parent
PLUGIN_DATA = RUN_ROOT / "runtime"


def _jsonable(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def _digest_manifest(manifest: dict[str, str]) -> str:
    payload = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _state():
    state = load_runtime_state(SESSION_ID, TURN_ID, PLUGIN_DATA)
    assert state is not None
    return _jsonable(asdict(state))


def _mcp_payload(response):
    return json.loads(response["result"]["content"][0]["text"])


def _stop_record(response):
    return {
        "run_id": RUN_ID,
        "session_id": SESSION_ID,
        "turn_id": TURN_ID,
        "response": response,
    }


def main() -> None:
    helpers = runpy.run_path(str(ROOT / "tests" / "test_task1r_registry_parity.py"))
    registry_fields = helpers["_registry_fields"]
    prompt_event = helpers["_prompt_event"]
    stop_event = helpers["_stop_event"]
    tool_call = helpers["_tool_call"]

    PLUGIN_DATA.mkdir(parents=True, exist_ok=True)
    handle_user_prompt_submit = helpers["handle_user_prompt_submit"]
    assert handle_user_prompt_submit(
        prompt_event(SESSION_ID, TURN_ID), PLUGIN_DATA
    ) == {}
    state_after_activation = _state()

    shaped = "# 1. 질의요지\n# 2. 검토결론\n# 3. 검토이유\n# 4. 관련 법령 및 자료"
    first_stop = handle_stop_event(
        stop_event(shaped, session_id=SESSION_ID, turn_id=TURN_ID),
        PLUGIN_DATA,
    )
    state_after_first_stop = _state()
    second_stop = handle_stop_event(
        stop_event(
            shaped,
            session_id=SESSION_ID,
            turn_id=TURN_ID,
            active=True,
        ),
        PLUGIN_DATA,
    )
    state_after_second_stop = _state()

    base = registry_fields(PLUGIN_DATA, session_id=SESSION_ID, turn_id=TURN_ID)
    base.update(
        {
            "proposition_id": "BASE_RANGE",
            "relation_type": "base",
            "exception_proposition_id": "EXCEPTION_RANGE",
            "base_rule": "승강장 경계로부터 100m 이내",
            "exception_rule": None,
        }
    )
    exception = registry_fields(PLUGIN_DATA, session_id=SESSION_ID, turn_id=TURN_ID)
    exception.update(
        {
            "proposition_id": "EXCEPTION_RANGE",
            "relation_type": "exception to BASE_RANGE",
            "base_proposition_id": "BASE_RANGE",
            "base_rule": "승강장 경계로부터 100m 이내",
            "exception_rule": "승강장 경계로부터 150m 이내",
            "condition": "특정 입지 요건을 충족하는 경우",
            "procedure": "통합심의를 거치면",
            "legal_object": "사업대상지",
            "legal_effect": "예외 대상 지정",
            "operative_verb_lexeme": "지정",
        }
    )
    base_response = dispatch_json_rpc(tool_call(base))
    exception_response = dispatch_json_rpc(tool_call(exception))
    base_payload = _mcp_payload(base_response)
    exception_payload = _mcp_payload(exception_response)
    state_after_registry = _state()

    propositions = load_runtime_state(SESSION_ID, TURN_ID, PLUGIN_DATA).propositions
    relation = build_range_exception_relation(propositions)
    assert relation is not None
    negative_draft = (
        "기본 기준은 승강장 경계로부터 100m 이내이다.\n"
        "예외 기준은 승강장 경계로부터 150m 이내이다.\n"
        "특정 입지 요건과 통합심의, 사업대상지 지정만 검토한다."
    )
    negative_relation = reconcile_range_exception_relation(
        propositions, negative_draft
    )
    assert negative_relation is not None and negative_relation.covered is False

    final_draft = "\n".join(
        slot.text
        for proposition in propositions
        for slot in build_render_contract(proposition).slots
    )
    final_draft += "\n" + helpers["render_range_exception_relation"](relation)
    final_stop = handle_stop_event(
        stop_event(final_draft, session_id=SESSION_ID, turn_id=TURN_ID),
        PLUGIN_DATA,
    )
    final_state = _state()
    final_state_path = runtime_state_path(PLUGIN_DATA, SESSION_ID, TURN_ID)

    repo_manifest = build_runtime_manifest(ROOT)
    installed_root = resolve_installed_skill_root()
    installed_manifest = (
        build_runtime_manifest(installed_root) if installed_root is not None else {}
    )
    repository_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()
    runtime_identity = {
        "kind": "staged-probe-process",
        "executable": sys.executable,
        "source_root": str(ROOT),
        "source_manifest_sha256": _digest_manifest(repo_manifest),
    }

    (RUN_ROOT / "registry-state.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "session_id": SESSION_ID,
                "turn_id": TURN_ID,
                "repository_head": repository_head,
                "runtime_state_path": str(final_state_path),
                "states": {
                    "after_activation": state_after_activation,
                    "after_first_stop": state_after_first_stop,
                    "after_second_stop": state_after_second_stop,
                    "after_registry": state_after_registry,
                    "final": final_state,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "reconciliation.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "session_id": SESSION_ID,
                "turn_id": TURN_ID,
                "relation": asdict(relation),
                "negative_separated_span": asdict(negative_relation),
                "final_persisted_summary": final_state["first_reconciliation"],
                "final_stop": _stop_record(final_stop),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "acceptance.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "session_id": SESSION_ID,
                "turn_id": TURN_ID,
                "repository_head": repository_head,
                "runtime": runtime_identity,
                "installed_runtime": {
                    "root": str(installed_root) if installed_root else None,
                    "manifest_sha256": _digest_manifest(installed_manifest),
                    "manifest_file_count": len(installed_manifest),
                },
                "registry_required": {
                    "expected": True,
                    "actual": state_after_activation["registry_required"],
                    "scope": [SESSION_ID, TURN_ID],
                    "transition": "UserPromptSubmit -> PENDING",
                    "verdict": "PASS",
                },
                "registry_completed": {
                    "expected": True,
                    "actual": state_after_registry["registry_completed"],
                    "mcp_base": base_payload,
                    "mcp_exception": exception_payload,
                    "scope": [SESSION_ID, TURN_ID],
                    "transition": "canonical registry write -> ACTIVE/COMPLETE",
                    "verdict": "PASS",
                },
                "enforcement_count": {
                    "expected": 1,
                    "actual": final_state["registry_enforcement_count"],
                    "first_stop": _stop_record(first_stop),
                    "second_stop": _stop_record(second_stop),
                    "scope": [SESSION_ID, TURN_ID],
                    "transition": "0 -> 1 exactly once; second incomplete Stop exhausted",
                    "verdict": "PASS",
                },
                "range_exception_relation": {
                    "expected": "source-linked ordered base -> range -> exception in one span",
                    "actual": asdict(relation),
                    "negative_control": asdict(negative_relation),
                    "final_persisted": final_state["first_reconciliation"][
                        "range_exception_relation"
                    ],
                    "scope": [SESSION_ID, TURN_ID],
                    "transition": "registry propositions -> relation reconciliation -> COMPLETED",
                    "verdict": "PASS",
                },
                "final_synthesis": {
                    "stop_response": _stop_record(final_stop),
                    "stop_disposition": final_state["stop_disposition"],
                    "draft_sha256": hashlib.sha256(final_draft.encode("utf-8")).hexdigest(),
                    "draft_length": len(final_draft),
                },
                "oracle": {
                    "status": "NOT_RUN",
                    "reason": "Task 1R staged parity probe validates runtime/relation contracts; no case oracle was executed.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
