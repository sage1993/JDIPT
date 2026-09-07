import json
from pathlib import Path

import pytest

from scripts.legal_proposition import (
    AuthorityRequirement,
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
    TemporalRequirement,
)
from scripts.material_obligation_ledger import (
    MaterialObligation,
    MaterialObligationLedger,
    ObligationSourceStatus,
    ObligationValidationError,
    evaluate_registry_closure,
)
from scripts.proposition_registry import RegistryService
from scripts.proposition_rendering import build_render_contract
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    runtime_state_path,
    save_runtime_state,
)


SOURCE_CONFIRMED = ObligationSourceStatus.SOURCE_CONFIRMED
SOURCE_UNRESOLVED = ObligationSourceStatus.SOURCE_UNRESOLVED
NOT_APPLICABLE = ObligationSourceStatus.NOT_APPLICABLE


def evidence(source_id: str = "law-base", *, temporal_status: str = "CURRENT_CONFIRMED"):
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title="검증 법령",
        source_locator=f"https://example.test/{source_id}",
        evidence_span="행정청은 요건을 충족하고 절차를 거쳐 대상에 법적 효과를 부여할 수 있다.",
        temporal_status=temporal_status,
        temporal_render_text="현행 기준에 따른다.",
    )


def closed_proposition(
    proposition_id: str = "P_BASE",
    *,
    proposition_evidence: EvidenceRef | None = None,
    temporal_requirement: TemporalRequirement = TemporalRequirement.CURRENT,
    required_source_type: str | None = None,
):
    return LegalProposition(
        proposition_id=proposition_id,
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition="요건",
        procedure="절차",
        modality=Modality.MAY,
        legal_action="부여",
        operative_verb_lexeme="부여",
        legal_object="대상",
        legal_effect="법적 효과",
        polarity=Polarity.POSITIVE,
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=proposition_evidence or evidence(),
        required_authority=AuthorityRequirement.PRIMARY,
        required_temporal_status=temporal_requirement,
        required_source_type=required_source_type,
    )


def open_proposition(proposition_id: str = "P_RANGE"):
    return LegalProposition(
        proposition_id=proposition_id,
        status=PropositionStatus.OPEN,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition="요건",
        procedure="절차",
        modality=Modality.MAY,
        legal_action="부여",
        operative_verb_lexeme="부여",
        legal_object="대상",
        legal_effect="법적 효과",
        polarity=Polarity.POSITIVE,
        relation_type="exception",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=None,
    )


def obligation(
    obligation_id: str,
    issue_type: str,
    source_status: ObligationSourceStatus,
    *,
    evidence_source_ids: tuple[str, ...] = (),
    proposition_ids: tuple[str, ...] = (),
):
    return MaterialObligation(
        obligation_id=obligation_id,
        issue_type=issue_type,
        source_status=source_status,
        evidence_source_ids=evidence_source_ids,
        proposition_ids=proposition_ids,
    )


def codes(result) -> set[str]:
    return {item.code for item in result.violations}


@pytest.mark.parametrize(
    "status",
    [SOURCE_CONFIRMED, SOURCE_UNRESOLVED, NOT_APPLICABLE],
)
def test_supported_source_statuses_are_typed(status):
    value = obligation("O1", "BASE_RULE", status)

    assert value.source_status is status


@pytest.mark.parametrize("status", ["SOURCE_UNKNOWN", "confirmed", 1, None])
def test_unknown_or_malformed_source_status_is_rejected(status):
    with pytest.raises(ObligationValidationError):
        obligation("O1", "BASE_RULE", status)


def test_mapping_does_not_silently_normalize_unknown_source_status():
    with pytest.raises(ObligationValidationError):
        MaterialObligation.from_mapping(
            {
                "obligation_id": "O1",
                "issue_type": "BASE_RULE",
                "source_status": "SOURCE_CONFIRMED ",
            }
        )


def test_valid_confirmed_obligation_closes_through_evidence_and_proposition():
    source = evidence()
    proposition = closed_proposition(proposition_evidence=source)
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=(source.source_id,),
        proposition_ids=(proposition.proposition_id,),
    )

    result = evaluate_registry_closure((required,), (source,), (proposition,))

    assert result.registry_closure_passed is True
    assert result.violations == ()


def test_confirmed_obligation_with_verified_evidence_but_no_proposition_fails():
    source = evidence()
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=(source.source_id,),
    )

    result = evaluate_registry_closure((required,), (source,), ())

    assert result.registry_closure_passed is False
    assert "CONFIRMED_OBLIGATION_WITHOUT_PROPOSITION" in codes(result)


def test_confirmed_obligation_without_resolved_evidence_fails_closed():
    proposition = closed_proposition()
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=("law-base",),
        proposition_ids=(proposition.proposition_id,),
    )

    result = evaluate_registry_closure((required,), (), (proposition,))

    assert result.registry_closure_passed is False
    assert "CONFIRMED_EVIDENCE_UNRESOLVED" in codes(result)


def test_closed_proposition_without_explicit_resolved_evidence_fails():
    proposition = closed_proposition()

    result = evaluate_registry_closure((), (), (proposition,))

    assert result.registry_closure_passed is False
    assert "PROPOSITION_WITHOUT_REQUIRED_EVIDENCE" in codes(result)


def test_linked_proposition_with_different_evidence_reference_fails():
    required_source = evidence("law-base")
    proposition = closed_proposition(proposition_evidence=evidence("law-other"))
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=(required_source.source_id,),
        proposition_ids=(proposition.proposition_id,),
    )

    result = evaluate_registry_closure((required,), (required_source,), (proposition,))

    assert result.registry_closure_passed is False
    assert "PROPOSITION_WITHOUT_REQUIRED_EVIDENCE" in codes(result)


def test_unresolved_obligation_cannot_promote_a_closed_proposition():
    required = obligation(
        "O_RANGE",
        "RANGE_EXCEPTION",
        SOURCE_UNRESOLVED,
        proposition_ids=("P_RANGE",),
    )

    result = evaluate_registry_closure(
        (required,),
        (),
        (closed_proposition("P_RANGE"),),
    )

    assert result.registry_closure_passed is False
    assert "UNRESOLVED_SOURCE_PROMOTED_TO_CLOSED" in codes(result)


def test_unresolved_obligation_with_open_proposition_is_structurally_valid():
    required = obligation(
        "O_RANGE",
        "RANGE_EXCEPTION",
        SOURCE_UNRESOLVED,
        proposition_ids=("P_RANGE",),
    )

    result = evaluate_registry_closure((required,), (), (open_proposition(),))

    assert result.registry_closure_passed is True


def test_not_applicable_cannot_hide_evidence_or_proposition_links():
    required = obligation(
        "O_OPTIONAL",
        "OTHER_ISSUE",
        NOT_APPLICABLE,
        evidence_source_ids=("law-base",),
        proposition_ids=("P_BASE",),
    )

    result = evaluate_registry_closure(
        (required,),
        (evidence(),),
        (closed_proposition(),),
    )

    assert result.registry_closure_passed is False
    assert "NOT_APPLICABLE_WITH_LINKAGE" in codes(result)


def test_temporal_evidence_conflict_fails_closed():
    source = evidence("law-base", temporal_status="HISTORICAL_CONFIRMED")
    proposition = closed_proposition(proposition_evidence=source)
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=(source.source_id,),
        proposition_ids=(proposition.proposition_id,),
    )

    result = evaluate_registry_closure((required,), (source,), (proposition,))

    assert result.registry_closure_passed is False
    assert "TEMPORAL_CONTRADICTION" in codes(result)


def test_required_source_type_conflict_fails_closed():
    source = evidence()
    proposition = closed_proposition(
        proposition_evidence=source,
        required_source_type="precedent",
    )
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=(source.source_id,),
        proposition_ids=(proposition.proposition_id,),
    )

    result = evaluate_registry_closure((required,), (source,), (proposition,))

    assert result.registry_closure_passed is False
    assert "INSUFFICIENT_AUTHORITY" in codes(result)


def test_confirmed_obligation_requires_a_closed_canonical_proposition():
    source = evidence()
    proposition = open_proposition("P_BASE")
    required = obligation(
        "O_BASE",
        "BASE_RULE",
        SOURCE_CONFIRMED,
        evidence_source_ids=(source.source_id,),
        proposition_ids=(proposition.proposition_id,),
    )

    result = evaluate_registry_closure((required,), (source,), (proposition,))

    assert result.registry_closure_passed is False
    assert "CONFIRMED_OBLIGATION_NOT_CLOSED" in codes(result)


def test_required_exception_is_not_hidden_by_a_base_proposition_only():
    base_source = evidence("law-base")
    base = closed_proposition("P_BASE", proposition_evidence=base_source)
    required = (
        obligation(
            "O_BASE",
            "BASE_RULE",
            SOURCE_CONFIRMED,
            evidence_source_ids=(base_source.source_id,),
            proposition_ids=(base.proposition_id,),
        ),
        obligation(
            "O_RANGE",
            "RANGE_EXCEPTION",
            SOURCE_CONFIRMED,
            evidence_source_ids=("law-range",),
            proposition_ids=("P_RANGE",),
        ),
    )

    result = evaluate_registry_closure(required, (base_source,), (base,))

    assert result.registry_closure_passed is False
    assert "CONFIRMED_EVIDENCE_UNRESOLVED" in codes(result)
    assert "LINKED_PROPOSITION_MISSING" in codes(result)


def test_ledger_keeps_required_obligations_independent_from_propositions():
    ledger = MaterialObligationLedger(
        obligations=(
            obligation(
                "O_BASE",
                "BASE_RULE",
                SOURCE_CONFIRMED,
                evidence_source_ids=("law-base",),
                proposition_ids=("P_BASE",),
            ),
        ),
        verified_source_evidence=(evidence(),),
    )

    assert ledger.obligations[0].proposition_ids == ("P_BASE",)
    assert ledger.obligations[0].issue_type == "BASE_RULE"


def test_registry_service_persists_ledger_through_canonical_state_boundary(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    ledger = MaterialObligationLedger(
        obligations=(obligation("O_BASE", "BASE_RULE", SOURCE_UNRESOLVED),),
        verified_source_evidence=(),
    )

    updated = service.record_material_obligation_ledger(pending, ledger)
    loaded = service.read_state("session-a", "turn-1")

    assert updated.material_obligation_ledger == ledger
    assert loaded is not None
    assert loaded.material_obligation_ledger == ledger


def test_ledger_participates_in_registry_stale_state_protection(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    ledger = MaterialObligationLedger(
        obligations=(obligation("O_BASE", "BASE_RULE", SOURCE_UNRESOLVED),),
        verified_source_evidence=(),
    )
    service.record_material_obligation_ledger(pending, ledger)

    with pytest.raises(RuntimeStateError):
        service.record_material_obligation_ledger(pending, ledger)


def test_stop_gate_records_and_enforces_registry_closure(tmp_path):
    source = evidence()
    proposition = closed_proposition(proposition_evidence=source)
    ledger = MaterialObligationLedger(
        obligations=(
            obligation(
                "O_BASE",
                "BASE_RULE",
                SOURCE_CONFIRMED,
                evidence_source_ids=(source.source_id,),
                proposition_ids=(proposition.proposition_id,),
            ),
        ),
        verified_source_evidence=(source,),
    )
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    service.record_material_obligation_ledger(pending, ledger)

    state = service.read_state("session-a", "turn-1")
    assert state is not None
    assert state.material_obligation_ledger == ledger


def _active_state(
    propositions: tuple[LegalProposition, ...],
    ledger: MaterialObligationLedger,
) -> RuntimeTurnState:
    return RuntimeTurnState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=True,
        repair_count=0,
        propositions=list(propositions),
        registry_required=True,
        registry_completed=True,
        registry_invocation_count=1,
        material_obligation_ledger=ledger,
    )


def _adopted_draft(proposition: LegalProposition) -> str:
    contract = build_render_contract(proposition)
    return "\n".join(
        (
            "# 2. 검토결론",
            *(slot.text for slot in contract.slots),
            f"근거: {proposition.evidence.source_id} {proposition.evidence.source_title} "
            f"{proposition.evidence.source_locator}",
        )
    )


def test_stop_accepts_a_valid_material_obligation_registry_closure(tmp_path):
    source = evidence()
    proposition = closed_proposition(proposition_evidence=source)
    ledger = MaterialObligationLedger(
        obligations=(
            obligation(
                "O_BASE",
                "BASE_RULE",
                SOURCE_CONFIRMED,
                evidence_source_ids=(source.source_id,),
                proposition_ids=(proposition.proposition_id,),
            ),
        ),
        verified_source_evidence=(source,),
    )
    save_runtime_state(_active_state((proposition,), ledger), tmp_path)

    result = handle_stop_event(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "last_assistant_message": _adopted_draft(proposition),
        },
        tmp_path,
    )
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result == {}
    assert stored is not None
    assert stored.first_reconciliation["registry_closure"]["registry_closure_passed"] is True


def test_stop_blocks_when_required_obligation_is_missing_from_canonical_registry(tmp_path):
    source = evidence()
    proposition = closed_proposition(proposition_evidence=source)
    ledger = MaterialObligationLedger(
        obligations=(
            obligation(
                "O_BASE",
                "BASE_RULE",
                SOURCE_CONFIRMED,
                evidence_source_ids=(source.source_id,),
                proposition_ids=(proposition.proposition_id,),
            ),
            obligation(
                "O_RANGE",
                "RANGE_EXCEPTION",
                SOURCE_CONFIRMED,
                evidence_source_ids=("law-range",),
                proposition_ids=("P_RANGE",),
            ),
        ),
        verified_source_evidence=(source,),
    )
    save_runtime_state(_active_state((proposition,), ledger), tmp_path)

    result = handle_stop_event(
        {
            "session_id": "session-a",
            "turn_id": "turn-1",
            "last_assistant_message": _adopted_draft(proposition),
        },
        tmp_path,
    )
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result["decision"] == "block"
    assert "registry_closure" in result["reason"]
    assert stored is not None
    assert stored.first_reconciliation["registry_closure"]["registry_closure_passed"] is False


def test_stop_ignores_a_shadow_obligation_artifact(tmp_path):
    source = evidence()
    proposition = closed_proposition(proposition_evidence=source)
    ledger = MaterialObligationLedger(
        obligations=(
            obligation(
                "O_BASE",
                "BASE_RULE",
                SOURCE_CONFIRMED,
                evidence_source_ids=(source.source_id,),
                proposition_ids=(proposition.proposition_id,),
            ),
        ),
        verified_source_evidence=(source,),
    )
    save_runtime_state(_active_state((proposition,), ledger), tmp_path)
    (tmp_path / "shadow-obligation-ledger.json").write_text(
        json.dumps(
            {
                "obligations": [
                    {
                        "obligation_id": "O_STALE",
                        "issue_type": "STALE_ISSUE",
                        "source_status": "SOURCE_CONFIRMED",
                        "evidence_source_ids": ["missing"],
                        "proposition_ids": ["P_STALE"],
                    }
                ],
                "verified_source_evidence": [],
            }
        ),
        encoding="utf-8",
    )

    assert (
        handle_stop_event(
            {
                "session_id": "session-a",
                "turn_id": "turn-1",
                "last_assistant_message": _adopted_draft(proposition),
            },
            tmp_path,
        )
        == {}
    )


def test_malformed_persisted_ledger_fails_closed(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    path = runtime_state_path(tmp_path, pending.session_id, pending.turn_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["material_obligation_ledger"] = {
        "obligations": [
            {
                "obligation_id": "O1",
                "issue_type": "BASE_RULE",
                "source_status": "UNKNOWN",
                "evidence_source_ids": [],
                "proposition_ids": [],
            }
        ],
        "verified_source_evidence": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        service.read_state("session-a", "turn-1")


def test_present_ledger_without_required_top_level_fields_fails_closed(tmp_path):
    service = RegistryService(tmp_path)
    pending = service.begin_pending("session-a", "turn-1")
    path = runtime_state_path(tmp_path, pending.session_id, pending.turn_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["material_obligation_ledger"] = {}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(RuntimeStateError):
        service.read_state("session-a", "turn-1")


def test_task8_required_active_state_without_ledger_fails_closed():
    with pytest.raises(RuntimeStateError):
        RuntimeTurnState(
            schema_version=3,
            session_id="session-a",
            turn_id="turn-1",
            registry_active=True,
            repair_count=0,
            propositions=[],
            registry_required=True,
            registry_completed=True,
            registry_invocation_count=1,
            material_obligation_ledger_required=True,
        )


def test_begin_pending_can_explicitly_require_task8_ledger(tmp_path):
    pending = RegistryService(tmp_path).begin_pending(
        "session-a",
        "turn-1",
        material_obligations_required=True,
    )

    assert pending.material_obligation_ledger_required is True


def test_task8_does_not_add_a_second_runtime_reader():
    source = Path("scripts/stop_synthesis_gate.py").read_text(encoding="utf-8")

    assert "load_runtime_state" not in source
    assert ".read_state(" in source
