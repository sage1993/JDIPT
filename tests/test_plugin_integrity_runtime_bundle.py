from pathlib import Path

from scripts.plugin_integrity import build_runtime_manifest, compare_runtime_manifests


PLUGIN_FILES = (
    ".codex-plugin/plugin.json",
    ".mcp.json",
    "hooks/hooks.json",
    "scripts/inject_registry_runtime.py",
    "scripts/jdipt_runtime_mcp.py",
    "scripts/runtime_registry_state.py",
    "scripts/stop_synthesis_gate.py",
    "scripts/synthesis_runtime_state.py",
    "scripts/synthesis_integrity.py",
)


def _write_bundle(root: Path, *, omit: str | None = None) -> None:
    skill = root / "skills" / "law-interpretation-request"
    (skill / "agents").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text("skill", encoding="utf-8")
    (skill / "agents" / "openai.yaml").write_text("agent", encoding="utf-8")
    (skill / "references" / "source-policy.md").write_text("source", encoding="utf-8")
    for relative in PLUGIN_FILES:
        if relative == omit:
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")


def test_manifest_includes_plugin_runtime_bundle(tmp_path):
    _write_bundle(tmp_path)

    manifest = build_runtime_manifest(tmp_path)

    assert "plugin/hooks/hooks.json" in manifest
    assert "plugin/.mcp.json" in manifest
    assert "plugin/scripts/inject_registry_runtime.py" in manifest
    assert "plugin/scripts/runtime_registry_state.py" in manifest


def test_compare_fails_when_installed_runtime_bridge_is_missing(tmp_path):
    repo = tmp_path / "repo"
    installed = tmp_path / "installed"
    _write_bundle(repo)
    _write_bundle(installed, omit="scripts/inject_registry_runtime.py")

    mismatches = compare_runtime_manifests(
        repo,
        installed / "skills" / "law-interpretation-request",
    )

    assert mismatches == [
        "missing installed file: plugin/scripts/inject_registry_runtime.py"
    ]
