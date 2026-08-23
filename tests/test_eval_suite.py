from scripts.eval_suite import load_suite_manifest, suite_case_ids
from scripts.run_eval_suite import load_catalog, select_case_ids


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
