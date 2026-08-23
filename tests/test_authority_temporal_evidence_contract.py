from pathlib import Path

from scripts.run_release_gate import AUTHORITY_TEMPORAL_VALIDATOR, CommandResult, deterministic_gate

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"
EVALS = SKILL_ROOT / "evals"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"missing markers: {missing}"


def test_issue_mapping_requires_applicable_reference_date():
    text = _read(REFERENCES / "legal-issue-mapping.md")
    _require(
        text,
        (
            "적용 기준시점",
            "허가일",
            "신청일",
            "처분일",
            "경과조치",
            "확인 필요",
        ),
    )


def test_interpretation_principles_lock_version_and_authority_before_application():
    text = _read(REFERENCES / "interpretation-principles.md")
    _require(
        text,
        (
            "적용 법령 버전",
            "시행일",
            "경과조치",
            "법제처 해석례",
            "법적 구속력",
        ),
    )


def test_source_policy_separates_authority_and_legal_effect():
    text = _read(REFERENCES / "source-policy.md")
    _require(
        text,
        (
            "Authority / Legal Effect Gate",
            "검색 우선순위",
            "법적 효력",
            "법제처 정부유권해석",
            "소관부처",
        ),
    )


def test_source_policy_separates_source_claim_and_inference():
    text = _read(REFERENCES / "source-policy.md")
    _require(
        text,
        (
            "Claim-level Evidence Gate",
            "Source Claim",
            "Analytical Inference",
            "material legal proposition",
            "추론",
        ),
    )


def test_v023_eval_spec_covers_e43_to_e48():
    text = _read(EVALS / "v0.2.3-authority-temporal-evidence.md")
    _require(text, tuple(f"E{i}." for i in range(43, 49)))


def test_v022_fail_closed_contracts_are_preserved():
    source_policy = _read(REFERENCES / "source-policy.md")
    for marker in (
        "Referenced Source Resolution Hard Gate",
        "Source Completeness / Counterevidence Gate",
        "URL provenance Gate",
    ):
        assert marker in source_policy


def test_deterministic_release_gate_runs_v023_contract_validator():
    commands: list[list[str]] = []

    def runner(command):
        commands.append(list(command))
        return CommandResult(0, "")

    result = deterministic_gate(command_runner=runner)

    assert result.passed
    assert any(str(AUTHORITY_TEMPORAL_VALIDATOR) in command for command in commands)
