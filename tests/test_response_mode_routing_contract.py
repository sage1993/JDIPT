from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
REFERENCES = ROOT / "skills" / "law-interpretation-request" / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_general_review_is_not_rejected_by_moleg_suitability_gate():
    skill = _read(SKILL)
    assert "MOLEG suitability correction applies only in explicit MOLEG request mode" in skill
    assert "General legal-review mode must not be converted into MOLEG suitability correction" in skill


def test_analyzable_general_review_with_missing_material_facts_uses_four_h1():
    skill = _read(SKILL)
    request_format = _read(REFERENCES / "request-format.md")
    marker = "검토 가능한 법적 쟁점이 특정되어 있으면 자료 부족만으로 질문-only 모드로 전환하지 않는다"
    assert marker in skill
    assert marker in request_format


def test_same_term_conflict_is_completed_conditional_review_not_question_only():
    skill = _read(SKILL)
    eligibility = _read(REFERENCES / "eligibility-checklist.md")
    marker = "동일 용어 충돌을 식별한 것 자체가 요청된 법적 관계 검토의 결과"
    assert marker in skill
    assert marker in eligibility


def test_question_only_mode_is_reserved_for_unanalyzable_input():
    skill = _read(SKILL)
    request_format = _read(REFERENCES / "request-format.md")
    marker = "질문-only 모드는 법적 쟁점·대상·규정 중 무엇을 검토해야 하는지조차 구성할 수 없는 경우에만"
    assert marker in skill
    assert marker in request_format
