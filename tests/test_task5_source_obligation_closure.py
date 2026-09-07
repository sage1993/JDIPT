import importlib

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_rendering import build_render_contract
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeTurnState,
    load_runtime_state,
    save_runtime_state,
)


def _module(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        return None


def _proposition(
    *,
    proposition_id: str = "P1",
    authority_kind: str = "statute",
    temporal_status: str = "CURRENT_CONFIRMED",
    evidence_span: str = "행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다.",
    status: PropositionStatus = PropositionStatus.CLOSED,
    materiality: Materiality = Materiality.MATERIAL,
    modality: Modality = Modality.MAY,
    relation_type: str | None = "base",
    base_proposition_id: str | None = None,
    exception_proposition_id: str | None = None,
    polarity: Polarity = Polarity.POSITIVE,
    exception_rule: str | None = None,
) -> LegalProposition:
    evidence = None
    if evidence_span is not None:
        evidence = EvidenceRef(
            source_id="law-001",
            authority_kind=authority_kind,
            source_title="검증 법령",
            source_locator="https://example.test/law-001",
            evidence_span=evidence_span,
            temporal_status=temporal_status,
            temporal_render_text="현행 기준에 따른다.",
        )
    return LegalProposition(
        proposition_id=proposition_id,
        status=status,
        materiality=materiality,
        subject="행정청",
        condition="요건 C",
        procedure="절차 P",
        modality=modality,
        legal_action="지정",
        operative_verb_lexeme="지정",
        legal_object="대상 O",
        legal_effect="지위 Z",
        polarity=polarity,
        relation_type=relation_type,
        base_proposition_id=base_proposition_id,
        exception_proposition_id=exception_proposition_id,
        evidence=evidence,
        exception_rule=exception_rule,
    )


def _source_result(propositions, draft):
    module = _module("scripts.proposition_source_closure")
    assert module is not None, "Task 5 source closure module is not implemented"
    return module.evaluate_source_closure(propositions, draft)


def _obligation_result(propositions, draft):
    module = _module("scripts.proposition_obligation_closure")
    assert module is not None, "Task 5 obligation closure module is not implemented"
    contracts = [build_render_contract(item) for item in propositions]
    return module.evaluate_obligation_closure(propositions, contracts, draft)


def _source_anchor(proposition: LegalProposition) -> str:
    return "근거: law-001 검증 법령 https://example.test/law-001"


def _adopted_draft(proposition: LegalProposition) -> str:
    contract = build_render_contract(proposition)
    return "\n".join(
        (
            "# 2. 검토결론",
            contract.slots[0].text,
            contract.slots[1].text,
            _source_anchor(proposition),
        )
    )


def _codes(result) -> set[str]:
    return {item.code for item in result.violations}


def _runtime_state(proposition: LegalProposition, *, repair_count: int = 0):
    return RuntimeTurnState(
        schema_version=RUNTIME_STATE_SCHEMA_VERSION,
        session_id="session-a",
        turn_id="turn-1",
        registry_active=True,
        repair_count=repair_count,
        propositions=[proposition],
    )


def _stop_event(message: str, *, stop_hook_active: bool = False) -> dict:
    return {
        "session_id": "session-a",
        "turn_id": "turn-1",
        "stop_hook_active": stop_hook_active,
        "last_assistant_message": message,
    }


def test_missing_source_is_not_source_closed():
    proposition = _proposition(status=PropositionStatus.OPEN, evidence_span=None)

    result = _source_result((proposition,), "# 2. 검토결론\n확인 필요")

    assert result.source_closure_passed is False
    assert "SOURCE_REQUIRED_BUT_MISSING" in _codes(result)


def test_irrelevant_source_span_is_not_supporting():
    proposition = _proposition(evidence_span="다른 기관의 일반적인 절차를 설명하는 문장이다.")

    result = _source_result((proposition,), _adopted_draft(proposition))

    assert result.source_closure_passed is False
    assert _codes(result) & {
        "SOURCE_PRESENT_BUT_NOT_SUPPORTING",
        "SOURCE_PROPOSITION_MISMATCH",
    }


def test_lower_authority_source_does_not_satisfy_primary_requirement():
    proposition = _proposition(authority_kind="guidance")

    result = _source_result((proposition,), _adopted_draft(proposition))

    assert result.authority_closure_passed is False
    assert "INSUFFICIENT_AUTHORITY" in _codes(result)


def test_outdated_source_does_not_satisfy_current_requirement():
    proposition = _proposition(temporal_status="HISTORICAL_CONFIRMED")

    result = _source_result((proposition,), _adopted_draft(proposition))

    assert result.temporal_source_closure_passed is False
    assert "OUTDATED_SOURCE_USED" in _codes(result)


def test_unresolved_temporal_source_is_not_closed():
    proposition = _proposition(temporal_status="CURRENT_UNRESOLVED")

    result = _source_result((proposition,), _adopted_draft(proposition))

    assert result.temporal_source_closure_passed is False
    assert "TEMPORAL_SOURCE_UNRESOLVED" in _codes(result)


def test_material_source_citation_is_required_in_final_answer():
    proposition = _proposition()
    draft = build_render_contract(proposition).slots[0].text

    result = _source_result((proposition,), draft)

    assert "MATERIAL_SOURCE_OMITTED" in _codes(result)
    assert result.assessments[0].status.value == "SOURCE_TEMPORALLY_VALID"


def test_source_closure_keeps_positive_state_and_forensic_fields():
    proposition = _proposition()
    result = _source_result((proposition,), _adopted_draft(proposition))
    module = _module("scripts.proposition_source_closure")

    assert result.source_closure_passed is True
    assert result.assessments[0].status.value == "SOURCE_CLOSED"
    payload = module.source_closure_result_to_dict(result)
    assessment = payload["assessments"][0]
    assert assessment["source_id"] == "law-001"
    assert assessment["source_span"] == proposition.evidence.evidence_span
    assert assessment["required_authority"] == "PRIMARY"
    assert assessment["actual_temporal_status"] == "CURRENT_CONFIRMED"


def test_source_with_opposite_legal_polarity_is_not_supporting():
    proposition = _proposition(
        evidence_span="행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정하여서는 안 된다."
    )

    result = _source_result((proposition,), _adopted_draft(proposition))

    assert "SOURCE_PROPOSITION_MISMATCH" in _codes(result)


def test_source_citation_in_rejected_region_does_not_close_source():
    proposition = _proposition()
    effect = build_render_contract(proposition).slots[0].text
    draft = f"# 2. 검토결론\n반대 견해: {effect}\n근거: law-001 검증 법령 https://example.test/law-001"

    result = _source_result((proposition,), draft)

    assert "MATERIAL_SOURCE_OMITTED" in _codes(result)


def test_must_obligation_cannot_be_dropped():
    proposition = _proposition(modality=Modality.MUST)
    draft = "# 2. 검토결론\n행정청은 해당 절차를 고려할 수 있다."

    result = _obligation_result((proposition,), draft)

    assert result.obligation_closure_passed is False
    assert "OBLIGATION_DROPPED" in _codes(result)


def test_missing_render_contract_cannot_close_material_obligation():
    proposition = _proposition()

    module = _module("scripts.proposition_obligation_closure")
    result = module.evaluate_obligation_closure(
        (proposition,),
        (),
        _adopted_draft(proposition),
    )

    assert result.obligation_closure_passed is False
    assert "OBLIGATION_DROPPED" in _codes(result)


def test_must_cannot_be_degraded_to_may():
    proposition = _proposition(modality=Modality.MUST)
    draft = "# 2. 검토결론\n요건 C와 절차 P가 있으면 행정청은 대상 O를 지위 Z로 지정할 수 있다."

    result = _obligation_result((proposition,), draft)

    assert "MUST_DEGRADED_TO_MAY" in _codes(result)


def test_must_not_cannot_become_caution_only():
    proposition = _proposition(modality=Modality.MUST_NOT)
    draft = "# 2. 검토결론\n행정청은 대상 O에 대하여 주의하는 것이 좋다."

    result = _obligation_result((proposition,), draft)

    assert "MUST_NOT_DEGRADED" in _codes(result)


def test_condition_is_not_optional_in_final_conclusion():
    proposition = _proposition()
    draft = "# 2. 검토결론\n행정청은 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다."

    result = _obligation_result((proposition,), draft)

    assert "CONDITION_DROPPED" in _codes(result)


def test_procedure_is_not_optional_in_final_conclusion():
    proposition = _proposition()
    draft = "# 2. 검토결론\n요건 C를 충족하면 행정청은 대상 O를 지위 Z로 지정할 수 있다."

    result = _obligation_result((proposition,), draft)

    assert "PROCEDURAL_PREREQUISITE_DROPPED" in _codes(result)


def test_exception_is_not_generalized_away():
    proposition = _proposition(
        relation_type="exception",
        exception_rule="예외 요건 E",
    )
    draft = "# 2. 검토결론\n요건 C와 절차 P가 있으면 행정청은 대상 O를 지위 Z로 지정할 수 있다."

    result = _obligation_result((proposition,), draft)

    assert "EXCEPTION_DROPPED" in _codes(result)


def test_obligation_in_rejected_quotation_does_not_close():
    proposition = _proposition()
    effect = build_render_contract(proposition).slots[0].text
    draft = f"# 2. 검토결론\n반대 견해: {effect}"

    result = _obligation_result((proposition,), draft)

    assert "OBLIGATION_DROPPED" in _codes(result)


def test_missing_dependency_is_not_closed():
    proposition = _proposition(exception_proposition_id="P2")

    result = _obligation_result((proposition,), _adopted_draft(proposition))

    assert result.dependency_closure_passed is False
    assert "DEPENDENCY_OMITTED" in _codes(result)


def test_open_dependency_blocks_definitive_parent():
    parent = _proposition(exception_proposition_id="P2")
    dependency = _proposition(
        proposition_id="P2",
        status=PropositionStatus.OPEN,
        evidence_span=None,
    )

    result = _obligation_result(
        (parent, dependency),
        _adopted_draft(parent),
    )

    assert "DEPENDENCY_OPEN" in _codes(result)


def test_dependency_in_rejected_quotation_does_not_close():
    parent = _proposition(exception_proposition_id="P2")
    dependency = _proposition(proposition_id="P2")
    dependency_effect = build_render_contract(dependency).slots[0].text
    draft = "\n".join(
        (
            "# 2. 검토결론",
            build_render_contract(parent).slots[0].text,
            _source_anchor(parent),
            f"반대 견해: {dependency_effect}",
        )
    )

    result = _obligation_result((parent, dependency), draft)

    assert result.dependency_closure_passed is False
    assert "DEPENDENCY_OMITTED" in _codes(result)


def test_unsupported_final_conclusion_is_not_closed():
    proposition = _proposition()
    draft = "# 2. 검토결론\n일반적으로 허용된다."

    result = _obligation_result((proposition,), draft)

    assert result.final_conclusion_support_passed is False
    assert "FINAL_CONCLUSION_UNSUPPORTED" in _codes(result)


def test_non_material_proposition_does_not_force_source_closure():
    proposition = _proposition(
        materiality=Materiality.NON_MATERIAL,
        evidence_span=None,
        status=PropositionStatus.OPEN,
    )

    source_result = _source_result((proposition,), "# 2. 검토결론\n설명")
    obligation_result = _obligation_result((proposition,), "# 2. 검토결론\n설명")

    assert source_result.source_closure_passed is True
    assert obligation_result.obligation_closure_passed is True


def test_stop_blocks_when_coverage_and_soundness_pass_but_source_is_omitted(tmp_path):
    proposition = _proposition()
    save_runtime_state(_runtime_state(proposition), tmp_path)
    contract = build_render_contract(proposition)
    draft = "# 2. 검토결론\n" + "\n".join(slot.text for slot in contract.slots)

    result = handle_stop_event(_stop_event(draft), tmp_path)
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result["decision"] == "block"
    assert stored.first_reconciliation["covered"] is True
    assert stored.first_reconciliation["soundness"]["soundness_passed"] is True
    assert stored.first_reconciliation["source_closure"]["source_closure_passed"] is False
    assert "MATERIAL_SOURCE_OMITTED" in {
        item["code"] for item in stored.first_reconciliation["source_closure"]["violations"]
    }


def test_stop_persists_source_and_obligation_closure_independently(tmp_path):
    proposition = _proposition()
    save_runtime_state(_runtime_state(proposition), tmp_path)

    result = handle_stop_event(_stop_event(_adopted_draft(proposition)), tmp_path)
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result == {}
    assert stored.first_reconciliation["source_closure"]["source_closure_passed"] is True
    assert stored.first_reconciliation["obligation_closure"]["obligation_closure_passed"] is True
    assert stored.first_reconciliation["overall_covered"] is True


def test_stop_blocks_final_conclusion_modality_degradation_after_valid_effect_slot(tmp_path):
    proposition = _proposition(modality=Modality.MUST)
    save_runtime_state(_runtime_state(proposition), tmp_path)
    contract = build_render_contract(proposition)
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "요건 C와 절차 P가 있으면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
            "# 3. 검토이유",
            contract.slots[0].text,
            contract.slots[1].text,
            _source_anchor(proposition),
        )
    )

    result = handle_stop_event(_stop_event(draft), tmp_path)
    stored = load_runtime_state("session-a", "turn-1", tmp_path)

    assert result["decision"] == "block"
    assert stored.first_reconciliation["covered"] is True
    assert stored.first_reconciliation["soundness"]["soundness_passed"] is True
    assert "MUST_DEGRADED_TO_MAY" in {
        item["code"] for item in stored.first_reconciliation["obligation_closure"]["violations"]
    }


def test_second_task5_failure_is_fail_closed_without_continuation(tmp_path):
    proposition = _proposition()
    save_runtime_state(_runtime_state(proposition, repair_count=1), tmp_path)

    result = handle_stop_event(
        _stop_event("# 2. 검토결론\n일반적으로 허용된다.", stop_hook_active=True),
        tmp_path,
    )

    assert result["continue"] is False
    assert "failed-closed" in result["systemMessage"]
