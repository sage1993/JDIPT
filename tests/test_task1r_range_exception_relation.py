from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_relations import (
    build_range_exception_relation,
    reconcile_range_exception_relation,
    render_range_exception_relation,
)


def _evidence(source_id="law-range-001"):
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/제1조",
        evidence_span="기본 기준과 예외 조건이 함께 확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="현행 기준에 따른다.",
    )


def _base():
    return LegalProposition(
        proposition_id="BASE_RANGE",
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition="기본 요건",
        procedure="기본 절차",
        modality=Modality.MUST,
        legal_action="apply",
        operative_verb_lexeme="적용",
        legal_object="사업대상지",
        legal_effect="기본 기준 적용",
        polarity=Polarity.POSITIVE,
        relation_type="base",
        base_proposition_id=None,
        exception_proposition_id="EXCEPTION_RANGE",
        base_rule="승강장 경계로부터 100m 이내",
        exception_rule=None,
        evidence=_evidence("law-range-base"),
    )


def _exception():
    return LegalProposition(
        proposition_id="EXCEPTION_RANGE",
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject="행정청",
        condition="특정 입지 요건을 충족하는 경우",
        procedure="통합심의를 거치면",
        modality=Modality.MAY,
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="사업대상지",
        legal_effect="예외 대상 지정",
        polarity=Polarity.POSITIVE,
        relation_type="exception to BASE_RANGE",
        base_proposition_id="BASE_RANGE",
        exception_proposition_id=None,
        base_rule="승강장 경계로부터 100m 이내",
        exception_rule="승강장 경계로부터 150m 이내",
        evidence=_evidence(),
    )


def test_relation_preserves_structured_graph_and_source_identity():
    relation = build_range_exception_relation([_base(), _exception()])

    assert relation is not None
    assert relation.base_proposition_id == "BASE_RANGE"
    assert relation.exception_proposition_id == "EXCEPTION_RANGE"
    assert relation.base_rule == "승강장 경계로부터 100m 이내"
    assert relation.exception_rule == "승강장 경계로부터 150m 이내"
    assert relation.base_value == "100m"
    assert relation.exception_value == "150m"
    assert relation.condition == "특정 입지 요건을 충족하는 경우"
    assert relation.procedure == "통합심의를 거치면"
    assert relation.legal_action == "designate"
    assert relation.legal_object == "사업대상지"
    assert relation.legal_effect == "예외 대상 지정"
    assert relation.source_id == "law-range-001"
    assert relation.evidence_span == "기본 기준과 예외 조건이 함께 확인된 원문"


def test_same_span_ordered_relation_passes():
    relation = build_range_exception_relation([_base(), _exception()])
    draft = render_range_exception_relation(relation)

    result = reconcile_range_exception_relation([_base(), _exception()], draft)

    assert result is not None
    assert result.covered is True
    assert result.source_proposition_ids == ("BASE_RANGE", "EXCEPTION_RANGE")


def test_token_cooccurrence_across_separate_sentences_fails():
    draft = (
        "기본 기준은 승강장 경계로부터 100m 이내이다. "
        "예외 기준은 승강장 경계로부터 150m 이내이다. "
        "특정 입지 요건과 통합심의, 사업대상지 지정만 검토한다."
    )

    result = reconcile_range_exception_relation([_base(), _exception()], draft)

    assert result is not None
    assert result.covered is False
    assert "relation_span" in result.missing_fields


def test_reversed_range_direction_fails():
    draft = (
        "기본 기준은 승강장 경계로부터 150m 이내이고 예외 기준은 "
        "승강장 경계로부터 100m 이내인 경우, 특정 입지 요건을 충족하는 경우 "
        "통합심의를 거치면 행정청은 사업대상지를 예외 대상 지정으로 지정할 수 있다."
    )

    result = reconcile_range_exception_relation([_base(), _exception()], draft)

    assert result is not None
    assert result.covered is False
    assert "base_rule" in result.missing_fields


def test_generic_relaxation_does_not_preserve_legal_effect_relation():
    draft = (
        "기본 기준은 승강장 경계로부터 100m 이내이고 예외 기준은 "
        "승강장 경계로부터 150m 이내인 경우, 특정 입지 요건을 충족하는 경우 "
        "통합심의를 거치면 행정청은 사업대상지의 범위를 완화할 수 있다."
    )

    result = reconcile_range_exception_relation([_base(), _exception()], draft)

    assert result is not None
    assert result.covered is False
    assert "legal_effect" in result.missing_fields
