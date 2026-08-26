from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.regression_oracles import (
    CHECKS,
    EXPECTED_CRITICAL_CASES,
    evaluate_all,
    evaluate_case,
    load_oracle_definitions,
    validate_oracle_definitions,
)
from scripts.regression_checks import DEFAULT_H1


def default_answer(body: str = "결론은 제공된 전제 범위에서 확인됩니다.") -> str:
    return "\n\n".join([*DEFAULT_H1[:2], body, *DEFAULT_H1[2:]])


def test_e02_runtime_contract_requires_explicit_unsuitability_sentence():
    skill = Path("skills/law-interpretation-request/SKILL.md").read_text(encoding="utf-8")
    assert "첫 문장에서 법제처 법령해석 대상으로 부적합할 수 있음을 명시한다" in skill
    expected = bytes.fromhex("EC9DB420EC9CA0ED9895EC9790EC849CEB8A9420ECB2AB20EBACB8EC9EA5EC9D8420EBB098EB939CEC8B9C20E2809CEC9DB420EC9A94ECB2ADEC9D8020EBB295ECA09CECB29820EBB295EBA0B9ED95B4EC849D20EB8C80EC8381EC9CBCEBA19CEB8A9420EBB680ECA081ED95A9ED95A020EC889820EC9E88EC8AB5EB8B88EB8BA42eE2809DEBA19C20EC9E91EC84B1ED959CEB8BA42e").decode("utf-8")
    assert expected in skill


def test_machine_oracle_registry_is_exactly_e01_to_e46():
    definitions = load_oracle_definitions()
    assert [item["case"] for item in definitions] == [f"E{i:02d}" for i in range(1, 47)]
    assert {
        int(item["case"][1:]) for item in definitions if item["release_critical"]
    } == EXPECTED_CRITICAL_CASES
    assert len(EXPECTED_CRITICAL_CASES) == 14
    assert all(item["checks"] for item in definitions)


def test_unknown_named_check_is_rejected():
    definitions = load_oracle_definitions()
    bad = deepcopy(definitions)
    bad[0]["checks"].append("unknown_contract_check")

    with pytest.raises(ValueError, match="unknown checks"):
        validate_oracle_definitions(bad)


def test_known_bad_same_term_fixture_fails_strong_oracle():
    answer = default_answer(
        "같은 조문의 건축물에 대한 갑설은 타당하고 을설은 타당하므로 각 실체 논거를 병렬로 제시합니다."
    )
    result = evaluate_case(18, answer)
    assert result["contract_oracle"] == "FAIL"
    assert any("same_term_conflict_hard_stop" in failure for failure in result["contract_failures"])


def test_same_term_oracle_accepts_common_meaning_variant():
    answer = default_answer(
        "갑설은 부속시설을 포함하고 을설은 부속시설을 제외하여 동일한 법률용어의 범위를 다르게 정합니다. 공통 의미 기준이 확인되기 전에는 우열을 확정할 수 없습니다."
    )
    result = evaluate_case(18, answer)
    assert result["contract_oracle"] == "PASS"
    assert result["contract_failures"] == []


def test_known_good_critical_fixture_passes_answer_first_oracle():
    answer = default_answer("소형 주택은 공동주택이고 30세대 본칙이 적용되며 50세대 예외 대상이 아니므로 승인 대상입니다.")
    result = evaluate_case(36, answer)
    assert result["contract_oracle"] == "PASS"
    assert result["contract_failures"] == []
    assert result["release_critical"] is True


def test_e37_good_fixture_rejects_unstable_url_and_accepts_stable_url():
    stable = default_answer(
        "두 규정의 동일 사항을 비교합니다. [공식 원문](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=287405)"
    )
    bad = default_answer(
        "[별표](https://www.law.go.kr/LSW/flDownload.do?flNm=%EC%8A%B9%EA%B0%95%EA%B8%B0&flSeq=143339963)"
    )
    assert evaluate_case(37, stable)["contract_oracle"] == "PASS"
    bad_result = evaluate_case(37, bad)
    assert bad_result["contract_oracle"] == "FAIL"
    assert any("no_unstable_download_links" in failure for failure in bad_result["contract_failures"])


def test_e02_live_response_variant_passes_suitability_oracle():
    answer = """현재 질문은 특정 건물이 법정 시설에 해당하는지를 직접 판단해 달라는 형태라서 법제처 법령해석 대상으로는 부적합할 수 있습니다. 제10조에서 말하는 시설의 객관적 의미와 적용범위에 해당 유형이 포함되는지를 묻는 방식으로 보정해야 합니다.

1. 해당 법률의 정확한 명칭은 무엇인가요?
2. 제10조의 정확한 문언은 무엇인가요?
3. 건물의 현재 용도는 무엇인가요?
4. 구조와 규모는 어떻게 되나요?
5. 해당 시설에서 수행하는 업무는 무엇인가요?
"""
    assert evaluate_case(2, answer)["contract_oracle"] == "PASS"


def test_live_language_variants_satisfy_strong_oracles():
    e03 = """현재 요청은 처분의 위법성을 직접 판단하는 내용이어서 법제처 질의로는 부적합할 수 있습니다. 근거 조문이 어떤 의미·범위로 적용되는지를 묻는 법령해석 질문으로 보정해야 합니다.

1. 어떤 허가 신청이었나요?
2. 근거 조문은 무엇인가요?
3. 처분 사유를 붙여주세요.
4. 핵심 사실을 적어 주세요.
5. 양측 해석은 어떻게 다른가요?
6. 제출 주체를 알려주세요.
"""
    assert evaluate_case(3, e03)["contract_oracle"] == "PASS"

    e13 = default_answer(
        "서로 다른 특례라는 사실만으로 중첩 적용 여부를 바로 정할 수는 없습니다. 규범적 연결 전제와 적용 배제 문언을 확인해야 하며, 중첩 적용될 여지도 있습니다."
    )
    assert evaluate_case(13, e13)["contract_oracle"] == "PASS"

    e18 = default_answer(
        "갑설과 을설은 동일한 법률용어의 외연을 달리 전제하고 있습니다. 공통 판단기준이 확정되기 전에는 양설의 실체 논거를 병렬로 구성할 수 없습니다."
    )
    assert evaluate_case(18, e18)["contract_oracle"] == "PASS"

    e39 = default_answer(
        "제공된 규정만으로는 신축이 승인요건이라고 볼 수 없습니다. 다만 별지의 신설·증설 구분의 법적 기능이 확인되지 않아 기존 건축물의 승인 가능 여부를 확정할 수는 없습니다."
    )
    assert evaluate_case(39, e39)["contract_oracle"] == "PASS"


def test_e39_directional_support_or_adverse_language_fails():
    supportive = default_answer(
        "별지의 신설·증설 의미는 확인 필요하여 승인 여부를 확정할 수 없습니다. 다만 법률에 신축 제한이 없다는 점은 승인 가능성을 뒷받침합니다."
    )
    adverse = default_answer(
        "별지의 신설·증설 의미는 확인 필요하여 승인 여부를 확정할 수 없습니다. 기존 건축물은 신설로 보기 어려워 승인받기 어렵습니다."
    )
    for answer in (supportive, adverse):
        result = evaluate_case(39, answer)
        assert result["contract_oracle"] == "FAIL"
        assert any("no_directional_abstract_conclusion" in failure for failure in result["contract_failures"])


def test_v023_temporal_authority_evidence_oracles():
    e43 = default_answer(
        "2024년 최초 허가 당시 법령 버전과 2026년 변경허가를 분리해야 합니다. 2025년 개정의 시행일과 경과조치를 확인하여 종전 규정과 신법 중 어느 기준이 각 행위에 적용되는지 판단해야 합니다."
    )
    assert evaluate_case(43, e43)["contract_oracle"] == "PASS"

    e44 = default_answer(
        "2024년 최초 허가 이후 기준이 개정되었고 변경허가를 준비하는 경우, 허가일·개정법 시행일·변경허가 신청일이 확인되지 않았으므로 적용법을 확정할 수 없습니다. 이 날짜와 경과조치를 확인할 필요가 있어 결론은 조건부입니다."
    )
    assert evaluate_case(44, e44)["contract_oracle"] == "PASS"

    e45 = default_answer(
        "법제처 해석은 행정부의 통일적 집행기준이지만 대법원 판결과 같은 법적 구속력을 갖는 것은 아닙니다. 2020년 개정으로 조문 문언과 정의가 달라졌으므로 2014년 판결 당시 조문과 후속 대법원 판단의 적용범위를 비교해야 합니다."
    )
    assert evaluate_case(45, e45)["contract_oracle"] == "PASS"

    e46 = default_answer(
        "법률 조문과 판례가 제시하는 기준은 근거가 되지만, 현재 사실관계가 판례의 C와 유사한지 또는 차이가 있는지는 별도의 포섭 문제입니다. 그 사실 차이에 따라 적용 결론이 달라질 수 있습니다."
    )
    assert evaluate_case(46, e46)["contract_oracle"] == "PASS"


def test_evaluate_all_reports_deterministic_pass_count_and_skip():
    summary = evaluate_all([
        {"case": 4, "answer": default_answer()},
        {"case": 37},
    ])
    assert summary["contract_oracle_pass"] == "1/2"
    assert summary["results"][1]["contract_oracle"] == "SKIP"
    assert set(CHECKS) >= {
        "exact_default_h1",
        "no_unstable_download_links",
        "temporal_lifecycle",
        "authority_versioning",
        "claim_inference_separation",
    }


def test_runner_result_contract_fields_are_additive():
    import run_jdipt_full_regression_v4 as runner

    result = runner.Result(
        case=36,
        title="fixture",
        returncode=0,
        duration_seconds=0.0,
        answer_file="E36.md",
        log_file="E36.log.txt",
        process_ok=True,
        first_nonblank="# 1. 질의요지",
        h1_lines=DEFAULT_H1,
        h1_check="PASS",
        hygiene_check="PASS",
        incomplete_url_check="PASS",
        timeout=False,
        environment_error=None,
        error=None,
        contract_oracle="PASS",
        contract_failures=[],
        release_critical=True,
    )
    assert result.contract_oracle == "PASS"
    assert result.contract_failures == []
    assert result.release_critical is True
