from __future__ import annotations

from pathlib import Path

from scripts.plugin_integrity import build_runtime_manifest, compare_runtime_manifests


def make_runtime(root: Path) -> Path:
    skill = root / "skills" / "law-interpretation-request"
    (skill / "agents").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_bytes(b"skill\n")
    (skill / "agents" / "openai.yaml").write_bytes(b"allow_implicit_invocation: false\n")
    (skill / "references" / "source-policy.md").write_bytes(b"policy\n")
    return skill


def test_exact_runtime_copy_has_matching_manifest(tmp_path):
    repo = make_runtime(tmp_path / "repo")
    installed = make_runtime(tmp_path / "installed")

    assert build_runtime_manifest(repo) == build_runtime_manifest(installed)
    assert compare_runtime_manifests(repo, installed) == []


def test_one_byte_skill_change_is_a_digest_mismatch(tmp_path):
    repo = make_runtime(tmp_path / "repo")
    installed = make_runtime(tmp_path / "installed")
    (installed / "SKILL.md").write_bytes(b"skill!\n")

    assert compare_runtime_manifests(repo, installed) == ["digest mismatch: SKILL.md"]


def test_reference_change_is_a_digest_mismatch(tmp_path):
    repo = make_runtime(tmp_path / "repo")
    installed = make_runtime(tmp_path / "installed")
    (installed / "references" / "source-policy.md").write_bytes(b"changed\n")

    assert compare_runtime_manifests(repo, installed) == ["digest mismatch: references/source-policy.md"]


def test_missing_runtime_file_is_reported(tmp_path):
    repo = make_runtime(tmp_path / "repo")
    installed = make_runtime(tmp_path / "installed")
    (installed / "agents" / "openai.yaml").unlink()

    assert compare_runtime_manifests(repo, installed) == ["missing installed file: agents/openai.yaml"]
