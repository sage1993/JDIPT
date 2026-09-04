from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_runs_deterministic_python_and_node_gates():
    path = ROOT / ".github" / "workflows" / "ci.yml"
    text = path.read_text(encoding="utf-8")

    assert 'python-version: "3.13"' in text
    assert 'node-version: "20.19.0"' in text
    assert "timeout-minutes:" in text
    for command in (
        "python -m pytest -q",
        "python scripts/validate_repo.py",
        "python scripts/validate_authority_temporal_contract.py",
        "python -m compileall -q scripts tests",
        "npm ci",
        "npm audit --omit=dev",
        "npm run mcp -- --help",
    ):
        assert command in text
