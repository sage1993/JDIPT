from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
AGENT_CONFIG = ROOT / "skills" / "law-interpretation-request" / "agents" / "openai.yaml"
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


def test_temporal_lifecycle_without_named_statute_stays_in_general_review_mode():
    agent_config = _read(AGENT_CONFIG)
    assert "과거 허가와 후속 변경허가" in agent_config
    assert "법령명이 특정되지 않았더라도 질문-only로 전환하지 마세요" in agent_config
    assert "일반 법률검토형" in agent_config
    assert "확인 필요" in agent_config


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


def test_agent_default_prompt_stays_within_codex_interface_limit():
    prompt_line = next(line for line in _read(AGENT_CONFIG).splitlines() if line.startswith("  default_prompt:"))
    prompt = prompt_line.split(": ", 1)[1].strip().strip('"')

    assert len(prompt.encode("utf-8")) <= 1024


def test_temporal_unknown_without_dates_stays_in_four_h1():
    skill = _read(SKILL)

    assert "건축허가 후 관련 법 변경과 강화기준의 변경허가 적용 여부" in skill
    assert "질문-only가 아니라 기본 4단" in skill
    assert "질문 목록만 출력하면 실패하므로 반드시 네 H1을 렌더링" in skill
    assert "always render the default four-H1 review immediately" in skill


def test_authority_versioning_fixture_without_identifiers_stays_in_four_h1():
    skill = _read(SKILL)

    assert "법제처 해석례·대법원 판결·개정문언의 관계가 제공되면" in skill
    assert "식별번호가 없어도 기본 4단 추상 검토" in skill


def test_agent_prompt_hardens_temporal_unknown_rendering():
    agent_config = _read(AGENT_CONFIG)

    assert "확인질문으로 시작하지 말고" in agent_config
    for heading in (
        "# 1. 질의요지",
        "# 2. 검토결론",
        "# 3. 검토이유",
        "# 4. 관련 법령 및 자료",
    ):
        assert heading in agent_config
    assert "최초 허가·변경허가를 분리" in agent_config
    assert "시행일·경과조치·변경범위 미확인" in agent_config


def test_agent_prompt_hardens_authority_legal_effect_distinction():
    agent_config = _read(AGENT_CONFIG)

    assert "행정부 해석·사법판단의 기능·구속력 차이" in agent_config
    assert "구법·개정법 문언" in agent_config


def test_agent_prompt_rejects_blank_query_urls_and_internal_metadata():
    agent_config = _read(AGENT_CONFIG)

    assert "빈 query 값(`x=`)" in agent_config
    assert "[공식 링크 확인 필요]" in agent_config
    assert "Skill/Plugin 이름·상태·경로를 출력하지" in agent_config
