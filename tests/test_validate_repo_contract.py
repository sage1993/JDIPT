from scripts import validate_repo


def test_output_marker_matches_current_moleg_routing_contract():
    markers = validate_repo.REQUIRED_OUTPUT_SKILL_MARKERS

    assert "MOLEG suitability correction applies only in explicit MOLEG request mode" in markers
    assert "MOLEG suitability correction takes precedence over clarification" not in markers
    assert "질문만 하고 그 응답에서는 중단한다" in markers
    assert "정보 부족으로 질문만 하고 중단" not in markers


def test_agent_config_markers_are_stable_semantic_contracts():
    markers = validate_repo.REQUIRED_AGENT_CONFIG_MARKERS

    assert "모드를 먼저 확정하세요" in markers
    assert "과거 건축허가→법 개정→후속 변경허가" in markers
    assert "질문-only·확인질문으로 시작하지 말고" in markers
    assert "URL은 검증된 것만 쓰고 빈 query 값" in markers
    assert "WINDOWS UTF-8 IO:" not in markers
    assert "기본 4단 법률검토형" not in markers
