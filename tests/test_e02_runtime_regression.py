import yaml
from pathlib import Path

from scripts.regression_oracles import evaluate_case

ROOT = Path(__file__).resolve().parents[1]
E02_FAILED_RUNTIME_RESPONSE = "이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다.\n\n1. “법 제10조”의 정확한 법령명과 조문 전문 또는 관련 법령 링크는 무엇인가요?\n\n2. 해당 건물의 용도, 규모, 구조, 사용 현황 등 제10조의 시설 해당 여부와 관련된 구체적 특징은 무엇인가요?\n\n3. 이 질문이 제기된 행정절차는 무엇인가요? 예: 건축허가, 용도변경, 등록, 영업허가 등\n\n4. 해당 건물에 대해 이미 행정청의 처분이나 공식 회신이 있었나요? 있다면 그 내용은 무엇인가요?\n\n5. 법령 문언상 어떤 두 해석이 대립하고 있나요? 관련 도면, 허가서, 사업계획서 또는 행정청 의견이 있으면 함께 알려주세요."
E02_EXPECTED_RUNTIME_RESPONSE = "이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다. 제시된 요청은 특정 건물의 용도·규모·구조·사용 현황과 행정절차에 따라 결론이 달라지는 구체적 사실판단에 가까울 수 있습니다. 다만 법령해석 문제로 재구성하려면 해당 근거조항의 객관적 법령 의미, 적용범위, 요건 및 근거조항이 정한 시설 해당 여부를 먼저 특정하고, 사실관계가 그 요건을 충족하는지를 구분해 검토해야 합니다.\n\n1. “법 제10조”의 정확한 법령명과 조문 전문 또는 관련 법령 링크는 무엇인가요?\n\n2. 해당 건물의 용도, 규모, 구조, 사용 현황 등 제10조의 시설 해당 여부와 관련된 구체적 특징은 무엇인가요?\n\n3. 이 질문이 제기된 행정절차는 무엇인가요? 예: 건축허가, 용도변경, 등록, 영업허가 등\n\n4. 해당 건물에 대해 이미 행정청의 처분이나 공식 회신이 있었나요? 있다면 그 내용은 무엇인가요?\n\n5. 법령 문언상 어떤 두 해석이 대립하고 있나요? 관련 도면, 허가서, 사업계획서 또는 행정청 의견이 있으면 함께 알려주세요."

def test_e02_failed_runtime_response_reproduces_suitability_failure():
    result = evaluate_case(2, E02_FAILED_RUNTIME_RESPONSE)
    assert result['contract_oracle'] == 'FAIL'
    assert any('suitability_explained' in failure for failure in result['contract_failures'])


def test_e02_expected_runtime_response_satisfies_existing_oracle():
    result = evaluate_case(2, E02_EXPECTED_RUNTIME_RESPONSE)
    assert result['contract_oracle'] == 'PASS', result
