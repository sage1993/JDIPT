from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
AGENT_CONFIG = SKILL.parent / "agents" / "openai.yaml"
REFERENCES = SKILL.parent / "references"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _skill_description(skill: str) -> str:
    for line in skill.splitlines():
        if line.startswith("description: "):
            return line.removeprefix("description: ")
    raise AssertionError("SKILL.md frontmatter description is missing")


def test_general_review_is_not_rejected_by_moleg_suitability_gate():
    skill = _read(SKILL)
    assert "General legal-review mode comes first" in skill
    assert "명시적 법제처 모드" in skill


def test_analyzable_general_review_with_missing_material_facts_uses_four_h1():
    skill = _read(SKILL)
    request_format = _read(REFERENCES / "request-format.md")
    marker = "검토 가능한 법적 쟁점이 특정되어 있으면 자료 부족만으로 질문-only 모드로 전환하지 않는다"
    assert marker in skill
    assert marker in request_format


def test_skill_description_pre_routes_identifiable_general_review_before_file_read():
    description = _skill_description(_read(SKILL))

    assert "일반 법률검토" in description
    assert "쟁점이 식별되면" in description
    assert "법령명·날짜 미확인" in description
    assert "질문-only" in description
    assert "4-H1 조건부 검토" in description
    assert description.index("쟁점이 식별되면") < description.index("질문-only")


def test_skill_description_keeps_authority_distinction_visible_before_file_read():
    description = _skill_description(_read(SKILL))

    assert "법제처 해석례·대법원" in description
    assert "기능·구속력" in description


def test_skill_config_is_explicit_only_and_concise():
    data = yaml.safe_load(_read(AGENT_CONFIG))
    prompt = data["interface"]["default_prompt"]

    assert data["policy"]["allow_implicit_invocation"] is False
    assert len(prompt.encode("utf-8")) <= 1024
    assert "직접 근거" in prompt
    assert "질문 3~7개" not in prompt


def test_temporal_unknown_without_dates_stays_in_four_h1():
    skill = _read(SKILL)

    assert "건축허가 후 관련 법 변경과 강화기준의 변경허가 적용 여부" in skill
    assert "질문-only가 아니라 기본 4단" in skill
    assert "질문 목록만 출력하면 실패하므로 반드시 네 H1을 렌더링" in skill
    assert "반드시 네 H1을 렌더링한다" in skill


def test_authority_versioning_fixture_without_identifiers_stays_in_four_h1():
    skill = _read(SKILL)

    assert "법제처 해석례·대법원 판결·개정문언의 관계가 제공되면" in skill
    assert "식별번호가 없어도 기본 4단 추상 검토" in skill


def test_authority_comparison_requires_explicit_function_and_binding_effect_statement():
    skill = _read(SKILL)

    assert "Authority comparison hard stop" in skill
    assert "행정부의 공식 해석" in skill
    assert "사법적 판단" in skill
    assert "법원 확정판결과 같은 법적 구속력" in skill


def test_prompt_does_not_duplicate_detailed_routing_or_source_policy():
    prompt = yaml.safe_load(_read(AGENT_CONFIG))["interface"]["default_prompt"]
    assert "최초 허가" not in prompt
    assert "구법" not in prompt
    assert "flDownload" not in prompt
    assert "빈 query" not in prompt