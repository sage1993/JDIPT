"""Central JDIPT evaluation-suite manifest loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "skills" / "law-interpretation-request" / "evals" / "suite-manifest.json"
VALID_SUITES = {"core", "full", "legacy", "all"}


def load_suite_manifest(path: Path | None = None) -> dict[str, Any]:
    source = path or DEFAULT_MANIFEST
    data = json.loads(source.read_text(encoding="utf-8"))
    validate_suite_manifest(data)
    return data


def _case_set(data: dict[str, Any], key: str) -> set[int]:
    values = data.get(key)
    if not isinstance(values, list) or any(not isinstance(item, int) for item in values):
        raise ValueError(f"{key} must be a list of integers")
    if len(values) != len(set(values)):
        raise ValueError(f"{key} contains duplicate case ids")
    return set(values)


def validate_suite_manifest(data: dict[str, Any]) -> None:
    catalog = _case_set(data, "catalog_cases")
    core = _case_set(data, "core_cases")
    full = _case_set(data, "full_cases")
    legacy = _case_set(data, "legacy_cases")

    expected_catalog = set(range(1, 47))
    if catalog != expected_catalog:
        raise ValueError(f"catalog_cases must be exactly E01-E46, found {sorted(catalog)}")
    if len(core) != 14:
        raise ValueError(f"core_cases must contain 14 cases, found {len(core)}")
    if len(full) != 26:
        raise ValueError(f"full_cases must contain 26 cases, found {len(full)}")
    if len(legacy) != 20:
        raise ValueError(f"legacy_cases must contain 20 cases, found {len(legacy)}")
    if not core <= full:
        raise ValueError("core_cases must be a subset of full_cases")
    if full & legacy:
        raise ValueError(f"full_cases and legacy_cases overlap: {sorted(full & legacy)}")
    if full | legacy != catalog:
        raise ValueError("full_cases and legacy_cases must partition catalog_cases")

    coverage = data.get("legacy_coverage")
    if not isinstance(coverage, dict):
        raise ValueError("legacy_coverage must be an object")
    coverage_ids: set[int] = set()
    for legacy_id, active_id in coverage.items():
        if not isinstance(legacy_id, str) or not isinstance(active_id, str):
            raise ValueError("legacy_coverage keys and values must be E## strings")
        try:
            legacy_number = int(legacy_id.removeprefix("E"))
            active_number = int(active_id.removeprefix("E"))
        except ValueError as exc:
            raise ValueError("legacy_coverage keys and values must be E## strings") from exc
        coverage_ids.add(legacy_number)
        if active_number not in full:
            raise ValueError(f"legacy coverage target {active_id} is not in full_cases")
    if coverage_ids != legacy:
        raise ValueError("legacy_coverage must contain exactly every legacy case")


def suite_case_ids(name: str, manifest: dict[str, Any] | None = None) -> set[int]:
    if name not in VALID_SUITES:
        raise ValueError(f"unknown suite: {name}")
    data = manifest if manifest is not None else load_suite_manifest()
    key = "catalog_cases" if name == "all" else f"{name}_cases"
    return set(data[key])


def ordered_suite_case_ids(name: str, manifest: dict[str, Any] | None = None) -> list[int]:
    data = manifest if manifest is not None else load_suite_manifest()
    ids = suite_case_ids(name, data)
    return [case_id for case_id in data["catalog_cases"] if case_id in ids]
