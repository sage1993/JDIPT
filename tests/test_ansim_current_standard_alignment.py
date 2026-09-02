from pathlib import Path

from scripts.ansim_housing_oracle import (
    detect_ansim_markers,
    evaluate_ansim_case,
    load_ansim_oracle,
)


ROOT = Path(__file__).resolve().parents[1]
ORACLE = (
    ROOT
    / "skills"
    / "law-interpretation-request"
    / "evals"
    / "v0.2.4-ansim-housing-oracle.json"
)

EXPECTED_REQUIRED_MARKERS = {
    "ASH-01": ["GENERAL_MIN_1000_CURRENT", "CURRENT_STANDARD_REQUIRED"],
    "ASH-02": ["BASE_250M", "EXCEPTION_350M_REVIEW"],
    "ASH-03": ["DORM_300_NATIONAL", "DORM_200_SEOUL", "SPECIAL_PARKING_RULE"],
    "ASH-04": [
        "BASE_250M",
        "EXCEPTION_350M_REVIEW",
        "DISTANCE_NOT_REPLACED",
        "UNCERTAINTY_PRESERVED",
    ],
    "ASH-05": [
        "SPECIAL_PARKING_RULE",
        "MIXED_USE_SEPARATE",
        "PHYSICAL_USE_SEPARATE",
    ],
    "ASH-06": [
        "BASE_250M",
        "EXCEPTION_350M_REVIEW",
        "CURRENT_STANDARD_REQUIRED",
    ],
    "ASH-07": [
        "MAJORITY_RULE",
        "MAJORITY_EXCEPTION",
        "EXCEPTION_350M_REVIEW",
        "SEPARATE_EXCEPTIONS",
        "UNCERTAINTY_PRESERVED",
    ],
    "ASH-08": [
        "MIXED_USE_SEPARATE",
        "FAR_400_CONDITIONAL",
        "INDUSTRIAL_SITE_BY_COMMITTEE",
        "DELEGATION_CHAIN",
    ],
    "ASH-09": [
        "REPEALED_LAW_BLOCK",
        "CURRENT_STANDARD_REQUIRED",
        "MEDICAL_350",
        "UNCERTAINTY_PRESERVED",
    ],
}


def _ash01() -> dict:
    oracle = load_ansim_oracle(ORACLE)
    return next(case for case in oracle["cases"] if case["id"] == "ASH-01")


def test_all_cases_declare_complete_required_marker_source_of_truth():
    cases = load_ansim_oracle(ORACLE)["cases"]

    assert {
        case["id"]: case["must_markers"]
        for case in cases
    } == EXPECTED_REQUIRED_MARKERS


def test_ash01_oracle_uses_current_general_target_site_minimum():
    case = _ash01()

    assert case["must_markers"] == [
        "GENERAL_MIN_1000_CURRENT",
        "CURRENT_STANDARD_REQUIRED",
    ]
    assert "PROMOTION_1000_DISTINCTION" not in case["must_markers"]
    assert "UNCERTAINTY_PRESERVED" not in case["must_markers"]


def test_current_general_1000_minimum_is_detected_from_operating_standard():
    answer = (
        "현행 서울시 안심주택 건립 및 운영기준상 일반적인 사업대상지의 "
        "최소 면적 기준은 1,000㎡ 이상입니다."
    )

    markers = detect_ansim_markers(answer)

    assert "GENERAL_MIN_1000_CURRENT" in markers
    assert "CURRENT_STANDARD_REQUIRED" in markers


def test_negated_current_general_1000_minimum_is_not_positive_marker():
    answer = "현행 공식 기준상 일반 사업대상지 최소면적은 1,000㎡가 아닙니다."

    markers = detect_ansim_markers(answer)

    assert "GENERAL_MIN_1000_CURRENT" not in markers


def test_promotion_district_1000_alone_is_not_general_minimum_marker():
    answer = (
        "현행 조례상 촉진지구는 1,000㎡ 이상입니다. "
        "일반 사업대상지 최소면적은 운영기준을 별도로 확인해야 합니다."
    )

    assert "GENERAL_MIN_1000_CURRENT" not in detect_ansim_markers(answer)


def test_ash01_current_official_standard_answer_passes():
    answer = (
        "현행 서울시 안심주택 건립 및 운영기준은 일반 사업대상지의 최소 면적을 "
        "1,000㎡ 이상으로 정하고 있습니다. "
        "다만 임대주택을 어르신에게 100% 공급하면서 자연녹지지역 또는 "
        "제1종일반주거지역에 추진하는 경우에는 5,000㎡ 이상 기준이 적용됩니다. "
        "과거 500㎡ 기준은 현재 일반 최소면적으로 적용하지 않습니다."
    )

    result = evaluate_ansim_case("ASH-01", answer, oracle_path=ORACLE)

    assert result["verdict"] == "PASS", result
    assert result["findings"] == []


def test_ash01_legacy_uncertainty_answer_no_longer_bypasses_current_rule():
    answer = (
        "현행 조례의 촉진지구 1,000㎡와 일반 사업대상지는 구분해야 한다. "
        "일반 최소면적은 최신 공식 운영기준을 확인해야 하므로 500㎡로 단정할 수 없다."
    )

    result = evaluate_ansim_case("ASH-01", answer, oracle_path=ORACLE)

    assert result["verdict"] == "FAIL"
    assert "GENERAL_MIN_1000_CURRENT" in {
        finding["marker"] for finding in result["findings"]
    }


def test_ash01_still_rejects_stale_general_500_minimum():
    answer = "안심주택 사업대상지는 일반적으로 500㎡ 이상입니다."

    result = evaluate_ansim_case("ASH-01", answer, oracle_path=ORACLE)

    assert result["verdict"] == "FAIL"
    assert "GENERAL_MIN_500" in {
        finding["marker"] for finding in result["findings"]
    }
