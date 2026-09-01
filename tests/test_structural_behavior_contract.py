from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"missing markers: {missing}"


def _section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
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


def test_logic_validation_blocks_material_proposition_omission_at_rendering():
    text = _read(REFERENCES / "logic-validation.md")
    _require(
        text,
        (
            "Material Proposition Coverage BLOCK",
            "본칙과 예외",
            "일반규정과 직접 규율하는 특별규정",
            "과거 기준과 현행 기준",
            "최종 문안에서 누락",
            "재렌더링",
        ),
    )


def test_new_structural_contracts_are_not_ansim_case_hardcodes():
    source_policy = _read(REFERENCES / "source-policy.md")
    logic_validation = _read(REFERENCES / "logic-validation.md")

    source_section = _section(
        source_policy,
        "## Named-scheme Special Rule Completeness Gate",
        "## Source Completeness / Counterevidence Gate",
    )
    logic_section = _section(
        logic_validation,
        "### Material Proposition Coverage BLOCK",
        "### WARN — 표현 강도·범위를 조정",
    )

    forbidden = ("안심주택", "250m", "350m", "300㎡", "200㎡", "1,000㎡", "1,500㎡")
    for token in forbidden:
        assert token not in source_section
        assert token not in logic_section
