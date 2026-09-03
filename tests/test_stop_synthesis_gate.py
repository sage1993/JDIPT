import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    MaterialProposition,
    RuntimeTurnState,
    save_runtime_state,
)


ROOT = Path(__file__).resolve().parents[1]


def _proposition(*, status: str = "CLOSED") -> MaterialProposition:
    return MaterialProposition(
        proposition_id="P1",
        status=status,
        subject="A",
        condition="C",
        procedure="P",
        operative_verb_lexeme="지정",
        legal_object="O",
        legal_effect="Z",
        source_clause="확인된 원문",
        mandatory_render_clause=(
            "기본 기준으로 C을 충족하고 P를 거치면 A는 O를 Z로 지정할 수 있다."
            if status == "CLOSED"
            else None
        ),
        relation_type="base",
        current_status="CURRENT_CONFIRMED",
    )


def _state(tmp_path, *, repair_count: int = 0, active: bool = True, status: str = "CLOSED"):
    return RuntimeTurnState(
        session_id="session-a",
        turn_id="turn-1",
        jdipt_active=active,
        repair_count=repair_count,
        propositions=[_proposition(status=status)],
    )


def _event(message: str, *, stop_hook_active: bool = False) -> dict:
    return {
        "session_id": "session-a",
        "turn_id": "turn-1",
        "stop_hook_active": stop_hook_active,
        "last_assistant_message": message,
    }


def test_unrelated_turn_without_authoritative_state_is_a_noop(tmp_path):
    result = handle_stop_event(_event("범위만 설명"), tmp_path)

    assert result == {}


def test_inactive_state_is_a_noop(tmp_path):
    save_runtime_state(_state(tmp_path, active=False), tmp_path)

    assert handle_stop_event(_event("범위만 설명"), tmp_path) == {}


def test_active_reconciled_message_is_accepted(tmp_path):
    save_runtime_state(_state(tmp_path), tmp_path)

    result = handle_stop_event(
        _event("기본 기준으로 C을 충족하고 P를 거치면 A는 O를 Z로 지정할 수 있다."),
        tmp_path,
    )

    assert result == {}


def test_first_mismatch_blocks_with_deterministic_repair_clause(tmp_path):
    save_runtime_state(_state(tmp_path), tmp_path)

    result = handle_stop_event(_event("범위 완화와 일반적인 혜택만 설명"), tmp_path)

    assert result["decision"] == "block"
    assert "지정" in result["reason"]
    assert "P1" in result["reason"]
    stored = json.loads(
        (tmp_path / "synthesis-runtime" / "session-a" / "turn-1.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored["repair_count"] == 1


def test_second_mismatch_stops_without_unbounded_continuation(tmp_path):
    save_runtime_state(_state(tmp_path, repair_count=1), tmp_path)

    result = handle_stop_event(
        _event("범위 완화와 일반적인 혜택만 설명", stop_hook_active=True),
        tmp_path,
    )

    assert result["continue"] is False
    assert "failed-closed" in result["systemMessage"]
    assert "decision" not in result


def test_open_proposition_cannot_be_promoted_by_a_specific_answer(tmp_path):
    save_runtime_state(_state(tmp_path, status="OPEN"), tmp_path)

    result = handle_stop_event(_event("기본 기준으로 C을 충족하고 P를 거치면 A는 O를 Z로 지정할 수 있다."), tmp_path)

    assert result["decision"] == "block"
    assert "확인 필요" in result["reason"]


def test_malformed_authoritative_state_fails_closed(tmp_path):
    path = tmp_path / "synthesis-runtime" / "session-a" / "turn-1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    result = handle_stop_event(_event("anything"), tmp_path)

    assert result["continue"] is False
    assert "failed closed" in result["systemMessage"]


def test_stop_hook_entrypoint_runs_by_path_on_an_unrelated_turn(tmp_path):
    env = os.environ.copy()
    env["PLUGIN_ROOT"] = str(ROOT)
    env["PLUGIN_DATA"] = str(tmp_path)
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "stop_synthesis_gate.py")],
        input='{"session_id":"unrelated","turn_id":"turn-1","last_assistant_message":"noop"}\n',
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )

    assert process.returncode == 0
    assert json.loads(process.stdout) == {}
