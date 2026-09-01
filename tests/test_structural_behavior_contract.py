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

    forbidden = ("안심주택", "250m", "350m", "300㎡", "200㎡", "1,000㎡", "1,500㎡")
    for token in forbidden:
        assert token not in skill_contract
        assert token not in source_section
