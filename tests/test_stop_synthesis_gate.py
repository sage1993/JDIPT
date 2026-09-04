import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.proposition_rendering import build_render_contract
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    RuntimeTurnState,
    load_runtime_state,
    save_runtime_state,
)


ROOT = Path(__file__).resolve().parents[1]


def _evidence():
    return EvidenceRef(
        source_id="law-001",
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/조문",
        evidence_span="확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="2026-09-04 현재 시행 중인 기준이다.",
    )


def _proposition(*, proposition_id: str = "P1", status: str = "CLOSED", condition: str = "C"):
    return LegalProposition(
        proposition_id=proposition_id,
        status=status,
        materiality="material",
        subject="A",
        condition=condition,
        procedure="P",
        modality="may",
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="O",
        legal_effect="Z",
        polarity="positive",
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=None if status == "OPEN" else _evidence(),
    )


def _state(*, repair_count: int = 0, active: bool = True, propositions=None):
    return RuntimeTurnState(
        schema_version=2,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=active,
        repair_count=repair_count,
        propositions=propositions or [_proposition()],
    )


def _event(message: str, *, session_id: str = "session-a", turn_id: str = "turn-1", stop_hook_active: bool = False) -> dict:
    return {
        "session_id": session_id,
        "turn_id": turn_id,
        "stop_hook_active": stop_hook_active,
        "last_assistant_message": message,
    }


def test_no_state_is_a_noop(tmp_path):
    assert handle_stop_event(_event("범위만 설명"), tmp_path) == {}


def test_inactive_registry_state_is_a_noop(tmp_path):
    save_runtime_state(_state(active=False), tmp_path)

    assert handle_stop_event(_event("범위만 설명"), tmp_path) == {}


def test_valid_exact_effect_and_temporal_slots_are_accepted(tmp_path):
    state = _state()
    save_runtime_state(state, tmp_path)
    contract = build_render_contract(state.propositions[0])
    draft = "\n\n".join(slot.text for slot in contract.slots)

    assert handle_stop_event(_event(draft), tmp_path) == {}


def test_cross_sentence_stitched_answer_is_blocked(tmp_path):
    save_runtime_state(_state(), tmp_path)

    result = handle_stop_event(
        _event("C 요건은 충족한다. P 절차도 거친다. A는 O를 Z로 지정할 수 있다."),
        tmp_path,
    )

    assert result["decision"] == "block"


def test_generic_range_only_answer_is_blocked(tmp_path):
    save_runtime_state(_state(), tmp_path)

    result = handle_stop_event(_event("범위 완화와 일반적인 혜택만 설명"), tmp_path)

    assert result["decision"] == "block"
    assert "P1" in result["reason"]


def test_effect_present_but_temporal_slot_missing_is_blocked(tmp_path):
    state = _state()
    save_runtime_state(state, tmp_path)
    effect = build_render_contract(state.propositions[0]).slots[0].text

    result = handle_stop_event(_event(effect), tmp_path)

    assert result["decision"] == "block"
    assert "2026-09-04 현재 시행 중인 기준이다." in result["reason"]


def test_one_generic_neutral_phrase_does_not_cover_two_open_propositions(tmp_path):
    propositions = [
        _proposition(proposition_id="P_OPEN_1", status="OPEN", condition="시행일 확인"),
        _proposition(proposition_id="P_OPEN_2", status="OPEN", condition="예외요건 확인"),
    ]
    save_runtime_state(_state(propositions=propositions), tmp_path)

    result = handle_stop_event(_event("일부 사항은 확인 필요하다."), tmp_path)

    assert result["decision"] == "block"
    assert "시행일 확인" in result["reason"]
    assert "예외요건 확인" in result["reason"]


def test_first_mismatch_blocks_and_persists_one_repair(tmp_path):
    save_runtime_state(_state(), tmp_path)

    result = handle_stop_event(_event("불충분한 설명"), tmp_path)

    assert result["decision"] == "block"
    stored = load_runtime_state("session-a", "turn-1", tmp_path)
    assert stored.repair_count == 1
    assert "P1" in result["reason"]
    assert "지정할 수 있다" in result["reason"]
    assert "mandatory legal" in result["reason"]


def test_second_mismatch_fails_closed_without_continuation(tmp_path):
    save_runtime_state(_state(repair_count=1), tmp_path)

    result = handle_stop_event(
        _event("불충분한 설명", stop_hook_active=True),
        tmp_path,
    )

    assert result["continue"] is False
    assert "failed-closed" in result["systemMessage"]
    assert "decision" not in result


def test_malformed_state_fails_closed(tmp_path):
    path = tmp_path / "synthesis-runtime" / "session-a" / "turn-1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    result = handle_stop_event(_event("anything"), tmp_path)

    assert result["continue"] is False
    assert "failed closed" in result["systemMessage"]


def test_wrong_session_or_turn_cannot_reuse_state(tmp_path):
    save_runtime_state(_state(), tmp_path)
    contract = build_render_contract(_proposition())
    draft = "\n\n".join(slot.text for slot in contract.slots)

    assert handle_stop_event(
        _event(draft, session_id="other-session"),
        tmp_path,
    ) == {}
    assert handle_stop_event(
        _event(draft, turn_id="other-turn"),
        tmp_path,
    ) == {}


def test_stop_hook_entrypoint_runs_by_path_on_unrelated_turn(tmp_path):
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
