from types import SimpleNamespace

from scripts.eval_suite import ansim_case_ids, load_suite_manifest, suite_case_ids
from scripts import run_eval_suite
from scripts.run_eval_suite import ansim_attempt_plan, execute_ansim_attempts, load_ansim_catalog, load_catalog, select_case_ids


def test_suite_manifest_partitions_catalog():
    manifest = load_suite_manifest()

    core = suite_case_ids("core", manifest)
    full = suite_case_ids("full", manifest)
    legacy = suite_case_ids("legacy", manifest)
    all_cases = suite_case_ids("all", manifest)

    assert len(core) == 14
    assert len(full) == 26
    assert len(legacy) == 20
    assert len(all_cases) == 46
    assert core <= full
    assert full.isdisjoint(legacy)
    assert full | legacy == all_cases == set(range(1, 47))


def test_core_contains_new_v023_fail_closed_cases():
    core = suite_case_ids("core")
    assert {43, 44, 45, 46} <= core


def test_legacy_coverage_targets_are_active():
    manifest = load_suite_manifest()
    full = suite_case_ids("full", manifest)
    legacy = suite_case_ids("legacy", manifest)
    coverage = manifest["legacy_coverage"]

    assert {int(case_id[1:]) for case_id in coverage} == legacy
    for active_case in coverage.values():
        assert int(active_case[1:]) in full


def test_ansim_suite_is_additive_to_core14_and_full26():
    assert ansim_case_ids() == [f"ASH-{number:02d}" for number in range(1, 10)]
    assert len(suite_case_ids("core")) == 14
    assert len(suite_case_ids("full")) == 26


def test_unknown_suite_is_rejected():
    try:
        suite_case_ids("unknown")
    except ValueError as exc:
        assert "unknown suite" in str(exc)
    else:
        raise AssertionError("unknown suite must fail")


def test_runner_catalog_contains_all_e01_to_e46_cases():
    catalog = load_catalog()
    assert sorted(catalog) == list(range(1, 47))


def test_runner_defaults_to_manifest_full_suite():
    selected = select_case_ids(suite="full", from_case=None, to_case=None)
    assert len(selected) == 26
    assert selected == sorted(suite_case_ids("full"))


def test_targeted_range_overrides_suite_selection():
    selected = select_case_ids(suite="core", from_case=43, to_case=46)
    assert selected == [43, 44, 45, 46]


def test_consolidated_runner_requires_marketplace_plugin_identity():
    assert run_eval_suite.REQUIRED_PLUGIN_ID == "jdipt@sage1993"
    assert run_eval_suite.legacy.REQUIRED_PLUGIN_VERSION == "0.2.4"


def test_ansim_runner_loads_oracle_catalog_without_extending_e_catalog():
    catalog = load_ansim_catalog()
    assert list(catalog) == [f"ASH-{number:02d}" for number in range(1, 10)]
    assert [case.prompt for case in catalog.values()]
    assert sorted(load_catalog()) == list(range(1, 47))


def test_ansim_attempt_plan_uses_fresh_case_runs():
    core = ansim_attempt_plan(1)
    stability = ansim_attempt_plan(3)
    assert len(core) == 9
    assert len(stability) == 27
    assert len(set(core)) == 9
    assert len(set(stability)) == 27
    assert stability[0] == ("ASH-01", 1)


def test_ansim_execution_helper_keeps_27_fresh_results(tmp_path):
    catalog = load_ansim_catalog()
    called_dirs = []

    def runner(attempt_dir, case):
        called_dirs.append(attempt_dir)
        answer_file = f"E{case.number:02d}.md"
        (attempt_dir / answer_file).write_text("fixture answer", encoding="utf-8")
        return SimpleNamespace(
            process_ok=True,
            environment_error=None,
            answer_file=answer_file,
            returncode=0,
            duration_seconds=0.1,
        )

    def evaluator(case_id, answer, process_ok):
        assert answer == "fixture answer"
        assert process_ok
        return {"case_id": case_id, "verdict": "PASS", "findings": [], "critical_negative_markers": []}

    results = execute_ansim_attempts(tmp_path, catalog, repetitions=3, run_case=runner, evaluate=evaluator)

    assert len(results) == 27
    assert len(set(called_dirs)) == 27
    assert all(path.is_dir() for path in called_dirs)


def test_ansim_cli_parses_repetitions_before_loading_e_catalog(monkeypatch):
    monkeypatch.setattr("sys.argv", ["run_eval_suite.py", "--suite", "ansim", "--repetitions", "3"])
    monkeypatch.setattr(run_eval_suite, "_run_ansim_cli", lambda args, root: 17)
    monkeypatch.setattr(
        run_eval_suite,
        "load_catalog",
        lambda: (_ for _ in ()).throw(AssertionError("E catalog must not load for ansim")),
    )
    assert run_eval_suite.main() == 17

    assert run_eval_suite.legacy.REQUIRED_PLUGIN_ID == "jdipt@sage1993"
