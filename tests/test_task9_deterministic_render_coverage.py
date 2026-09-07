from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.material_obligation_ledger import (
    MaterialObligation,
    MaterialObligationLedger,
    ObligationSourceStatus,
)
from scripts.proposition_rendering import build_render_contract
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeTurnState,
    load_runtime_state,
    save_runtime_state,
)


def _evidence(source_id: str) -> EvidenceRef:
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title=f"Verified source {source_id}",
        source_locator=f"https://example.test/{source_id}",
        evidence_span=f"A rule for {source_id} has a verified legal effect.",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text=f"The current verified standard for {source_id} applies.",
    )


def _proposition(proposition_id: str, source_id: str, relation_type: str = "base"):
    return LegalProposition(
        proposition_id=proposition_id,
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject="the authority",
        condition=f"the required condition for {proposition_id}",
        procedure=f"the required procedure for {proposition_id}",
        modality=Modality.MAY,
        legal_action="apply",
        operative_verb_lexeme="apply",
        legal_object=f"the subject {proposition_id}",
        legal_effect=f"the legal effect for {proposition_id}",
        polarity=Polarity.POSITIVE,
        relation_type=relation_type,
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=_evidence(source_id),
    )


def _ledger(*propositions):
    return MaterialObligationLedger(
        obligations=tuple(
            MaterialObligation(
                obligation_id=f"O_{proposition.proposition_id}",
                issue_type="EXCEPTION_RULE"
                if proposition.relation_type == "exception"
                else "BASE_RULE",
                source_status=ObligationSourceStatus.SOURCE_CONFIRMED,
                evidence_source_ids=(proposition.evidence.source_id,),
                proposition_ids=(proposition.proposition_id,),
            )
            for proposition in propositions
        ),
        verified_source_evidence=tuple(
            proposition.evidence for proposition in propositions
        ),
    )


def _state(propositions, ledger):
    return RuntimeTurnState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=True,
        repair_count=0,
        propositions=list(propositions),
        registry_required=True,
        registry_completed=True,
        registry_invocation_count=len(propositions),
        material_obligation_ledger=ledger,
        material_obligation_ledger_required=True,
    )


def _draft(*propositions):
    return "\n".join(
        slot.text
        for proposition in propositions
        for slot in build_render_contract(proposition).slots
    )


def test_task8_closure_pass_does_not_hide_omitted_final_proposition(tmp_path):
    first = _proposition("P1", "S1")
    second = _proposition("P2", "S2")
    ledger = _ledger(first, second)
    save_runtime_state(_state((first, second), ledger), tmp_path)

    result = handle_stop_event(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "last_assistant_message": _draft(first),
        },
        tmp_path,
    )
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result["decision"] == "block"
    assert stored.first_reconciliation["registry_closure"]["registry_closure_passed"] is True
    assert stored.first_reconciliation["render_coverage"]["coverage_passed"] is False
    assert stored.first_reconciliation["render_coverage"]["missing_proposition_ids"] == [
        "P2"
    ]


def test_task9_missing_required_exception_is_blocked_at_stop_boundary(tmp_path):
    base = _proposition("P_BASE", "S_BASE")
    exception = _proposition("P_EXCEPTION", "S_EXCEPTION", relation_type="exception")
    ledger = _ledger(base, exception)
    save_runtime_state(_state((base, exception), ledger), tmp_path)

    result = handle_stop_event(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "last_assistant_message": _draft(base),
        },
        tmp_path,
    )

    assert result["decision"] == "block"
    assert "P_EXCEPTION" in result["reason"]


def test_coverage_can_pass_for_example_only_text_while_soundness_blocks(tmp_path):
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    save_runtime_state(_state((proposition,), ledger), tmp_path)
    rendered = _draft(proposition)

    result = handle_stop_event(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "last_assistant_message": f"Review example only: '{rendered}'",
        },
        tmp_path,
    )
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result["decision"] == "block"
    assert stored.first_reconciliation["render_coverage"]["coverage_passed"] is True
    assert stored.first_reconciliation["soundness"]["soundness_passed"] is False
