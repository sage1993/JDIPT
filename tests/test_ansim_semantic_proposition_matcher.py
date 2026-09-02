from scripts.ansim_housing_oracle import detect_ansim_markers, evaluate_ansim_case


ASH04_PROPOSITION_PARAPHRASE = (
    "역세권 기본 범위는 승강장 경계로부터 250m 이내입니다. "
    "300m 부지는 350m까지 통합심의위원회 심의를 통해 지정될 수 있습니다. "
    "대지면적 1,500㎡는 최소면적 기준을 충족하더라도 거리만으로 사업대상지 자격이 확정되는 것은 아니며 "
    "나머지 요건도 충족해야 합니다."
)

ASH07_PROPOSITION_PARAPHRASE = (
    "45%는 중심지역에 과반이 포함되어야 한다는 원칙에 미달합니다. "
    "다만 토지의 효율적 이용과 구역 정형화 등의 사유가 있으면 통합심의위원회 심의를 거쳐 인정될 수 있습니다. "
    "350m 사업대상지 지정 역시 별도의 심의 요건에 따라 판단됩니다. "
    "따라서 다른 계획요건까지 검토해야 합니다."
)


def test_ash04_accepts_distance_requirement_as_independent_proposition():
    result = evaluate_ansim_case("ASH-04", ASH04_PROPOSITION_PARAPHRASE)

    assert result["verdict"] == "PASS", result
    assert result["findings"] == []


def test_ash07_accepts_majority_and_350m_exceptions_as_separate_propositions():
    result = evaluate_ansim_case("ASH-07", ASH07_PROPOSITION_PARAPHRASE)

    assert result["verdict"] == "PASS", result
    assert result["findings"] == []


def test_distance_independence_does_not_match_unconditional_area_entitlement():
    answer = "대지면적 1,500㎡를 충족하므로 거리요건과 관계없이 사업대상지로 확정됩니다."

    markers = detect_ansim_markers(answer)

    assert "DISTANCE_NOT_REPLACED" not in markers
    assert "UNCERTAINTY_PRESERVED" not in markers


def test_majority_exception_does_not_match_when_exception_is_denied():
    answer = (
        "45%는 과반 원칙에 미달합니다. "
        "통합심의위원회가 검토하더라도 과반 예외는 인정되지 않습니다. "
        "350m 사업대상지 지정과 동일한 기준입니다."
    )

    markers = detect_ansim_markers(answer)

    assert "MAJORITY_EXCEPTION" not in markers
    assert "SEPARATE_EXCEPTIONS" not in markers


def test_ash07_accepts_distinct_exception_structures_without_separate_keyword():
    answer = (
        "45%는 과반 원칙에 미달합니다. "
        "토지의 효율적 이용과 구역 정형화 등의 사유가 있으면 통합심의위원회 심의를 통해 "
        "예외로 인정될 수 있습니다. "
        "역세권 기본 범위는 250m 이내이고, 일정 사유가 있으면 통합심의를 거쳐 "
        "350m 이내 토지를 사업대상지로 지정할 수 있습니다."
    )

    markers = detect_ansim_markers(answer)

    assert "MAJORITY_EXCEPTION" in markers
    assert "SEPARATE_EXCEPTIONS" in markers


def test_distance_independence_is_not_hardcoded_to_1500_square_meters():
    answer = (
        "대지면적 2,000㎡는 최소면적 기준을 충족합니다. "
        "다만 거리요건은 별도로 적용되므로 면적 충족만으로 사업대상지 자격이 확정되는 것은 아닙니다."
    )

    markers = detect_ansim_markers(answer)

    assert "DISTANCE_NOT_REPLACED" in markers
    assert "UNCERTAINTY_PRESERVED" in markers


def test_350m_exception_does_not_borrow_unrelated_designation_from_another_proposition():
    answer = (
        "역세권은 승강장 경계 250m가 원칙이며 통합심의를 거치면 350m까지 완화될 수 있습니다. "
        "용도지역의 지정·변경은 별도 절차에 따라 검토합니다."
    )

    markers = detect_ansim_markers(answer)

    assert "BASE_250M" in markers
    assert "EXCEPTION_350M_REVIEW" not in markers


def test_separate_exceptions_does_not_match_when_same_proposition_conflates_rules():
    answer = (
        "45%는 과반 원칙에 미달하지만 과반 예외 가능하며, 통합심의를 거치면 "
        "같은 기준으로 350m까지 사업대상지 지정이 가능합니다."
    )

    markers = detect_ansim_markers(answer)

    assert "MAJORITY_EXCEPTION" in markers
    assert "EXCEPTION_350M_REVIEW" in markers
    assert "SEPARATE_EXCEPTIONS" not in markers


def test_unrelated_denial_does_not_suppress_supported_majority_exception():
    answer = (
        "45%는 과반 원칙에 미달합니다. "
        "토지의 효율적 이용 사유가 있으면 통합심의위원회 심의를 거쳐 과반 예외로 인정될 수 있습니다. "
        "다만 다른 별도 예외는 인정되지 않습니다. "
        "350m 사업대상지 지정은 별도 심의가 필요합니다."
    )

    markers = detect_ansim_markers(answer)

    assert "MAJORITY_EXCEPTION" in markers
