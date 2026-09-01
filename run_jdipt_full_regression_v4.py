from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse, parse_qsl
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from scripts.regression_oracles import evaluate_case
from scripts.plugin_integrity import compare_runtime_manifests, resolve_installed_skill_root
from scripts.regression_checks import (
    check_h1 as _check_h1,
    check_output_hygiene,
    check_urls,
    detect_environment_error as _detect_environment_error,
    exact_h1_lines as _exact_h1_lines,
    first_nonblank_line as _first_nonblank_line,
)


REQUIRED_PLUGIN_ID = "jdipt@jdipt-local"
REQUIRED_PLUGIN_VERSION = "0.2.4"
DEFAULT_REGRESSION_MODEL = "gpt-5.6-luna"


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


_configure_utf8_stdio()

DEFAULT_H1 = [
    "# 1. 질의요지",
    "# 2. 검토결론",
    "# 3. 검토이유",
    "# 4. 관련 법령 및 자료",
]

MOLEG_H1 = [
    "# 1. 질의요지",
    "# 2. 해석대상 법령조문 및 관련 법령",
    "# 3. 대립되는 의견 및 이유",
]

MOLEG_CASES = {1, 7, 22}
SPECIAL_FORMAT_CASES = {2, 3, 9}
H1_DEFAULT_CASES = set(range(1, 43)) - MOLEG_CASES - SPECIAL_FORMAT_CASES

HYGIENE_FORBIDDEN = [
    "$law-interpretation-request",
    "@jdipt",
    "Skill activated",
    "Plugin activated",
    "references/logic-validation.md",
    "references/legal-issue-mapping.md",
    "references/source-policy.md",
    "references/request-format.md",
]


def _node_codex_from_npm_shim(shim_path: Path) -> list[str] | None:
    """Resolve an npm-installed codex.ps1/codex.cmd to node + codex.js directly."""
    base = shim_path.parent
    js_candidates = [
        base / "node_modules" / "@openai" / "codex" / "bin" / "codex.js",
        base / "node_modules" / "@openai" / "codex" / "bin" / "codex",
    ]
    node = (
        shutil.which("node.exe")
        or shutil.which("node")
        or (str(base / "node.exe") if (base / "node.exe").is_file() else None)
    )
    if not node:
        return None

    for js in js_candidates:
        if js.is_file():
            return [str(node), str(js)]
    return None


def resolve_codex_command(explicit_path: str | None = None) -> list[str]:
    """
    Resolve Codex CLI.

    On Windows, avoid invoking npm's codex.ps1 through powershell.exe -File:
    PowerShell 5.1 can mis-handle Codex's GNU-style --options at that boundary.
    Prefer node.exe + @openai/codex/bin/codex.js directly.
    """
    if explicit_path:
        explicit = Path(explicit_path).expanduser().resolve()
        if not explicit.is_file():
            raise SystemExit(f"Explicit Codex path does not exist: {explicit}")

        if explicit.suffix.lower() in {".ps1", ".cmd", ".bat"}:
            direct = _node_codex_from_npm_shim(explicit)
            if direct:
                return direct

        if explicit.suffix.lower() == ".exe":
            return [str(explicit)]

        # If the user explicitly supplied the JS entrypoint.
        if explicit.suffix.lower() == ".js":
            node = shutil.which("node.exe") or shutil.which("node")
            if node:
                return [node, str(explicit)]

    # First try true executables.
    for candidate in ("codex.exe",):
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved]

    # Then inspect npm shims.
    for candidate in ("codex.ps1", "codex.cmd", "codex.bat"):
        resolved = shutil.which(candidate)
        if resolved:
            direct = _node_codex_from_npm_shim(Path(resolved))
            if direct:
                return direct

    # Ask PowerShell where codex is, then resolve its npm shim without invoking it.
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell:
        probe = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-Command",
                "(Get-Command codex -ErrorAction Stop).Source",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        source = (probe.stdout or "").strip()
        if probe.returncode == 0 and source:
            source_path = Path(source)
            if source_path.suffix.lower() in {".ps1", ".cmd", ".bat"}:
                direct = _node_codex_from_npm_shim(source_path)
                if direct:
                    return direct
            if source_path.suffix.lower() == ".exe":
                return [source]

    raise SystemExit(
        "Codex CLI could not be resolved to a native executable or node entrypoint.\n"
        "Run these commands and inspect the paths:\n"
        "  Get-Command codex | Format-List Name,CommandType,Source,Path\n"
        "  Get-Command node  | Format-List Name,CommandType,Source,Path"
    )


@dataclass
class Case:
    number: int
    title: str
    prompt: str
    expected: str
    source_file: str


@dataclass
class Result:
    case: int
    title: str
    returncode: int | None
    duration_seconds: float
    answer_file: str
    log_file: str
    process_ok: bool
    first_nonblank: str | None
    h1_lines: list[str]
    h1_check: str
    hygiene_check: str
    incomplete_url_check: str
    timeout: bool
    environment_error: str | None
    error: str | None
    contract_oracle: str
    contract_failures: list[str]
    release_critical: bool


def parse_cases(path: Path) -> list[Case]:
    text = path.read_text(encoding="utf-8")
    header_re = re.compile(r"^## E(\d+)\.\s*(.+)$", re.MULTILINE)
    matches = list(header_re.finditer(text))
    cases: list[Case] = []

    for i, match in enumerate(matches):
        number = int(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end]

        prompt_match = re.search(r"^프롬프트:\s*`(.+?)`\s*$", section, re.MULTILINE)
        if not prompt_match:
            continue
        prompt = prompt_match.group(1).strip()

        expected_match = re.search(
            r"^기대:\s*(.*?)(?=\n(?:FAIL:|## |\Z))",
            section,
            re.MULTILINE | re.DOTALL,
        )
        expected = expected_match.group(1).strip() if expected_match else ""

        cases.append(
            Case(
                number=number,
                title=title,
                prompt=prompt,
                expected=expected,
                source_file=path.as_posix(),
            )
        )

    return cases


def load_all_cases(root: Path) -> list[Case]:
    primary = root / "skills" / "law-interpretation-request" / "evals" / "scenarios.md"
    v022 = root / "skills" / "law-interpretation-request" / "evals" / "v0.2.2-regressions.md"

    missing = [str(p) for p in (primary, v022) if not p.is_file()]
    if missing:
        raise SystemExit(f"Missing eval file(s): {', '.join(missing)}")

    by_number: dict[int, Case] = {}
    for case in parse_cases(primary) + parse_cases(v022):
        if 1 <= case.number <= 42:
            by_number[case.number] = case

    missing_ids = [n for n in range(1, 43) if n not in by_number]
    if missing_ids:
        raise SystemExit(f"Could not parse scenarios: missing E{missing_ids}")

    return [by_number[n] for n in range(1, 43)]


def validate_plugin(codex_cmd: list[str]) -> str:
    proc = subprocess.run(
        [*codex_cmd, "plugin", "list"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        raise SystemExit(f"`codex plugin list` failed:\n{output}")

    # Example:
    # jdipt@jdipt-local  installed, enabled  0.2.2    C:\Users\...\jdipt
    pattern = re.compile(
        rf"(?m)^\s*{re.escape(REQUIRED_PLUGIN_ID)}\s+installed,\s*enabled\s+"
        rf"{re.escape(REQUIRED_PLUGIN_VERSION)}(?:\s|$)"
    )
    if not pattern.search(output):
        raise SystemExit(
            f"Required plugin not active: {REQUIRED_PLUGIN_ID} {REQUIRED_PLUGIN_VERSION}\n\n"
            f"`codex plugin list` output:\n{output}"
        )
    return output


def normalize_prompt(prompt: str) -> str:
    if prompt.lstrip().startswith("$law-interpretation-request"):
        return prompt
    return "$law-interpretation-request\n\n" + prompt


def first_nonblank_line(text: str) -> str | None:
    return _first_nonblank_line(text)


def exact_h1_lines(text: str) -> list[str]:
    return _exact_h1_lines(text)


def check_h1(case_no: int, text: str) -> str:
    return _check_h1(text, case_no)


def check_hygiene(text: str) -> str:
    ok, problems = check_output_hygiene(text)
    return "PASS" if ok else "FAIL forbidden=" + repr(problems)


def check_incomplete_urls(text: str) -> str:
    ok, problems = check_urls(text)
    return "PASS" if ok else "FAIL incomplete=" + repr(problems)


def write_case_bundle(out_dir: Path, case: Case, answer: str) -> None:
    bundle = out_dir / f"E{case.number:02d}.case.md"
    bundle.write_text(
        "\n".join(
            [
                f"# E{case.number}. {case.title}",
                "",
                "## Prompt",
                "",
                "```text",
                normalize_prompt(case.prompt),
                "```",
                "",
                "## Expected",
                "",
                case.expected or "(expected text not parsed)",
                "",
                "## Raw answer",
                "",
                answer,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _terminate_process_tree(proc: subprocess.Popen[str]) -> bool:
    """Terminate a timed-out Codex child and its Windows descendants."""
    if os.name == "nt":
        taskkill = shutil.which("taskkill")
        if taskkill:
            result = subprocess.run(
                [taskkill, "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            return result.returncode == 0
    proc.kill()
    return True


def run_case(root: Path, out_dir: Path, case: Case, timeout_seconds: int, codex_cmd: list[str], model: str, unsafe_bypass_sandbox: bool) -> Result:
    answer_path = out_dir / f"E{case.number:02d}.md"
    log_path = out_dir / f"E{case.number:02d}.log.txt"
    prompt = normalize_prompt(case.prompt)

    sandbox_args = (
        ["--dangerously-bypass-approvals-and-sandbox"]
        if unsafe_bypass_sandbox
        else ["--sandbox", "read-only"]
    )

    cmd = [
        *codex_cmd,
        "exec",
        "--model",
        model,
        *sandbox_args,
        "--ephemeral",
        "--output-last-message",
        str(answer_path),
        prompt,
    ]

    started = time.monotonic()
    timed_out = False
    error = None
    returncode: int | None = None
    stdout = ""
    pid: int | None = None
    spawned_at = datetime.now().astimezone().isoformat()
    killed = False
    stderr = ""

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pid = proc.pid
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        error = f"timeout after {timeout_seconds}s"
        killed = _terminate_process_tree(proc)
        stdout, stderr = proc.communicate()
        if not stdout and isinstance(exc.stdout, str):
            stdout = exc.stdout
        if not stderr and isinstance(exc.stderr, str):
            stderr = exc.stderr
        returncode = proc.returncode
    except Exception as exc:  # pragma: no cover - operational guard
        error = f"{type(exc).__name__}: {exc}"

    environment_error = None
    combined_error_text = f"{stdout}\n{stderr}"
    fatal_environment_markers = [
        "apply deny-read ACLs",
        "Failed to create unified exec process",
        "helper_unknown_error",
    ]
    if any(marker in combined_error_text for marker in fatal_environment_markers):
        environment_error = "Codex Windows sandbox/ACL failure prevented reliable Skill file access"

    detected_environment_error = _detect_environment_error(combined_error_text)
    if detected_environment_error is not None:
        environment_error = detected_environment_error

    duration = time.monotonic() - started

    log_path.write_text(
        "\n".join(
            [
                f"COMMAND: {' '.join(cmd)}",
                "STDIN: DEVNULL",
                f"PID: {pid}",
                f"SPAWNED_AT_UTC: {spawned_at}",
                f"KILLED: {killed}",
                f"ANSWER_FILE_EXISTS: {answer_path.is_file()}",
                f"TIMEOUT_REASON: {error if timed_out else None}",
                f"RETURN_CODE: {returncode}",
                f"TIMEOUT: {timed_out}",
                f"ENVIRONMENT_ERROR: {environment_error}",
                f"ERROR: {error}",
                f"DURATION_SECONDS: {duration:.3f}",
                "",
                "=== PROMPT ===",
                prompt,
                "",
                "=== STDOUT ===",
                stdout,
                "",
                "=== STDERR ===",
                stderr,
                "",
                "=== STDOUT TAIL ===",
                stdout[-8192:],
                "",
                "=== STDERR TAIL ===",
                stderr[-8192:],
                "",
            ]
        ),
        encoding="utf-8",
    )

    answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    write_case_bundle(out_dir, case, answer)
    oracle = evaluate_case(case.number, answer)

    return Result(
        case=case.number,
        title=case.title,
        returncode=returncode,
        duration_seconds=round(duration, 3),
        answer_file=answer_path.name,
        log_file=log_path.name,
        process_ok=(
            returncode == 0
            and bool(answer.strip())
            and not timed_out
            and environment_error is None
        ),
        first_nonblank=first_nonblank_line(answer),
        h1_lines=exact_h1_lines(answer),
        h1_check=check_h1(case.number, answer),
        hygiene_check=check_hygiene(answer),
        incomplete_url_check=check_incomplete_urls(answer),
        timeout=timed_out,
        environment_error=environment_error,
        error=error,
        contract_oracle=oracle["contract_oracle"],
        contract_failures=oracle["contract_failures"],
        release_critical=oracle["release_critical"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run JDIPT v0.2.2 E1-E42 behavior regression in isolated codex exec sessions."
    )
    parser.add_argument(
        "--codex",
        type=str,
        default=None,
        help="Explicit Codex CLI path, e.g. C:\\Users\\KSH\\AppData\\Roaming\\npm\\codex.ps1",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_REGRESSION_MODEL,
        help=f"Codex model for regression calls (default: {DEFAULT_REGRESSION_MODEL}).",
    )
    parser.add_argument(
        "--installed-skill-root",
        type=Path,
        default=None,
        help="Explicit installed law-interpretation-request Skill root for integrity checking.",
    )
    parser.add_argument(
        "--unsafe-bypass-sandbox",
        action="store_true",
        help=(
            "Disable Codex sandbox/approvals for this regression run. "
            "Use only if native Windows read-only sandbox still fails with ACL errors."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Per-case timeout in seconds (default: 900).",
    )
    parser.add_argument(
        "--from-case",
        type=int,
        default=1,
        dest="from_case",
        help="First case number (default: 1).",
    )
    parser.add_argument(
        "--to-case",
        type=int,
        default=42,
        dest="to_case",
        help="Last case number (default: 42).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Default: regression-results/v0.2.2-<timestamp>",
    )
    args = parser.parse_args()

    root = Path.cwd().resolve()
    cases = load_all_cases(root)

    if not (1 <= args.from_case <= args.to_case <= 42):
        raise SystemExit("case range must satisfy 1 <= from-case <= to-case <= 42")

    codex_cmd = resolve_codex_command(args.codex)
    print("Resolved Codex CLI:", " ".join(codex_cmd))
    plugin_output = validate_plugin(codex_cmd)
    installed_root = resolve_installed_skill_root(args.installed_skill_root)
    if installed_root is None:
        print("INSTALLATION_INTEGRITY: FAIL")
        print("installed runtime root could not be resolved")
        return 4
    integrity_mismatches = compare_runtime_manifests(root, installed_root)
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
        else root / "regression-results" / f"v0.2.2-{timestamp}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "environment.txt").write_text(
        "\n".join(
            [
                f"timestamp={datetime.now().isoformat()}",
                f"repo={root}",
                f"required_plugin={REQUIRED_PLUGIN_ID}",
                f"required_version={REQUIRED_PLUGIN_VERSION}",
                f"resolved_codex={' '.join(codex_cmd)}",
                f"sandbox_mode={'BYPASS' if args.unsafe_bypass_sandbox else 'read-only'}",
                "",
                "=== codex plugin list ===",
                plugin_output,
            ]
        ),
        encoding="utf-8",
    )

    selected = [c for c in cases if args.from_case <= c.number <= args.to_case]
    results: list[Result] = []

    print(f"JDIPT v0.2.2 regression: E{args.from_case}-E{args.to_case}")
    print(f"Output: {out_dir}")
    print()

    for index, case in enumerate(selected, start=1):
        print(f"[{index:02d}/{len(selected):02d}] E{case.number:02d} {case.title}")
        result = run_case(root, out_dir, case, args.timeout, codex_cmd, args.model, args.unsafe_bypass_sandbox)
        results.append(result)
        status = "OK" if result.process_ok else ("ENV_ERROR" if result.environment_error else "ERROR")
        print(
            f"  process={status} h1={result.h1_check.split()[0]} "
            f"hygiene={result.hygiene_check.split()[0]} "
            f"url={result.incomplete_url_check.split()[0]} "
            f"duration={result.duration_seconds:.1f}s"
        )
        if result.environment_error:
            print(f"  environment_error={result.environment_error}")

    summary = {
        "plugin_id": REQUIRED_PLUGIN_ID,
        "plugin_version": REQUIRED_PLUGIN_VERSION,
        "case_range": [args.from_case, args.to_case],
        "generated_at": datetime.now().isoformat(),
        "contract_oracle_pass": f"{sum(r.contract_oracle == 'PASS' for r in results)}/{len(results)}",
        "results": [asdict(r) for r in results],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    combined_parts = []
    for case in selected:
        bundle = out_dir / f"E{case.number:02d}.case.md"
        if bundle.is_file():
            combined_parts.append(bundle.read_text(encoding="utf-8"))
    (out_dir / "ALL_RESPONSES.md").write_text(
        "\n\n---\n\n".join(combined_parts),
        encoding="utf-8",
    )

    process_ok = sum(1 for r in results if r.process_ok)
    environment_errors = sum(1 for r in results if r.environment_error is not None)
    h1_pass = sum(1 for r in results if r.h1_check == "PASS")
    hygiene_pass = sum(1 for r in results if r.hygiene_check == "PASS")
    url_pass = sum(1 for r in results if r.incomplete_url_check == "PASS")

    print()
    print("=== MACHINE-CHECK SUMMARY ===")
    print(f"process_ok: {process_ok}/{len(results)}")
    print(f"environment_errors: {environment_errors}/{len(results)}")
    print(f"h1_pass: {h1_pass}/{len(results)} (special-format cases may be SKIP)")
    print(f"hygiene_pass: {hygiene_pass}/{len(results)}")
    print(f"incomplete_url_pass: {url_pass}/{len(results)}")
    contract_pass = sum(1 for r in results if r.contract_oracle == "PASS")
    print(f"contract_oracle_pass: {contract_pass}/{len(results)}")
    print("semantic verdict: NOT AUTOMATICALLY GRADED")

    archive_base = str(out_dir)
    zip_path = Path(shutil.make_archive(archive_base, "zip", root_dir=out_dir))
    print(f"ZIP: {zip_path}")

    if environment_errors:
        return 3
    if process_ok != len(results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
