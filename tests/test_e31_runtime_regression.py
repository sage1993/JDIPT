from scripts.regression_oracles import evaluate_case


E31_RUNTIME_RESPONSE_20260829_ATTEMPT1 = "# 1. 질의요지\n\n허가요건이 A, B, C이고 A와 B는 충족하지만 C에 관한 정보가 없는 경우, 허가 가능 여부를 검토합니다.\n\n# 2. 검토결론\n\n현재 제공된 전제만으로는 허가 가능 여부를 판단할 수 없습니다.\n\nA와 B의 충족만으로 C까지 충족되었다고 볼 수 없으며, C의 충족 여부를 확인해야 합니다. C가 충족되면 허가요건 충족 여부를 긍정적으로 검토할 수 있고, C가 충족되지 않으면 허가요건을 충족하지 못합니다.\n\n# 3. 검토이유\n\nA, B, C가 모두 필요한 누적적 허가요건이라는 전제에서는 각 요건의 충족 여부가 독립적으로 확인되어야 합니다.\n\n따라서 C에 관한 정보가 없다는 것은 C가 불충족된다는 의미도, 충족된다는 의미도 아닙니다. 현재 상태는 C에 관해 `확인 필요`로 보아야 하므로, A와 B가 충족되었다는 사정만으로 허가 가능하다고 결론낼 수 없습니다.\n\n# 4. 관련 법령 및 자료\n\n- 사용자 제공 전제: 허가요건 A, B, C\n- 구체적인 법령명·조문 및 C의 판단기준: 확인 필요\n- 공식 법령 링크: [공식 링크 확인 필요]"

def test_e31_runtime_response_accepts_neutral_unknown_conclusion():
    result = evaluate_case(31, E31_RUNTIME_RESPONSE_20260829_ATTEMPT1)
    assert result['contract_oracle'] == 'PASS', result
