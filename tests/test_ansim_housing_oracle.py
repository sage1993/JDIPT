from pathlib import Path

import pytest

from scripts.ansim_housing_oracle import detect_ansim_markers, load_ansim_oracle


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "skills" / "law-interpretation-request" / "evals" / "v0.2.4-ansim-housing-oracle.json"


def test_ansim_oracle_preserves_release_contract():
    oracle = load_ansim_oracle(ORACLE)

    assert oracle["contract"] == "ansim_housing_regression_oracle=v0.2.4-candidate"
    assert oracle["effective_date"] == "2026-08-31"
    assert oracle["verdicts"] == ["PASS", "FAIL", "INVALID"]
    assert oracle["global_hard_gates"] == [
        "TEMPORAL_AUTHORITY",
        "AUTHORITY_PRIORITY",
        "SPECIAL_RULE_PRECEDENCE",
        "EXCEPTION_SEMANTICS",
        "EVIDENCE_GROUNDING",
        "UNCERTAINTY_PRESERVATION",
    ]
    assert oracle["critical_negative_markers"] == [
        "REPEALED_AS_CURRENT",
        "GENERAL_350M",
        "AUTO_350M",
        "GENERAL_RULE_OVERRIDES_SPECIAL",
        "ASSUMED_FACTS",
    ]
    assert oracle["acceptance"] == {
        "core": "9/9 PASS and zero global hard-gate violations",
        "stability": "3 fresh independent runs per case; >=26/27 PASS, but any critical negative marker causes release FAIL",
    }


def test_ansim_oracle_loads_exactly_ash_01_through_ash_09():
    cases = load_ansim_oracle(ORACLE)["cases"]

    assert [case["id"] for case in cases] == [f"ASH-{number:02d}" for number in range(1, 10)]
    assert len({case["id"] for case in cases}) == 9
    for case in cases:
        assert case["prompt"].strip()
        assert case["severity"].strip()
        assert case.get("must") or case.get("must_markers")
        assert isinstance(case["must_not"], list)
        assert case["authorities"]


def test_ansim_oracle_rejects_duplicate_case_ids(tmp_path):
    duplicate = ORACLE.read_text(encoding="utf-8").replace('"ASH-02"', '"ASH-01"', 1)
    path = tmp_path / "duplicate.json"
    path.write_text(duplicate, encoding="utf-8")

    with pytest.raises(ValueError, match="ASH-01 through ASH-09"):
        load_ansim_oracle(path)


@pytest.mark.parametrize(
    ("answer", "markers"),
    [
        ("기본 범위는 승강장 경계에서 250미터 이내다.", {"BASE_250M"}),
        ("원칙적으로 승강장 경계 250m까지이며 350m는 통합심의를 거친 특례다.", {"BASE_250M", "EXCEPTION_350M_REVIEW"}),
        ("45%는 과반수에 못 미치지만 통합심의위원회가 과반 예외를 판단할 수 있다.", {"MAJORITY_RULE", "MAJORITY_EXCEPTION"}),
        ("두 주택용도는 각각 주차대수를 산정하고 안심주택 특별 조항을 우선 적용한다.", {"MIXED_USE_SEPARATE", "SPECIAL_PARKING_RULE"}),
        ("공동주택 용적률은 400%까지 완화할 수 있을 뿐 자동 적용은 아니다.", {"FAR_400_CONDITIONAL"}),
        ("산업부지 확보비율은 통합심의위원회의 결정에 따른다.", {"INDUSTRIAL_SITE_BY_COMMITTEE"}),
        ("폐지된 종전 조례는 현행 근거로 쓸 수 없고 현재 통합 조례를 적용해야 한다.", {"REPEALED_LAW_BLOCK", "CURRENT_STANDARD_REQUIRED"}),
    ],
)
def test_positive_semantic_markers_accept_paraphrases(answer, markers):
    assert markers <= detect_ansim_markers(answer)


@pytest.mark.parametrize(
    ("answer", "marker"),
    [
        ("안심주택 역세권은 승강장 경계에서 350m 이내입니다.", "GENERAL_350M"),
        ("300m이므로 역세권에 해당하며 사업이 가능합니다.", "AUTO_350M"),
        ("안심주택 사업대상지는 일반적으로 500㎡ 이상입니다.", "GENERAL_MIN_500"),
        ("2026년 현재 서울특별시 어르신안심주택 공급 지원에 관한 조례에 따르면 가능합니다.", "REPEALED_AS_CURRENT"),
        ("안심주택 임대형기숙사는 국가기준 300㎡당 1대만 적용하면 됩니다.", "GENERAL_RULE_OVERRIDES_SPECIAL"),
        ("준공업지역이면 용적률 400%가 적용됩니다.", "AUTO_FAR_400"),
        ("교통 여건이 좋으므로 주차기준이 자동 완화됩니다.", "AUTO_PARKING_RELAX"),
        ("조건은 충족된 것으로 보고 승인 가능합니다.", "ASSUMED_FACTS"),
    ],
)
def test_negative_semantic_markers_detect_legal_regressions(answer, marker):
    assert marker in detect_ansim_markers(answer)


def test_historical_repealed_law_reference_is_not_current_authority_violation():
    answer = "과거 서울특별시 어르신안심주택 공급 지원에 관한 조례는 폐지되었고 현행 통합 안심주택 조례를 적용한다."
    markers = detect_ansim_markers(answer)
    assert "REPEALED_LAW_BLOCK" in markers


PASS_ANSWERS = {
    "ASH-01": "현행 조례의 촉진지구 1,000㎡와 일반 사업대상지는 구분해야 한다. 일반 최소면적은 최신 공식 운영기준을 확인해야 하므로 500㎡로 단정할 수 없다.",
    "ASH-02": "원칙은 승강장 경계 250m 이내이고, 350m는 법정 사유가 있을 때 통합심의를 거치는 예외적 사업대상지 지정이다.",
    "ASH-03": "일반 비학생용 임대형기숙사는 국가기준상 300㎡당 1대, 서울은 200㎡당 1대를 구분한다. 안심주택이면 제13조 특별규정을 우선 적용한다.",
    "ASH-04": "300m는 원칙 250m 밖이다. 350m 안이라도 법정 사유와 통합심의가 필요한 특례이며, 1,500㎡ 면적이 거리요건을 대체하지 않아 사업 가능 여부를 확정할 수 없다.",
    "ASH-05": "안심주택 제13조 특별규정에 따라 공공지원민간임대주택과 임대형기숙사는 용도별로 각각 주차대수를 산정한다. 물리적 공동사용과 법정 최소대수 산정은 구분한다.",
    "ASH-06": "원칙은 승강장 경계 250m이고 350m는 통합심의 예외다. 면적·도로·인접 조건은 현행 공식 운영기준을 직접 확인해야 하며 과거 청년주택 수치를 승계할 수 없다.",
    "ASH-07": "45%는 과반 본칙에 미달한다. 통합심의위원회의 과반 예외와 350m 사업대상지 지정 특례는 서로 별개의 판단이므로 사업 가능 여부를 확정할 수 없다.",
    "ASH-08": "두 주택용도는 용도별로 각각 주차대수를 산정한다. 공동주택 용적률은 400%까지 완화할 수 있고 산업부지 비율은 통합심의위원회가 결정한다. 주차완화는 국토계획법 시행령 제46조제6항과 하위 위임규정 및 실제 지구단위계획 결정내용을 확인해야 한다.",
    "ASH-09": "폐지된 어르신안심주택 조례는 현행 근거로 쓸 수 없고 현재 통합 안심주택 조례를 적용한다. 의료시설 중심지역 350m 규정과 자연녹지·공급구성의 최신 공식 운영기준을 확인해야 하므로 즉시 사업 가능 여부를 확정할 수 없다.",
}


@pytest.mark.parametrize("case_id", [f"ASH-{number:02d}" for number in range(1, 10)])
def test_each_ansim_case_has_a_semantic_pass_fixture(case_id):
    from scripts.ansim_housing_oracle import evaluate_ansim_case

    result = evaluate_ansim_case(case_id, PASS_ANSWERS[case_id], oracle_path=ORACLE)

    assert result["verdict"] == "PASS", result
    assert result["findings"] == []


def test_unusable_response_is_invalid_not_legal_fail():
    from scripts.ansim_housing_oracle import evaluate_ansim_case

    result = evaluate_ansim_case("ASH-09", "", process_ok=False, oracle_path=ORACLE)

    assert result["verdict"] == "INVALID"
    assert result["findings"][0]["reason"] == "usable response is unavailable"


def test_critical_marker_forces_fail_and_preserves_all_findings():
    from scripts.ansim_housing_oracle import evaluate_ansim_case

    answer = "안심주택 역세권은 승강장 경계에서 350m 이내입니다. 조건은 충족된 것으로 보고 승인 가능합니다."
    result = evaluate_ansim_case("ASH-04", answer, oracle_path=ORACLE)

    assert result["verdict"] == "FAIL"
    assert {"GENERAL_350M", "ASSUMED_FACTS"} <= {finding["marker"] for finding in result["findings"]}
    assert all(finding["case_id"] == "ASH-04" for finding in result["findings"])
    assert result["critical_negative_markers"] == ["GENERAL_350M", "ASSUMED_FACTS"]


def test_global_gate_finding_keeps_gate_marker_case_and_reason():
    from scripts.ansim_housing_oracle import evaluate_ansim_case

    result = evaluate_ansim_case(
        "ASH-09",
        "2026년 현재 서울특별시 어르신안심주택 공급 지원에 관한 조례에 따르면 가능합니다.",
        oracle_path=ORACLE,
    )

    finding = next(item for item in result["findings"] if item["marker"] == "REPEALED_AS_CURRENT")
    assert finding == {
        "gate": "TEMPORAL_AUTHORITY",
        "passed": False,
        "marker": "REPEALED_AS_CURRENT",
        "case_id": "ASH-09",
        "reason": "폐지·통합된 법령을 질의 기준일의 현행 근거로 사용",
    }



def test_ansim_summary_contains_required_writer_fields_and_core_acceptance():
    from scripts.ansim_housing_oracle import build_ansim_summary

    results = [
        {"case_id": case_id, "process_ok": True, "verdict": "PASS", "findings": [], "critical_negative_markers": []}
        for case_id in PASS_ANSWERS
    ]
    summary = build_ansim_summary(results, model="gpt-test", plugin_version="0.2.4", repetitions=1)

    assert summary["contract"] == "ansim_housing_regression_oracle=v0.2.4-candidate"
    assert summary["model"] == "gpt-test"
    assert summary["plugin_version"] == "0.2.4"
    assert summary["case_count"] == 9
    assert summary["process_success"] == 9
    assert summary["pass_count"] == 9
    assert summary["fail_count"] == 0
    assert summary["invalid_count"] == 0
    assert summary["global_hard_gate_violations"] == []
    assert summary["critical_negative_markers"] == []
    assert summary["per_case_verdict"] == {case_id: ["PASS"] for case_id in PASS_ANSWERS}
    assert summary["stability_acceptance"] is None
    assert summary["release_verdict"] == "PASS"


def test_stability_release_fails_on_one_critical_marker_even_at_26_of_27():
    from scripts.ansim_housing_oracle import build_ansim_summary

    results = []
    for run in range(3):
        for case_id in PASS_ANSWERS:
            verdict = "FAIL" if case_id == "ASH-04" and run == 2 else "PASS"
            critical = ["AUTO_350M"] if verdict == "FAIL" else []
            findings = [{"gate": "EXCEPTION_SEMANTICS", "marker": "AUTO_350M"}] if verdict == "FAIL" else []
            results.append({"case_id": case_id, "process_ok": True, "verdict": verdict, "findings": findings, "critical_negative_markers": critical})

    summary = build_ansim_summary(results, model="gpt-test", plugin_version="0.2.4", repetitions=3)

    assert summary["process_success"] == 27
    assert summary["pass_count"] == 26
    assert summary["stability_acceptance"] is False
    assert summary["critical_negative_markers"] == ["AUTO_350M"]
    assert summary["release_verdict"] == "FAIL"


def test_stability_release_accepts_one_noncritical_failure():
    from scripts.ansim_housing_oracle import build_ansim_summary
