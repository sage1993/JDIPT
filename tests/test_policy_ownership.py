from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
OPENAI_YAML = ROOT / "skills" / "law-interpretation-request" / "agents" / "openai.yaml"
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"


def test_agents_is_bootstrap_not_second_runtime_contract():
    agents = AGENTS.read_text(encoding="utf-8")

    assert "$law-interpretation-request" in agents
    assert "SKILL.md를 먼저 읽는다" in agents

    assert "CURRENT_CONFIRMED" not in agents
    assert "mandatory_render_clause" not in agents
    assert "Range/effect coupling hard stop" not in agents


def test_openai_yaml_remains_explicit_only():
    text = OPENAI_YAML.read_text(encoding="utf-8")

    assert "allow_implicit_invocation: false" in text


def test_skill_owns_runtime_registration_sequence():
    text = SKILL.read_text(encoding="utf-8")

    order = [
        "Material Proposition Ledger",
        "register_material_proposition",
        "mandatory render",
        "explanatory synthesis",
        "Stop",
    ]

    positions = [text.index(marker) for marker in order]
    assert positions == sorted(positions)


def test_detailed_policy_has_reference_owners():
    source_policy = (
        ROOT
        / "skills"
        / "law-interpretation-request"
        / "references"
        / "source-policy.md"
    ).read_text(encoding="utf-8")
    issue_mapping = (
        ROOT
        / "skills"
        / "law-interpretation-request"
        / "references"
        / "legal-issue-mapping.md"
    ).read_text(encoding="utf-8")
    logic_validation = (
        ROOT
        / "skills"
        / "law-interpretation-request"
        / "references"
        / "logic-validation.md"
    ).read_text(encoding="utf-8")

    assert "Material Source Dependency Closure Gate" in source_policy
    assert "Compound-Issue Coverage Gate" in issue_mapping
    assert "Synthesis Integrity Gate" in logic_validation
