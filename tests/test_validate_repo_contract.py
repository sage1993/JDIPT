from scripts import validate_repo


def test_output_marker_matches_current_moleg_routing_contract():
    markers = validate_repo.REQUIRED_OUTPUT_SKILL_MARKERS

    assert "MOLEG suitability correction applies only in explicit MOLEG request mode" in markers
    assert "MOLEG suitability correction takes precedence over clarification" not in markers
    assert "질문만 하고 그 응답에서는 중단한다" in markers
    assert "정보 부족으로 질문만 하고 중단" not in markers


def test_agent_config_markers_match_current_runtime_prompt_contract():
    markers = validate_repo.REQUIRED_AGENT_CONFIG_MARKERS

    assert "모드를 먼저 확정하세요" in markers
    assert "일반 법률검토형은 질문-only 금지" in markers
    assert "`검토해줘`·`적용되는지`" in markers
    assert "건축허가→법 개정→변경허가" in markers
    assert "쟁점·사실·규정이 모두 없는 요청" in markers
    assert "URL 끝이 `=`" in markers
    assert "핵심 식별자" in markers
    assert "WINDOWS UTF-8 IO:" not in markers
    assert "기본 4단 법률검토형" not in markers
    assert "빈 query 값" not in markers
