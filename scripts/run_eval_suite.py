"""Run consolidated JDIPT Core/Full/Legacy evaluation suites."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ansim_housing_oracle import DEFAULT_ORACLE_PATH as ANSIM_ORACLE_PATH, build_ansim_summary, evaluate_ansim_case, load_ansim_oracle  # noqa: E402
import run_jdipt_full_regression_v4 as legacy  # noqa: E402
from scripts.eval_suite import ordered_suite_case_ids  # noqa: E402
from scripts.regression_checks import detect_environment_error  # noqa: E402

REQUIRED_PLUGIN_ID = "jdipt@sage1993"
legacy.REQUIRED_PLUGIN_ID = REQUIRED_PLUGIN_ID

EVAL_DIR = ROOT / "skills" / "law-interpretation-request" / "evals"
CATALOG_FILES = (
    EVAL_DIR / "scenarios.md",
    EVAL_DIR / "v0.2.2-regressions.md",
    EVAL_DIR / "v0.2.3-authority-temporal-evidence.md",
)
DEFAULT_MODEL = legacy.DEFAULT_REGRESSION_MODEL


def load_catalog() -> dict[int, legacy.Case]:
    missing = [str(path) for path in CATALOG_FILES if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing eval file(s): {', '.join(missing)}")

    by_number: dict[int, legacy.Case] = {}
    for source in CATALOG_FILES:
        for case in legacy.parse_cases(source):
            if case.number in by_number:
                raise SystemExit(f"Duplicate eval case E{case.number:02d}: {source}")
            by_number[case.number] = case

    expected = set(range(1, 47))
    actual = set(by_number)
    if actual != expected:
        missing_ids = sorted(expected - actual)
        extras = sorted(actual - expected)
        raise SystemExit(f"Eval catalog must be E01-E46; missing={missing_ids} extras={extras}")
    return by_number


def load_ansim_catalog() -> dict[str, legacy.Case]:
    oracle = load_ansim_oracle(ANSIM_ORACLE_PATH)
    return {
        case["id"]: legacy.Case(
            number=index,
            title=f'{case["id"]} {case["severity"]}',
            prompt=case["prompt"],
            expected="; ".join(case.get("must", []) + case.get("must_markers", [])),
            source_file=ANSIM_ORACLE_PATH.as_posix(),
        )
        for index, case in enumerate(oracle["cases"], start=1)
    }


def ansim_attempt_plan(repetitions: int) -> list[tuple[str, int]]:
    if repetitions not in {1, 3}:
        raise ValueError("repetitions must be 1 or 3")
    return [(case_id, attempt) for case_id in load_ansim_catalog() for attempt in range(1, repetitions + 1)]



def execute_ansim_attempts(
    out_dir: Path,
    catalog: dict[str, legacy.Case],
    *,
    repetitions: int,
    run_case,
    evaluate,
) -> list[dict]:
    results: list[dict] = []
    for case_id, attempt in ansim_attempt_plan(repetitions):
        attempt_dir = out_dir / case_id / f"run-{attempt:02d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        raw = run_case(attempt_dir, catalog[case_id])
        answer_path = attempt_dir / raw.answer_file
        answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
        evaluated = evaluate(case_id, answer, raw.process_ok)
        evaluated.update(
            {
                "attempt": attempt,
                "process_ok": raw.process_ok,
                "environment_error": raw.environment_error,
                "returncode": raw.returncode,
                "duration_seconds": raw.duration_seconds,
                "answer_file": answer_path.relative_to(out_dir).as_posix(),
            }
        )
        results.append(evaluated)
    return results



def select_case_ids(*, suite: str, from_case: int | None, to_case: int | None) -> list[int]:
    if from_case is None and to_case is None:
        return ordered_suite_case_ids(suite)
    if from_case is None:
        from_case = to_case
    if to_case is None:
        to_case = from_case
    assert from_case is not None and to_case is not None
    if not (1 <= from_case <= to_case <= 46):
        raise SystemExit("case range must satisfy 1 <= from-case <= to-case <= 46")
    return list(range(from_case, to_case + 1))


def _promote_answer_environment_error(result: legacy.Result, out_dir: Path) -> None:
    """Treat explicit Skill-unavailable final answers as runtime failures, not behavior samples."""
    if result.environment_error is not None:
        return
    answer_path = out_dir / result.answer_file
    if not answer_path.is_file():
        return
    detected = detect_environment_error(answer_path.read_text(encoding="utf-8"))
    if detected is None:
        return
    result.environment_error = detected
    result.process_ok = False




def _run_ansim_cli(args, root: Path) -> int:
    catalog = load_ansim_catalog()
    codex_cmd = legacy.resolve_codex_command(args.codex)
    print("Resolved Codex CLI:", " ".join(codex_cmd))
    legacy.validate_plugin(codex_cmd)

    installed_root = legacy.resolve_installed_skill_root(args.installed_skill_root)
    if installed_root is None:
        print("INSTALLATION_INTEGRITY: FAIL")
        print("installed runtime root could not be resolved")
        return 4
    mismatches = legacy.compare_runtime_manifests(root, installed_root)
    if mismatches:
        print("INSTALLATION_INTEGRITY: FAIL")
        for mismatch in mismatches:
            print("  " + mismatch)
        return 4
    print("INSTALLATION_INTEGRITY: PASS")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = args.output_dir.resolve() if args.output_dir else root / "regression-results" / f"ansim-v024-{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    def runner(attempt_dir: Path, case: legacy.Case):
        result = legacy.run_case(
            root,
            attempt_dir,
            case,
            args.timeout,
            codex_cmd,
            args.model,
            args.unsafe_bypass_sandbox,
        )
        _promote_answer_environment_error(result, attempt_dir)
        return result

    def evaluator(case_id: str, answer: str, process_ok: bool):
        return evaluate_ansim_case(
            case_id,
            answer,
            process_ok=process_ok,
            oracle_path=ANSIM_ORACLE_PATH,
        )

    results = execute_ansim_attempts(
        out_dir,
        catalog,
        repetitions=args.repetitions,
        run_case=runner,
        evaluate=evaluator,
    )
    summary = build_ansim_summary(
        results,
        model=args.model,
        plugin_version=legacy.REQUIRED_PLUGIN_VERSION,
        repetitions=args.repetitions,
    )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    finding_lines = ["# Ansim Housing Oracle Findings", ""]
    for result in results:
        for finding in result["findings"]:
            finding_lines.append(
                f'- {result["case_id"]} run {result["attempt"]}: '
                f'{finding["marker"]} — {finding["reason"]}'
            )
    if len(finding_lines) == 2:
        finding_lines.append("- None")
    (out_dir / "oracle-findings.md").write_text("\n".join(finding_lines) + "\n", encoding="utf-8")

    print("=== ANSIM MACHINE-CHECK SUMMARY ===")
    print(f"process_ok: {summary['process_success']}/{summary['case_count']}")
    print(f"contract_oracle_pass: {summary['pass_count']}/{summary['case_count']}")
    print(f"critical_negative_markers: {len(summary['critical_negative_markers'])}")
    print(f"release_verdict: {summary['release_verdict']}")
    print(f"Output: {out_dir}")
    if summary["process_success"] != summary["case_count"]:
        return 3
    return 0 if summary["release_verdict"] == "PASS" else 1

def main() -> int:
    parser = argparse.ArgumentParser(description="Run JDIPT consolidated behavior evaluation suites.")
    parser.add_argument("--suite", choices=("core", "full", "legacy", "all", "ansim"), default="full")
    parser.add_argument("--codex", type=str, default=None)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--installed-skill-root", type=Path, default=None)
    parser.add_argument("--unsafe-bypass-sandbox", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--from-case", type=int, default=None, dest="from_case")
    parser.add_argument("--to-case", type=int, default=None, dest="to_case")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--repetitions", type=int, choices=(1, 3), default=1)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    if args.suite == "ansim":
        return _run_ansim_cli(args, root)
    catalog = load_catalog()
    selected_ids = select_case_ids(suite=args.suite, from_case=args.from_case, to_case=args.to_case)
    selected = [catalog[case_id] for case_id in selected_ids]

    codex_cmd = legacy.resolve_codex_command(args.codex)
    print("Resolved Codex CLI:", " ".join(codex_cmd))
    plugin_output = legacy.validate_plugin(codex_cmd)

    installed_root = legacy.resolve_installed_skill_root(args.installed_skill_root)
    if installed_root is None:
        print("INSTALLATION_INTEGRITY: FAIL")
        print("installed runtime root could not be resolved")
        return 4
    integrity_mismatches = legacy.compare_runtime_manifests(root, installed_root)
    if integrity_mismatches:
        print("INSTALLATION_INTEGRITY: FAIL")
        for mismatch in integrity_mismatches:
            print("  " + mismatch)
        return 4
    print("INSTALLATION_INTEGRITY: PASS")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else root / "regression-results" / f"{args.suite}-{timestamp}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "environment.txt").write_text(
        "\n".join(
            [
                f"timestamp={datetime.now().isoformat()}",
                f"repo={root}",
                f"suite={args.suite}",
                f"selected_cases={','.join(f'E{case_id:02d}' for case_id in selected_ids)}",
                f"required_plugin={legacy.REQUIRED_PLUGIN_ID}",
                f"required_version={legacy.REQUIRED_PLUGIN_VERSION}",
                f"resolved_codex={' '.join(codex_cmd)}",
                f"sandbox_mode={'BYPASS' if args.unsafe_bypass_sandbox else 'read-only'}",
                "",
                "=== codex plugin list ===",
                plugin_output,
            ]
        ),
        encoding="utf-8",
    )

    results: list[legacy.Result] = []
    print(f"JDIPT {args.suite} suite: {len(selected)} cases")
    print("Cases:", ", ".join(f"E{case_id:02d}" for case_id in selected_ids))
    print(f"Output: {out_dir}")
    print()

    for index, case in enumerate(selected, start=1):
        print(f"[{index:02d}/{len(selected):02d}] E{case.number:02d} {case.title}")
        result = legacy.run_case(
            root,
            out_dir,
            case,
            args.timeout,
            codex_cmd,
            args.model,
            args.unsafe_bypass_sandbox,
        )
        _promote_answer_environment_error(result, out_dir)
        results.append(result)
        status = "OK" if result.process_ok else ("ENV_ERROR" if result.environment_error else "ERROR")
        print(
            f"  process={status} h1={result.h1_check.split()[0]} "
            f"hygiene={result.hygiene_check.split()[0]} "
            f"url={result.incomplete_url_check.split()[0]} "
            f"oracle={result.contract_oracle} duration={result.duration_seconds:.1f}s"
        )
        if result.environment_error:
            print(f"  environment_error={result.environment_error}")

    summary = {
        "plugin_id": legacy.REQUIRED_PLUGIN_ID,
        "plugin_version": legacy.REQUIRED_PLUGIN_VERSION,
        "suite": args.suite,
        "selected_cases": selected_ids,
        "generated_at": datetime.now().isoformat(),
        "contract_oracle_pass": f"{sum(r.contract_oracle == 'PASS' for r in results)}/{len(results)}",
        "results": [asdict(result) for result in results],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    combined_parts: list[str] = []
    for case in selected:
        bundle = out_dir / f"E{case.number:02d}.case.md"
        if bundle.is_file():
            combined_parts.append(bundle.read_text(encoding="utf-8"))
    (out_dir / "ALL_RESPONSES.md").write_text("\n\n---\n\n".join(combined_parts), encoding="utf-8")

    process_ok = sum(1 for result in results if result.process_ok)
    environment_errors = sum(1 for result in results if result.environment_error is not None)
    h1_pass = sum(1 for result in results if result.h1_check == "PASS")
    hygiene_pass = sum(1 for result in results if result.hygiene_check == "PASS")
    url_pass = sum(1 for result in results if result.incomplete_url_check == "PASS")
    contract_pass = sum(1 for result in results if result.contract_oracle == "PASS")

    print()
    print("=== MACHINE-CHECK SUMMARY ===")
    print(f"suite: {args.suite}")
    print(f"process_ok: {process_ok}/{len(results)}")
    print(f"environment_errors: {environment_errors}/{len(results)}")
    print(f"h1_pass: {h1_pass}/{len(results)} (special-format cases may be SKIP)")
    print(f"hygiene_pass: {hygiene_pass}/{len(results)}")
    print(f"incomplete_url_pass: {url_pass}/{len(results)}")
    print(f"contract_oracle_pass: {contract_pass}/{len(results)}")
    print("semantic verdict: NOT AUTOMATICALLY GRADED")

    zip_path = Path(shutil.make_archive(str(out_dir), "zip", root_dir=out_dir))
    print(f"ZIP: {zip_path}")

    if environment_errors:
        return 3
    if process_ok != len(results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
