from scripts.regression_oracles import evaluate_case


E18_RUNTIME_RESPONSE_20260829_ATTEMPT1 = "# 1. 질의요지\n\n같은 조문에서 사용된 “건축물”에 부속시설이 포함되는지 여부에 관하여, 갑설은 포함된다고 보고 을설은 제외된다고 보는 양쪽 논거를 작성하는 사안이다. 별도의 정의규정이나 해석 근거는 제공되지 않았다.\n\n# 2. 검토결론\n\n제공된 전제만으로는 갑설과 을설 중 어느 견해가 타당한지, 또는 양쪽의 실체적 논거를 확정적으로 구성할 수 없다.\n\n이는 양쪽이 같은 조문의 같은 용어인 “건축물”에 서로 다른 범위를 부여하고 있으나, 그 차이를 뒷받침할 문언·정의규정·체계·위임관계 등의 공통 기준이 제공되지 않았기 때문이다.\n\n# 3. 검토이유\n\n갑설은 “건축물”이라는 동일 용어의 범위에 부속시설이 포함된다는 전제를 취한다. 따라서 부속시설도 해당 조문이 규율하는 “건축물”에 해당하여 조문의 적용대상이 된다는 방향으로 주장할 수 있다. 다만 그 포함을 뒷받침하는 구체적인 문언이나 정의 근거는 현재 확인되지 않는다.\n\n을설은 같은 “건축물”이라는 용어에서 부속시설을 제외한다는 전제를 취한다. 따라서 해당 조문은 본체인 건축물에만 적용되고 부속시설에는 적용되지 않는다는 방향으로 주장할 수 있다. 그러나 이 제외를 뒷받침하는 별도의 제한 문언이나 법적 근거 역시 현재 확인되지 않는다.\n\n결국 현재 제시된 내용은 갑설과 을설의 결론 전제를 각각 제시한 것에 그치며, 어느 전제를 채택할지를 결정할 공통 해석기준이 없다. 따라서 현 단계에서는 양 설의 주장범위만 정리할 수 있고, 어느 설이 법적으로 우세하다고 평가할 수는 없다.\n\n# 4. 관련 법령 및 자료\n\n- 사용자 제공 전제: 같은 조문의 “건축물”에 대하여 갑설은 부속시설 포함, 을설은 부속시설 제외\n- 별도 정의규정·조문 문언·하위법령·판례·해석례: 제공되지 않음\n- 관련 법령 및 공식 자료: 확인 필요"

def test_e18_runtime_response_accepts_semantic_hard_stop_variant():
    result = evaluate_case(18, E18_RUNTIME_RESPONSE_20260829_ATTEMPT1)
    assert result['contract_oracle'] == 'PASS', result


def test_e18_negated_substantive_phrase_is_not_treated_as_parallel_argument():
    answer = """# 1. 질의요지

갑설은 포함, 을설은 제외라는 전제를 둔다.

# 2. 검토결론

갑설의 실체적 타당성이나 을설의 실체적 타당성은 공통 정의가 없어 판단할 수 없다.

# 3. 검토이유

동일한 용어의 범위가 충돌하고 공통 기준이 제공되지 않았다.

# 4. 관련 법령 및 자료

확인 필요
"""
    result = evaluate_case(18, answer)
    assert result['contract_oracle'] == 'PASS', result


def test_e18_positive_substantive_phrase_remains_blocked():
    answer = """# 1. 질의요지

갑설은 포함, 을설은 제외라는 전제를 둔다.

# 2. 검토결론

갑설의 실체적 타당성은 인정된다.

# 3. 검토이유

동일한 용어의 범위가 충돌하고 공통 기준이 제공되지 않았다.

# 4. 관련 법령 및 자료

확인 필요
"""
    result = evaluate_case(18, answer)
    assert result['contract_oracle'] == 'FAIL', result

def test_e18_conclusion_reservation_counts_as_hard_stop():
    answer = """# 1. 질의요지

갑설은 포함, 을설은 제외라는 전제를 둔다.

# 2. 검토결론

같은 용어의 범위가 충돌하고 공통 정의가 없으므로 결론을 유보해야 한다.

# 3. 검토이유

양쪽 전제의 공통 기준은 확인 필요하다.

# 4. 관련 법령 및 자료

확인 필요
"""
    result = evaluate_case(18, answer)
    assert result['contract_oracle'] == 'PASS', result
