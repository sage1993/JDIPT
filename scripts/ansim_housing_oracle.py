"""Loader and schema validation for the JDIPT Ansim Housing oracle."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_CASE_IDS = [f"ASH-{number:02d}" for number in range(1, 10)]
EXPECTED_VERDICTS = ["PASS", "FAIL", "INVALID"]
EXPECTED_GLOBAL_HARD_GATES = [
    "TEMPORAL_AUTHORITY",
    "AUTHORITY_PRIORITY",
    "SPECIAL_RULE_PRECEDENCE",
    "EXCEPTION_SEMANTICS",
    "EVIDENCE_GROUNDING",
    "UNCERTAINTY_PRESERVATION",
]
EXPECTED_CRITICAL_MARKERS = [
    "REPEALED_AS_CURRENT",
    "GENERAL_350M",
    "AUTO_350M",
    "GENERAL_RULE_OVERRIDES_SPECIAL",
    "ASSUMED_FACTS",
]


def load_ansim_oracle(path: Path) -> dict[str, Any]:
    oracle = json.loads(path.read_text(encoding="utf-8"))
    _validate_ansim_oracle(oracle)
    return oracle


def detect_ansim_markers(answer: str) -> set[str]:
    """Return semantic findings without requiring one exact answer phrase."""
    normalized = re.sub(r"\s+", " ", answer).strip()
    propositions = [
        re.sub(r"\s+", " ", proposition).strip()
        for proposition in re.split(r"(?<=[.!?。！？])\s+|\n+", answer)
        if proposition.strip()
    ]
    markers: set[str] = set()

    def has(*terms: str) -> bool:
        return all(term in normalized for term in terms)

    def any_of(*terms: str) -> bool:
        return any(term in normalized for term in terms)

    def matches(pattern: str) -> bool:
        return re.search(pattern, normalized) is not None

    def proposition_has_350m_exception(proposition: str) -> bool:
        has_350m = re.search(r"350\s*(?:m|미터)", proposition) is not None
        if not has_350m:
            return False
        has_review = "통합심의" in proposition or "심의위원회" in proposition
        has_exception_effect = any(term in proposition for term in ("예외", "특례", "지정"))
        explicit_target_designation = (
            "사업대상지" in proposition
            and "지정" in proposition
            and "심의" in proposition
        )
        return (has_review and has_exception_effect) or explicit_target_designation

    def proposition_has_majority_exception(proposition: str) -> bool:
        has_review = "통합심의" in proposition or "심의위원회" in proposition
        if not has_review:
            return False
        denied = re.search(
            r"(?:과반수?\s*예외|예외).{0,20}(?:인정되지|인정할 수 없|불가|허용되지)",
            proposition,
        )
        if denied:
            return False
        explicit = any(
            term in proposition for term in ("과반 예외", "과반수 예외", "예외 가능")
        )
        reasoned = (
            any(
                term in proposition
                for term in ("토지의 효율", "토지 효율", "구역 정형화", "정형화")
            )
            and any(term in proposition for term in ("인정될 수", "허용될 수", "가능"))
        )
        return explicit or reasoned

    if re.search(r"250\s*(?:m|미터)", normalized) and any_of("원칙", "기본", "본칙"):
        markers.add("BASE_250M")

    exception_350_indices = {
        index
        for index, proposition in enumerate(propositions)
        if proposition_has_350m_exception(proposition)
    }
    if exception_350_indices:
        markers.add("EXCEPTION_350M_REVIEW")

    if any_of("과반수", "과반") and any_of("미달", "못 미", "원칙", "본칙"):
        markers.add("MAJORITY_RULE")

    majority_exception_indices = {
        index
        for index, proposition in enumerate(propositions)
        if proposition_has_majority_exception(proposition)
    }
    if majority_exception_indices and any_of("과반수", "과반"):
        markers.add("MAJORITY_EXCEPTION")

    if any_of("용도별", "두 주택용도") and any_of("각각", "별도") and any_of("주차", "주차대수"):
        markers.add("MIXED_USE_SEPARATE")
    if "안심주택" in normalized and any_of("특별규정", "특별 조항", "제13조") and any_of("우선", "먼저", "따라"):
        markers.add("SPECIAL_PARKING_RULE")
    if "400%" in normalized and any_of("완화할 수", "완화 가능") and not any_of("자동 적용됩니다", "당연히 적용됩니다"):
        markers.add("FAR_400_CONDITIONAL")
    if "산업부지" in normalized and any_of("통합심의위원회", "통합심의 위원회") and any_of("결정", "판단"):
        markers.add("INDUSTRIAL_SITE_BY_COMMITTEE")
    if any_of("폐지", "종전") and (any_of("현행 근거로 쓸 수 없", "현재 근거로 사용할 수 없") or ("통합" in normalized and "조례" in normalized)):
        markers.add("REPEALED_LAW_BLOCK")
    if any_of("현행", "현재", "최신") and any_of("운영기준", "통합 조례", "공식 기준"):
        markers.add("CURRENT_STANDARD_REQUIRED")

    if "1,000㎡" in normalized and any_of("구분", "다르", "별도") and any_of("촉진지구", "일반 사업대상지"):
        markers.add("PROMOTION_1000_DISTINCTION")
    if re.search(r"300\s*㎡.{0,10}(?:당\s*)?1대", normalized) and any_of("국가", "일반"):
        markers.add("DORM_300_NATIONAL")
    if re.search(r"200\s*㎡.{0,10}(?:당\s*)?1대", normalized) and "서울" in normalized:
        markers.add("DORM_200_SEOUL")

    area_requirement_present = (
        re.search(r"\d[\d,]*\s*㎡", normalized) is not None
        and any_of("면적", "대지면적", "최소면적", "최소 면적")
        and any_of("충족", "기준", "요건")
    )
    distance_requirement_present = (
        any_of("거리", "거리요건", "거리 요건")
        or re.search(r"(?:250|300|350)\s*(?:m|미터)", normalized) is not None
    )
    conditional_eligibility = (
        matches(r"만으로.{0,50}(?:확정|자격|사업\s*가능).{0,25}(?:아니|아닙|않|없)")
        or matches(r"(?:확정|단정).{0,25}(?:아니|아닙|않|없)")
    )
    separate_requirements = (
        any_of("각각", "별도", "별도로", "독립")
        and any_of("면적", "대지면적", "최소면적", "최소 면적")
        and any_of("거리", "250m", "350m")
    )
    if any_of("거리요건을 대체하지", "거리 요건을 대체하지") or (
        area_requirement_present
        and distance_requirement_present
        and (conditional_eligibility or separate_requirements)
    ):
        markers.add("DISTANCE_NOT_REPLACED")

    if any_of("물리적 공동사용", "물리적 공동 사용") and any_of("법정 최소대수", "법정 산정"):
        markers.add("PHYSICAL_USE_SEPARATE")

    explicit_separation = any_of(
        "별도", "별도의", "별개", "별개의", "서로 독립", "각각", "따로"
    )
    distinct_exception_propositions = any(
        majority_index != exception_index
        for majority_index in majority_exception_indices
        for exception_index in exception_350_indices
    )
    if (
        "MAJORITY_EXCEPTION" in markers
        and "EXCEPTION_350M_REVIEW" in markers
        and (distinct_exception_propositions or explicit_separation)
    ):
        markers.add("SEPARATE_EXCEPTIONS")

    if any_of("제46조제6항", "제46조 제6항") and any_of("하위 위임", "위임규정") and any_of("지구단위계획 결정", "결정내용"):
        markers.add("DELEGATION_CHAIN")
    if any_of("의료시설 중심지역", "종합병원") and "350m" in normalized:
        markers.add("MEDICAL_350")
    if (
        any_of("확정할 수 없", "단정할 수 없", "확인해야", "확인 필요")
        or matches(r"(?:확정|단정).{0,25}(?:아니|아닙|않|없)")
        or (
            any_of("나머지 요건", "다른 요건", "추가 요건", "기타 요건", "별도 요건", "다른 계획요건")
            and any_of("충족해야", "검토해야", "확인해야", "검토 필요", "확인 필요")
        )
    ):
        markers.add("UNCERTAINTY_PRESERVED")

    if re.search(r"역세권(?:은|의 범위는).{0,30}350\s*(?:m|미터).{0,10}(?:이내|까지)", normalized) and not any_of("예외", "특례", "통합심의"):
        markers.add("GENERAL_350M")
    if re.search(r"(?:300|350)\s*(?:m|미터).{0,20}(?:이므로|이기 때문에).{0,30}(?:역세권|가능)", normalized) and not any_of("심의", "예외", "특례"):
        markers.add("AUTO_350M")
    if re.search(r"(?:일반적으로|일반적인).{0,30}500\s*㎡.{0,10}이상", normalized):
        markers.add("GENERAL_MIN_500")
    repealed_title = "서울특별시 어르신안심주택 공급 지원에 관한 조례"
    if repealed_title in normalized and any_of("현재", "현행", "2026년") and not any_of("폐지", "과거", "종전", "통합"):
        markers.add("REPEALED_AS_CURRENT")
    if has("안심주택", "임대형기숙사") and re.search(r"국가(?:기준)?.{0,20}300\s*㎡.{0,20}(?:만|최종)", normalized):
        markers.add("GENERAL_RULE_OVERRIDES_SPECIAL")
    if "400%" in normalized and any_of("적용됩니다", "자동 적용", "당연히 적용") and not any_of("완화 가능", "완화할 수"):
        markers.add("AUTO_FAR_400")
    if has("주차", "자동 완화") or (has("주차", "완화됩니다") and any_of("교통", "보행")):
        markers.add("AUTO_PARKING_RELAX")
    if any_of("조건은 충족된 것으로", "사실은 충족된 것으로", "충족되었다고 가정") and any_of("사업 가능", "사업이 가능", "승인 가능", "허가 가능"):
        markers.add("ASSUMED_FACTS")
    return markers


DEFAULT_ORACLE_PATH = Path(__file__).resolve().parents[1] / "skills" / "law-interpretation-request" / "evals" / "v0.2.4-ansim-housing-oracle.json"

REQUIRED_CASE_MARKERS = {
    "ASH-01": {"PROMOTION_1000_DISTINCTION", "CURRENT_STANDARD_REQUIRED", "UNCERTAINTY_PRESERVED"},
    "ASH-02": {"BASE_250M", "EXCEPTION_350M_REVIEW"},
    "ASH-03": {"DORM_300_NATIONAL", "DORM_200_SEOUL", "SPECIAL_PARKING_RULE"},
    "ASH-04": {"BASE_250M", "EXCEPTION_350M_REVIEW", "DISTANCE_NOT_REPLACED", "UNCERTAINTY_PRESERVED"},
    "ASH-05": {"SPECIAL_PARKING_RULE", "MIXED_USE_SEPARATE", "PHYSICAL_USE_SEPARATE"},
    "ASH-06": {"BASE_250M", "EXCEPTION_350M_REVIEW", "CURRENT_STANDARD_REQUIRED"},
    "ASH-07": {"MAJORITY_RULE", "MAJORITY_EXCEPTION", "SEPARATE_EXCEPTIONS", "UNCERTAINTY_PRESERVED"},
    "ASH-08": {"MIXED_USE_SEPARATE", "FAR_400_CONDITIONAL", "INDUSTRIAL_SITE_BY_COMMITTEE", "DELEGATION_CHAIN"},
    "ASH-09": {"REPEALED_LAW_BLOCK", "CURRENT_STANDARD_REQUIRED", "MEDICAL_350", "UNCERTAINTY_PRESERVED"},
}

MARKER_GATES = {
    "REPEALED_AS_CURRENT": "TEMPORAL_AUTHORITY",
    "STALE_POLICY_CONTROLS": "AUTHORITY_PRIORITY",
    "GENERAL_RULE_OVERRIDES_SPECIAL": "SPECIAL_RULE_PRECEDENCE",
    "GENERAL_350M": "EXCEPTION_SEMANTICS",
    "AUTO_350M": "EXCEPTION_SEMANTICS",
    "AUTO_FAR_400": "EXCEPTION_SEMANTICS",
    "AUTO_PARKING_RELAX": "EXCEPTION_SEMANTICS",
    "GENERAL_MIN_500": "EVIDENCE_GROUNDING",
    "ASSUMED_FACTS": "UNCERTAINTY_PRESERVATION",
}

MARKER_REASONS = {
    "REPEALED_AS_CURRENT": "폐지·통합된 법령을 질의 기준일의 현행 근거로 사용",
    "STALE_POLICY_CONTROLS": "과거 정책자료를 현행 공식 기준보다 우선 사용",
    "GENERAL_RULE_OVERRIDES_SPECIAL": "특별규정 대신 일반규정만으로 최종 결론을 확정",
    "GENERAL_350M": "350m 예외범위를 일반 역세권 범위로 표현",
    "AUTO_350M": "350m 예외의 법정 사유·통합심의를 생략하고 자동 적용",
    "AUTO_FAR_400": "재량적 용적률 완화를 자동 적용으로 표현",
    "AUTO_PARKING_RELAX": "법정 요건과 위임관계 없이 주차완화를 자동 적용",
    "GENERAL_MIN_500": "직접 현행 근거 없이 일반 최소면적을 500㎡로 확정",
    "ASSUMED_FACTS": "확인되지 않은 사실을 보충해 사업·승인 가능성을 확정",
}


def evaluate_ansim_case(
    case_id: str,
    answer: str,
    *,
    process_ok: bool = True,
    oracle_path: Path = DEFAULT_ORACLE_PATH,
) -> dict[str, Any]:
    oracle = load_ansim_oracle(oracle_path)
    cases = {case["id"]: case for case in oracle["cases"]}
    if case_id not in cases:
        raise ValueError(f"unknown ansim case: {case_id}")

    if not process_ok or not answer.strip():
        return {
            "case_id": case_id,
            "verdict": "INVALID",
            "findings": [{"gate": None, "passed": False, "marker": "UNUSABLE_RESPONSE", "case_id": case_id, "reason": "usable response is unavailable"}],
            "critical_negative_markers": [],
        }

    detected = detect_ansim_markers(answer)
    forbidden = set(cases[case_id]["must_not"]) | set(MARKER_GATES)
    negative = sorted(detected & forbidden)
    findings = [
        {
            "gate": MARKER_GATES.get(marker),
            "passed": False,
            "marker": marker,
            "case_id": case_id,
            "reason": MARKER_REASONS.get(marker, f"forbidden marker detected: {marker}"),
        }
        for marker in negative
    ]

    missing = sorted(REQUIRED_CASE_MARKERS[case_id] - detected)
    findings.extend(
        {
            "gate": None,
            "passed": False,
            "marker": marker,
            "case_id": case_id,
            "reason": f"required semantic marker missing: {marker}",
        }
        for marker in missing
    )
    critical = [marker for marker in oracle["critical_negative_markers"] if marker in detected]
    return {
        "case_id": case_id,
        "verdict": "FAIL" if findings else "PASS",
        "findings": findings,
        "critical_negative_markers": critical,
    }


def _validate_ansim_oracle(oracle: dict[str, Any]) -> None:
    if oracle.get("contract") != "ansim_housing_regression_oracle=v0.2.4-candidate":
        raise ValueError("invalid ansim housing oracle contract")
    if oracle.get("effective_date") != "2026-08-31":
        raise ValueError("invalid ansim housing oracle effective date")
    if oracle.get("verdicts") != EXPECTED_VERDICTS:
        raise ValueError("verdicts must be PASS, FAIL, INVALID")
    if oracle.get("global_hard_gates") != EXPECTED_GLOBAL_HARD_GATES:
        raise ValueError("invalid global hard gates")
    if oracle.get("critical_negative_markers") != EXPECTED_CRITICAL_MARKERS:
        raise ValueError("invalid critical negative markers")

    cases = oracle.get("cases")
    if not isinstance(cases, list) or [case.get("id") for case in cases] != EXPECTED_CASE_IDS:
        raise ValueError("cases must be exactly ASH-01 through ASH-09")
    for case in cases:
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"{case.get('id')} prompt must be non-empty")
        if not isinstance(case.get("severity"), str) or not case["severity"].strip():
            raise ValueError(f"{case['id']} severity must be non-empty")
        if not case.get("must") and not case.get("must_markers"):
            raise ValueError(f"{case['id']} requires must or must_markers")
        if not isinstance(case.get("must_not"), list):
            raise ValueError(f"{case['id']} must_not must be a list")
        if not isinstance(case.get("authorities"), list) or not case["authorities"]:
            raise ValueError(f"{case['id']} authorities must be non-empty")


def build_ansim_summary(
    results: list[dict[str, Any]],
    *,
    model: str,
    plugin_version: str,
    repetitions: int,
) -> dict[str, Any]:
    process_success = sum(bool(result.get("process_ok")) for result in results)
    pass_count = sum(result.get("verdict") == "PASS" for result in results)
    fail_count = sum(result.get("verdict") == "FAIL" for result in results)
    invalid_count = sum(result.get("verdict") == "INVALID" for result in results)
    gate_violations = [
        finding
        for result in results
        for finding in result.get("findings", [])
        if finding.get("gate")
    ]
    critical = [
        marker
        for marker in EXPECTED_CRITICAL_MARKERS
        if any(marker in result.get("critical_negative_markers", []) for result in results)
    ]
    per_case: dict[str, list[str]] = {case_id: [] for case_id in EXPECTED_CASE_IDS}
    for result in results:
        per_case[result["case_id"]].append(result["verdict"])

    if repetitions == 1:
        stability_acceptance = None
        accepted = (
            len(results) == 9
            and process_success == 9
            and pass_count == 9
            and not gate_violations
            and not critical
        )
    elif repetitions == 3:
        stability_acceptance = (
            len(results) == 27
            and process_success == 27
            and pass_count >= 26
            and not critical
        )
        accepted = stability_acceptance
    else:
        raise ValueError("repetitions must be 1 or 3")

    return {
        "contract": "ansim_housing_regression_oracle=v0.2.4-candidate",
        "model": model,
        "plugin_version": plugin_version,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "case_count": len(results),
        "process_success": process_success,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "invalid_count": invalid_count,
        "global_hard_gate_violations": gate_violations,
        "critical_negative_markers": critical,
        "per_case_verdict": per_case,
        "stability_acceptance": stability_acceptance,
        "release_verdict": "PASS" if accepted else "FAIL",
    }
