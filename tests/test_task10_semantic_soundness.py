from dataclasses import replace

import pytest

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
from scripts.proposition_soundness import evaluate_soundness
from scripts.proposition_soundness import SoundnessResult
from scripts.proposition_soundness import classify_answer_regions


def _evidence(source_id: str = "law-001") -> EvidenceRef:
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title="검증 법령",
        source_locator=f"https://example.test/{source_id}",
        evidence_span="행정청은 요건 C를 충족하고 절차 P를 거쳐 대상 O를 지위 Z로 지정할 수 있다.",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="현행 기준에 따른다.",
    )


def _proposition(
    *,
    proposition_id: str = "P1",
    status: PropositionStatus = PropositionStatus.CLOSED,
    materiality: Materiality = Materiality.MATERIAL,
    modality: Modality = Modality.MAY,
    polarity: Polarity = Polarity.POSITIVE,
    relation_type: str | None = "base",
    legal_action: str = "지정",
    operative_verb_lexeme: str = "지정",
    legal_object: str = "대상 O",
    legal_effect: str = "지위 Z",
    condition: str = "요건 C",
    procedure: str = "절차 P",
    evidence: EvidenceRef | None = None,
) -> LegalProposition:
    return LegalProposition(
        proposition_id=proposition_id,
        status=status,
        materiality=materiality,
        subject="행정청",
        condition=condition,
        procedure=procedure,
        modality=modality,
        legal_action=legal_action,
        operative_verb_lexeme=operative_verb_lexeme,
        legal_object=legal_object,
        legal_effect=legal_effect,
        polarity=polarity,
        relation_type=relation_type,
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=evidence if evidence is not None else _evidence(),
    )


def _codes(result) -> set[str]:
    return {violation.code for violation in result.violations}


def _rendered(proposition: LegalProposition) -> str:
    return "\n".join(slot.text for slot in build_render_contract(proposition).slots)


def _draft_with_contract(
    proposition: LegalProposition,
    *,
    prefix: str = "",
    suffix: str = "",
) -> str:
    rendered = _rendered(proposition)
    body = rendered if not prefix else f"{prefix}{rendered}"
    if suffix:
        body = f"{body}{suffix}"
    return body


def _soundness(proposition: LegalProposition, draft: str):
    contract = build_render_contract(proposition)
    return evaluate_soundness([proposition], [contract], draft)


def _soundness_many(propositions: list[LegalProposition], draft: str):
    contracts = [build_render_contract(proposition) for proposition in propositions]
    return evaluate_soundness(propositions, contracts, draft)


def _coverage(contract, draft: str):
    return reconcile_render_contracts([contract], draft)


def _empty_contract_authority():
    return []


def test_closed_positive_with_matching_final_adoption_passes():
    proposition = _proposition()
    draft = _draft_with_contract(
        proposition,
        prefix="# 2. 검토결론\n",
        suffix="\n# 3. 검토이유\n위 결론은 같은 전제를 따른다.",
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is True
    assert soundness.violations == ()


def test_closed_negative_with_matching_final_adoption_passes():
    proposition = _proposition(
        polarity=Polarity.NEGATIVE,
        legal_action="금지",
        operative_verb_lexeme="금지",
    )
    draft = _rendered(proposition)

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is True
    assert soundness.violations == ()


def test_exact_proposition_with_harmless_extra_prose_passes():
    proposition = _proposition()
    draft = f"추가 설명이 있습니다. {_rendered(proposition)}. 추가 설명이 이어집니다."

    soundness = _soundness(proposition, draft)

    assert soundness.soundness_passed is True


def test_duplicate_consistent_adoption_passes():
    proposition = _proposition()
    rendered = _rendered(proposition)
    draft = f"{rendered}\n{rendered}"

    soundness = _soundness(proposition, draft)

    assert soundness.soundness_passed is True


def test_source_quote_plus_separate_correct_conclusion_passes():
    proposition = _proposition()
    rendered = _rendered(proposition)
    draft = f"반대 견해의 인용: '{rendered}'\n분석: {rendered}"

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is True


def test_open_proposition_remains_explicitly_open():
    proposition = _proposition(status=PropositionStatus.OPEN, evidence=None)
    draft = "확인 필요: 요건 C와 절차 P에 관한 근거와 적용 여부는 현재 확정할 수 없다."

    soundness = _soundness(proposition, draft)

    assert soundness.soundness_passed is True


def test_required_proposition_and_exception_adopted_consistently_passes():
    base = _proposition(proposition_id="P1")
    exception = _proposition(
        proposition_id="P2",
        relation_type="exception",
        legal_action="제외",
        operative_verb_lexeme="제외",
        legal_object="예외 대상",
        legal_effect="예외 효과",
    )
    draft = "\n".join(
        (
            "# 2. 검토결론",
            _rendered(base),
            _rendered(exception),
            "위 결론은 본칙과 예외를 함께 반영한다.",
        )
    )

    coverage = _coverage(build_render_contract(base), draft)
    base_soundness = _soundness_many([base, exception], draft)

    assert coverage.covered is True
    assert base_soundness.soundness_passed is True
    assert _codes(base_soundness) == set()


def test_rejected_quotation_only_has_coverage_but_fails_soundness():
    proposition = _proposition()
    rendered = _rendered(proposition)
    draft = f"다음 견해가 제시될 수 있다: '{rendered}' 그러나 이 견해는 타당하지 않다."

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"REJECTED_QUOTATION_ONLY"}
    assert soundness.violations[0].matched_region == "quotation"


def test_code_block_only_has_coverage_but_fails_soundness():
    proposition = _proposition()
    rendered = _rendered(proposition)
    draft = f"```text\n{rendered}\n```"

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"CODE_BLOCK_OR_EXAMPLE_ONLY"}
    assert soundness.violations[0].matched_region == "code_block"


def test_example_only_has_coverage_but_fails_soundness():
    proposition = _proposition()
    rendered = _rendered(proposition)
    draft = f"예시:\n\n    {rendered}"

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"CODE_BLOCK_OR_EXAMPLE_ONLY"}
    assert soundness.violations[0].matched_region == "example"


def test_open_proposition_with_definitive_positive_conclusion_fails():
    proposition = _proposition(status=PropositionStatus.OPEN, evidence=None)
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 따라서 이 행위는 허용된다.",
            "",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"OPEN_PROMOTED_TO_CLOSED"}


def test_open_proposition_with_definitive_negative_conclusion_fails():
    proposition = _proposition(status=PropositionStatus.OPEN, evidence=None)
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 따라서 이 행위는 허용되지 않는다.",
            "",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"OPEN_PROMOTED_TO_CLOSED"}


def test_positive_canonical_polarity_rejects_negative_final_conclusion():
    proposition = _proposition()
    draft = f"{_rendered(proposition)}\n결론: 요건 C와 절차 P에 따라 행정청은 대상 O를 지위 Z로 지정할 수 있지만 결국 불가능하다."

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert "POLARITY_CONTRADICTION" in _codes(soundness)


def test_negative_canonical_polarity_rejects_positive_final_conclusion():
    proposition = _proposition(
        polarity=Polarity.NEGATIVE,
        legal_action="금지",
        operative_verb_lexeme="금지",
    )
    draft = f"{_rendered(proposition)}\n결론: 요건 C와 절차 P에 따라 행정청은 대상 O를 지위 Z로 지정할 수 있다."

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert "POLARITY_CONTRADICTION" in _codes(soundness)


def test_must_weakened_to_may_fails_with_structured_violation():
    proposition = _proposition(modality=Modality.MUST)
    conclusion = "결론: 요건 C를 충족하고 절차 P를 거치면 행정청은 대상 O를 지위 Z로 지정할 수 있다."
    assert all(value in conclusion for value in (
        proposition.condition, proposition.procedure, proposition.operative_verb_lexeme,
        proposition.legal_object, proposition.legal_effect,
    ))
    assert "지정할 수 있다" in conclusion
    draft = "\n".join(
        (
            "# 2. 검토결론",
            conclusion,
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"MUST_DEGRADED_TO_MAY"}


def test_must_not_weakened_to_may_not_fails_with_structured_violation():
    proposition = _proposition(
        modality=Modality.MUST_NOT,
        polarity=Polarity.NEGATIVE,
    )
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C를 충족하고 절차 P를 거치면 행정청은 대상 O를 지위 Z로 지정하지 않아도 된다.",
            "",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"MUST_NOT_DEGRADED"}
    assert soundness.violations[0].modality is Modality.MUST_NOT
    assert soundness.violations[0].polarity is Polarity.NEGATIVE


def test_correct_intermediate_render_plus_contradictory_final_conclusion_fails():
    proposition = _proposition()
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C와 절차 P를 거쳐도 행정청은 대상 O를 지위 Z로 지정할 수 없으므로 불가능하다.",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(soundness)


def test_one_correct_duplicate_plus_one_contradictory_duplicate_fails():
    proposition = _proposition()
    rendered = _rendered(proposition)
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C와 절차 P를 거쳐도 행정청은 대상 O를 지위 Z로 지정할 수 없으므로 불가능하다.",
            "# 3. 검토이유",
            rendered,
            rendered,
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(soundness)


def test_source_specific_legal_action_removed_while_other_keywords_remain_fails():
    proposition = _proposition()
    conclusion = "결론: 요건 C를 충족하고 절차 P를 거치면 행정청은 대상 O를 지위 Z로 처리할 수 있다."
    assert proposition.legal_action not in conclusion
    assert proposition.operative_verb_lexeme not in conclusion
    assert all(
        value in conclusion
        for value in (
            proposition.condition,
            proposition.procedure,
            proposition.legal_object,
            proposition.legal_effect,
        )
    )
    draft = "\n".join(
        (
            "# 2. 검토결론",
            conclusion,
            "",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"LEGAL_RELATION_DEGRADATION"}
    assert soundness.violations[0].relation_fields == ("legal_action",)


def test_source_specific_legal_effect_removed_while_other_keywords_remain_fails():
    proposition = _proposition(legal_effect="지위 Z")
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C와 절차 P를 충족하면 행정청은 대상 O를 지위 Y로 지정할 수 있다.",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"LEGAL_RELATION_DEGRADATION"}
    assert soundness.violations[0].relation_fields == ("legal_effect",)


def test_exception_condition_preserved_but_exception_effect_changed_fails():
    proposition = _proposition(
        proposition_id="P2",
        relation_type="exception",
        legal_action="제외",
        operative_verb_lexeme="제외",
        legal_object="예외 대상",
        legal_effect="예외 효과",
        condition="요건 E",
    )
    conclusion = "결론: 다만, 예외로 요건 E를 충족하고 절차 P를 거치면 행정청은 예외 대상을 변경 효과로 제외할 수 있다."
    assert proposition.legal_effect not in conclusion
    assert all(
        value in conclusion
        for value in (
            proposition.condition,
            proposition.procedure,
            proposition.legal_action,
            proposition.operative_verb_lexeme,
            proposition.legal_object,
        )
    )
    draft = "\n".join(
        (
            "# 2. 검토결론",
            conclusion,
            "",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"LEGAL_RELATION_DEGRADATION"}
    assert soundness.violations[0].relation_fields == ("legal_effect",)


def test_malformed_semantic_identity_fails():
    proposition = _proposition()
    malformed_contract = replace(build_render_contract(proposition), proposition_id="bad-identity")
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C와 절차 P를 충족하면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
            "# 3. 검토이유",
            _rendered(_proposition()),
        )
    )
    soundness = evaluate_soundness([proposition], [malformed_contract], draft)

    assert soundness.soundness_passed is False
    assert "MALFORMED_SEMANTIC_IDENTITY" in _codes(soundness)


def test_ambiguous_adopted_identity_fails():
    first = _proposition(proposition_id="P1")
    second = _proposition(proposition_id="P2")
    draft = "\n".join((
        _rendered(first),
        _rendered(second),
        "# 2. 검토결론",
        "위 결론은 두 제안을 함께 언급할 뿐이다.",
    ))

    coverage = _coverage(build_render_contract(first), draft)
    soundness = evaluate_soundness(
        [first, second],
        [build_render_contract(first), build_render_contract(second)],
        draft,
    )

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert "AMBIGUOUS_ADOPTED_IDENTITY" in _codes(soundness)


def test_unavailable_semantic_authority_fails():
    proposition = _proposition()
    contract_authority = _empty_contract_authority()
    soundness = evaluate_soundness(
        [proposition],
        contract_authority,
        "\n".join(
            (
                "# 2. 검토결론",
                "결론: 요건 C와 절차 P를 충족하면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
                "# 3. 검토이유",
                f"```text\n{_rendered(_proposition())}\n```",
            )
        ),
    )

    assert isinstance(soundness, SoundnessResult)
    assert soundness.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(soundness)


def test_open_promotion_under_subheading_remains_a_final_conclusion():
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "\n".join((
        "# 2. 검토결론", "## 판단", "따라서 이 행위는 허용된다.",
        "# 3. 검토이유", _rendered(proposition),
    ))

    assert _coverage(build_render_contract(proposition), draft).covered is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)
    violation = next(v for v in result.violations if v.code == "OPEN_PROMOTED_TO_CLOSED")
    assert "허용된다" in violation.final_conclusion_span


@pytest.mark.parametrize("prerequisites, fields", [
    ("요건 C를 충족하지 않고 절차 P를 거치면", ("condition",)),
    ("요건 C를 충족하고 절차 P를 거치지 않아도", ("procedure",)),
    ("요건 C를 충족하지 않고 절차 P를 거치지 않아도", ("condition", "procedure")),
])
def test_negated_canonical_prerequisites_are_not_preserved(prerequisites, fields):
    proposition = _proposition()
    draft = "\n".join((
        "# 2. 검토결론",
        f"{prerequisites} 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
        "# 3. 검토이유", _rendered(proposition),
    ))

    assert _coverage(build_render_contract(proposition), draft).covered is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "LEGAL_RELATION_DEGRADATION" in _codes(result)
    violation = next(v for v in result.violations if v.code == "LEGAL_RELATION_DEGRADATION")
    assert violation.relation_fields == fields


@pytest.mark.parametrize("earlier_adoption", [False, True])
def test_false_wrapper_cannot_adopt_or_hide_a_contradictory_slot(earlier_adoption):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    earlier = _rendered(proposition) + "\n" if earlier_adoption else ""
    draft = earlier + "\n".join((
        "# 2. 검토결론",
        f"다음 명제는 거짓이다: {contract.slots[0].text}",
        contract.slots[1].text,
    ))

    assert _coverage(contract, draft).covered is True
    result = evaluate_soundness([proposition], [contract], draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)
    if not earlier_adoption:
        assert "REJECTED_QUOTATION_ONLY" in _codes(result)


@pytest.mark.parametrize("before, after", [
    ({"polarity": Polarity.POSITIVE}, {"polarity": Polarity.NEGATIVE}),
    ({"polarity": Polarity.NEGATIVE}, {"polarity": Polarity.POSITIVE}),
    ({"modality": Modality.MUST_NOT}, {"modality": Modality.MAY_NOT}),
    ({"modality": Modality.MAY_NOT}, {"modality": Modality.MUST_NOT}),
])
def test_semantic_authority_detects_staleness_even_when_slots_are_equal(before, after):
    old = _proposition(**before)
    old_contract = build_render_contract(old)
    current = replace(old, **after)
    # This is the representation collision; coverage must stay unchanged.
    assert old_contract.slots == build_render_contract(current).slots
    draft = _rendered(old)
    assert _coverage(old_contract, draft).covered is True

    result = evaluate_soundness([current], [old_contract], draft)

    assert result.soundness_passed is False
    assert "STALE_SEMANTIC_AUTHORITY" in _codes(result)


def test_render_only_contract_cannot_prove_semantic_authority():
    proposition = _proposition()
    contract = build_render_contract(proposition)
    render_only = type(contract)(contract.proposition_id, contract.slots)
    draft = _rendered(proposition)
    assert _coverage(render_only, draft).covered is True

    result = evaluate_soundness([proposition], [render_only], draft)

    assert result.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(result)


@pytest.mark.parametrize("separator", [" ", "\n"])
def test_unrelated_uncertainty_does_not_adopt_an_open_proposition(separator):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "요건 C는 검토 대상이다." + separator + "보고서 발행일은 확인 필요하다."

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(result)


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_numbered_heading_in_fence_cannot_end_final_open_conclusion(fence):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "\n".join((
        "# 2. 검토결론", fence, "# 3. 검토이유", fence,
        "따라서 이 행위는 허용된다.", "# 3. 검토이유", _rendered(proposition),
    ))

    assert _coverage(build_render_contract(proposition), draft).covered is True
    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)


@pytest.mark.parametrize("condition, procedure, effect, degraded", [
    ("요건 C가 충족되지 않아도", "절차 P를 거치면", "지위 Z로", "condition"),
    ("요건 C 없이", "절차 P를 거치면", "지위 Z로", "condition"),
    ("요건 C를 충족하고", "절차 P 없이", "지위 Z로", "procedure"),
    ("요건 C를 충족하고", "절차 P를 거치면", "지위 Z가 아닌 지위 Y로", "legal_effect"),
    ("요건 C를 충족하고", "절차 P를 거치면", "지위 Z 아닌 지위 Y로", "legal_effect"),
    ("요건 C를 충족하고", "절차 P를 거치면", "지위 Z로 변경된 지위 Y로", "legal_effect"),
    ("요건 C를 충족하고", "절차 P를 거치면", "변경된 지위 Z로", "legal_effect"),
])
def test_field_local_absence_or_alternate_effect_is_not_relation_preservation(
    condition, procedure, effect, degraded,
):
    proposition = _proposition()
    assertion = f"{condition} {procedure} 행정청은 대상 O를 {effect} 지정할 수 있다."
    assert all(value in assertion for value in (
        proposition.condition, proposition.procedure, proposition.operative_verb_lexeme,
        proposition.legal_object, proposition.legal_effect,
    ))
    draft = f"# 2. 검토결론\n{assertion}\n# 3. 검토이유\n{_rendered(proposition)}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "LEGAL_RELATION_DEGRADATION" in _codes(result)
    violation = next(v for v in result.violations if v.code == "LEGAL_RELATION_DEGRADATION")
    assert violation.relation_fields == (degraded,)


@pytest.mark.parametrize("position", ["before", "after"])
@pytest.mark.parametrize("earlier_adoption", [False, True])
def test_false_wrapper_with_period_or_suffix_cannot_adopt_exact_slot(position, earlier_adoption):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    slot = contract.slots[0].text
    wrapped = f"다음 명제는 거짓이다. {slot}" if position == "before" else f"{slot} 이 명제는 거짓이다."
    earlier = _rendered(proposition) + "\n" if earlier_adoption else ""
    draft = earlier + f"# 2. 검토결론\n{wrapped}\n{contract.slots[1].text}"
    assert _coverage(contract, draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)
    if not earlier_adoption:
        assert "REJECTED_QUOTATION_ONLY" in _codes(result)


@pytest.mark.parametrize("boundary", [". ", "\n", "\r\n"])
def test_open_uncertainty_preserves_raw_assertion_boundaries(boundary):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "요건 C는 검토 대상이다" + boundary + "보고서 발행일은 확인 필요하다."

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(result)


@pytest.mark.parametrize("newline, close", [("\n", "````"), ("\r\n", "```"), ("\r\n", "````"), ("\r", "````")])
def test_fence_scanner_closes_longer_fences_and_preserves_final_promotion(newline, close):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = newline.join((
        _rendered(proposition), "# 2. 검토결론", "```text", "# 3. 검토이유",
        close, "따라서 이 행위는 허용된다.",
    ))
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)


@pytest.mark.parametrize("marker", ["예시:", "반대 견해: 이 명제는 타당하지 않다."])
def test_fenced_structural_markers_cannot_hide_final_open_promotion(marker):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "\n".join((
        _rendered(proposition), "# 2. 검토결론", "```", marker, "```",
        "따라서 이 행위는 허용된다.",
    ))
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)


@pytest.mark.parametrize("condition, procedure, effect, field", [
    ("요건 C가 없어도", "절차 P를 거치면", "지위 Z로", "condition"),
    ("요건 C를 충족하고", "절차 P가 없어도", "지위 Z로", "procedure"),
    ("요건 C를 충족하고", "절차 P를 거치면", "지위 Z가 아니라 지위 Y로", "legal_effect"),
    ("요건 C를 충족하고", "절차 P를 거치면", "지위 Z 아니라 지위 Y로", "legal_effect"),
])
def test_local_absence_or_not_effect_cannot_preserve_relation(condition, procedure, effect, field):
    proposition = _proposition()
    conclusion = f"{condition} {procedure} 행정청은 대상 O를 {effect} 지정할 수 있다."
    draft = f"# 2. 검토결론\n{conclusion}\n# 3. 검토이유\n{_rendered(proposition)}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(v for v in result.violations if v.code == "LEGAL_RELATION_DEGRADATION")
    assert violation.relation_fields == (field,)


@pytest.mark.parametrize("earlier_adoption", [False, True])
def test_exclamation_false_wrapper_rejects_exact_slot(earlier_adoption):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    earlier = _rendered(proposition) + "\n" if earlier_adoption else ""
    draft = earlier + f"# 2. 검토결론\n다음 명제는 거짓이다! {contract.slots[0].text}\n{contract.slots[1].text}"
    assert _coverage(contract, draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)
    if not earlier_adoption:
        assert "REJECTED_QUOTATION_ONLY" in _codes(result)


@pytest.mark.parametrize("boundary", [".", "!", "?", "\r"])
def test_open_neutral_adoption_cannot_cross_tight_punctuation_or_cr(boundary):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "요건 C와 절차 P는 검토 대상이다" + boundary + "보고서 발행일은 확인 필요하다."

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(result)


def test_open_paraphrase_with_only_one_relation_anchor_is_not_adoption():
    proposition = _proposition(status=PropositionStatus.OPEN)

    result = _soundness(proposition, "요건 C는 확인 필요하다.")

    assert result.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(result)


def test_exact_open_slot_can_adopt_with_one_anchor():
    proposition = _proposition(status=PropositionStatus.OPEN)

    result = _soundness(proposition, _rendered(proposition))

    assert result.soundness_passed is True


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("heading", ["", "# 2. 검토결론"])
@pytest.mark.parametrize("opener, closer", [("```", "````"), ("~~~~", "~~~~~")])
def test_round4_label_fence_preserves_final_assertion(newline, heading, opener, closer):
    proposition = _proposition(status=PropositionStatus.OPEN)
    final = "따라서 이 행위는 허용된다."
    draft = newline.join((
        _rendered(proposition), heading, "결론:", opener, "# 3. 검토이유", "",
        closer, final,
    ))
    assert _coverage(build_render_contract(proposition), draft).covered is True

    spans = classify_answer_regions(draft)
    result = _soundness(proposition, draft)

    assert any(span.kind == "final_conclusion" and final in span.text for span in spans)
    assert result.soundness_passed is False
    assert "OPEN_PROMOTED_TO_CLOSED" in _codes(result)
    violation = next(v for v in result.violations if v.code == "OPEN_PROMOTED_TO_CLOSED")
    assert violation.final_conclusion_span == final


@pytest.mark.parametrize("condition, procedure, effect, field", [
    ("요건 C를 충족하지 못해도", "절차 P를 거치면", "지위 Z로", "condition"),
    ("요건 C를 충족하고", "절차 P를 거치지 아니하고", "지위 Z로", "procedure"),
    ("요건 C를 충족하고", "절차 P를 거치면", "지위 Z 대신 지위 Y로", "legal_effect"),
])
def test_round4_bounded_relation_conflicts_fail(condition, procedure, effect, field):
    proposition = _proposition()
    claim = f"{condition} {procedure} 행정청은 대상 O를 {effect} 지정할 수 있다."
    assert all(value in claim for value in (
        proposition.condition, proposition.procedure, proposition.operative_verb_lexeme,
        proposition.legal_object, proposition.legal_effect,
    ))
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(v for v in result.violations if v.code == "LEGAL_RELATION_DEGRADATION")
    assert violation.relation_fields == (field,)
    assert violation.proposition_id == proposition.proposition_id
    assert violation.final_conclusion_span == claim.lower()


@pytest.mark.parametrize("earlier_adoption", [False, True])
@pytest.mark.parametrize("prefix, suffix", [
    ("다음 명제는 거짓이다!! ", ""),
    ("다음  명제는\t거짓이다!? \t", ""),
    ("", " \t이  명제는 거짓이다!!"),
    ("", "\n이 명제는 거짓이다."),
])
def test_round4_false_wrapper_repetition_and_whitespace(prefix, suffix, earlier_adoption):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    earlier = _rendered(proposition) + "\n" if earlier_adoption else ""
    draft = earlier + f"# 2. 검토결론\n{prefix}{contract.slots[0].text}{suffix}\n{contract.slots[1].text}"
    assert _coverage(contract, draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)
    if not earlier_adoption:
        assert "REJECTED_QUOTATION_ONLY" in _codes(result)


@pytest.mark.parametrize("separator", [", ", "; ", " "])
def test_round4_unrelated_clause_uncertainty_cannot_adopt_open(separator):
    proposition = _proposition(status=PropositionStatus.OPEN)
    draft = "요건 C와 절차 P는 검토 대상이며" + separator + "보고서 발행일은 확인 필요하다."

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(result)


@pytest.mark.parametrize("status", [PropositionStatus.CLOSED, PropositionStatus.OPEN])
@pytest.mark.parametrize("extra", [
    "보고서는 다운로드할 수 있다.",
    "요건 C는 보고서의 색인 항목이다.",
    "요건 C와 절차 P는 검토 대상이며, 보고서는 다운로드할 수 있다.",
])
def test_round4_unrelated_final_prose_has_no_legal_owner(status, extra):
    proposition = _proposition(status=status)
    draft = f"# 2. 검토결론\n{_rendered(proposition)}\n{extra}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is True
    assert result.violations == ()


@pytest.mark.parametrize("wrapped", [
    "다음 명제는 거짓이다!! 별개의 설명이다. {slot}",
    "{slot} 별개의 설명이다. 이 명제는 거짓이다!!",
])
def test_round4_false_wrapper_does_not_cross_intervening_assertion(wrapped):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    draft = "# 2. 검토결론\n" + wrapped.format(slot=contract.slots[0].text) + "\n" + contract.slots[1].text

    assert _soundness(proposition, draft).soundness_passed is True


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_round4_real_blank_after_fence_still_ends_label(newline):
    draft = newline.join(("결론:", "```", "# 3. 검토이유", "````", "", "다른 문단이다."))

    spans = classify_answer_regions(draft)

    assert any(span.kind == "affirmative" and "다른 문단이다." in span.text for span in spans)


@pytest.mark.parametrize("position", ["prefix", "suffix"])
def test_round4_false_wrapper_cannot_cross_blank_paragraph(position):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    effect = contract.slots[0].text
    wrapped = f"다음 명제는 거짓이다!!\n\n{effect}" if position == "prefix" else f"{effect}\n\n이 명제는 거짓이다!!"
    draft = f"# 2. 검토결론\n{contract.slots[1].text}\n{wrapped}"

    assert _soundness(proposition, draft).soundness_passed is True


def test_round4_false_wrapper_after_unpunctuated_line_still_rejects():
    proposition = _proposition()
    contract = build_render_contract(proposition)
    draft = f"# 2. 검토결론\n검토 결과\n다음 명제는 거짓이다!! {contract.slots[0].text}\n{contract.slots[1].text}"

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(result)


@pytest.mark.parametrize("earlier_adoption", [False, True])
@pytest.mark.parametrize("wrapped", [
    "{slot}!! 이 명제는 거짓이다!!",
    "{slot}!?\r\n이 명제는 거짓이다!!",
    "다음 명제는 거짓이다!!\r\n{slot}",
])
def test_round5_punctuated_wrapper_is_checked_before_slot_consumption(wrapped, earlier_adoption):
    proposition = _proposition()
    contract = build_render_contract(proposition)
    earlier = _rendered(proposition) + "\n" if earlier_adoption else ""
    draft = earlier + "# 2. 검토결론\n" + wrapped.format(slot=contract.slots[0].text)
    draft += "\n" + contract.slots[1].text
    assert _coverage(contract, draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(v for v in result.violations if v.code == "FINAL_CONCLUSION_CONTRADICTION")
    assert "거짓이다!!" in violation.final_conclusion_span
    assert violation.proposition_id == proposition.proposition_id
    if not earlier_adoption:
        assert "REJECTED_QUOTATION_ONLY" in _codes(result)


@pytest.mark.parametrize("condition, procedure, effect", [
    ("요건 C", "절차 P", "지위 Z"),
    ("조건 R7", "심사 S8", "자격 T9"),
])
@pytest.mark.parametrize("condition_suffix, procedure_suffix, effect_suffix, field", [
    ("를 충족하지 못해도", "를 거치면", "로", "condition"),
    ("를 충족하고", "를 생략하면", "로", "procedure"),
    ("를 충족하고", "를 거치지 아니하고", "로", "procedure"),
    ("를 충족하고", "를 거치면", " 대신 지위 Y로", "legal_effect"),
])
def test_round5_relation_conflicts_follow_typed_field_values(
    condition, procedure, effect, condition_suffix, procedure_suffix, effect_suffix, field,
):
    proposition = _proposition(condition=condition, procedure=procedure, legal_effect=effect)
    claim = (f"{condition}{condition_suffix} {procedure}{procedure_suffix} "
             f"행정청은 대상 O를 {effect}{effect_suffix} 지정할 수 있다.")
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(v for v in result.violations if v.code == "LEGAL_RELATION_DEGRADATION")
    assert violation.relation_fields == (field,)
    assert violation.final_conclusion_span == claim.lower()
    assert violation.modality is Modality.MAY


@pytest.mark.parametrize("status, polarity, predicate, code", [
    (PropositionStatus.CLOSED, Polarity.POSITIVE, "금지된다", "FINAL_CONCLUSION_CONTRADICTION"),
    (PropositionStatus.CLOSED, Polarity.NEGATIVE, "허용된다", "FINAL_CONCLUSION_CONTRADICTION"),
    (PropositionStatus.OPEN, Polarity.POSITIVE, "금지된다", "OPEN_PROMOTED_TO_CLOSED"),
    (PropositionStatus.OPEN, Polarity.NEGATIVE, "허용된다", "OPEN_PROMOTED_TO_CLOSED"),
])
def test_round5_explicit_final_anaphora_inspects_unique_authority(status, polarity, predicate, code):
    proposition = _proposition(status=status, polarity=polarity)
    claim = f"따라서 이 행위는 {predicate}."
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is False
    violation = next(v for v in result.violations if v.code == code)
    assert violation.proposition_id == proposition.proposition_id
    assert violation.final_conclusion_span == claim
    assert violation.proposition_status is status
    assert violation.polarity is polarity


@pytest.mark.parametrize("predicate", ["금지된다", "허용된다"])
def test_round5_anaphora_does_not_select_between_multiple_authorities(predicate):
    first = _proposition(status=PropositionStatus.OPEN)
    second = _proposition(proposition_id="P2", status=PropositionStatus.OPEN, condition="요건 D")
    draft = f"# 2. 검토결론\n{_rendered(first)}\n{_rendered(second)}\n따라서 이 행위는 {predicate}."

    result = _soundness_many([first, second], draft)

    assert result.soundness_passed is True
    assert result.violations == ()


@pytest.mark.parametrize("predicate", ["지정하지 않을 수 있다", "지정하지 않아도 된다"])
def test_round5_open_may_not_claim_is_definitive(predicate):
    proposition = _proposition(status=PropositionStatus.OPEN)
    claim = f"요건 C를 충족하고 절차 P를 거치면 행정청은 대상 O를 지위 Z로 {predicate}."
    draft = f"# 2. 검토결론\n{claim}\n# 3. 검토이유\n{_rendered(proposition)}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert _codes(result) == {"OPEN_PROMOTED_TO_CLOSED"}
    assert result.violations[0].final_conclusion_span == claim.lower()


@pytest.mark.parametrize("status", [PropositionStatus.CLOSED, PropositionStatus.OPEN])
@pytest.mark.parametrize("extra", [
    "요건 C 및 대상 O는 색인 항목이며, 보고서는 다운로드할 수 있다.",
    "요건 C 및 지정은 색인 항목이며, 보고서는 다운로드할 수 있다.",
    "요건 C 및 지위 Z는 색인 항목이며, 보고서는 다운로드할 수 있다.",
    "따라서 보고서는 다운로드할 수 있다.",
    "금지된다.",
])
def test_round5_unrelated_assertions_cannot_borrow_legal_ownership(status, extra):
    proposition = _proposition(status=status)
    draft = f"# 2. 검토결론\n{_rendered(proposition)}\n{extra}"
    assert _coverage(build_render_contract(proposition), draft).covered is True

    result = _soundness(proposition, draft)

    assert result.soundness_passed is True
    assert result.violations == ()


@pytest.mark.parametrize("opener, false_close, closer", [
    ("````", "```", "````"),
    ("````", "~~~~", "`````"),
    ("~~~~", "~~~", "~~~~~"),
])
def test_round5_crlf_fence_length_character_and_numbered_headings(opener, false_close, closer):
    proposition = _proposition(status=PropositionStatus.OPEN)
    claim = "따라서 이 행위는 허용된다."
    draft = "\r\n".join((
        _rendered(proposition), "# 2. 검토결론", opener, false_close,
        "# 3. 검토이유", claim, closer, claim,
    ))

    spans = classify_answer_regions(draft)
    result = _soundness(proposition, draft)

    assert any(span.kind == "code_block" and false_close in span.text
               and "# 3. 검토이유" in span.text and claim in span.text for span in spans)
    assert any(span.kind == "final_conclusion" and claim in span.text for span in spans)
    assert all(draft[span.start:span.end] == span.text for span in spans)
    assert _codes(result) == {"OPEN_PROMOTED_TO_CLOSED"}
