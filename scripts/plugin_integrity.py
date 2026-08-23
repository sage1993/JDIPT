"""SHA-256 integrity checks for the installed JDIPT runtime Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

RUNTIME_FILES = ("SKILL.md", "agents/openai.yaml")


def _skill_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if (root / "SKILL.md").is_file():
        return root
    candidate = root / "skills" / "law-interpretation-request"
    if (candidate / "SKILL.md").is_file():
        return candidate
    return root


def _runtime_paths(skill_root: Path) -> list[Path]:
    root = _skill_root(skill_root)
    paths = [root / relative for relative in RUNTIME_FILES]
    paths.extend(sorted((root / "references").glob("*.md")))
    return paths


def build_runtime_manifest(skill_root: Path) -> dict[str, str]:
    """Return a relative POSIX path → SHA-256 raw-byte digest manifest."""

    root = _skill_root(skill_root)
    manifest: dict[str, str] = {}
    for path in _runtime_paths(root):
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            manifest[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(manifest.items()))


def compare_runtime_manifests(repo_root: Path, installed_root: Path) -> list[str]:
    """Return deterministic mismatch descriptions; an empty list means exact."""

    repo = build_runtime_manifest(repo_root)
    installed_path = _skill_root(installed_root)
    if not installed_path.exists():
        return [f"installed runtime root missing: {installed_path}"]
    installed = build_runtime_manifest(installed_path)
    mismatches: list[str] = []
    for relative in sorted(set(repo) | set(installed)):
        if relative not in repo:
            mismatches.append(f"extra installed file: {relative}")
        elif relative not in installed:
            mismatches.append(f"missing installed file: {relative}")
        elif repo[relative] != installed[relative]:
            mismatches.append(f"digest mismatch: {relative}")
    return mismatches


def resolve_installed_skill_root(explicit: Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    env_value = os.environ.get("JDIPT_INSTALLED_SKILL_ROOT")
    if env_value:
        candidates.append(Path(env_value))
    home = Path.home()
    candidates.extend(
        [
            home / ".codex" / "plugins" / "jdipt" / "skills" / "law-interpretation-request",
            home / ".codex" / "plugins" / "jdipt@jdipt-local" / "skills" / "law-interpretation-request",
        ]
    )
    for candidate in candidates:
        if (_skill_root(candidate) / "SKILL.md").is_file():
            return _skill_root(candidate)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare repo and installed JDIPT runtime SHA-256 manifests.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--installed-root", type=Path, default=None)
    args = parser.parse_args()
    installed = resolve_installed_skill_root(args.installed_root)
    if installed is None:
        print("INSTALLATION_INTEGRITY: FAIL")
        print("installed runtime root could not be resolved")
        return 1
    mismatches = compare_runtime_manifests(args.repo_root, installed)
    print(json.dumps({"repo": build_runtime_manifest(args.repo_root), "installed": build_runtime_manifest(installed), "mismatches": mismatches}, ensure_ascii=False, indent=2))
    print("INSTALLATION_INTEGRITY:", "PASS" if not mismatches else "FAIL")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
