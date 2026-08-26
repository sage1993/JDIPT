"""Deterministic contract oracles for JDIPT evaluation cases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Iterable

from scripts.eval_suite import suite_case_ids
from scripts.regression_checks import (
    check_h1,
    check_output_hygiene,
    check_urls,
    exact_h1_lines,
    first_nonblank_line,
)

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "skills" / "law-interpretation-request" / "evals"
DEFAULT_ORACLE_PATH = EVAL_ROOT / "machine-oracles.json"
DEFAULT_EXTENSION_ORACLE_PATH = EVAL_ROOT / "v0.2.3-machine-oracles.json"
EXPECTED_CRITICAL_CASES = suite_case_ids("core")


def _pass() -> tuple[bool, str]:
    return True, ""


def _fail(reason: str) -> tuple[bool, str]:
    return False, reason


def _contains(answer: str, *terms: str) -> bool:
    return all(term in answer for term in terms)


def _contains_any(answer: str, terms: tuple[str, ...]) -> bool:
    return any(term in answer for term in terms)


def _default_h1(answer: str, case: int) -> tuple[bool, str]:
    result = check_h1(answer, case, "default")
    return (True, "") if result == "PASS" else _fail(f"default H1 contract failed: {result}")


def _moleg_h1(answer: str, case: int) -> tuple[bool, str]:
    result = check_h1(answer, case, "moleg")
    return (True, "") if result == "PASS" else _fail(f"MOLEG H1 contract failed: {result}")


def _questions_only(answer: str, case: int) -> tuple[bool, str]:
    if exact_h1_lines(answer):
        return _fail("question-only response contains a draft H1")
    return _pass()


def _question_count(answer: str, case: int) -> tuple[bool, str]:
    punctuation_count = sum(1 for line in answer.splitlines() if line.strip().endswith(("?", "？")))
    numbered_count = len(re.findall(r"(?m)^\s*\d+[.)]\s+\S", answer))
    count = max(punctuation_count, numbered_count)
    return (True, "") if 3 <= count <= 7 else _fail(f"expected 3-7 questions, found {count}")


def _suitability(answer: str, case: int) -> tuple[bool, str]:
    if not _contains_any(answer, ("부적합", "적합하지", "법령해석 대상이 아닐", "사실판단에 가까")):
        return _fail("missing objective suitability explanation")
    objective_scope = _contains_any(
        answer,
        ("객관적", "법령의 의미", "적용범위", "적용 범위", "요건", "근거조항"),
    ) or bool(
        re.search(
            r"(?:법령|조문|근거[ ]*조문|근거조항|법[ ]*제[ ]*\d+[ ]*조|제[ ]*\d+[ ]*조).{0,60}(의미|범위|포함|적용|판단기준)",
            answer,
        )
    )
    if not objective_scope:
        return _fail("missing objective legal-scope correction")
    return _pass()


def _no_draft_h1(answer: str, case: int) -> tuple[bool, str]:
    return _questions_only(answer, case)


def _not_question_only(answer: str, case: int) -> tuple[bool, str]:
    if exact_h1_lines(answer):
        return _pass()
    return _fail("required substantive default-format response became question-only")


def _missing_premise(answer: str, case: int) -> tuple[bool, str]:
    if not _contains_any(answer, ("전제", "연결 근거", "해석근거")):
        return _fail("missing premise/connecting-ground discussion")
    if not _contains_any(
        answer,
        ("확인 필요", "확인해야", "확정할 수 없", "단정할 수 없", "불확실", "배제할 수 없", "여지도"),
    ):
        return _fail("missing indeterminate treatment")
    return _pass()


def _same_term_conflict(answer: str, case: int) -> tuple[bool, str]:
    conflict_terms = ("충돌", "상충", "서로 다른 의미", "의미 자체", "전제 차이", "다르게 설정", "범위를 달리", "외연을 달리", "포함하는 의미", "제외하는 의미")
    common_terms = ("공통 정의", "공통 기준", "공통 의미 기준", "개념 기준", "공통된 개념", "공통 해석 기준", "동일한 용어", "동일한 법률용어", "같은 용어", "용어의 범위", "공통 판단기준")
    premise_conflict = bool(re.search(r"갑설.{0,60}포함.{0,60}을설.{0,60}제외", answer, re.S))
    if not (_contains_any(answer, conflict_terms) or premise_conflict) or not _contains_any(answer, common_terms):
        return _fail("missing same-term conflict and common-definition hard stop")
    forbidden = ("갑설의 실체적 타당성", "을설의 실체적 타당성", "갑설은 타당", "을설은 타당")
    if _contains_any(answer, forbidden):
        return _fail("parallel substantive arguments were generated before common term resolution")
    return _pass()


def _minimal_question_facts(answer: str, case: int) -> tuple[bool, str]:
    if first_nonblank_line(answer) != "# 1. 질의요지":
        return _fail("question summary does not start with the exact first H1")
    for marker in ("사업목적", "처분경위", "기관입장"):
        if marker in answer and not _contains_any(answer, ("제공되지", "확인되지", "확인 필요")):
            return _fail(f"invented fact marker in question summary: {marker}")
    return _pass()


def _provided_premises_not_reasked(answer: str, case: int) -> tuple[bool, str]:
    if _contains_any(answer, ("다시 제공해", "전제를 다시 알려", "추가로 제공해")):
        return _fail("provided premises were re-requested")
    return _pass()


def _conditional_unknown(answer: str, case: int) -> tuple[bool, str]:
    if not _contains(answer, "A", "B") or "C" not in answer:
        return _fail("A/B/C requirement mapping is missing")
    if not _contains_any(answer, ("확인 필요", "확인되지 않", "정보가 없")):
        return _fail("unknown C state was not preserved")
    if not _contains_any(answer, ("조건부", "조건에 따라", "확정할 수 없")):
        return _fail("conclusion is not conditional")
    return _pass()


def _classification_chain(answer: str, case: int) -> tuple[bool, str]:
    if not _contains(answer, "소형 주택", "공동주택", "30세대", "50세대"):
        return _fail("classification/main-rule/exception chain is incomplete")
    if not _contains_any(answer, ("대상", "승인")):
        return _fail("classification case does not state the approval consequence")
    return _pass()


def _no_false_history(answer: str, case: int) -> tuple[bool, str]:
    years = re.findall(r"20\d{2}년", answer)
    if years and not _contains_any(answer, ("제정", "개정문", "시행일", "확인")):
        return _fail("specific history year lacks an identified source/check")
    return _pass()


def _no_unstable_download(answer: str, case: int) -> tuple[bool, str]:
    ok, problems = check_urls(answer)
    return (True, "") if ok else _fail("URL contract failed: " + "; ".join(problems))


def _no_directional_conclusion(answer: str, case: int) -> tuple[bool, str]:
    start = answer.find("# 2. 검토결론")
    end = answer.find("# 3. 검토이유", start + 1) if start >= 0 else -1
    conclusion = answer[start:end] if start >= 0 and end > start else answer
    if not _contains_any(conclusion, ("조건부", "확인 필요", "확정할 수 없", "확정할 수는 없", "단정할 수 없", "단정할 수는 없", "확정하기 어렵")):
        return _fail("unresolved abstract fixture lacks a conditional/neutral conclusion")
    forbidden = (
        "가능합니다",
        "불가능합니다",
        "반드시 가능",
        "반드시 불가",
        "가능성을 뒷받침",
        "가능성이 높",
        "가능성이 크",
        "가능성은 열려",
        "승인받기 어렵",
        "허가받기 어렵",
        "적용받기 어렵",
    )
    if _contains_any(conclusion, forbidden):
        return _fail("unresolved abstract fixture received a directional conclusion")
    return _pass()


def _source_form_conditional(answer: str, case: int) -> tuple[bool, str]:
    if not _contains_any(answer, ("별지", "신설", "증설")):
        return _fail("source-form classification was not discussed")
    if not _contains_any(answer, ("조건부", "확인 필요", "미해결", "확정할 수 없", "확정할 수는 없", "확정하기 어렵")):
        return _fail("source-form conflict was not left conditional")
    return _pass()


def _absence_neutral(answer: str, case: int) -> tuple[bool, str]:
    if not _contains_any(answer, ("규정이 없", "금지하지 않", "명시적 제한 없음", "부재")):
        return _fail("absence-of-rule issue was not addressed")
    return _no_directional_conclusion(answer, case)


def _referenced_source_block(answer: str, case: int) -> tuple[bool, str]:
    if not _contains(answer, "별지 제3호서식"):
        return _fail("referenced annex identity is missing")
    if not _contains_any(answer, ("미확인", "확인하지 못", "실제 문언", "제공되지 않")):
        return _fail("unresolved annex state is missing")
    return _no_directional_conclusion(answer, case)


def _unresolved_source_neutral(answer: str, case: int) -> tuple[bool, str]:
    if not _contains(answer, "별지 제5호서식"):
        return _fail("referenced form identity is missing")
    if not _contains_any(answer, ("미확인", "확인하지 못", "실제 문언", "제공되지 않")):
        return _fail("unresolved form state is missing")
    return _no_directional_conclusion(answer, case)


def _temporal_lifecycle(answer: str, case: int) -> tuple[bool, str]:
    if not _contains_any(answer, ("최초 허가", "허가 당시", "2024")):
        return _fail("initial permit reference date was not separated")
    if "변경허가" not in answer:
        return _fail("later modification-permit event was not separated")
    if not _contains_any(answer, ("시행일", "경과조치")):
        return _fail("effective date/transitional provision check is missing")
    if not _contains_any(answer, ("종전", "신법", "개정", "법령 버전")):
        return _fail("old/new law version relationship is missing")
    return _pass()


def _temporal_unknown(answer: str, case: int) -> tuple[bool, str]:
    if not _contains(answer, "허가일", "시행일") or "변경허가" not in answer:
        return _fail("material dates were not identified")
    if not _contains_any(answer, ("확인 필요", "확인해야", "확정할 수 없", "조건부")):
        return _fail("missing dates did not lower conclusion strength")
    return _pass()


def _authority_versioning(answer: str, case: int) -> tuple[bool, str]:
    if not _contains(answer, "법제처", "대법원"):
        return _fail("authority comparison is incomplete")
    if not _contains_any(answer, ("구속력", "법원을 구속", "사법적", "행정부")):
        return _fail("legal function/binding effect distinction is missing")
    if not _contains_any(answer, ("개정", "조문 버전", "문언", "정의")):
        return _fail("precedent-to-current-text version check is missing")
    forbidden = ("법제처가 공식 해석했으므로 법원도", "법제처 해석이 법원을 구속")
    if _contains_any(answer, forbidden):
        return _fail("government interpretation was treated as binding on the court")
    return _pass()


def _claim_inference_separation(answer: str, case: int) -> tuple[bool, str]:
    if not _contains_any(answer, ("조문", "법률")) or "판례" not in answer:
        return _fail("source propositions are not identified")
    if not _contains_any(answer, ("사실관계", "유사", "포섭", "같은지", "차이")):
        return _fail("fact-to-rule analytical step is missing")
    forbidden = ("판례가 귀하의 경우에도", "판례가 이 사안에도 B가 적용된다고 판시")
    if _contains_any(answer, forbidden):
        return _fail("analytical inference was misrepresented as a source holding")
    return _pass()


def _hygiene(answer: str, case: int) -> tuple[bool, str]:
    ok, problems = check_output_hygiene(answer)
    return (True, "") if ok else _fail("; ".join(problems))


def _urls(answer: str, case: int) -> tuple[bool, str]:
    ok, problems = check_urls(answer)
    return (True, "") if ok else _fail("; ".join(problems))


CHECKS: dict[str, Callable[[str, int], tuple[bool, str]]] = {
    "exact_default_h1": _default_h1,
    "exact_moleg_h1": _moleg_h1,
    "questions_only": _questions_only,
    "question_count_3_to_7": _question_count,
    "suitability_explained": _suitability,
    "no_draft_h1": _no_draft_h1,
    "not_question_only": _not_question_only,
    "missing_premise_treatment": _missing_premise,
    "same_term_conflict_hard_stop": _same_term_conflict,
    "minimal_question_facts": _minimal_question_facts,
    "provided_premises_not_reasked": _provided_premises_not_reasked,
    "conditional_unknown_state": _conditional_unknown,
    "classification_chain": _classification_chain,
    "no_false_history": _no_false_history,
    "no_unstable_download_links": _no_unstable_download,
    "no_directional_abstract_conclusion": _no_directional_conclusion,
    "source_form_conditional": _source_form_conditional,
    "absence_neutral": _absence_neutral,
    "referenced_source_block": _referenced_source_block,
    "unresolved_source_neutral": _unresolved_source_neutral,
    "temporal_lifecycle": _temporal_lifecycle,
    "temporal_unknown": _temporal_unknown,
    "authority_versioning": _authority_versioning,
    "claim_inference_separation": _claim_inference_separation,
    "moleg_submission_note": lambda answer, case: (
        _pass() if "※ 제출 전 확인" in answer else _fail("missing submission confirmation note")
    ),
    "answer_first_default": lambda answer, case: (
        _pass() if first_nonblank_line(answer) == "# 1. 질의요지" and answer.find("# 2. 검토결론") < answer.find("# 3. 검토이유")
        else _fail("answer-first default rendering failed")
    ),
    "hygiene_clean": _hygiene,
    "urls_complete": _urls,
}


def _load_cases(source: Path) -> list[dict[str, Any]]:
    data = json.loads(source.read_text(encoding="utf-8"))
    definitions = data.get("cases")
    if not isinstance(definitions, list):
        raise ValueError(f"{source.name} must contain a cases list")
    return definitions


def load_oracle_definitions(path: Path | None = None) -> list[dict[str, Any]]:
    if path is not None:
        definitions = _load_cases(path)
    else:
        definitions = [
            *_load_cases(DEFAULT_ORACLE_PATH),
            *_load_cases(DEFAULT_EXTENSION_ORACLE_PATH),
        ]
    validate_oracle_definitions(definitions)
    return definitions


def validate_oracle_definitions(definitions: list[dict[str, Any]]) -> None:
    if len(definitions) != 46:
        raise ValueError(f"expected 46 oracle definitions, found {len(definitions)}")
    numbers: list[int] = []
    for definition in definitions:
        case_id = definition.get("case")
        match = re.fullmatch(r"E(\d{2})", str(case_id))
        if not match:
            raise ValueError(f"invalid oracle case id: {case_id!r}")
        number = int(match.group(1))
        numbers.append(number)
        checks = definition.get("checks")
        if not isinstance(checks, list) or not checks:
            raise ValueError(f"E{number:02d} must have a non-empty checks list")
        unknown = sorted(set(checks) - set(CHECKS))
        if unknown:
            raise ValueError(f"E{number:02d} has unknown checks: {unknown}")
        if not isinstance(definition.get("release_critical"), bool):
            raise ValueError(f"E{number:02d} release_critical must be boolean")
    if sorted(numbers) != list(range(1, 47)):
        raise ValueError(f"oracle cases must be exactly E01-E46, found {numbers}")
    actual_critical = {
        int(str(d["case"])[1:]) for d in definitions if d["release_critical"]
    }
    if actual_critical != EXPECTED_CRITICAL_CASES:
        raise ValueError(f"release-critical cases mismatch: {sorted(actual_critical)}")


def evaluate_case(
    case_number: int,
    answer: str,
    *,
    definitions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    definitions = definitions if definitions is not None else load_oracle_definitions()
    definition = next((item for item in definitions if int(str(item["case"])[1:]) == case_number), None)
    if definition is None:
        raise ValueError(f"no oracle definition for E{case_number:02d}")
    failures: list[str] = []
    for name in definition["checks"]:
        passed, reason = CHECKS[name](answer, case_number)
        if not passed:
            failures.append(f"{name}: {reason}")
    return {
        "contract_oracle": "PASS" if not failures else "FAIL",
        "contract_failures": failures,
        "release_critical": definition["release_critical"],
    }


def evaluate_all(
    results: Iterable[object],
    *,
    definitions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    definitions = definitions if definitions is not None else load_oracle_definitions()
    evaluated: list[dict[str, Any]] = []
    for item in results:
        if isinstance(item, dict):
            case_number = int(item["case"])
            answer = item.get("answer") or item.get("answer_text") or item.get("raw_answer")
        else:
            case_number = int(getattr(item, "case"))
            answer = getattr(item, "answer", None) or getattr(item, "answer_text", None)
        if not isinstance(answer, str):
            evaluated.append({
                "case": case_number,
                "contract_oracle": "SKIP",
                "contract_failures": ["answer text unavailable"],
            })
            continue
        evaluated.append({"case": case_number, **evaluate_case(case_number, answer, definitions=definitions)})
    passed = sum(item["contract_oracle"] == "PASS" for item in evaluated)
    return {
        "results": evaluated,
        "contract_oracle_pass": f"{passed}/{len(evaluated)}",
        "contract_oracle_pass_count": passed,
        "contract_oracle_total": len(evaluated),
    }
