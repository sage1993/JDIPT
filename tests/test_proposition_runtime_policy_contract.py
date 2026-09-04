from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"missing markers: {missing}"


def _runtime() -> str:
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    return text[start:end]


def test_canonical_model_is_the_single_legal_proposition_schema():
    model = _read(ROOT / "scripts" / "legal_proposition.py")
    _require(
        model,
        (
            "class LegalProposition",
            "proposition_id",
            "condition",
            "procedure",
            "modality",
            "legal_action",
            "legal_object",
            "resulting_status_or_effect",
            "temporal_status",
            "closure_status",
        ),
    )


def test_runtime_contract_is_render_contract_first_and_answer_last():
    runtime = _runtime()
    _require(
        runtime,
        (
            "Material Proposition Ledger",
            "register_material_proposition",
            "render_contract",
            "mandatory render slots",
            "explanatory synthesis",
            "final rendering",
            "Stop reconciliation",
            "one targeted repair",
            "one bounded re-check",
        ),
    )


def test_source_policy_preserves_complete_relation_and_fail_closed_open_state():
    source_policy = _read(REFERENCES / "source-policy.md")
    _require(
        source_policy,
        (
            "Material Coverage Invariant",
            "Every CLOSED material proposition must be represented",
            "equivalent legal relation",
            "Relation Preservation Invariant",
            "legal actor",
            "legal action",
            "legal object",
            "resulting legal status/effect",
            "generic relaxation",
            "numeric value alone",
            "OPEN proposition",
            "must not be converted into a confirmed legal effect",
        ),
    )


def test_issue_mapping_keeps_base_exception_and_temporal_slots_independent():
    mapping = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        mapping,
        (
            "P1 = base rule",
            "P2 = exception",
            "P3 = P2 is exception-to P1",
            "independently preserved",
            "temporal status",
            "closure status",
        ),
    )


def test_runtime_contract_is_generic_not_case_hardcoded():
    production = "\n".join(
        (
            _read(SKILL_ROOT / "SKILL.md"),
            _read(REFERENCES / "legal-issue-mapping.md"),
            _read(REFERENCES / "source-policy.md"),
        )
    )
    for token in ("ASH-06", "안심주택", "250m", "350m", "400%", "사업대상지"):
        assert token not in production


def test_validator_labels_runtime_checks_as_structural_not_behavioral_proof():
    validator = _read(ROOT / "scripts" / "validate_repo.py")
    _require(
        validator,
        (
            "structural_synthesis_contract",
            "behavioral semantic regression",
            "test_proposition_runtime_behavior.py",
        ),
    )