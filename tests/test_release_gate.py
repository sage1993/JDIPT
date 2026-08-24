from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

from scripts.run_release_gate import (
    CRITICAL_CASES,
    FULL_CASES,
    REPEAT_CASES,
    CommandResult,
    GateResult,
    _single_case_pass,
    critical_stability_gate,
    orchestrate,
)


def _case_output(h1: str) -> str:
    return (
        "process_ok: 1/1\n"
        "environment_errors: 0/1\n"
        f"  process=OK h1={h1} hygiene=PASS url=PASS\n"
        "hygiene_pass: 1/1\n"
        "incomplete_url_pass: 1/1\n"
        "contract_oracle_pass: 1/1\n"
    )


def test_regression_runner_stdout_is_utf8_safe_when_captured():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp949"
    result = subprocess.run(
        [sys.executable, "-c", "import run_jdipt_full_regression_v4; print('—')"],
        cwd=root,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "—" in result.stdout


def test_runner_command_propagates_explicit_model_and_suite():
    from scripts.run_release_gate import _runner_command

    command = _runner_command(
        codex="codex",
        installed_skill_root=None,
        model="gpt-5.6-sol",
        suite="core",
    )

    assert command[command.index("--model") + 1] == "gpt-5.6-sol"
    assert command[command.index("--suite") + 1] == "core"


def test_suite_sizes_are_reduced_and_core_is_subset():
    assert len(CRITICAL_CASES) == 14
    assert len(FULL_CASES) == 26
    assert set(CRITICAL_CASES) <= set(FULL_CASES)


def test_release_critical_instability_cases_have_required_repeats():
    assert REPEAT_CASES == {37: 2, 44: 3, 45: 3}


def test_critical_case_requires_h1_pass_except_special_cases():
    assert _single_case_pass(_case_output("PASS"), 36)
    assert _single_case_pass(_case_output("SKIP_SPECIAL_FORMAT"), 2)
    assert not _single_case_pass(_case_output("FAIL"), 36)
    assert not _single_case_pass(_case_output("PASS"), 2)


def passing(name: str) -> GateResult:
    return GateResult(name, True)


def failing(name: str) -> GateResult:
    return GateResult(name, False, ("failure",))


def test_critical_attempts_use_unique_output_directories():
    commands: list[list[str]] = []

    def runner(command):
        command = list(command)
        commands.append(command)
        case = int(command[command.index("--from-case") + 1])
        h1 = "SKIP_SPECIAL_FORMAT" if case in {2, 3} else "PASS"
        return CommandResult(0, _case_output(h1))

    result = critical_stability_gate(command_runner=runner)

    assert result.passed
    output_dirs = [command[command.index("--output-dir") + 1] for command in commands]
    expected_attempts = sum(REPEAT_CASES.get(case, 1) for case in CRITICAL_CASES)
    assert len(output_dirs) == expected_attempts
    assert len(set(output_dirs)) == expected_attempts
    assert expected_attempts == 19


def test_gate_a_failure_stops_before_critical_and_full():
    calls: list[str] = []
    results = orchestrate(
        mode="full",
        deterministic_fn=lambda: (calls.append("A") or failing("A")),
        critical_fn=lambda: (calls.append("B") or passing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
    )

    assert calls == ["A"]
    assert [result.name for result in results] == ["A"]


def test_gate_b_failure_stops_before_full():
    calls: list[str] = []
    results = orchestrate(
        mode="full",
        deterministic_fn=lambda: (calls.append("A") or passing("A")),
        critical_fn=lambda: (calls.append("B") or failing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
    )

    assert calls == ["A", "B"]
    assert [result.name for result in results] == ["A", "B"]


def test_full_mode_runs_full_regression_exactly_once_after_a_and_b():
    calls: list[str] = []
    results = orchestrate(
        mode="full",
        deterministic_fn=lambda: (calls.append("A") or passing("A")),
        critical_fn=lambda: (calls.append("B") or passing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
        package_fn=lambda: (calls.append("D") or passing("D")),
    )

    assert calls == ["A", "B", "C", "D"]
    assert [result.name for result in results] == ["A", "B", "C", "D"]


def test_critical_mode_never_runs_full_regression():
    calls: list[str] = []
    results = orchestrate(
        mode="critical",
        deterministic_fn=lambda: (calls.append("A") or passing("A")),
        critical_fn=lambda: (calls.append("B") or passing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
    )

    assert calls == ["A", "B"]
    assert [result.name for result in results] == ["A", "B"]
