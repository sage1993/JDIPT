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
from scripts.proposition_soundness import evaluate_soundness


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
    draft = _draft_with_contract(
        proposition,
        prefix="# 2. 검토결론\n",
        suffix="\n결론: 요건 C와 절차 P를 충족하더라도 행정청은 대상 O를 지위 Z로 금지된다.",
    )

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
    draft = "확인 필요: 요건 C와 절차 P에 관한 근거와 적용 여부는 현재 확정할 수 없다.\n결론: 따라서 이 행위는 허용된다."

    coverage = _coverage(build_render_contract(_proposition()), _rendered(_proposition()))
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"OPEN_PROMOTED_TO_CLOSED"}


def test_open_proposition_with_definitive_negative_conclusion_fails():
    proposition = _proposition(status=PropositionStatus.OPEN, evidence=None)
    draft = "확인 필요: 요건 C와 절차 P에 관한 근거와 적용 여부는 현재 확정할 수 없다.\n결론: 따라서 이 행위는 허용되지 않는다."

    coverage = _coverage(build_render_contract(_proposition()), _rendered(_proposition()))
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
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C와 절차 P가 있으면 행정청은 대상 O를 지위 Z로 된다.",
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
        legal_action="금지",
        operative_verb_lexeme="금지",
    )
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 행정청은 대상 O를 지위 Z로 금지하지 않아도 된다.",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"MUST_NOT_DEGRADED"}


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
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 C와 절차 P를 충족하면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
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
    draft = "\n".join(
        (
            "# 2. 검토결론",
            "결론: 요건 E가 있으면 예외 대상도 일반 대상과 같이 처리된다.",
            "# 3. 검토이유",
            _rendered(proposition),
        )
    )

    coverage = _coverage(build_render_contract(proposition), draft)
    soundness = _soundness(proposition, draft)

    assert coverage.covered is True
    assert soundness.soundness_passed is False
    assert _codes(soundness) == {"LEGAL_RELATION_DEGRADATION"}


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
    soundness = evaluate_soundness(
        [proposition],
        [],
        "\n".join(
            (
                "# 2. 검토결론",
                "결론: 요건 C와 절차 P를 충족하면 행정청은 대상 O를 지위 Z로 지정할 수 있다.",
                "# 3. 검토이유",
                f"```text\n{_rendered(_proposition())}\n```",
            )
        ),
    )

    assert soundness.soundness_passed is False
    assert "UNAVAILABLE_SEMANTIC_AUTHORITY" in _codes(soundness)
