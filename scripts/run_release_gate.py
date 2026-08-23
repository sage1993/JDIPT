"""Fail-closed local release gate orchestration for JDIPT."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from scripts.eval_suite import ordered_suite_case_ids

ROOT = Path(__file__).resolve().parents[1]
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
REPEAT_CASES = {37: 2}
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
            output_dir = ROOT / "regression-results" / "core-stability" / run_id / f"E{case_number:02d}-attempt{attempt}"
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
            if result.returncode != 0 or not _single_case_pass(result.output, case_number):
                failures.append(f"E{case_number:02d} attempt {attempt}: critical output did not pass")
    return GateResult("B: core stability", not failures, tuple(failures))


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
    return GateResult(
        f"C: full active Evals ({total})",
        passed,
        () if passed else ("full active regression acceptance did not pass",),
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


def orchestrate(
    *,
    mode: str = "deterministic",
    installed_skill_root: Path | None = None,
    codex: str | None = None,
    model: str | None = None,
    deterministic_fn: Callable[[], GateResult] | None = None,
    critical_fn: Callable[[], GateResult] | None = None,
    full_fn: Callable[[], GateResult] | None = None,
    package_fn: Callable[[], GateResult] | None = None,
) -> list[GateResult]:
    if mode not in {"deterministic", "critical", "full"}:
        raise ValueError(f"unknown release gate mode: {mode}")
    results: list[GateResult] = []
    gate_a = deterministic_fn() if deterministic_fn else deterministic_gate(installed_skill_root=installed_skill_root)
    results.append(gate_a)
    if not gate_a.passed or mode == "deterministic":
        return results

    gate_b = critical_fn() if critical_fn else critical_stability_gate(
        codex=codex,
        installed_skill_root=installed_skill_root,
        model=model,
    )
    results.append(gate_b)
    if not gate_b.passed or mode == "critical":
        return results

    gate_c = full_fn() if full_fn else full_regression_gate(
        codex=codex,
        installed_skill_root=installed_skill_root,
        model=model,
    )
    results.append(gate_c)
    if not gate_c.passed:
        return results
    results.append(package_fn() if package_fn else package_gate())
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run JDIPT release gates in fixed order.")
    parser.add_argument("--critical-only", action="store_true", help="Run Gate A then the Core stability suite only.")
    parser.add_argument("--full", action="store_true", help="Run Gate A, Core stability, Full active regression, and package gate.")
    parser.add_argument("--codex", default=None)
    parser.add_argument("--model", default=DEFAULT_REGRESSION_MODEL)
    parser.add_argument("--installed-skill-root", type=Path, default=None)
    args = parser.parse_args()
    mode = "full" if args.full else "critical" if args.critical_only else "deterministic"
    results = orchestrate(
        mode=mode,
        installed_skill_root=args.installed_skill_root,
        codex=args.codex,
        model=args.model,
    )
    for result in results:
        print(f"{result.name}: {'PASS' if result.passed else 'FAIL'}")
        for detail in result.details:
            print(f"  {detail}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
