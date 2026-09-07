from dataclasses import replace

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract
from scripts.proposition_soundness import (
    evaluate_soundness,
    soundness_result_to_dict,
)


def _evidence():
    return EvidenceRef(
        source_id="law-001",
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/조문",
        evidence_span="확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="2026-09-04 현재 시행 중인 기준이다.",
    )


def _closed_proposition(
    *,
    proposition_id: str = "P1",
    polarity: Polarity = Polarity.POSITIVE,
):
    return LegalProposition(
        proposition_id=proposition_id,
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition="요건",
        procedure="절차",
        modality=Modality.MAY,
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="대상",
        legal_effect="법적 지위",
        polarity=polarity,
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=_evidence(),
    )


def _open_proposition():
    return LegalProposition(
        proposition_id="P_OPEN",
        status=PropositionStatus.OPEN,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition="적용 요건 확인",
        procedure="절차 확인",
        modality=None,
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="대상",
        legal_effect="법적 지위",
        polarity=None,
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=None,
    )


def _codes(result):
    return {violation.code for violation in result.violations}


def _covered_draft(proposition):
    contract = build_render_contract(proposition)
    return contract, "\n".join(slot.text for slot in contract.slots)


def test_rejected_quotation_only_has_coverage_but_fails_soundness():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"다음 견해가 제시될 수 있다: '{rendered}' 그러나 이 견해는 타당하지 않다."

    coverage = reconcile_render_contracts([contract], draft)
    soundness = evaluate_soundness([proposition], [contract], draft)

    assert coverage.covered
    assert not soundness.soundness_passed
    assert _codes(soundness) == {"REJECTED_QUOTATION_ONLY"}
    assert soundness.violations[0].matched_region == "quotation"
    assert soundness.violations[0].matched_span


def test_fenced_code_block_only_is_not_an_adopted_proposition():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"```text\n{rendered}\n```"

    coverage = reconcile_render_contracts([contract], draft)
    soundness = evaluate_soundness([proposition], [contract], draft)

    assert coverage.covered
    assert not soundness.soundness_passed
    assert _codes(soundness) == {"CODE_BLOCK_OR_EXAMPLE_ONLY"}
    assert soundness.violations[0].matched_region == "code_block"


def test_example_only_is_not_an_adopted_proposition():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"예시:\n\n    {rendered}"

    coverage = reconcile_render_contracts([contract], draft)
    soundness = evaluate_soundness([proposition], [contract], draft)

    assert coverage.covered
    assert not soundness.soundness_passed
    assert _codes(soundness) == {"CODE_BLOCK_OR_EXAMPLE_ONLY"}
    assert soundness.violations[0].matched_region == "example"


def test_explicitly_rejected_alternative_cannot_count_as_adopted():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"반대 견해:\n{rendered}\n이 견해는 타당하지 않다."

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert _codes(soundness) == {"REJECTED_QUOTATION_ONLY"}
    assert soundness.violations[0].matched_region == "rejected_alternative"


def test_discussed_proposition_followed_by_rejection_cannot_count_as_adopted():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"검토 대상 명제는 다음과 같다. {rendered} 그러나 이 명제는 타당하지 않다."

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert _codes(soundness) == {"REJECTED_QUOTATION_ONLY"}
    assert soundness.violations[0].matched_region == "rejected_alternative"


def test_open_same_direction_definitive_conclusion_is_not_closed():
    proposition = _open_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"{rendered}\n결론: 따라서 이 행위는 허용된다."

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert _codes(soundness) == {"OPEN_PROMOTED_TO_CLOSED"}
    assert soundness.violations[0].proposition_status is PropositionStatus.OPEN
    assert "허용된다" in soundness.violations[0].final_conclusion_span


def test_open_opposite_direction_definitive_conclusion_is_not_closed():
    proposition = _open_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"{rendered}\n결론: 따라서 이 행위는 허용되지 않는다."

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert _codes(soundness) == {"OPEN_PROMOTED_TO_CLOSED"}


def test_positive_canonical_polarity_rejects_negative_final_conclusion():
    proposition = _closed_proposition(polarity=Polarity.POSITIVE)
    contract, rendered = _covered_draft(proposition)
    draft = (
        f"{rendered}\n결론: 요건과 절차에 따라 행정청은 대상에 법적 지위로 지정할 수 있지만 "
        "결국 불가능하다."
    )

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert "POLARITY_CONTRADICTION" in _codes(soundness)
    violation = next(
        item for item in soundness.violations if item.code == "POLARITY_CONTRADICTION"
    )
    assert violation.polarity is Polarity.POSITIVE


def test_negative_canonical_polarity_rejects_positive_final_conclusion():
    proposition = _closed_proposition(polarity=Polarity.NEGATIVE)
    contract, rendered = _covered_draft(proposition)
    draft = f"{rendered}\n결론: 요건과 절차에 따라 행정청은 대상에 법적 지위로 지정할 수 있다."

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert "POLARITY_CONTRADICTION" in _codes(soundness)


def test_condition_bypass_is_a_final_conclusion_contradiction():
    proposition = _closed_proposition(polarity=Polarity.POSITIVE)
    contract, rendered = _covered_draft(proposition)
    draft = (
        f"{rendered}\n결론: 요건과 관계없이 절차를 거쳐도 행정청은 대상에 법적 지위로 "
        "지정할 수 없으므로 불가능하다."
    )

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert not soundness.soundness_passed
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(soundness)


def test_generic_relaxation_does_not_preserve_source_specific_relation():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"분석에서 확인한 내용:\n{rendered}\n결론: 일부 완화가 가능하다."

    coverage = reconcile_render_contracts([contract], draft)
    soundness = evaluate_soundness([proposition], [contract], draft)

    assert coverage.covered
    assert not soundness.soundness_passed
    assert _codes(soundness) == {"LEGAL_RELATION_DEGRADATION"}
    violation = soundness.violations[0]
    assert violation.relation_fields
    assert "legal_action" in violation.relation_fields


def test_quotation_plus_separate_adopted_proposition_passes():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"반대 견해의 인용: '{rendered}'\n분석: {rendered}"

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert soundness.soundness_passed
    assert soundness.violations == ()


def test_fully_consistent_adopted_answer_passes():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"# 2. 검토결론\n{rendered}\n# 3. 검토이유\n위 결론은 같은 관계를 전제로 한다."

    soundness = evaluate_soundness([proposition], [contract], draft)

    assert soundness.soundness_passed
    assert soundness.violations == ()


def test_soundness_evidence_serializes_typed_fields_and_spans():
    proposition = _closed_proposition()
    contract, rendered = _covered_draft(proposition)
    draft = f"```text\n{rendered}\n```"
    result = evaluate_soundness([proposition], [contract], draft)

    evidence = soundness_result_to_dict(result)

    assert evidence["soundness_passed"] is False
    violation = evidence["violations"][0]
    assert violation["code"] == "CODE_BLOCK_OR_EXAMPLE_ONLY"
    assert violation["proposition_status"] == "CLOSED"
    assert violation["materiality"] == "MATERIAL"
    assert violation["modality"] == "MAY"
    assert violation["polarity"] == "POSITIVE"
    assert violation["matched_span"]
    assert violation["final_conclusion_span"] == ""


def test_non_material_proposition_has_no_soundness_obligation():
    proposition = replace(
        _closed_proposition(),
        materiality=Materiality.NON_MATERIAL,
    )

    result = evaluate_soundness([proposition], [], "어떤 보조 설명")

    assert result.soundness_passed
    assert result.violations == ()
