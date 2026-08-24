from scripts.regression_oracles import evaluate_case


def test_e44_accepts_neutral_fail_closed_wording_with_temporal_lifecycle():
    answer = """# 1. 질의요지

최초 건축허가 뒤 기준이 개정되었고 변경허가를 준비하는 경우 강화 기준 적용 여부.

# 2. 검토결론

허가일과 개정 기준의 시행일 및 변경허가 시점이 확인되기 전에는 강화 기준 적용 여부를 단정할 수 없습니다.

# 3. 검토이유

최초 허가 당시 적용 기준과 후속 변경허가는 구분해야 합니다. 개정 기준의 시행일과 부칙 경과조치를 확인하고, 변경허가에 종전 기준 또는 신법이 적용되는지는 그 결과에 따라 판단해야 합니다.

# 4. 관련 법령 및 자료

허가일, 시행일, 변경허가 신청일 및 경과조치 확인 필요.
"""

    result = evaluate_case(44, answer)

    assert result["contract_oracle"] == "PASS"
    assert result["contract_failures"] == []
