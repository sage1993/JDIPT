from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-qm", "baseline")
    return repo


def _gate_module():
    import importlib

    return importlib.import_module("scripts.canonical_baseline_gate")


class CanonicalBaselineGateTests(unittest.TestCase):
    def test_dirty_worktree_is_hold_and_native_is_not_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory))
            (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")

            result = _gate_module().evaluate_repository(
                repo,
                required_files=("tracked.txt",),
                probe_modules=(),
                create_clean_checkout=False,
            )

            self.assertEqual(result["verdict"], "HOLD")
            self.assertFalse(result["allow_native"])
            self.assertFalse(result["checks"]["worktree_clean"])
            self.assertIn("DIRTY_WORKTREE", result["reasons"])


    def test_untracked_required_runtime_file_is_hold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory))
            (repo / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")

            result = _gate_module().evaluate_repository(
                repo,
                required_files=("tracked.txt", "runtime.py"),
                probe_modules=(),
                create_clean_checkout=False,
            )

            self.assertEqual(result["verdict"], "HOLD")
            self.assertFalse(result["checks"]["required_files_tracked"])
            self.assertIn("REQUIRED_FILE_NOT_TRACKED:runtime.py", result["reasons"])


    def test_clean_committed_snapshot_can_pass_with_clean_checkout_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory))
            package = repo / "scripts"
            package.mkdir()
            (package / "__init__.py").write_text("\n", encoding="utf-8")
            (package / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
            _git(repo, "add", "scripts")
            _git(repo, "commit", "-qm", "runtime")

            result = _gate_module().evaluate_repository(
                repo,
                required_files=("tracked.txt", "scripts/probe.py"),
                probe_modules=("scripts.probe",),
                create_clean_checkout=True,
            )

            self.assertEqual(result["verdict"], "PASS")
            self.assertTrue(result["allow_native"])
            self.assertTrue(result["checks"]["worktree_clean"])
            self.assertTrue(result["checks"]["committed_tree_complete"])
            self.assertTrue(result["checks"]["clean_checkout_import"])
