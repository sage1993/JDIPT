"""Fail-closed local release gate orchestration for JDIPT."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_suite import ordered_suite_case_ids  # noqa: E402
from scripts.ansim_housing_oracle import (  # noqa: E402
    DEFAULT_ORACLE_PATH as ANSIM_ORACLE_PATH,
    EXPECTED_CASE_IDS as ANSIM_CASE_IDS,
)
from scripts.release_manifest import (  # noqa: E402
    EXPECTED_PLUGIN_ID,
    RELEASE_SCHEMA_VERSION,
    ReleaseDecision,
    build_changed_file_digest_manifest,
    build_runtime_manifest_digest,
    build_snapshot_id,
    digest_file,
    evaluate_release_manifest,
    load_release_manifest,
    repository_sha,
    write_release_manifest,
)

RUNNER = ROOT / "scripts" / "run_eval_suite.py"
LEGACY_RUNNER = ROOT / "run_jdipt_full_regression_v4.py"
AUTHORITY_TEMPORAL_VALIDATOR = ROOT / "scripts" / "validate_authority_temporal_contract.py"
PYTHON_FILES = [
    RUNNER,
    LEGACY_RUNNER,
    ROOT / "scripts" / "eval_suite.py",
    ROOT / "scripts" / "regression_checks.py",
    ROOT / "scripts" / "regression_oracles.py",
    ROOT / "scripts" / "plugin_integrity.py",
    ROOT / "scripts" / "run_release_gate.py",
    AUTHORITY_TEMPORAL_VALIDATOR,
]
CRITICAL_CASES = tuple(ordered_suite_case_ids("core"))
FULL_CASES = tuple(ordered_suite_case_ids("full"))
REPEAT_CASES = {37: 2, 44: 3, 45: 3}
MAX_ENVIRONMENT_RETRIES = 2
DEFAULT_REGRESSION_MODEL = "gpt-5.6-luna"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    details: tuple[str, ...] = ()
    suite: str | None = None
    case_ids: tuple[str, ...] = ()
    hard_gate_violations: tuple[str, ...] = ()
    critical_negative_markers: tuple[str, ...] = ()


def run_command(command: Sequence[str], *, cwd: Path = ROOT) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return CommandResult(completed.returncode, (completed.stdout or "") + (completed.stderr or ""))


def _command_gate(
    name: str,
    commands: list[list[str]],
    command_runner: Callable[[Sequence[str]], CommandResult],
) -> GateResult:
    failures: list[str] = []
    for command in commands:
        result = command_runner(command)
        if result.returncode != 0:
            failures.append(f"{' '.join(command)}: exit {result.returncode}")
    return GateResult(name, not failures, tuple(failures))


def deterministic_gate(
    *,
    installed_skill_root: Path | None = None,
    command_runner: Callable[[Sequence[str]], CommandResult] = run_command,
) -> GateResult:
    commands = [
        [sys.executable, str(ROOT / "scripts" / "validate_repo.py")],
        [sys.executable, str(AUTHORITY_TEMPORAL_VALIDATOR)],
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "compileall", "-q", str(ROOT / "scripts"), str(ROOT / "tests")],
        *[[sys.executable, "-m", "py_compile", str(path)] for path in PYTHON_FILES],
        ["git", "diff", "--check"],
    ]
    if installed_skill_root is not None:
        commands.append([
            sys.executable,
            str(ROOT / "scripts" / "plugin_integrity.py"),
            "--repo-root",
            str(ROOT),
            "--installed-root",
            str(installed_skill_root),
        ])
    else:
        commands.append([sys.executable, str(ROOT / "scripts" / "plugin_integrity.py"), "--repo-root", str(ROOT)])
    return _command_gate("A: deterministic", commands, command_runner)


def _runner_command(
    *,
    codex: str | None,
    installed_skill_root: Path | None,
    from_case: int | None = None,
    to_case: int | None = None,
    output_dir: Path | None = None,
    model: str | None = None,
    suite: str = "full",
    repetitions: int | None = None,
) -> list[str]:
    command = [sys.executable, str(RUNNER), "--suite", suite]
    if codex:
        command.extend(["--codex", codex])
    if model:
        command.extend(["--model", model])
    if installed_skill_root:
        command.extend(["--installed-skill-root", str(installed_skill_root)])
    if from_case is not None:
        command.extend(["--from-case", str(from_case)])
    if to_case is not None:
        command.extend(["--to-case", str(to_case)])
    if output_dir is not None:
        command.extend(["--output-dir", str(output_dir)])
    if repetitions is not None:
        command.extend(["--repetitions", str(repetitions)])
    return command


def _single_case_pass(output: str, case_number: int) -> bool:
    h1_pattern = r"h1=SKIP_SPECIAL_FORMAT" if case_number in {2, 3} else r"h1=PASS"
    expected = (
        r"process_ok:\s*1/1",
        r"environment_errors:\s*0/1",
        h1_pattern,
        r"hygiene_pass:\s*1/1",
        r"incomplete_url_pass:\s*1/1",
        r"contract_oracle_pass:\s*1/1",
    )
    return all(re.search(pattern, output) for pattern in expected)


def _single_case_environment_error(output: str) -> bool:
    return bool(re.search(r"environment_errors:\s*1/1", output))


def _observed_eval_case_ids(output: str) -> tuple[str, ...]:
    observed = re.findall(r"\[\s*\d+\s*/\s*\d+\s*\]\s+(E\d{2})\b", output)
    if observed:
        return tuple(observed)
    cases_line = re.search(r"^Cases:\s*(.+)$", output, flags=re.MULTILINE)
    if not cases_line:
        return ()
    return tuple(re.findall(r"\bE\d{2}\b", cases_line.group(1)))


def _observed_ansim_case_ids(output: str) -> tuple[str, ...]:
    cases_line = re.search(r"^observed_case_ids:\s*(.*)$", output, flags=re.MULTILINE)
    if not cases_line:
        return ()
    return tuple(re.findall(r"\bASH-\d{2}\b", cases_line.group(1)))


def critical_stability_gate(
    *,
    codex: str | None = None,
    installed_skill_root: Path | None = None,
    model: str | None = None,
    command_runner: Callable[[Sequence[str]], CommandResult] = run_command,
) -> GateResult:
    failures: list[str] = []
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    for case_number in CRITICAL_CASES:
        for attempt in range(1, REPEAT_CASES.get(case_number, 1) + 1):
            env_retry = 0
            while True:
                suffix = f"E{case_number:02d}-attempt{attempt}"
                if env_retry:
                    suffix += f"-envretry{env_retry}"
                output_dir = ROOT / "regression-results" / "core-stability" / run_id / suffix
                result = command_runner(
                    _runner_command(
                        codex=codex,
                        installed_skill_root=installed_skill_root,
                        from_case=case_number,
                        to_case=case_number,
                        output_dir=output_dir,
                        model=model,
                        suite="core",
                    )
                )
                if _single_case_environment_error(result.output):
                    if env_retry < MAX_ENVIRONMENT_RETRIES:
                        env_retry += 1
                        continue
                    failures.append(
                        f"E{case_number:02d} attempt {attempt}: environment retries exhausted"
                    )
                    break
                if result.returncode != 0 or not _single_case_pass(result.output, case_number):
                    failures.append(f"E{case_number:02d} attempt {attempt}: critical output did not pass")
                break
    return GateResult(
        "C: core stability",
        not failures,
        tuple(failures),
        suite="stability",
        case_ids=tuple(f"E{case_number:02d}" for case_number in CRITICAL_CASES),
    )


def core_regression_gate(
    *,
    codex: str | None = None,
    installed_skill_root: Path | None = None,
    model: str | None = None,
    command_runner: Callable[[Sequence[str]], CommandResult] = run_command,
) -> GateResult:
    """Run the complete Core suite once and retain its case identity."""

    result = command_runner(
        _runner_command(
            codex=codex,
            installed_skill_root=installed_skill_root,
            model=model,
            suite="core",
        )
    )
    total = len(CRITICAL_CASES)
    h1_expected = total - len({2, 3} & set(CRITICAL_CASES))
    required = (
        rf"process_ok:\s*{total}/{total}",
        rf"environment_errors:\s*0/{total}",
        rf"h1_pass:\s*{h1_expected}/{total}",
        rf"hygiene_pass:\s*{total}/{total}",
        rf"incomplete_url_pass:\s*{total}/{total}",
        rf"contract_oracle_pass:\s*{total}/{total}",
    )
    passed = result.returncode == 0 and all(re.search(pattern, result.output) for pattern in required)
    observed_case_ids = _observed_eval_case_ids(result.output)
    return GateResult(
        "B: core active Evals",
        passed,
        () if passed else ("core active regression acceptance did not pass",),
        suite="core",
        case_ids=observed_case_ids,
    )


def full_regression_gate(
    *,
    codex: str | None = None,
    installed_skill_root: Path | None = None,
    model: str | None = None,
    command_runner: Callable[[Sequence[str]], CommandResult] = run_command,
) -> GateResult:
    result = command_runner(
        _runner_command(
            codex=codex,
            installed_skill_root=installed_skill_root,
            model=model,
            suite="full",
        )
    )
    total = len(FULL_CASES)
    h1_expected = total - len({2, 3} & set(FULL_CASES))
    required = (
        rf"process_ok:\s*{total}/{total}",
        rf"environment_errors:\s*0/{total}",
        rf"h1_pass:\s*{h1_expected}/{total}",
        rf"hygiene_pass:\s*{total}/{total}",
        rf"incomplete_url_pass:\s*{total}/{total}",
        rf"contract_oracle_pass:\s*{total}/{total}",
    )
    passed = result.returncode == 0 and all(re.search(pattern, result.output) for pattern in required)
    observed_case_ids = _observed_eval_case_ids(result.output)
    return GateResult(
        f"D: full active Evals ({total})",
        passed,
        () if passed else ("full active regression acceptance did not pass",),
        suite="full",
        case_ids=observed_case_ids,
    )



def ansim_regression_gate(
    *,
    repetitions: int,
    codex: str | None = None,
    installed_skill_root: Path | None = None,
    model: str | None = None,
    command_runner: Callable[[Sequence[str]], CommandResult] = run_command,
) -> GateResult:
    total = 9 if repetitions == 1 else 27
    minimum_pass = 9 if repetitions == 1 else 26
    result = command_runner(
        _runner_command(
            codex=codex,
            installed_skill_root=installed_skill_root,
            model=model,
            suite="ansim",
            repetitions=repetitions,
        )
    )
    required = (
        rf"process_ok:\s*{total}/{total}",
        rf"contract_oracle_pass:\s*(?:{total}|{minimum_pass})/{total}",
        r"critical_negative_markers:\s*0",
        r"suite_verdict:\s*PASS",
    )
    passed = result.returncode == 0 and all(re.search(pattern, result.output) for pattern in required)
    marker_count = re.search(r"critical_negative_markers:\s*(\d+)", result.output)
    critical_markers = (
        ("ANSIM_CRITICAL_NEGATIVE_MARKER",)
        if marker_count and int(marker_count.group(1)) > 0
        else ()
    )
    observed_case_ids = _observed_ansim_case_ids(result.output)
    return GateResult(
        f"Ansim housing {'core' if repetitions == 1 else 'stability'}",
        passed,
        () if passed else ("ansim regression acceptance did not pass",),
        suite="ansim",
        case_ids=observed_case_ids,
        critical_negative_markers=critical_markers,
    )


def package_gate(command_runner: Callable[[Sequence[str]], CommandResult] = run_command) -> GateResult:
    commands = [
        ["npm", "ci"],
        ["npm", "audit", "--omit=dev"],
        ["npm", "run", "mcp", "--", "--help"],
        ["git", "diff", "--check"],
        ["git", "status", "--short"],
    ]
    return _command_gate("D: package/static", commands, command_runner)


def _plugin_descriptor(root: Path | None) -> dict[str, Any]:
    if root is None:
        return {}
    resolved = root.expanduser().resolve()
    candidates = (
        resolved / ".codex-plugin" / "plugin.json",
        resolved.parent / ".codex-plugin" / "plugin.json",
        resolved.parent.parent / ".codex-plugin" / "plugin.json",
    )
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            value = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}
    return {}


def _runtime_identity(root: Path | None, *, fallback_plugin_id: str) -> dict[str, Any]:
    descriptor = _plugin_descriptor(root)
    if root is None or not root.expanduser().resolve().exists():
        return {
            "plugin_id": "UNRESOLVED",
            "plugin_version": "UNRESOLVED",
            "source_path": str(root) if root is not None else "UNRESOLVED",
            "runtime_digest": "0" * 64,
            "identity_status": "FAIL",
        }
    plugin_id = descriptor.get("id") or fallback_plugin_id
    plugin_version = descriptor.get("version") or "UNRESOLVED"
    return {
        "plugin_id": str(plugin_id),
        "plugin_version": str(plugin_version),
        "source_path": str(root.expanduser().resolve()),
        "runtime_digest": build_runtime_manifest_digest(root),
        "identity_status": "PASS",
    }


def _suite_expectations() -> dict[str, list[str]]:
    return {
        "core": [f"E{case_id:02d}" for case_id in CRITICAL_CASES],
        "full": [f"E{case_id:02d}" for case_id in FULL_CASES],
        "ansim": list(ANSIM_CASE_IDS),
        "stability": [f"E{case_id:02d}" for case_id in CRITICAL_CASES],
    }


def build_release_manifest(
    results: Sequence[GateResult],
    *,
    installed_skill_root: Path | None,
    active_runtime_root: Path | None,
    oracle_path: Path = ANSIM_ORACLE_PATH,
    mode: str,
) -> dict[str, Any]:
    """Convert component evidence into one manifest before authority evaluation."""

    from scripts.plugin_integrity import compare_runtime_manifests, resolve_installed_skill_root

    if installed_skill_root is None:
        installed_skill_root = resolve_installed_skill_root()
    installed_identity = _runtime_identity(
        installed_skill_root,
        fallback_plugin_id=EXPECTED_PLUGIN_ID,
    )
    installed_mismatches = (
        compare_runtime_manifests(ROOT, installed_skill_root)
        if installed_skill_root is not None and installed_skill_root.exists()
        else ["installed runtime root could not be resolved"]
    )
    installed = {
        "plugin_version": installed_identity["plugin_version"],
        "plugin_id": installed_identity["plugin_id"],
        "manifest_digest": installed_identity["runtime_digest"],
        "integrity_status": "PASS" if not installed_mismatches else "FAIL",
        "mismatches": installed_mismatches,
    }
    active_identity = _runtime_identity(
        active_runtime_root,
        fallback_plugin_id=installed.get("plugin_id", EXPECTED_PLUGIN_ID),
    )
    active_matches_installed = (
        installed["integrity_status"] == "PASS"
        and active_identity["identity_status"] == "PASS"
        and active_identity["plugin_id"] == installed["plugin_id"]
        and active_identity["runtime_digest"] == installed["manifest_digest"]
    )
    active = {
        key: value
        for key, value in active_identity.items()
        if key in {"plugin_id", "source_path", "runtime_digest", "identity_status"}
    }
    active["identity_status"] = "PASS" if active_matches_installed else "FAIL"

    try:
        oracle_value = json.loads(oracle_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        oracle_value = {}
    oracle = {
        "version": str(oracle_value.get("contract", "UNRESOLVED")),
        "digest": digest_file(oracle_path) if oracle_path.is_file() else "0" * 64,
        "source_path": str(oracle_path.resolve()),
    }

    suite_results: dict[str, list[GateResult]] = {}
    for result in results:
        if result.suite:
            suite_results.setdefault(result.suite, []).append(result)
    expectations = _suite_expectations()
    suites: dict[str, dict[str, Any]] = {}
    case_inventory: dict[str, dict[str, list[str]]] = {}
    for suite_name, expected in expectations.items():
        candidates = suite_results.get(suite_name, [])
        result = candidates[0] if len(candidates) == 1 else None
        observed = [case_id for candidate in candidates for case_id in candidate.case_ids]
        if len(candidates) > 1:
            status = "FAIL"
        else:
            status = "PASS" if result and result.passed else "FAIL" if result else "NOT_RUN"
        suites[suite_name] = {
            "status": status,
            "snapshot_id": "UNSET",
            "case_ids": observed,
            "pass_count": len(observed) if result and result.passed else 0,
            "expected_count": len(expected),
        }
        case_inventory[suite_name] = {"expected": expected, "observed": observed}

    deterministic = next((result for result in results if result.name.startswith("A:")), None)
    package = next((result for result in results if result.name == "D: package/static"), None)
    base_status = "PASS" if deterministic and deterministic.passed else "FAIL" if deterministic else "NOT_RUN"
    package_status = "PASS" if package and package.passed else "FAIL" if package else "NOT_RUN"
    static_validation = {
        "pytest": base_status,
        "validate_repo": base_status,
        "authority_temporal": base_status,
        "compileall": base_status,
        "npm_ci": package_status,
        "npm_audit": package_status,
        "plugin_integrity": base_status,
        "diff_check": base_status if package is None else package_status,
    }

    hard_gate_violations = [
        marker
        for result in results
        for marker in result.hard_gate_violations
    ]
    critical_markers = [
        marker
        for result in results
        for marker in result.critical_negative_markers
    ]
    suite_failures = [
        detail
        for result in results
        if result.suite
        and not result.passed
        for detail in result.details
    ]
    source_failures = list(deterministic.details) if deterministic and not deterministic.passed else []
    host_failures = list(suite_failures)
    if not active_matches_installed:
        host_failures.append("active runtime does not match installed runtime identity")
    all_suites_pass = all(value["status"] == "PASS" for value in suites.values())

    manifest: dict[str, Any] = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "repository": {
            "sha": repository_sha(ROOT),
            "dirty": bool(build_changed_file_digest_manifest(ROOT)),
            "changed_file_digest_manifest": build_changed_file_digest_manifest(ROOT),
        },
        "installed": installed,
        "active_runtime": active,
        "oracle": oracle,
        "static_validation": static_validation,
        "suites": suites,
        "hard_gates": {
            "status": "PASS" if not hard_gate_violations else "FAIL",
            "violations": hard_gate_violations,
            "critical_negative_markers": critical_markers,
        },
        "source_correctness": {
            "status": "PASS" if not source_failures else "FAIL",
            "failures": source_failures,
        },
        "runtime_host_acceptance": {
            "status": "PASS" if mode == "full" and all_suites_pass and not host_failures else "FAIL",
            "identity_status": "PASS" if active_matches_installed else "FAIL",
            "failures": host_failures,
        },
        "case_inventory": case_inventory,
        "evidence": {
            "generated_at": datetime.now().astimezone().isoformat(),
            "snapshot_id": "UNSET",
        },
        "final": {"verdict": "UNSET", "reasons": []},
    }
    snapshot_id = build_snapshot_id(
        {
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
    )
    manifest["evidence"]["snapshot_id"] = snapshot_id
    for suite in manifest["suites"].values():
        suite["snapshot_id"] = snapshot_id
    decision = authoritative_release_gate(manifest)
    manifest["final"] = {
        "verdict": decision.verdict,
        "reasons": list(decision.reasons),
        "details": list(decision.details),
    }
    return manifest


def authoritative_release_gate(manifest: dict[str, Any]) -> ReleaseDecision:
    """The sole final PASS/HOLD authority for a release manifest."""

    return evaluate_release_manifest(manifest)


def orchestrate(
    *,
    mode: str = "deterministic",
    installed_skill_root: Path | None = None,
    codex: str | None = None,
    model: str | None = None,
    deterministic_fn: Callable[[], GateResult] | None = None,
    core_fn: Callable[[], GateResult] | None = None,
    critical_fn: Callable[[], GateResult] | None = None,
    full_fn: Callable[[], GateResult] | None = None,
    ansim_fn: Callable[[], GateResult] | None = None,
    package_fn: Callable[[], GateResult] | None = None,
) -> list[GateResult]:
    if mode not in {"deterministic", "critical", "full"}:
        raise ValueError(f"unknown release gate mode: {mode}")
    results: list[GateResult] = []
    gate_a = deterministic_fn() if deterministic_fn else deterministic_gate(installed_skill_root=installed_skill_root)
    results.append(gate_a)
    if not gate_a.passed or mode == "deterministic":
        return results

    gate_core = core_fn() if core_fn else core_regression_gate(
        codex=codex,
        installed_skill_root=installed_skill_root,
        model=model,
    )
    results.append(gate_core)
    if not gate_core.passed:
        return results

    gate_stability = critical_fn() if critical_fn else critical_stability_gate(
        codex=codex,
        installed_skill_root=installed_skill_root,
        model=model,
    )
    results.append(gate_stability)
    if not gate_stability.passed or mode == "critical":
        return results

    gate_full = full_fn() if full_fn else full_regression_gate(
        codex=codex,
        installed_skill_root=installed_skill_root,
        model=model,
    )
    results.append(gate_full)
    if not gate_full.passed:
        return results

    gate_ansim = ansim_fn() if ansim_fn else ansim_regression_gate(
        repetitions=1,
        codex=codex,
        installed_skill_root=installed_skill_root,
        model=model,
    )
    results.append(gate_ansim)
    if not gate_ansim.passed:
        return results

    results.append(package_fn() if package_fn else package_gate())
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run JDIPT release gates in fixed order.")
    parser.add_argument("--critical-only", action="store_true", help="Run static, Core, and Core stability evidence; final release remains HOLD until all suites are present.")
    parser.add_argument("--full", action="store_true", help="Run every mandatory suite and evaluate one authoritative release manifest.")
    parser.add_argument("--manifest", type=Path, default=None, help="Evaluate an existing release manifest without rerunning suites.")
    parser.add_argument("--manifest-output", type=Path, default=None, help="Write the generated release manifest to this path.")
    parser.add_argument("--codex", default=None)
    parser.add_argument("--model", default=DEFAULT_REGRESSION_MODEL)
    parser.add_argument(
        "--installed-skill-root",
        "--installed-root",
        dest="installed_skill_root",
        type=Path,
        default=None,
    )
    parser.add_argument("--active-runtime-root", type=Path, default=None)
    parser.add_argument("--oracle-path", type=Path, default=ANSIM_ORACLE_PATH)
    args = parser.parse_args()

    if args.manifest is not None:
        try:
            manifest = load_release_manifest(args.manifest)
        except ValueError as exc:
            decision = ReleaseDecision("HOLD", ("INVALID_MANIFEST",), (str(exc),))
            print(json.dumps({"authoritative_release": decision.as_dict()}, ensure_ascii=False, indent=2))
            return 1
        decision = authoritative_release_gate(manifest)
        output = {"authoritative_release": decision.as_dict(), "manifest": manifest}
        if args.manifest_output is not None:
            write_release_manifest(args.manifest_output, manifest)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if decision.verdict == "PASS" else 1

    mode = "full" if args.full else "critical" if args.critical_only else "deterministic"
    results = orchestrate(
        mode=mode,
        installed_skill_root=args.installed_skill_root,
        codex=args.codex,
        model=args.model,
    )
    manifest = build_release_manifest(
        results,
        installed_skill_root=args.installed_skill_root,
        active_runtime_root=args.active_runtime_root,
        oracle_path=args.oracle_path,
        mode=mode,
    )
    if args.manifest_output is not None:
        write_release_manifest(args.manifest_output, manifest)
    decision = authoritative_release_gate(manifest)
    print(json.dumps({"authoritative_release": decision.as_dict(), "manifest": manifest}, ensure_ascii=False, indent=2))
    return 0 if decision.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
