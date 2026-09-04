from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_architecture_documents_the_v2_runtime_flow_and_activation_boundary():
    text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    sequence = (
        "Explicit JDIPT Skill",
        "Legal Issue Mapping",
        "Source / Temporal / Authority Resolution",
        "LegalProposition Ledger",
        "register_material_proposition",
        "PLUGIN_DATA Runtime State",
        "Render Contract",
        "Answer",
        "Stop Gate",
    )
    positions = [text.index(marker) for marker in sequence]
    assert positions == sorted(positions)
    assert "registry_active" in text
    assert "does not independently prove host Plugin invocation" in text
    assert "deterministic slots" in text
    assert "semantic proposition matching" in text
    assert "Tier 1~3 static PASS" in text
    assert "Tier 4 Live PASS" in text


def test_evaluation_document_separates_static_and_live_runtime_acceptance():
    text = (ROOT / "docs" / "evaluation-suites.md").read_text(encoding="utf-8")

    assert "Runtime bridge acceptance" in text
    assert "register_material_proposition" in text
    assert "registry_active=true" in text
    assert "Stop" in text
    assert "static PASS" in text
    assert "Live PASS" in text
