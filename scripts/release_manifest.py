"""Versioned, fail-closed release evidence and snapshot authority."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

RELEASE_SCHEMA_VERSION = "1.0"
EXPECTED_PLUGIN_ID = "jdipt@sage1993"
MANDATORY_SUITES = ("core", "full", "ansim", "stability")
STATIC_VALIDATION_KEYS = (
    "pytest",
    "validate_repo",
    "authority_temporal",
    "compileall",
    "npm_ci",
    "npm_audit",
    "plugin_integrity",
    "diff_check",
)
REASON_CODES = (
    "REQUIRED_SUITE_NOT_RUN",
    "SUITE_FAILURE",
    "HARD_GATE_FAILURE",
    "MISSING_CASE",
    "UNEXPECTED_CASE",
    "DUPLICATE_CASE",
    "CASE_INVENTORY_MISMATCH",
    "SNAPSHOT_MISMATCH",
    "INSTALLED_PARITY_FAILURE",
    "ACTIVE_RUNTIME_IDENTITY_MISMATCH",
    "CRITICAL_NEGATIVE",
    "STATIC_VALIDATION_FAILURE",
    "SOURCE_CORRECTNESS_FAILURE",
    "HOST_ACCEPTANCE_FAILURE",
    "INVALID_MANIFEST",
)
_DIGEST_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_CASE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class ReleaseDecision:
    """The only object allowed to carry the authoritative final verdict."""

    verdict: str
    reasons: tuple[str, ...] = ()
    details: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "details": list(self.details),
        }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git_output(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"git command failed: {' '.join(args)}")
    return result.stdout


def repository_sha(repo_root: Path) -> str:
    return _git_output(repo_root.resolve(), "rev-parse", "HEAD").strip()


def build_changed_file_digest_manifest(repo_root: Path) -> dict[str, str]:
    """Hash every tracked/untracked changed file, including deleted markers."""

    root = repo_root.resolve()
    changed_names = set(
        name.strip()
        for name in _git_output(root, "diff", "--name-only", "HEAD").splitlines()
        if name.strip()
    )
    changed_names.update(
        name.strip()
        for name in _git_output(root, "ls-files", "--others", "--exclude-standard").splitlines()
        if name.strip()
    )
    manifest: dict[str, str] = {}
    for name in sorted(changed_names):
        path = root / Path(name)
        manifest[name.replace("\\", "/")] = _sha256_file(path) if path.is_file() else "MISSING"
    return manifest


def build_runtime_manifest_digest(root: Path) -> str:
    """Return the digest of the installed/runtime logical file manifest."""

    from scripts.plugin_integrity import build_runtime_manifest

    return _sha256_bytes(_canonical_bytes(build_runtime_manifest(root)))


def digest_file(path: Path) -> str:
    """Return the SHA-256 digest of a source/oracle file's raw bytes."""

    return _sha256_bytes(path.read_bytes())


def build_snapshot_id(identity: Mapping[str, Any]) -> str:
    """Hash the complete release identity, including contract version."""

    return _sha256_bytes(_canonical_bytes(dict(identity)))


def snapshot_identity(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "repository_sha": manifest["repository"]["sha"],
        "repository_changed_file_digest_manifest": manifest["repository"][
            "changed_file_digest_manifest"
        ],
        "installed_manifest_digest": manifest["installed"]["manifest_digest"],
        "active_runtime_digest": manifest["active_runtime"]["runtime_digest"],
        "oracle_version": manifest["oracle"]["version"],
        "oracle_digest": manifest["oracle"]["digest"],
        "release_contract_version": manifest["schema_version"],
    }


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(_DIGEST_RE.fullmatch(value))


def _canonical_case_ids(suite_name: str) -> list[str] | None:
    if suite_name == "ansim":
        from scripts.ansim_housing_oracle import EXPECTED_CASE_IDS

        return list(EXPECTED_CASE_IDS)
    if suite_name in {"core", "full", "stability"}:
        from scripts.eval_suite import ordered_suite_case_ids

        case_ids = ordered_suite_case_ids("core" if suite_name == "stability" else suite_name)
        return [f"E{case_id:02d}" for case_id in case_ids]
    return None


def _unique_append(
    reasons: list[str], details: list[str], reason: str, detail: str,
) -> None:
    if reason not in reasons:
        reasons.append(reason)
    if detail and detail not in details:
        details.append(detail)


def _collect_issues(manifest: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
    reasons: list[str] = []
    details: list[str] = []

    if not isinstance(manifest, Mapping):
        return ("INVALID_MANIFEST",), ("manifest must be an object",)

    required_sections = {
        "schema_version",
        "repository",
        "installed",
        "active_runtime",
        "oracle",
        "static_validation",
        "suites",
        "hard_gates",
        "source_correctness",
        "runtime_host_acceptance",
        "case_inventory",
        "evidence",
        "final",
    }
    missing_sections = sorted(required_sections - set(manifest))
    if missing_sections:
        _unique_append(
            reasons,
            details,
            "INVALID_MANIFEST",
            f"missing sections: {', '.join(missing_sections)}",
        )
        return tuple(reasons), tuple(details)

    if manifest.get("schema_version") != RELEASE_SCHEMA_VERSION:
        _unique_append(
            reasons,
            details,
            "INVALID_MANIFEST",
            f"unsupported schema_version: {manifest.get('schema_version')!r}",
        )

    repository = manifest["repository"]
    if not isinstance(repository, Mapping):
        _unique_append(reasons, details, "INVALID_MANIFEST", "repository must be an object")
    else:
        sha = repository.get("sha")
        dirty = repository.get("dirty")
        changed = repository.get("changed_file_digest_manifest")
        if not isinstance(sha, str) or not _SHA_RE.fullmatch(sha):
            _unique_append(reasons, details, "INVALID_MANIFEST", "repository.sha must be a 40-character SHA")
        if not isinstance(dirty, bool) or not isinstance(changed, Mapping):
            _unique_append(reasons, details, "INVALID_MANIFEST", "repository dirty/digest manifest shape is invalid")
        elif dirty and not changed:
            _unique_append(
                reasons,
                details,
                "SNAPSHOT_MISMATCH",
                "dirty repository requires changed_file_digest_manifest",
            )
        elif not dirty and changed:
            _unique_append(
                reasons,
                details,
                "SNAPSHOT_MISMATCH",
                "clean repository cannot carry changed-file digests",
            )
        if isinstance(changed, Mapping):
            for path, digest in changed.items():
                if not _is_nonempty_text(path) or not (digest == "MISSING" or _is_digest(digest)):
                    _unique_append(
                        reasons,
                        details,
                        "INVALID_MANIFEST",
                        "repository changed-file digest manifest contains an invalid entry",
                    )
                    break

    installed = manifest["installed"]
    if not isinstance(installed, Mapping):
        _unique_append(reasons, details, "INVALID_MANIFEST", "installed must be an object")
    else:
        if not _is_nonempty_text(installed.get("plugin_version")) or not _is_digest(installed.get("manifest_digest")):
            _unique_append(reasons, details, "INVALID_MANIFEST", "installed identity is incomplete")
        if installed.get("plugin_id", EXPECTED_PLUGIN_ID) != EXPECTED_PLUGIN_ID:
            _unique_append(reasons, details, "INSTALLED_PARITY_FAILURE", "installed plugin_id is not JDIPT marketplace identity")
        if installed.get("integrity_status") != "PASS":
            _unique_append(reasons, details, "INSTALLED_PARITY_FAILURE", "installed integrity is not PASS")

    active = manifest["active_runtime"]
    if not isinstance(active, Mapping):
        _unique_append(reasons, details, "INVALID_MANIFEST", "active_runtime must be an object")
    else:
        if not all(
            _is_nonempty_text(active.get(field))
            for field in ("plugin_id", "source_path", "runtime_digest")
        ) or not _is_digest(active.get("runtime_digest")):
            _unique_append(reasons, details, "INVALID_MANIFEST", "active runtime identity is incomplete")
        if active.get("plugin_id") != EXPECTED_PLUGIN_ID:
            _unique_append(reasons, details, "ACTIVE_RUNTIME_IDENTITY_MISMATCH", "active runtime plugin_id is not JDIPT marketplace identity")
        installed_section = manifest.get("installed")
        installed_digest = (
            installed_section.get("manifest_digest")
            if isinstance(installed_section, Mapping)
            else None
        )
        if _is_digest(active.get("runtime_digest")) and active.get("runtime_digest") != installed_digest:
            _unique_append(
                reasons,
                details,
                "ACTIVE_RUNTIME_IDENTITY_MISMATCH",
                "active runtime digest differs from installed manifest digest",
            )
        if active.get("identity_status") != "PASS":
            _unique_append(
                reasons,
                details,
                "ACTIVE_RUNTIME_IDENTITY_MISMATCH",
                "active runtime identity is not PASS",
            )

    oracle = manifest["oracle"]
    if not isinstance(oracle, Mapping) or not _is_nonempty_text(oracle.get("version")) or not _is_digest(oracle.get("digest")):
        _unique_append(reasons, details, "INVALID_MANIFEST", "oracle identity is incomplete")

    static = manifest["static_validation"]
    if not isinstance(static, Mapping):
        _unique_append(reasons, details, "INVALID_MANIFEST", "static_validation must be an object")
    else:
        missing_static = [key for key in STATIC_VALIDATION_KEYS if key not in static]
        if missing_static:
            _unique_append(
                reasons,
                details,
                "INVALID_MANIFEST",
                f"missing static checks: {', '.join(missing_static)}",
            )
        failed_static = [key for key in STATIC_VALIDATION_KEYS if static.get(key) != "PASS"]
        invalid_static = [
            key
            for key in STATIC_VALIDATION_KEYS
            if static.get(key) not in {"PASS", "FAIL", "NOT_RUN"}
        ]
        if invalid_static:
            _unique_append(
                reasons,
                details,
                "INVALID_MANIFEST",
                f"invalid static validation statuses: {', '.join(invalid_static)}",
            )
        if failed_static:
            _unique_append(
                reasons,
                details,
                "STATIC_VALIDATION_FAILURE",
                f"static validation failed: {', '.join(failed_static)}",
            )

    evidence = manifest["evidence"]
    evidence_snapshot = evidence.get("snapshot_id") if isinstance(evidence, Mapping) else None
    if not isinstance(evidence, Mapping) or not _is_nonempty_text(evidence.get("generated_at")) or not _is_nonempty_text(evidence_snapshot):
        _unique_append(reasons, details, "INVALID_MANIFEST", "evidence identity is incomplete")

    suites = manifest["suites"]
    inventory = manifest["case_inventory"]
    if not isinstance(suites, Mapping) or not isinstance(inventory, Mapping):
        _unique_append(reasons, details, "INVALID_MANIFEST", "suites and case_inventory must be objects")
        return tuple(reasons), tuple(details)

    observed_snapshot_ids: list[str] = []
    for suite_name in MANDATORY_SUITES:
        suite = suites.get(suite_name)
        if not isinstance(suite, Mapping):
            _unique_append(reasons, details, "INVALID_MANIFEST", f"suite {suite_name} must be an object")
            continue
        status = suite.get("status")
        if status not in {"PASS", "FAIL", "NOT_RUN"}:
            _unique_append(reasons, details, "INVALID_MANIFEST", f"invalid suite status: {suite_name}")
        elif status == "NOT_RUN":
            _unique_append(reasons, details, "REQUIRED_SUITE_NOT_RUN", f"required suite not run: {suite_name}")
        elif status != "PASS":
            _unique_append(reasons, details, "SUITE_FAILURE", f"required suite failed: {suite_name}")
        suite_snapshot = suite.get("snapshot_id")
        if not _is_nonempty_text(suite_snapshot):
            _unique_append(reasons, details, "INVALID_MANIFEST", f"suite {suite_name} has no snapshot_id")
        else:
            observed_snapshot_ids.append(suite_snapshot)
        case_ids = suite.get("case_ids")
        if not isinstance(case_ids, list):
            _unique_append(reasons, details, "INVALID_MANIFEST", f"suite {suite_name}.case_ids must be a list")
        pass_count = suite.get("pass_count")
        expected_count = suite.get("expected_count")
        if not isinstance(pass_count, int) or not isinstance(expected_count, int) or pass_count < 0 or expected_count < 0 or pass_count > expected_count:
            _unique_append(reasons, details, "INVALID_MANIFEST", f"suite {suite_name} pass counts are invalid")
        elif status == "PASS" and pass_count != expected_count:
            _unique_append(reasons, details, "SUITE_FAILURE", f"passing suite {suite_name} does not cover every expected case")

        record = inventory.get(suite_name)
        if not isinstance(record, Mapping):
            _unique_append(reasons, details, "INVALID_MANIFEST", f"case inventory missing: {suite_name}")
            continue
        expected = record.get("expected")
        observed = record.get("observed")
        if not isinstance(expected, list) or not isinstance(observed, list):
            _unique_append(reasons, details, "INVALID_MANIFEST", f"case inventory shape invalid: {suite_name}")
            continue
        invalid_ids = [item for item in expected + observed if not isinstance(item, str) or not _CASE_ID_RE.fullmatch(item)]
        if invalid_ids:
            _unique_append(reasons, details, "INVALID_MANIFEST", f"case inventory contains empty/invalid IDs: {suite_name}")
            continue
        if len(set(expected)) != len(expected):
            _unique_append(reasons, details, "INVALID_MANIFEST", f"expected case IDs contain duplicates: {suite_name}")
        if not expected:
            _unique_append(reasons, details, "INVALID_MANIFEST", f"expected case IDs are empty: {suite_name}")
        canonical_expected = _canonical_case_ids(suite_name)
        if canonical_expected is not None:
            canonical_missing = sorted(set(canonical_expected) - set(expected))
            canonical_unexpected = sorted(set(expected) - set(canonical_expected))
            if canonical_missing:
                _unique_append(
                    reasons,
                    details,
                    "MISSING_CASE",
                    f"{suite_name} missing canonical case IDs: {', '.join(canonical_missing)}",
                )
            if canonical_unexpected:
                _unique_append(
                    reasons,
                    details,
                    "UNEXPECTED_CASE",
                    f"{suite_name} contains non-canonical case IDs: {', '.join(canonical_unexpected)}",
                )
        duplicates = sorted({item for item in observed if observed.count(item) > 1})
        missing = sorted(set(expected) - set(observed))
        unexpected = sorted(set(observed) - set(expected))
        if missing:
            _unique_append(reasons, details, "MISSING_CASE", f"{suite_name} missing case IDs: {', '.join(missing)}")
        if unexpected:
            _unique_append(reasons, details, "UNEXPECTED_CASE", f"{suite_name} unexpected case IDs: {', '.join(unexpected)}")
        if duplicates:
            _unique_append(reasons, details, "DUPLICATE_CASE", f"{suite_name} duplicate case IDs: {', '.join(duplicates)}")
        if suite.get("case_ids") != observed:
            _unique_append(reasons, details, "CASE_INVENTORY_MISMATCH", f"{suite_name} suite and inventory IDs differ")
        if isinstance(case_ids, list) and pass_count == len(case_ids) and len(observed) != pass_count:
            _unique_append(reasons, details, "CASE_INVENTORY_MISMATCH", f"{suite_name} pass_count differs from observed IDs")
        if expected_count != len(expected):
            _unique_append(reasons, details, "CASE_INVENTORY_MISMATCH", f"{suite_name} expected_count differs from expected IDs")

    if _is_nonempty_text(evidence_snapshot):
        if any(snapshot != evidence_snapshot for snapshot in observed_snapshot_ids):
            _unique_append(reasons, details, "SNAPSHOT_MISMATCH", "suite evidence belongs to different snapshot")
    if len(set(observed_snapshot_ids)) > 1:
        _unique_append(reasons, details, "SNAPSHOT_MISMATCH", "mandatory suite snapshot IDs differ")

    if _is_nonempty_text(evidence_snapshot):
        try:
            expected_snapshot = build_snapshot_id(snapshot_identity(manifest))
        except (KeyError, TypeError):
            expected_snapshot = None
        if expected_snapshot is not None and evidence_snapshot != expected_snapshot:
            _unique_append(
                reasons,
                details,
                "SNAPSHOT_MISMATCH",
                "evidence snapshot_id does not match the complete release identity",
            )

    hard_gates = manifest["hard_gates"]
    if not isinstance(hard_gates, Mapping):
        _unique_append(reasons, details, "INVALID_MANIFEST", "hard_gates must be an object")
    else:
        violations = hard_gates.get("violations")
        if hard_gates.get("status") != "PASS" or not isinstance(violations, list) or violations:
            _unique_append(reasons, details, "HARD_GATE_FAILURE", "one or more hard gates failed")
        critical = hard_gates.get("critical_negative_markers")
        if not isinstance(critical, list):
            _unique_append(reasons, details, "INVALID_MANIFEST", "critical_negative_markers must be a list")
        elif critical:
            _unique_append(reasons, details, "CRITICAL_NEGATIVE", "critical negative markers are present")

    source = manifest["source_correctness"]
    if not isinstance(source, Mapping) or not isinstance(source.get("failures"), list):
        _unique_append(reasons, details, "INVALID_MANIFEST", "source_correctness is incomplete")
    elif source.get("status") != "PASS" or source.get("failures"):
        _unique_append(reasons, details, "SOURCE_CORRECTNESS_FAILURE", "source correctness is not PASS")

    host = manifest["runtime_host_acceptance"]
    if not isinstance(host, Mapping) or not isinstance(host.get("failures"), list):
        _unique_append(reasons, details, "INVALID_MANIFEST", "runtime_host_acceptance is incomplete")
    elif host.get("status") != "PASS" or host.get("identity_status") != "PASS" or host.get("failures"):
        _unique_append(reasons, details, "HOST_ACCEPTANCE_FAILURE", "runtime host acceptance is not PASS")

    final = manifest["final"]
    if (
        not isinstance(final, Mapping)
        or final.get("verdict") not in {"UNSET", "PASS", "HOLD"}
        or not isinstance(final.get("reasons"), list)
    ):
        _unique_append(reasons, details, "INVALID_MANIFEST", "final verdict/reasons shape is invalid")

    return tuple(reasons), tuple(details)


def validate_release_manifest(manifest: Any) -> tuple[str, ...]:
    """Return only structured reason codes; never return an optimistic status."""

    reasons, _ = _collect_issues(manifest)
    return reasons


def evaluate_release_manifest(manifest: Any) -> ReleaseDecision:
    """Evaluate every required input; no percentage or subsystem PASS can override a failure."""

    reasons, details = _collect_issues(manifest)
    return ReleaseDecision("PASS" if not reasons else "HOLD", reasons, details)


def load_release_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid release manifest: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("release manifest root must be an object")
    return value


def write_release_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
