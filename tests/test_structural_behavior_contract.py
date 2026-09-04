from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"missing markers: {missing}"


def _runtime(text: str) -> str:
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    return text[start:end]


def test_skill_owns_runtime_sequence_and_invariants():
    runtime = _runtime(_read(SKILL_ROOT / "SKILL.md"))
    _require(
        runtime,
        (
            "Material Proposition Ledger",
            "register_material_proposition",
            "mandatory render",
            "explanatory synthesis",
            "final rendering",
            "Stop",
            "registry_active=true",
            "OPEN",
            "CLOSED",
            "확인 필요",
        ),
    )
    sequence = (
        "Material Proposition Ledger",
        "register_material_proposition",
        "mandatory render",
        "explanatory synthesis",
        "final rendering",
        "Stop",
    )
    positions = [runtime.index(marker) for marker in sequence]
    assert positions == sorted(positions)


def test_skill_delegates_detailed_policy_to_named_reference_owners():
    skill = _read(SKILL_ROOT / "SKILL.md")
    source_policy = _read(REFERENCES / "source-policy.md")
    issue_mapping = _read(REFERENCES / "legal-issue-mapping.md")
    logic = _read(REFERENCES / "logic-validation.md")

    assert "Detailed source, issue-mapping, logic, and output rules remain in their named reference owners." in skill
    assert "Material Source Dependency Closure Gate" in source_policy
    assert "Compound-Issue Coverage Gate" in issue_mapping
    assert "Synthesis Integrity Gate" in logic


def test_source_policy_owns_special_rule_and_context_resolution():
    source_policy = _read(REFERENCES / "source-policy.md")
    _require(
        source_policy,
        (
            "Named-scheme Special Rule Completeness Gate",
            "직접 규율하는 특별규정",
            "Context-selector Branching Gate",
            "하나의 보편 기준",
            "조건부 분기",
        ),
    )


def test_issue_mapping_owns_compound_issue_and_category_boundaries():
    issue_mapping = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        issue_mapping,
        (
            "Compound-Issue Coverage Gate",
            "defined eligibility category",
            "material boundary",
            "specific legal effect",
            "최종 합성",
        ),
    )


def test_logic_validation_owns_fail_closed_reasoning_rules():
    logic = _read(REFERENCES / "logic-validation.md")
    _require(
        logic,
        (
            "추상 fixture 방향성 결론 BLOCK",
            "동일 용어 상충 전제 Hard Stop",
            "Referenced Source Resolution BLOCK",
            "Counterevidence BLOCK",
        ),
    )


def test_reference_contracts_are_not_case_hardcoded():
    production = "\n".join(
        (
            _read(SKILL_ROOT / "SKILL.md"),
            _read(REFERENCES / "legal-issue-mapping.md"),
            _read(REFERENCES / "source-policy.md"),
        )
    )
    for token in ("ASH-06", "안심주택", "250m", "350m", "400%", "사업대상지"):
        assert token not in production