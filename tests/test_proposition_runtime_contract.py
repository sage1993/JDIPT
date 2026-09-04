from pathlib import Path

from scripts.legal_proposition import EvidenceRef, LegalProposition
from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_model_and_render_contract_have_one_runtime_path():
    proposition = LegalProposition(
        proposition_id="P1",
        status="CLOSED",
        materiality="material",
        subject="행정청",
        condition="요건",
        procedure="절차",
        modality="may",
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="대상",
        legal_effect="법적 지위",
        polarity="positive",
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=EvidenceRef(
            source_id="law-001",
            authority_kind="statute",
            source_title="검증 법령",
            source_locator="법령 식별자/조문",
            evidence_span="확인된 원문",
            temporal_status="CURRENT_CONFIRMED",
            temporal_render_text="현재 시행 중인 기준이다.",
        ),
    )
    contract = build_render_contract(proposition)

    assert len(contract.slots) == 2
    assert reconcile_render_contracts(
        [contract],
        "\n\n".join(slot.text for slot in contract.slots),
    ).covered


def test_runtime_modules_do_not_import_legacy_synthesis_matcher():
    for relative in (
        "scripts/proposition_registry.py",
        "scripts/synthesis_runtime_state.py",
        "scripts/stop_synthesis_gate.py",
        "scripts/jdipt_runtime_mcp.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "synthesis_integrity" not in text
        assert "runtime_registry_state" not in text


def test_production_runtime_has_no_case_specific_fixture_literals():
    production = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            "scripts/legal_proposition.py",
            "scripts/proposition_rendering.py",
            "scripts/proposition_reconciliation.py",
            "scripts/proposition_registry.py",
            "scripts/synthesis_runtime_state.py",
            "scripts/stop_synthesis_gate.py",
            "scripts/jdipt_runtime_mcp.py",
        )
    )
    for token in ("ASH-06", "안심주택", "250m", "350m", "400%", "사업대상지"):
        assert token not in production


def test_explicit_only_skill_policy_is_preserved():
    agent_config = (
        ROOT / "skills" / "law-interpretation-request" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")

    assert "allow_implicit_invocation: false" in agent_config
