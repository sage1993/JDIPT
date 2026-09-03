from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"missing markers: {missing}"


def _section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def test_skill_requires_named_scheme_special_rule_completion_before_synthesis():
    text = _read(SKILL_ROOT / "SKILL.md")
    _require(
        text,
        (
            "Special-rule completeness hard stop",
            "named scheme",
            "general rule",
            "directly governing special rule",
            "reasonably implicated",
            "Synthesis coverage hard stop",
            "main rule and exception",
        ),
    )


def test_skill_preserves_unresolved_context_branches_instead_of_one_universal_rule():
    text = _read(SKILL_ROOT / "SKILL.md")
    _require(
        text,
        (
            "Context-branching hard stop",
            "jurisdiction",
            "special statutory status",
            "one universal rule",
            "selector",
            "conditional branches",
        ),
    )


def test_source_policy_named_scheme_gate_does_not_stop_at_general_rule():
    text = _read(REFERENCES / "source-policy.md")
    _require(
        text,
        (
            "Named-scheme Special Rule Completeness Gate",
            "특정 제도",
            "일반규정 확인만으로 Source Completeness를 통과하지 않는다",
            "직접 규율하는 특별규정",
            "규율대상",
            "법적 기능",
        ),
    )


def test_special_rule_search_is_bounded_not_exhaustive():
    text = _read(REFERENCES / "source-policy.md")
    section = _section(
        text,
        "## Named-scheme Special Rule Completeness Gate",
        "## Context-selector Branching Gate",
    )

    assert "전수조사하지 않는다" in section
    assert "합리적으로" in section


def test_source_policy_maps_material_context_selectors_when_they_change_the_rule():
    text = _read(REFERENCES / "source-policy.md")
    _require(
        text,
        (
            "Context-selector Branching Gate",
            "관할",
            "특별지위",
            "적용경로",
            "하나의 보편 기준",
            "조건부 분기",
        ),
    )


def test_issue_mapping_preserves_compound_issue_coverage_before_rendering():
    text = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        text,
        (
            "Compound-Issue Coverage Gate",
            "독립 판단요소",
            "본칙",
            "예외·특례",
            "적용시점",
            "확인 필요",
            "최종 합성",
        ),
    )


def test_issue_mapping_preserves_defined_category_boundaries_and_specific_effects():
    text = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        text,
        (
            "defined eligibility category",
            "material boundary",
            "exception",
            "specific legal effect",
            "generic relaxation",
            "지정·인정·승인",
        ),
    )


def test_skill_invokes_compound_coverage_and_legal_effect_preservation():
    text = _read(SKILL_ROOT / "SKILL.md")
    _require(
        text,
        (
            "compound-issue coverage",
            "defined eligibility category",
            "specific legal effect",
            "generic relaxation",
        ),
    )


def test_skill_promotes_direct_defining_authority_to_runtime_priority_contract():
    text = _read(SKILL_ROOT / "SKILL.md")
    runtime_contract = _section(
        text,
        "## ASCII execution contract",
        "## 응답 모드 라우팅",
    )
    _require(
        runtime_contract,
        (
            "Direct defining authority hard stop",
            "operating standard",
            "directly defines",
            "specific legal effect",
            "original source",
            "확인 필요",
            "bounded",
        ),
    )


def test_issue_mapping_resolves_direct_defining_authority_before_guidance_synthesis():
    text = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        text,
        (
            "Direct Defining Authority Gate",
            "법정 범주",
            "직접 정의",
            "운영기준",
            "법적 효과",
            "원문 확인 실패",
        ),
    )


def test_issue_mapping_preserves_mutable_standard_temporal_status_in_final_synthesis():
    text = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        text,
        (
            "Mutable Standard Temporal Status Gate",
            "개정일",
            "시행일",
            "현행성",
            "최종 합성",
            "링크만으로",
        ),
    )


def test_skill_blocks_material_proposition_omission_at_rendering():
    text = _read(SKILL_ROOT / "SKILL.md")
    _require(
        text,
        (
            "본칙/예외",
            "일반/특별",
            "현행/과거",
            "material proposition",
            "최종 문안에서 빠지면 BLOCK",
            "재렌더링",
        ),
    )


def test_new_structural_contracts_are_not_ansim_case_hardcodes():
    skill = _read(SKILL_ROOT / "SKILL.md")
    source_policy = _read(REFERENCES / "source-policy.md")
    issue_mapping = _read(REFERENCES / "legal-issue-mapping.md")

    skill_contract = _section(
        skill,
        "- Special-rule completeness hard stop:",
        "- MOLEG suitability correction",
    )
    source_section = _section(
        source_policy,
        "## Named-scheme Special Rule Completeness Gate",
        "## Source Completeness / Counterevidence Gate",
    )
    issue_section = issue_mapping

    forbidden = ("안심주택", "250m", "350m", "300㎡", "200㎡", "1,000㎡", "1,500㎡")
    for token in forbidden:
        assert token not in skill_contract
        assert token not in source_section
        assert token not in issue_section


def test_skill_requires_material_source_dependency_closure_before_synthesis():
    text = _read(SKILL_ROOT / "SKILL.md")
    runtime_contract = _section(
        text,
        "## ASCII execution contract",
        "## \uc751\ub2f5 \ubaa8\ub4dc \ub77c\uc6b0\ud305",
    )
    _require(
        runtime_contract,
        (
            "Material source dependency closure hard stop",
            "before synthesis",
            "source dependency closure",
            "direct definition",
            "main rule",
            "material boundary",
            "exception",
            "specific legal effect",
            "direct source",
            "temporal status",
            "OPEN",
            "CLOSED",
            "targeted retrieval retry",
            "\ud655\uc778 \ud544\uc694",
        ),
    )


def test_issue_mapping_tracks_material_evidence_slots_and_closure_status():
    text = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        text,
        (
            "Material Source Dependency Closure Ledger",
            "direct definition",
            "main rule",
            "material boundary",
            "exception",
            "specific legal effect",
            "direct source",
            "temporal status",
            "closure status",
            "OPEN",
            "CLOSED",
            "synthesis",
        ),
    )


def test_source_policy_retries_missing_material_fields_with_bounded_closure():
    text = _read(REFERENCES / "source-policy.md")
    _require(
        text,
        (
            "Material Source Dependency Closure Gate",
            "opaque label",
            "\uc9c1\uc811 \uc815\uc758\uaddc\uc815",
            "\uc608\uc678",
            "\uc131\ub9bd\uc870\uac74",
            "specific legal effect",
            "\uac80\uc0c9 \uacb0\uacfc \uc81c\ubaa9",
            "\uc6b4\uc601\uae30\uc900",
            "targeted retrieval retry",
            "\ub204\ub77d \ud544\ub4dc",
            "bounded",
            "\uaddc\uc815 \uc5c6\uc74c",
            "\ud655\uc778 \ud544\uc694",
        ),
    )


def test_material_proposition_ledger_preserves_effect_conditions_and_procedure():
    skill = _read(SKILL_ROOT / "SKILL.md")
    mapping = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        skill,
        (
            "condition",
            "procedure",
            "specific legal effect",
            "closure status",
            "unresolved",
            "final synthesis",
        ),
    )
    _require(
        mapping,
        (
            "condition",
            "procedure",
            "specific legal effect",
            "temporal status",
            "closure status",
            "OPEN",
            "CLOSED",
        ),
    )


def test_temporal_status_contract_distinguishes_confirmed_and_unresolved_currentness():
    text = _read(REFERENCES / "source-policy.md")
    _require(
        text,
        (
            "CURRENT_CONFIRMED",
            "HISTORICAL_CONFIRMED",
            "CURRENT_UNRESOLVED",
            "question-date applicability",
            "current applicability",
            "effective-status evidence",
            "recent publication",
            "revision date",
        ),
    )
