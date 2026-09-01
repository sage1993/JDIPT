from __future__ import annotations

import sys
from pathlib import Path

from run_jdipt_full_regression_v4 import Case, run_case


def test_run_case_log_records_child_lifecycle_and_artifact_state(tmp_path: Path):
    child = tmp_path / "fake_codex.py"
    child.write_text(
        "import pathlib, sys\n"
        "args = sys.argv[1:]\n"
        "out = pathlib.Path(args[args.index('--output-last-message') + 1])\n"
        "out.write_text('# 1. 질의요지\\n# 2. 검토결론\\n# 3. 검토이유\\n# 4. 관련 법령 및 자료\\n', encoding='utf-8')\n"
        "print('child completed')\n",
        encoding="utf-8",
    )
    case = Case(1, "diagnostic", "probe", "", "fixture")
    (tmp_path / "out").mkdir()

    result = run_case(
        tmp_path,
        tmp_path / "out",
        case,
        30,
        [sys.executable, str(child)],
        "test-model",
        False,
    )

    log = (tmp_path / "out" / "E01.log.txt").read_text(encoding="utf-8")
    assert result.process_ok
    assert "PID: " in log
    assert "SPAWNED_AT_UTC: " in log
    assert "ANSWER_FILE_EXISTS: True" in log
    assert "KILLED: False" in log
    assert "STDIN: DEVNULL" in log
    assert "=== STDOUT TAIL ===" in log
    assert "child completed" in log


def test_run_case_timeout_kills_child_and_records_reason(tmp_path: Path):
    child = tmp_path / "slow_codex.py"
    child.write_text(
        "import pathlib, sys, time\n"
        "args = sys.argv[1:]\n"
        "out = pathlib.Path(args[args.index('--output-last-message') + 1])\n"
        "print('child started', flush=True)\n"
        "time.sleep(30)\n"
        "out.write_text('late answer', encoding='utf-8')\n",
        encoding="utf-8",
    )
    case = Case(1, "slow diagnostic", "probe", "", "fixture")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = run_case(
        tmp_path,
        out_dir,
        case,
        1,
        [sys.executable, str(child)],
        "test-model",
        False,
    )

    log = (out_dir / "E01.log.txt").read_text(encoding="utf-8")
    assert result.timeout
    assert result.returncode is not None
    assert "TIMEOUT: True" in log
    assert "KILLED: True" in log
    assert "TIMEOUT_REASON: timeout after 1s" in log
    assert "child started" in log
