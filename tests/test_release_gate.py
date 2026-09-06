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
    ansim_regression_gate,
    _observed_ansim_case_ids,
    _observed_eval_case_ids,
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


def _environment_error_output() -> str:
    return (
        "process_ok: 0/1\n"
        "environment_errors: 1/1\n"
        "  process=ENV_ERROR h1=FAIL hygiene=FAIL url=PASS\n"
        "hygiene_pass: 0/1\n"
        "incomplete_url_pass: 1/1\n"
        "contract_oracle_pass: 0/1\n"
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


def test_observed_case_identity_is_parsed_from_runner_output():
    output = "Cases: E02, E03, E03\n"

    assert _observed_eval_case_ids(output) == ("E02", "E03", "E03")
    assert _observed_ansim_case_ids("observed_case_ids: ASH-01,ASH-02,ASH-02\n") == (
        "ASH-01",
        "ASH-02",
        "ASH-02",
    )


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


def test_environment_error_is_retried_without_consuming_behavior_attempt():
    calls: list[list[str]] = []
    failed_once = False

    def runner(command):
        nonlocal failed_once
        command = list(command)
        calls.append(command)
        case = int(command[command.index("--from-case") + 1])
        if case == 45 and not failed_once:
            failed_once = True
            return CommandResult(3, _environment_error_output())
        h1 = "SKIP_SPECIAL_FORMAT" if case in {2, 3} else "PASS"
        return CommandResult(0, _case_output(h1))

    result = critical_stability_gate(command_runner=runner)

    assert result.passed
    e45_commands = [
        command for command in calls
        if int(command[command.index("--from-case") + 1]) == 45
    ]
    assert len(e45_commands) == REPEAT_CASES[45] + 1
    assert any("envretry1" in command[command.index("--output-dir") + 1] for command in e45_commands)


def test_persistent_environment_error_fails_closed():
    def runner(command):
        command = list(command)
        case = int(command[command.index("--from-case") + 1])
        if case == 45:
            return CommandResult(3, _environment_error_output())
        h1 = "SKIP_SPECIAL_FORMAT" if case in {2, 3} else "PASS"
        return CommandResult(0, _case_output(h1))

    result = critical_stability_gate(command_runner=runner)

    assert not result.passed
    assert any("E45 attempt 1" in detail and "environment" in detail for detail in result.details)


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
        core_fn=lambda: (calls.append("core") or passing("core")),
        critical_fn=lambda: (calls.append("B") or failing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
    )

    assert calls == ["A", "core", "B"]
    assert [result.name for result in results] == ["A", "core", "B"]


def test_ansim_core_gate_requires_9_of_9_and_zero_critical_markers():
    def runner(command):
        assert command[command.index("--suite") + 1] == "ansim"
        assert command[command.index("--repetitions") + 1] == "1"
        return CommandResult(
            0,
            "process_ok: 9/9\ncontract_oracle_pass: 9/9\ncritical_negative_markers: 0\nsuite_verdict: PASS\n",
        )

    assert ansim_regression_gate(repetitions=1, command_runner=runner).passed


def test_ansim_stability_gate_allows_one_noncritical_failure():
    def runner(command):
        return CommandResult(
            0,
            "process_ok: 27/27\ncontract_oracle_pass: 26/27\ncritical_negative_markers: 0\nsuite_verdict: PASS\n",
        )

    assert ansim_regression_gate(repetitions=3, command_runner=runner).passed


def test_ansim_stability_gate_fails_on_any_critical_marker():
    def runner(command):
        return CommandResult(
            1,
            "process_ok: 27/27\ncontract_oracle_pass: 26/27\ncritical_negative_markers: 1\nsuite_verdict: FAIL\n",
        )

    result = ansim_regression_gate(repetitions=3, command_runner=runner)

    assert not result.passed
    assert result.details == ("ansim regression acceptance did not pass",)



def test_full_mode_runs_full_regression_exactly_once_after_a_and_b():
    calls: list[str] = []
    results = orchestrate(
        mode="full",
        deterministic_fn=lambda: (calls.append("A") or passing("A")),
        core_fn=lambda: (calls.append("core") or passing("core")),
        critical_fn=lambda: (calls.append("B") or passing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
        ansim_fn=lambda: (calls.append("ansim") or passing("ansim")),
        package_fn=lambda: (calls.append("D") or passing("D")),
    )

    assert calls == ["A", "core", "B", "C", "ansim", "D"]
    assert [result.name for result in results] == ["A", "core", "B", "C", "ansim", "D"]


def test_full_mode_runs_every_mandatory_suite_before_package_gate():
    calls: list[str] = []
    results = orchestrate(
        mode="full",
        deterministic_fn=lambda: (calls.append("static") or passing("static")),
        core_fn=lambda: (calls.append("core") or passing("core")),
        critical_fn=lambda: (calls.append("stability") or passing("stability")),
        full_fn=lambda: (calls.append("full") or passing("full")),
        ansim_fn=lambda: (calls.append("ansim") or passing("ansim")),
        package_fn=lambda: (calls.append("package") or passing("package")),
    )

    assert calls == ["static", "core", "stability", "full", "ansim", "package"]
    assert [result.name for result in results] == [
        "static",
        "core",
        "stability",
        "full",
        "ansim",
        "package",
    ]


def test_critical_mode_never_runs_full_regression():
    calls: list[str] = []
    results = orchestrate(
        mode="critical",
        deterministic_fn=lambda: (calls.append("A") or passing("A")),
        core_fn=lambda: (calls.append("core") or passing("core")),
        critical_fn=lambda: (calls.append("B") or passing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
    )

    assert calls == ["A", "core", "B"]
    assert [result.name for result in results] == ["A", "core", "B"]
