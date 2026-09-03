from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"missing markers: {missing}"


def test_material_proposition_schema_preserves_each_legal_relation_component():
    text = _read(SKILL_ROOT / "SKILL.md")

    _require(
        text,
        (
            "Material Proposition Schema",
            "proposition_id",
            "materiality",
            "subject / legal actor",
            "condition",
            "procedure",
            "modality",
            "legal_action",
            "legal_object",
            "resulting_status_or_effect",
            "polarity",
            "relation_to_base_or_exception",
            "direct_source",
            "evidence_span",
            "temporal_status",
            "closure_status",
        ),
    )


def test_synthesis_integrity_gate_reconciles_draft_before_final_rendering():
    text = _read(SKILL_ROOT / "SKILL.md")

    _require(
        text,
        (
            "Synthesis Integrity Gate",
            "Material Proposition Ledger",
            "draft synthesis",
            "proposition-to-draft reconciliation",
            "material mismatch",
            "final rendering",
            "one targeted repair",
            "bounded re-check",
            "final answer",
        ),
    )


def test_coverage_and_relation_invariants_block_deletion_and_generic_effect_substitution():
    text = _read(REFERENCES / "source-policy.md")

    _require(
        text,
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
            "exception exists",
        ),
    )


def test_base_exception_and_open_proposition_contracts_are_fail_closed():
    mapping = _read(REFERENCES / "legal-issue-mapping.md")
    source_policy = _read(REFERENCES / "source-policy.md")

    _require(
        mapping,
        (
            "P1 = base rule",
            "P2 = exception",
            "P3 = P2 is exception-to P1",
            "independently preserved",
            "OPEN",
            "확인 필요",
        ),
    )
    _require(
        source_policy,
        (
            "OPEN proposition",
            "must not be converted into a confirmed legal effect",
            "bounded repair",
            "unresolved material mismatch",
            "do not omit",
        ),
    )


def test_synthesis_integrity_contract_is_generic_not_ash06_case_hardcoded():
    production = "\n".join(
        (
            _read(SKILL_ROOT / "SKILL.md"),
            _read(REFERENCES / "legal-issue-mapping.md"),
            _read(REFERENCES / "source-policy.md"),
        )
    )
    for token in ("ASH-06", "안심주택", "250m", "350m", "400%", "사업대상지"):
        assert token not in production

def test_runtime_priority_contract_makes_reconciliation_a_hard_stop():
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    runtime = text[start:end]

    _require(
        runtime,
        (
            "Synthesis Integrity Gate (MUST)",
            "before final answer",
            "CLOSED material proposition",
            "condition, procedure, modality, legal action, legal object",
            "resulting legal status/effect",
            "final rendering is forbidden",
            "one targeted repair",
            "bounded re-check",
            "OPEN proposition",
            "확인 필요",
        ),
    )

def test_runtime_contract_requires_source_specific_effect_not_threshold_only():
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    runtime = text[start:end]

    _require(
        runtime,
        (
            "may designate an object as a legal status",
            "threshold alone is not coverage",
            "approval",
            "exclusion",
            "condition-effect relation",
        ),
    )

def test_runtime_contract_rejects_range_only_paraphrase_of_specific_legal_effect():
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    runtime = text[start:end]

    _require(
        runtime,
        (
            "range-only paraphrase",
            "designation/approval/exclusion action",
            "material mismatch",
            "must preserve the source-specific effect",
        ),
    )

def test_runtime_contract_requires_separate_base_and_exception_sentences():
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    runtime = text[start:end]

    _require(
        runtime,
        (
            "separate sentence for the base rule",
            "separate sentence for the exception",
            "exception sentence must include its procedure",
            "source-specific legal effect",
            "must not be absorbed into a range or threshold",
        ),
    )


def test_runtime_contract_builds_mandatory_effect_slots_before_free_synthesis():
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    runtime = text[start:end]

    _require(
        runtime,
        (
            "Mandatory Proposition Sentence",
            "operative_verb_lexeme",
            "mandatory_render_clause",
            "mandatory proposition sentence construction",
            "mandatory slots in draft",
            "explanatory synthesis",
            "legal effect before numbers, ranges, and practical explanation",
            "source-specific legal effect",
        ),
    )
    sequence = (
        "Material Proposition Ledger",
        "mandatory proposition sentence construction",
        "mandatory slots in draft",
        "explanatory synthesis",
        "proposition-to-draft reconciliation",
        "one targeted repair",
        "one bounded re-check",
        "final rendering",
    )
    positions = [runtime.index(marker) for marker in sequence]
    assert positions == sorted(positions)


def test_runtime_contract_extracts_and_preserves_the_source_operative_verb():
    text = _read(SKILL_ROOT / "SKILL.md")
    start = text.index("## ASCII execution contract")
    end = text.index("## 응답 모드 라우팅", start)
    runtime = text[start:end]

    _require(
        runtime,
        (
            "Source-clause extraction",
            "operative verb stem",
            "copy the verified operative clause",
            "do not use `인정` for `지정`",
            "do not use `완화` for a source-specific legal action",
        ),
    )


def test_validator_labels_synthesis_markers_as_structural_not_behavioral_proof():
    validator = _read(ROOT / "scripts" / "validate_repo.py")

    _require(
        validator,
        (
            "structural_synthesis_contract",
            "behavioral semantic regression",
            "test_synthesis_integrity_behavior.py",
        ),
    )
