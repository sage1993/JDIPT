from __future__ import annotations

from pathlib import Path

from scripts.runtime_acceptance import (
    build_runtime_identity,
    classify_plugin_mismatches,
    evaluate_release_authority,
    validate_exact_turn_lifecycle,
)


def _lifecycle(*, session_id: str = "session-a", turn_id: str = "turn-a") -> list[dict[str, object]]:
    return [
        {
            "stage": "NO_STATE",
            "run_id": "run-a",
            "session_id": session_id,
            "turn_id": turn_id,
            "state_identity": None,
            "activation_state": "INACTIVE",
            "jdipt_active": False,
        },
        {
            "stage": "PENDING",
            "run_id": "run-a",
            "session_id": session_id,
            "turn_id": turn_id,
            "state_identity": "state-a",
            "activation_state": "PENDING",
            "jdipt_active": False,
        },
        {
            "stage": "ACTIVE",
            "run_id": "run-a",
            "session_id": session_id,
            "turn_id": turn_id,
            "state_identity": "state-a",
            "activation_state": "ACTIVE",
            "jdipt_active": True,
        },
        {
            "stage": "SYNTHESIS/ENFORCEMENT",
            "run_id": "run-a",
            "session_id": session_id,
            "turn_id": turn_id,
            "state_identity": "state-a",
            "activation_state": "ACTIVE",
            "jdipt_active": True,
        },
        {
            "stage": "STOP RECONCILIATION",
            "run_id": "run-a",
            "session_id": session_id,
            "turn_id": turn_id,
            "state_identity": "state-a",
            "activation_state": "ACTIVE",
            "jdipt_active": True,
        },
        {
            "stage": "FINALIZED/CLOSED",
            "run_id": "run-a",
            "session_id": session_id,
            "turn_id": turn_id,
            "state_identity": "state-a",
            "activation_state": "FINALIZED",
            "jdipt_active": False,
        },
    ]


def _complete_release_evidence() -> dict[str, object]:
    return {
        "static_validation": {"status": "PASS"},
        "regression": {"status": "PASS"},
        "active_runtime_identity": {"status": "PROVEN", "source_relation": "SOURCE_MATCH"},
        "turn_continuity": {"status": "PASS", "cross_turn_state_reuse": 0},
        "ash06_3run": {"status": "PASS", "runs": ["PASS", "PASS", "PASS"]},
        "ash06_10run": {"status": "PASS", "runs": ["PASS"] * 10},
        "semantic_soundness": {
            "coverage": True,
            "sound": True,
            "false_green": 0,
            "critical_missing": 0,
            "invalid_promotion": 0,
        },
        "plugin_integrity_classification": {"introduced_mismatches": 0, "mismatches": []},
        "mcp_runtime": {"status": "PASS"},
    }


def test_valid_exact_turn_lifecycle_is_proven():
    result = validate_exact_turn_lifecycle(_lifecycle())

    assert result["status"] == "PASS"
    assert result["violations"] == []
    assert result["same_state_stop"] is True


def test_missing_authoritative_identity_fails_closed():
    events = _lifecycle()
    events[3]["turn_id"] = None

    result = validate_exact_turn_lifecycle(events)

    assert result["status"] == "FAIL_CLOSED"
    assert "MISSING_TURN_IDENTITY" in result["violations"]


def test_pending_and_active_true_is_not_atomic():
    events = _lifecycle()
    events[2]["activation_state"] = "PENDING"

    result = validate_exact_turn_lifecycle(events)

    assert result["status"] == "FAIL_CLOSED"
    assert "NON_ATOMIC_ACTIVATION" in result["violations"]


def test_stop_must_read_the_same_authoritative_state():
    events = _lifecycle()
    events[4]["state_identity"] = "state-b"

    result = validate_exact_turn_lifecycle(events)

    assert result["status"] == "FAIL_CLOSED"
    assert "STOP_STATE_MISMATCH" in result["violations"]


def test_release_authority_requires_all_evidence():
    evidence = _complete_release_evidence()
    evidence.pop("ash06_10run")

    result = evaluate_release_authority(evidence)

    assert result["verdict"] == "HOLD"
    assert "MISSING_ASH06_10RUN" in result["reasons"]


def test_release_authority_requires_exactly_ten_stability_runs():
    evidence = _complete_release_evidence()
    evidence["ash06_10run"] = {"status": "PASS", "runs": ["PASS"] * 9}

    result = evaluate_release_authority(evidence)

    assert result["verdict"] == "HOLD"
    assert "ASH06_10RUN_NOT_10_OF_10" in result["reasons"]


def test_release_authority_accepts_complete_all_pass_evidence():
    result = evaluate_release_authority(_complete_release_evidence())

    assert result == {"verdict": "PASS", "release_ready": True, "reasons": []}


def test_release_authority_rejects_semantic_false_green():
    evidence = _complete_release_evidence()
    evidence["semantic_soundness"]["false_green"] = 1  # type: ignore[index]

    result = evaluate_release_authority(evidence)

    assert result["verdict"] == "HOLD"
    assert "SEMANTIC_FALSE_GREEN" in result["reasons"]


def test_release_authority_rejects_stale_ambiguous_and_patched_unresolved_evidence():
    evidence = _complete_release_evidence()
    evidence["active_runtime_identity"]["stale"] = True  # type: ignore[index]
    evidence["turn_continuity"]["ambiguous"] = True  # type: ignore[index]
    evidence["unresolved_root_cause_with_patch"] = True

    result = evaluate_release_authority(evidence)

    assert result["verdict"] == "HOLD"
    assert "STALE_ACTIVE_RUNTIME_IDENTITY" in result["reasons"]
    assert "AMBIGUOUS_TURN_CONTINUITY" in result["reasons"]
    assert "UNRESOLVED_ROOT_CAUSE_WITH_PATCH" in result["reasons"]


def test_release_authority_rejects_malformed_plugin_inventory():
    evidence = _complete_release_evidence()
    evidence["plugin_integrity_classification"]["mismatches"] = {"not": "a list"}  # type: ignore[index]

    result = evaluate_release_authority(evidence)

    assert result["verdict"] == "HOLD"
    assert "MALFORMED_PLUGIN_INTEGRITY_CLASSIFICATION" in result["reasons"]


def test_identity_is_unresolved_when_loaded_module_path_is_not_observed():
    candidate = Path(__file__).resolve().parents[1]
    active = Path("F:/2026-PJ/JDIPT")

    result = build_runtime_identity(
        executable_path=Path("C:/codex.exe"),
        codex_version="codex-cli 0.153.3",
        candidate_root=candidate,
        active_root=active,
        plugin_data=Path("C:/missing-plugin-data"),
        hook_path=active / "hooks" / "hooks.json",
        registry_path=Path("C:/missing-registry.json"),
        runtime_state_path=Path("C:/missing-state.json"),
        loaded_module_paths=(),
    )

    assert result["identity_status"] == "IDENTITY_UNRESOLVED"
    assert result["source_relation"] == "SOURCE_MISMATCH"


def test_plugin_mismatch_classifier_marks_cache_difference_as_stale_install():
    installed = Path("C:/installed")
    active = Path("C:/active")

    result = classify_plugin_mismatches(
        ["digest mismatch: plugin/scripts/stop_synthesis_gate.py"],
        installed_root=installed,
        active_root=active,
    )

    assert result == [
        {
            "mismatch": "digest mismatch: plugin/scripts/stop_synthesis_gate.py",
            "classification": "EXPECTED_STALE_INSTALL",
            "active_runtime_relevant": False,
        }
    ]


def test_plugin_mismatch_classifier_marks_active_hook_difference_relevant():
    active = Path("C:/active")

    result = classify_plugin_mismatches(
        ["digest mismatch: plugin/hooks/hooks.json"],
        installed_root=active,
        active_root=active,
    )

    assert result[0]["classification"] == "ACTIVE_RUNTIME_RELEVANT"
    assert result[0]["active_runtime_relevant"] is True


def test_plugin_mismatch_classifier_marks_loaded_skill_and_runtime_module_relevant():
    active = Path("C:/active")

    result = classify_plugin_mismatches(
        [
            "digest mismatch: SKILL.md",
            "digest mismatch: plugin/scripts/legal_proposition.py",
            "digest mismatch: plugin/scripts/proposition_rendering.py",
        ],
        installed_root=active,
        active_root=active,
    )

    assert [item["classification"] for item in result] == [
        "ACTIVE_RUNTIME_RELEVANT",
        "ACTIVE_RUNTIME_RELEVANT",
        "ACTIVE_RUNTIME_RELEVANT",
    ]
