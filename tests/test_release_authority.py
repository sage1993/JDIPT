from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

from scripts.release_manifest import (
    build_snapshot_id,
    evaluate_release_manifest,
    snapshot_identity,
)
from scripts.run_release_gate import GateResult, build_release_manifest


CORE_CASES = [
    "E02", "E03", "E09", "E13", "E18", "E31", "E36", "E37",
    "E39", "E41", "E43", "E44", "E45", "E46",
]
FULL_CASES = [
    "E01", "E02", "E03", "E04", "E05", "E06", "E08", "E09", "E11",
    "E12", "E13", "E14", "E15", "E18", "E25", "E31", "E35", "E36",
    "E37", "E38", "E39", "E41", "E43", "E44", "E45", "E46",
]
ANSIM_CASES = [f"ASH-{number:02d}" for number in range(1, 10)]


def _suite(case_ids: list[str]) -> dict:
    return {
        "status": "PASS",
        "snapshot_id": "snapshot-a",
        "case_ids": list(case_ids),
        "pass_count": len(case_ids),
        "expected_count": len(case_ids),
    }


def valid_manifest() -> dict:
    manifest = {
        "schema_version": "1.0",
        "repository": {
            "sha": "a" * 40,
            "dirty": False,
            "changed_file_digest_manifest": {},
        },
        "installed": {
            "plugin_version": "0.2.4",
            "manifest_digest": "b" * 64,
            "integrity_status": "PASS",
        },
        "active_runtime": {
            "plugin_id": "jdipt@sage1993",
            "source_path": "C:/runtime/jdipt/0.2.4",
            "runtime_digest": "b" * 64,
            "identity_status": "PASS",
        },
        "oracle": {
            "version": "v0.2.4-candidate",
            "digest": "d" * 64,
        },
        "static_validation": {
            "pytest": "PASS",
            "validate_repo": "PASS",
            "authority_temporal": "PASS",
            "compileall": "PASS",
            "npm_ci": "PASS",
            "npm_audit": "PASS",
            "plugin_integrity": "PASS",
            "diff_check": "PASS",
        },
        "suites": {
            "core": _suite(CORE_CASES),
            "full": _suite(FULL_CASES),
            "ansim": _suite(ANSIM_CASES),
            "stability": _suite(CORE_CASES),
        },
        "hard_gates": {
            "status": "PASS",
            "violations": [],
            "critical_negative_markers": [],
        },
        "source_correctness": {
            "status": "PASS",
            "failures": [],
        },
        "runtime_host_acceptance": {
            "status": "PASS",
            "identity_status": "PASS",
            "failures": [],
        },
        "case_inventory": {
            "core": {"expected": list(CORE_CASES), "observed": list(CORE_CASES)},
            "full": {"expected": list(FULL_CASES), "observed": list(FULL_CASES)},
            "ansim": {"expected": list(ANSIM_CASES), "observed": list(ANSIM_CASES)},
            "stability": {"expected": list(CORE_CASES), "observed": list(CORE_CASES)},
        },
        "evidence": {
            "generated_at": "2026-09-06T12:00:00Z",
            "snapshot_id": "snapshot-a",
        },
        "final": {"verdict": "UNSET", "reasons": []},
    }
    snapshot_id = build_snapshot_id(snapshot_identity(manifest))
    for suite in manifest["suites"].values():
        suite["snapshot_id"] = snapshot_id
    manifest["evidence"]["snapshot_id"] = snapshot_id
    return manifest


def assert_hold(manifest: dict, reason: str) -> None:
    result = evaluate_release_manifest(manifest)
    assert result.verdict == "HOLD"
    assert reason in result.reasons


def test_required_suite_not_run_cannot_be_offset_by_other_passes():
    manifest = valid_manifest()
    manifest["suites"]["full"]["status"] = "NOT_RUN"

    assert_hold(manifest, "REQUIRED_SUITE_NOT_RUN")


def test_hard_gate_failure_cannot_be_offset_by_normal_case_passes():
    manifest = valid_manifest()
    manifest["hard_gates"]["status"] = "FAIL"
    manifest["hard_gates"]["violations"] = [{"id": "TEMPORAL_AUTHORITY", "status": "FAIL"}]

    assert_hold(manifest, "HARD_GATE_FAILURE")


def test_missing_case_identity_holds_even_when_count_is_lower_by_one():
    manifest = valid_manifest()
    manifest["case_inventory"]["full"]["observed"] = manifest["case_inventory"]["full"]["observed"][:-1]

    assert_hold(manifest, "MISSING_CASE")


def test_duplicate_case_identity_holds_even_when_count_is_unchanged():
    manifest = valid_manifest()
    observed = manifest["case_inventory"]["full"]["observed"]
    manifest["case_inventory"]["full"]["observed"] = observed[:-1] + [observed[-2]]

    assert_hold(manifest, "DUPLICATE_CASE")


def test_unknown_required_case_substitution_holds_even_when_expected_matches_observed():
    manifest = valid_manifest()
    replacement = list(manifest["case_inventory"]["full"]["expected"])
    replacement[-1] = "E99"
    manifest["case_inventory"]["full"] = {"expected": replacement, "observed": replacement}
    manifest["suites"]["full"]["case_ids"] = replacement

    assert_hold(manifest, "UNEXPECTED_CASE")


def test_mixed_suite_snapshot_holds():
    manifest = valid_manifest()
    manifest["suites"]["ansim"]["snapshot_id"] = "snapshot-b"

    assert_hold(manifest, "SNAPSHOT_MISMATCH")


def test_installed_parity_failure_holds():
    manifest = valid_manifest()
    manifest["installed"]["integrity_status"] = "FAIL"

    assert_hold(manifest, "INSTALLED_PARITY_FAILURE")


def test_active_runtime_identity_failure_holds():
    manifest = valid_manifest()
    manifest["active_runtime"]["identity_status"] = "FAIL"

    assert_hold(manifest, "ACTIVE_RUNTIME_IDENTITY_MISMATCH")


def test_active_runtime_digest_mismatch_holds_even_when_status_claims_pass():
    manifest = valid_manifest()
    manifest["active_runtime"]["runtime_digest"] = "c" * 64

    assert_hold(manifest, "ACTIVE_RUNTIME_IDENTITY_MISMATCH")


def test_critical_negative_marker_holds_even_when_normal_score_passes():
    manifest = valid_manifest()
    manifest["hard_gates"]["critical_negative_markers"] = ["EXCEPTION_350M_REVIEW"]

    assert_hold(manifest, "CRITICAL_NEGATIVE")


def test_source_correctness_failure_holds():
    manifest = valid_manifest()
    manifest["source_correctness"] = {"status": "FAIL", "failures": ["source evidence failed"]}

    assert_hold(manifest, "SOURCE_CORRECTNESS_FAILURE")


def test_runtime_host_acceptance_failure_holds():
    manifest = valid_manifest()
    manifest["runtime_host_acceptance"] = {
        "status": "FAIL",
        "identity_status": "PASS",
        "failures": ["host acceptance failed"],
    }

    assert_hold(manifest, "HOST_ACCEPTANCE_FAILURE")


def test_malformed_manifest_holds_with_invalid_manifest_reason():
    manifest = valid_manifest()
    del manifest["oracle"]

    assert_hold(manifest, "INVALID_MANIFEST")


def test_complete_same_snapshot_evidence_is_the_authoritative_positive_case():
    result = evaluate_release_manifest(valid_manifest())

    assert result.verdict == "PASS"
    assert result.reasons == ()


def test_fixture_mutation_does_not_change_the_valid_fixture():
    original = valid_manifest()
    mutated = deepcopy(original)
    mutated["suites"]["core"]["status"] = "FAIL"

    assert evaluate_release_manifest(original).verdict == "PASS"
    assert evaluate_release_manifest(mutated).verdict == "HOLD"


def test_run_release_gate_manifest_mode_publishes_only_authoritative_decision(tmp_path):
    manifest_path = tmp_path / "release-manifest.json"
    manifest_path.write_text(json.dumps(valid_manifest(), ensure_ascii=False), encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "run_release_gate.py"), "--manifest", str(manifest_path)],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    output = json.loads(completed.stdout)
    assert output["authoritative_release"]["verdict"] == "PASS"


def test_build_release_manifest_binds_all_component_results_to_one_snapshot():
    core = tuple(f"E{case_id:02d}" for case_id in [2, 3, 9, 13, 18, 31, 36, 37, 39, 41, 43, 44, 45, 46])
    full = tuple(f"E{case_id:02d}" for case_id in [1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 18, 25, 31, 35, 36, 37, 38, 39, 41, 43, 44, 45, 46])
    results = [
        GateResult("A: deterministic", True),
        GateResult("B: core active Evals", True, suite="core", case_ids=core),
        GateResult("C: core stability", True, suite="stability", case_ids=core),
        GateResult("D: full active Evals", True, suite="full", case_ids=full),
        GateResult("Ansim housing core", True, suite="ansim", case_ids=tuple(ANSIM_CASES)),
        GateResult("D: package/static", True),
    ]
    root = Path(__file__).resolve().parents[1]
    manifest = build_release_manifest(
        results,
        installed_skill_root=root,
        active_runtime_root=root,
        mode="full",
    )

    assert manifest["final"]["verdict"] == "PASS"
    assert all(suite["status"] == "PASS" for suite in manifest["suites"].values())
    assert manifest["evidence"]["snapshot_id"] == build_snapshot_id(snapshot_identity(manifest))
