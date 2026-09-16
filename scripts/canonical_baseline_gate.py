"""Fail-closed repository identity gate for Task 11 native qualification.

The gate answers one narrow question: can a native run be attributed to the
same complete, clean, committed product snapshot that was tested?
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


DEFAULT_REQUIRED_FILES: tuple[str, ...] = (
    "scripts/runtime_root.py",
    "scripts/runtime_host_preflight.py",
    "scripts/turn_anchor.py",
    "scripts/turn_capability.py",
    "scripts/runtime_transaction.py",
    "scripts/material_obligation_ingress.py",
    "scripts/material_obligation_ledger.py",
    "scripts/proposition_source_closure.py",
    "scripts/proposition_rendering.py",
    "scripts/proposition_reconciliation.py",
    "scripts/proposition_soundness.py",
    "scripts/proposition_obligation_closure.py",
    "scripts/proposition_render_coverage.py",
    "scripts/proposition_relations.py",
    "scripts/proposition_registry.py",
    "scripts/legal_proposition.py",
    "scripts/jdipt_runtime_mcp.py",
    "scripts/inject_registry_runtime.py",
    "scripts/jdipt_activation.py",
    "scripts/stop_synthesis_gate.py",
    "scripts/plugin_runtime_context.py",
    "scripts/runtime_acceptance.py",
    "scripts/task11r_runtime_probe.py",
    "hooks/hooks.json",
    ".mcp.json",
)

DEFAULT_PROBE_MODULES: tuple[str, ...] = (
    "scripts.jdipt_runtime_mcp",
    "scripts.proposition_registry",
    "scripts.stop_synthesis_gate",
)


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _git_ok(root: Path, *args: str) -> bool:
    return _run_git(root, *args).returncode == 0


def _head(root: Path) -> str | None:
    result = _run_git(root, "rev-parse", "--verify", "HEAD")
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _worktree_clean(root: Path) -> bool:
    result = _run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    return result.returncode == 0 and not result.stdout.strip()


def _required_files_tracked(root: Path, required_files: Iterable[str]) -> tuple[bool, list[str]]:
    missing = [
        path
        for path in sorted(set(required_files))
        if not _git_ok(root, "ls-files", "--error-unmatch", "--", path)
    ]
    return not missing, missing


def _committed_tree_complete(
    root: Path,
    head: str | None,
    required_files: Iterable[str],
) -> tuple[bool, list[str]]:
    if head is None:
        return False, sorted(set(required_files))
    missing = [
        path
        for path in sorted(set(required_files))
        if not _git_ok(root, "cat-file", "-e", f"{head}:{path}")
    ]
    return not missing, missing


def _clean_checkout_import(
    root: Path,
    head: str | None,
    probe_modules: Sequence[str],
) -> tuple[bool, str | None]:
    if head is None:
        return False, "HEAD_UNAVAILABLE"

    checkout_path = Path(tempfile.mkdtemp(prefix="jdipt-clean-checkout-"))
    try:
        added = _run_git(root, "worktree", "add", "--detach", "--quiet", str(checkout_path), head)
        if added.returncode != 0:
            return False, added.stderr.strip() or "CLEAN_CHECKOUT_CREATE_FAILED"

        if not probe_modules:
            return True, None

        import_code = "import " + ", ".join(probe_modules)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-c", import_code],
            cwd=checkout_path,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, None
        return False, (result.stderr or result.stdout).strip() or "CLEAN_CHECKOUT_IMPORT_FAILED"
    finally:
        _run_git(root, "worktree", "remove", "--force", str(checkout_path))
        shutil.rmtree(checkout_path, ignore_errors=True)


def evaluate_repository(
    root: Path,
    *,
    base_ref: str | None = None,
    required_files: Sequence[str] = DEFAULT_REQUIRED_FILES,
    probe_modules: Sequence[str] = DEFAULT_PROBE_MODULES,
    create_clean_checkout: bool = True,
) -> dict[str, object]:
    """Evaluate repository identity and return a fail-closed verdict."""

    root = root.expanduser().resolve()
    head = _head(root)
    clean = _worktree_clean(root)
    tracked, untracked_required = _required_files_tracked(root, required_files)
    committed, missing_from_commit = _committed_tree_complete(root, head, required_files)
    ancestry = (
        True
        if base_ref is None
        else head is not None and _git_ok(root, "merge-base", "--is-ancestor", base_ref, head)
    )

    if create_clean_checkout:
        clean_import, import_error = _clean_checkout_import(root, head, probe_modules)
    else:
        clean_import, import_error = True, None

    reasons: list[str] = []
    if not clean:
        reasons.append("DIRTY_WORKTREE")
    if not tracked:
        reasons.extend(f"REQUIRED_FILE_NOT_TRACKED:{path}" for path in untracked_required)
    if not committed:
        reasons.extend(f"REQUIRED_FILE_MISSING_FROM_COMMIT:{path}" for path in missing_from_commit)
    if not ancestry:
        reasons.append(f"CANONICAL_ANCESTRY_FAILED:{base_ref}")
    if not clean_import:
        reasons.append("CLEAN_CHECKOUT_IMPORT_FAILED")

    checks = {
        "worktree_clean": clean,
        "required_files_tracked": tracked,
        "committed_tree_complete": committed,
        "canonical_ancestry": ancestry,
        "clean_checkout_import": clean_import,
    }
    allow_native = all(checks.values())
    return {
        "verdict": "PASS" if allow_native else "HOLD",
        "allow_native": allow_native,
        "head": head,
        "base_ref": base_ref,
        "tested_product_sha": head if allow_native else None,
        "checks": checks,
        "reasons": reasons,
        "clean_checkout_import_error": import_error,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref", default=os.environ.get("JDIPT_CANONICAL_BASE_REF"))
    parser.add_argument("--no-clean-checkout", action="store_true")
    args = parser.parse_args(argv)

    result = evaluate_repository(
        args.root,
        base_ref=args.base_ref,
        create_clean_checkout=not args.no_clean_checkout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["allow_native"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
