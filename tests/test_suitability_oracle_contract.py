from scripts.regression_oracles import evaluate_case


def test_e02_full_run_scope_wording_is_accepted():
    answer = """법제처에 “내 건물이 시설에 해당하는지”라는 개별 사실판단을 직접 요청하는 방식은 부적합할 수 있습니다. 법제처 질의는 해당 건물의 구체적 판정보다, 「○○법」 제10조의 “시설”에 포함되는 범위와 판단기준을 묻는 형태로 다듬는 것이 적절합니다.

1. 해당 법률의 정확한 명칭은 무엇인가요?
2. 제10조의 정확한 문언은 무엇인가요?
3. 건물의 현재 용도는 무엇인가요?
4. 구조와 규모는 어떻게 되나요?
5. 해당 시설에서 수행하는 업무는 무엇인가요?
"""

    result = evaluate_case(2, answer)
    assert result["contract_oracle"] == "PASS"
    assert result["contract_failures"] == []


def test_e02_still_rejects_unsuitability_without_legal_scope_correction():
    answer = """이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다.

1. 건물 주소는 어디인가요?
2. 현재 용도는 무엇인가요?
3. 규모는 어떻게 되나요?
"""

    result = evaluate_case(2, answer)
    assert result["contract_oracle"] == "FAIL"
    assert any("suitability_explained" in failure for failure in result["contract_failures"])
