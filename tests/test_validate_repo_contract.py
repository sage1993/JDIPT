from scripts import validate_repo


def test_output_marker_matches_current_moleg_routing_contract():
    markers = validate_repo.REQUIRED_OUTPUT_SKILL_MARKERS

    assert "MOLEG suitability correction applies only in explicit MOLEG request mode" in markers
    assert "MOLEG suitability correction takes precedence over clarification" not in markers
    assert '질문만 하고 그 응답에서는 중단한다' in markers
    assert '정보 부족으로 질문만 하고 중단' not in markers
