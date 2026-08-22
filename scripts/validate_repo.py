from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
PACKAGE = ROOT / "package.json"
PACKAGE_LOCK = ROOT / "package-lock.json"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_DOC = ROOT / "docs" / "plugin-packaging.md"
CODEX = ROOT / "config" / "codex.example.toml"
AGENTS = ROOT / "AGENTS.md"
AGENT_CONFIG = SKILL.parent / "agents" / "openai.yaml"
REQUEST_FORMAT = SKILL.parent / "references" / "request-format.md"
SOURCE_POLICY = SKILL.parent / "references" / "source-policy.md"
ISSUE_MAPPING = SKILL.parent / "references" / "legal-issue-mapping.md"
ELIGIBILITY = SKILL.parent / "references" / "eligibility-checklist.md"
EVAL_SCENARIOS = SKILL.parent / "evals" / "scenarios.md"
EVAL_EXPECTED = SKILL.parent / "evals" / "expected-behavior.md"
EVAL_V022 = SKILL.parent / "evals" / "v0.2.2-regressions.md"
AGENT_SKILL_DUPLICATE = ROOT / ".agents" / "skills" / "law-interpretation-request"

REQUIRED_REFERENCES = {
    "baseline-document-policy.md",
    "case-patterns.md",
    "eligibility-checklist.md",
    "interpretation-principles.md",
    "legal-issue-mapping.md",
    "logic-validation.md",
    "request-format.md",
    "source-policy.md",
}
REQUIRED_MCP_TOOLS = {
    "search_law",
    "get_law_text",
    "search_decisions",
    "get_decision_text",
    "legal_analysis",
    "discover_tools",
    "execute_tool",
}
REQUIRED_LOGIC_SKILL_MARKERS = {
    "references/logic-validation.md",
    "내부 논리검증 Gate",
    "전건 부정",
    "후건 긍정",
    "비정형 자연어 추론",
    "사실성 미확인",
    "갑설과 을설을 각각 독립 검증",
    "추상 논리 시나리오",
    "선택지 완전성",
    "동일한 법률용어",
    "내부 오류분류명",
    "BLOCK",
}
REQUIRED_ISSUE_MAPPING_SKILL_MARKERS = {
    "references/legal-issue-mapping.md",
    "법적 쟁점 매핑 Gate",
    "문제 발생 지점",
    "규율 공백",
    "충족",
    "불충족",
    "확인 필요",
    "가상 규정·정의·본칙·예외·사실관계를 직접 제공",
}
REQUIRED_COUNTEREVIDENCE_SKILL_MARKERS = {
    "Source Completeness",
    "Counterevidence",
    "잠정 결론",
    "별표",
    "별지서식",
    "규정 부재",
    "위임근거",
    "실체·절차·신청양식 기능",
    "조건부 결론",
}
REQUIRED_V022_SKILL_MARKERS = {
    "Fail-closed Hard Gates",
    "Referenced Source Resolution Hard Gate",
    "참조자료 확인 실패",
    "정부24",
    "첫 비공백 줄",
    "초안을 **폐기**",
    "기존 일반 건축물의 최초 전환",
    "건축물 신축",
}
REQUIRED_OUTPUT_SKILL_MARKERS = {
    "모든 사용자용 최종 출력은 Markdown",
    "정식 요청서라는 표현이 없어도 일반적인 대한민국 법령 해석·적용 질문이면 사용한다",
    "기본 출력 모드 — 별도 형식 지시가 없을 때",
    "추상적인 A/B/P/Q 법적 논리 시나리오",
    "최상위 Markdown 제목은 아래 문자열과 순서를 그대로 사용한다",
    "# 1. 질의요지",
    "# 2. 검토결론",
    "# 3. 검토이유",
    "# 4. 관련 법령 및 자료",
    "검토결론을 상세 검토이유보다 먼저",
    "단일 쟁점",
    "서로 독립적으로 판단 가능한 복수의 법적 쟁점",
    "특수 출력 모드 — 사용자가 명시적으로 요청한 경우에만",
    "`법제처 법령해석요청서`",
    "클릭 가능한 Markdown 인라인 하이퍼링크",
    "최종 Rendering Hard Gate",
    "Output Hygiene check",
    "URL provenance check",
    "$law-interpretation-request",
    "정보 부족으로 질문만 하고 중단",
}
REQUIRED_REQUEST_FORMAT_MARKERS = {
    "사용자가 별도 형식을 명시하지 않으면",
    "기본 4단 법률검토형",
    "A/B/P/Q 같은 추상 법적 논리 시나리오",
    "문자열과 순서 그대로",
    "# 1. 질의요지",
    "# 2. 검토결론",
    "# 3. 검토이유",
    "# 4. 관련 법령 및 자료",
    "검토결론을 상세 검토이유보다 먼저",
    "Narrative Coherence 규칙",
    "서로 독립적으로 판단 가능한 복수의 법적 쟁점",
    "사용자가 명시적으로 법제처 법령해석요청서",
    "# 2. 해석대상 법령조문 및 관련 법령",
    "## 가. 해석대상 법령조문",
    "## 나. 관련 법령",
    "# 3. 대립되는 의견 및 이유",
    "## 가. 갑설",
    "## 나. 을설",
    "모든 사용자용 최종 출력은 Markdown",
    "정보 부족 응답",
    "Output Hygiene 및 최종 Rendering Hard Gate",
    "현재 실행에서 실제 확인한 완전한 공식 URL",
}
REQUIRED_RENDERING_HARD_GATE_MARKERS = {
    "최종 Rendering Hard Gate",
    "첫 비공백 줄",
    "H1의 개수가 정확히 4개",
    "그 초안은 폐기",
    "재렌더링한 결과",
    "# 1. 질의요지",
    "# 2. 검토결론",
    "# 3. 검토이유",
    "# 4. 관련 법령 및 자료",
}
REQUIRED_ISSUE_MAPPING_MARKERS = {
    "법적 쟁점 매핑 Gate",
    "주체",
    "행위",
    "법적 상태 또는 분류",
    "적용 규범 지도",
    "동일 사항의 중복 규율",
    "규율 공백",
    "충족",
    "불충족",
    "확인 필요",
    "문제 발생 지점",
    "해당 검토의 전제로 보존",
    "메타적으로만 말한 경우",
}
REQUIRED_COUNTEREVIDENCE_ISSUE_MAPPING_MARKERS = {
    "잠정 결론",
    "별표",
    "별지서식",
    "명문 제한 없음",
    "규정 부재",
    "결론을 확정하기 전에 우선 확인한다",
    "반대근거의 강제 생성",
    "단순 절차·서식상 분류",
}
REQUIRED_ELIGIBILITY_MARKERS = {
    "정보 부족과 형식상 부적합을 구분",
    "필수 정보 부족",
    "그 응답에서는 초안 작성을 중단",
    "형식상 부적합하지만 보정 가능",
}
REQUIRED_SOURCE_LINK_MARKERS = {
    "본문의 자료명 자체에 Markdown 인라인 하이퍼링크를 기본",
    "[표시 텍스트](실제로 확인한 공식 URL)",
    "원문 접근은 본문 인라인 링크를 우선",
    "URL 패턴을 추측하지 않는다",
    "URL provenance Gate",
    "현재 실행 중 실제로 관찰·확인한 URL만",
    "식별자가 비어 있는 URL",
    "끝이 `=`로 끝나는 미완성 query URL",
}
REQUIRED_COUNTEREVIDENCE_SOURCE_POLICY_MARKERS = {
    "Source Completeness",
    "Counterevidence",
    "잠정 결론",
    "별표",
    "별지서식",
    "명문 제한 없음",
    "규정 부재",
    "법적 기능",
    "명시적 위임근거",
    "잠정 결론을 실제로 제한하는지",
    "존재하지 않는 반대근거",
}
REQUIRED_REFERENCED_SOURCE_POLICY_MARKERS = {
    "Referenced Source Resolution Hard Gate",
    "필수 확인자료로 승격",
    "참조자료 확인 실패",
    "정부24",
    "설립승인사항 변경",
    "기존 일반 건축물의 최초 전환",
    "건축물 신축",
    "실제 문언을 끝내 확인하지 못했으면",
}
REQUIRED_AGENT_CONFIG_MARKERS = {
    "allow_implicit_invocation: false",
    "대한민국 법령의 의미·적용범위·요건·예외·특례·규정관계 검토",
    "기본 4단 법률검토형",
}
REQUIRED_LOGIC_REFERENCE_MARKERS = {
    "P → Q",
    "P ∨ Q",
    "¬P",
    "P ∧ Q",
    "전제 누락",
    "필요조건",
    "충분조건",
    "거짓 양자택일",
    "순환논증",
    "반례 가능성",
    "추상 입력 보존",
    "선택지 완전성",
    "동일 용어 의미 변경",
    "내부 오류분류명",
    "형식적 타당성 | 전제 명확성 | 연결성 | 개념 일관성",
    "형식적 타당성 | 50점",
    "전제의 명확성 | 20점",
    "근거와 결론의 연결성 | 20점",
    "개념 일관성과 반례 대응력 | 10점",
    "타당`: 85~100점",
    "부분 타당`: 65~84점",
    "취약`: 40~64점",
    "부당`: 0~39점",
    "건전성 상태",
    "갑설·을설 상호 비교",
    "수정 제안 작성",
    "원래 문장 번호 | 수정 전 문제 | 수정 원칙 | 수정 예시 | 추가가 필요한 전제",
    "수정 및 재검증 Gate",
}
REQUIRED_COUNTEREVIDENCE_LOGIC_MARKERS = {
    "Counterevidence BLOCK",
    "잠정 결론",
    "법적 기능",
    "위임근거",
    "조건부로 낮춘다",
    "명시적 제한이 없다는 이유만으로 무조건 가능하다고 결론내리지 않는다",
    "별지서식",
}
REQUIRED_REFERENCED_SOURCE_LOGIC_MARKERS = {
    "Referenced Source Resolution BLOCK",
    "실제 문언을 확인하지 못한 경우",
    "정부24",
    "기존 일반 건축물의 최초 전환",
    "건축물 신축",
    "참조자료의 미확인 상태",
}
REQUIRED_LOGIC_EVAL_MARKERS = {
    "E10. 전건 긍정 정상",
    "E11. 전건 부정 오류",
    "E12. 후건 긍정 오류",
    "E13. 핵심 전제 누락",
    "E14. 거짓 양자택일",
    "E15. 필요조건·충분조건 혼동",
    "E16. 사실성 미확인과 형식적 타당성 분리",
    "E17. 비정형 자연어 법적 추론",
    "E18. 갑설·을설 상호 불일치",
    "E19. 검증 결과 비노출",
    "E20. 오류 수정과 원문 대응",
}
REQUIRED_LOGIC_REGRESSION_MARKERS = {
    "E10~E20 공통 출력 조건",
    "추상 기호만 제시한 논리 테스트",
    "임의로 대응시키거나 만들어내지 않는다",
    "가능한 해석 전부",
    "동일 조문의 동일 용어 `건축물`의 의미가 양 설에서 달라졌다는 점을 BLOCK으로 탐지",
    "추가 질문 없이 기본 4단 Markdown 형식을 사용",
    "내부 기호·분류명은 기본 출력에 노출하지 않는다",
}
REQUIRED_OUTPUT_EVAL_MARKERS = {
    "E21. 기본 4단 Answer-first 출력",
    "E22. 명시적 법제처 1~3 출력",
    "E23. Markdown 출력 강제",
    "E24. 공식자료 인라인 하이퍼링크",
    "E25. 질의요지의 사실 최소화",
    "E26. Plugin 설치 후 명시적 Skill 호출 Smoke",
    "E27. 법적 대상·정의·하위분류 특정",
    "E28. 본칙·예외 선택",
    "E29. 동일 사항 중복규율과 특별규정",
    "E30. 규율 공백과 일반법 보충 적용",
    "E31. 사실관계와 법적 요건 연결",
    "E32. 문제 발생 지점 특정",
    "E33. Answer-first 결론 우선",
    "E34. 단일 쟁점 Narrative Coherence",
    "E35. 복수 독립 쟁점에서만 소제목 사용",
    "E36. Golden Case — 22-0351 법적 분류형",
    "E37. Golden Case — 17-0047 중복규율형",
    "E38. Golden Case — 20-0604 규율공백형",
}
REQUIRED_OUTPUT_HYGIENE_EVAL_MARKERS = {
    "공통 Output Hygiene 조건",
    "$law-interpretation-request",
    "사용자가 직접 붙인 `P`, `Q`",
    "Skill 호출 문자열",
    "실제 확인된 완전한 URL",
    "...lsiSeq=",
    "NOT_EXECUTED",
    "explicit-only",
}
REQUIRED_COUNTEREVIDENCE_EVAL_MARKERS = {
    "E39. Counterevidence — 별지서식 충돌형",
    "E40. 규정 부재 논증 Counterexample",
}
REQUIRED_V022_EVAL_MARKERS = {
    "E41. Referenced annex/form resolution BLOCK",
    "E42. Post-research final rendering hard gate",
    "첫 비공백 줄",
    "별지 제3호서식",
    "별지 제5호서식",
    "9/9 PASS",
    "42/42 PASS",
}
REQUIRED_COUNTEREVIDENCE_EXPECTED_MARKERS = {
    "Source Completeness",
    "Counterevidence",
    "명시적 제한 없음",
    "별지서식",
    "위임 또는 법적 기능",
    "존재하지 않는 반대근거",
    "E39",
    "E40",
}
REQUIRED_AGENTS_MARKERS = {
    "Legal Issue Mapping → Legal Interpretation → Logic Validation → Answer Rendering",
    "explicit-only Skill",
    "allow_implicit_invocation",
    "정보 부족 처리",
    "Output Hygiene 및 URL provenance",
    "최종 Rendering Gate",
    "# 2. 해석대상 법령조문 및 관련 법령",
}
LEGACY_DEFAULT_HEADINGS = {
    "\n# 1. 요청취지\n",
    "\n# 2. 질의 배경 및 사실관계\n",
    "\n# 3. 관련 법령 및 조문\n",
    "\n# 4. 해석상 쟁점\n",
    "\n# 5. 법률검토\n",
    "\n# 6. 첨부자료\n",
}

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?im)\b(?:GITHUB_TOKEN|GH_TOKEN|GITHUB_PAT|API_KEY|API_TOKEN|ACCESS_TOKEN|AUTH_TOKEN|BEARER_TOKEN|PRIVATE_KEY)\s*[:=]\s*[\"']?([^\"'\s,#]+)"
)
BEARER_ASSIGNMENT_RE = re.compile(
    r"(?im)\bAuthorization\s*:\s*Bearer\s+([A-Za-z0-9._~+/=-]{16,})"
)
PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "dummy",
    "example",
    "placeholder",
    "your-token",
    "your_api_key",
    "your_api_token",
    "replace-me",
    "replace_with_local_secret",
    "xxx",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require_markers(text: str, markers: set[str], scope: str) -> None:
    missing = sorted(marker for marker in markers if marker not in text)
    if missing:
        fail(f"{scope} markers missing: {missing}")


def reject_legacy_default_headings(text: str, scope: str) -> None:
    found = sorted(marker.strip() for marker in LEGACY_DEFAULT_HEADINGS if marker in text)
    if found:
        fail(f"{scope} legacy default headings remain: {found}")
    if "기본 1~6" in text or "1~6 법률검토형" in text:
        fail(f"{scope} legacy 1~6 default contract remains")


def read_tracked_files() -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = [Path(raw) for raw in result.stdout.decode("utf-8").split("\0") if raw]
    files: list[tuple[str, str]] = []
    for path in paths:
        absolute = ROOT / path
        if absolute.is_file():
            files.append((path.as_posix(), absolute.read_text(encoding="utf-8", errors="ignore")))
    return files


def is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("\"'").strip().lower()
    return (
        normalized in PLACEHOLDER_VALUES
        or normalized.startswith("your_")
        or normalized.startswith("your-")
        or normalized.startswith("replace_")
        or normalized.startswith("replace-")
        or normalized.startswith("발급받은")
        or normalized.startswith("<")
    )


def validate_tracked_secrets() -> None:
    tracked_files = read_tracked_files()
    for relative, file_text in tracked_files:
        if relative == "scripts/validate_repo.py":
            continue
        filename = Path(relative).name
        if filename == ".env" or (filename.startswith(".env.") and filename != ".env.example"):
            fail(f"tracked secret environment file found: {relative}")

        for line_number, line in enumerate(file_text.splitlines(), start=1):
            law_oc = re.search(r"(?i)(?:^|\s)(?:export\s+)?LAW_OC\s*=\s*(\S*)", line)
            if law_oc and not is_placeholder(law_oc.group(1)):
                fail(f"non-empty LAW_OC assignment found in {relative}:{line_number}")

            for match in SECRET_ASSIGNMENT_RE.finditer(line):
                if not is_placeholder(match.group(1)):
                    fail(f"secret-like assignment found in {relative}:{line_number}")

            bearer = BEARER_ASSIGNMENT_RE.search(line)
            if bearer and not is_placeholder(bearer.group(1)):
                fail(f"bearer token assignment found in {relative}:{line_number}")


def main() -> int:
    if not SKILL.is_file():
        fail("SKILL.md missing")

    skill_text = SKILL.read_text(encoding="utf-8")
    if not skill_text.startswith("---\n"):
        fail("SKILL.md YAML frontmatter missing")
    if "name: law-interpretation-request" not in skill_text:
        fail("skill name mismatch")
    if "4~8 항목을 생성하지 않는다" not in skill_text:
        fail("1~3 only output rule missing")
    if "최종 Markdown 본문은 다음 1~8 구조" in skill_text:
        fail("legacy 1~8 default output rule remains in SKILL.md")
    if "6. 질의사항" in skill_text:
        fail("legacy 질의사항 section remains in SKILL.md")
    reject_legacy_default_headings(skill_text, "SKILL.md")

    for tool in sorted(REQUIRED_MCP_TOOLS):
        if f"`{tool}`" not in skill_text:
            fail(f"MCP tool reference missing: {tool}")

    require_markers(skill_text, REQUIRED_LOGIC_SKILL_MARKERS, "skill logic")
    require_markers(skill_text, REQUIRED_ISSUE_MAPPING_SKILL_MARKERS, "skill issue mapping")
    require_markers(skill_text, REQUIRED_COUNTEREVIDENCE_SKILL_MARKERS, "skill counterevidence")
    require_markers(skill_text, REQUIRED_V022_SKILL_MARKERS, "skill v0.2.2 hard gates")
    require_markers(skill_text, REQUIRED_OUTPUT_SKILL_MARKERS, "skill output")

    if not AGENT_CONFIG.is_file():
        fail("skills/law-interpretation-request/agents/openai.yaml missing")
    agent_config_text = AGENT_CONFIG.read_text(encoding="utf-8")
    require_markers(agent_config_text, REQUIRED_AGENT_CONFIG_MARKERS, "skill invocation metadata")
    if "allow_implicit_invocation: true" in agent_config_text:
        fail("law-interpretation-request must remain explicit-only")

    ref_dir = SKILL.parent / "references"
    actual = {p.name for p in ref_dir.glob("*.md")}
    missing = REQUIRED_REFERENCES - actual
    if missing:
        fail(f"reference files missing: {sorted(missing)}")

    if not ISSUE_MAPPING.is_file():
        fail("legal-issue-mapping.md missing")
    issue_mapping_text = ISSUE_MAPPING.read_text(encoding="utf-8")
    require_markers(issue_mapping_text, REQUIRED_ISSUE_MAPPING_MARKERS, "issue mapping reference")
    require_markers(
        issue_mapping_text,
        REQUIRED_COUNTEREVIDENCE_ISSUE_MAPPING_MARKERS,
        "issue mapping counterevidence",
    )

    if not ELIGIBILITY.is_file():
        fail("eligibility-checklist.md missing")
    eligibility_text = ELIGIBILITY.read_text(encoding="utf-8")
    require_markers(eligibility_text, REQUIRED_ELIGIBILITY_MARKERS, "eligibility reference")

    logic_path = ref_dir / "logic-validation.md"
    logic_text = logic_path.read_text(encoding="utf-8")
    require_markers(logic_text, REQUIRED_LOGIC_REFERENCE_MARKERS, "logic reference")
    require_markers(logic_text, REQUIRED_COUNTEREVIDENCE_LOGIC_MARKERS, "logic counterevidence")
    require_markers(logic_text, REQUIRED_REFERENCED_SOURCE_LOGIC_MARKERS, "logic referenced source resolution")

    request_text = REQUEST_FORMAT.read_text(encoding="utf-8")
    source_text = SOURCE_POLICY.read_text(encoding="utf-8")
    if "다음 1~8 구조" in request_text or "# 6. 질의사항" in request_text:
        fail("legacy default output sections remain in request-format.md")
    reject_legacy_default_headings(request_text, "request-format.md")
    require_markers(request_text, REQUIRED_REQUEST_FORMAT_MARKERS, "request format")
    require_markers(request_text, REQUIRED_RENDERING_HARD_GATE_MARKERS, "final rendering hard gate")
    require_markers(source_text, REQUIRED_SOURCE_LINK_MARKERS, "source link policy")
    require_markers(
        source_text,
        REQUIRED_COUNTEREVIDENCE_SOURCE_POLICY_MARKERS,
        "source completeness policy",
    )
    require_markers(
        source_text,
        REQUIRED_REFERENCED_SOURCE_POLICY_MARKERS,
        "referenced source resolution policy",
    )

    if not AGENTS.is_file():
        fail("AGENTS.md missing")
    agents_text = AGENTS.read_text(encoding="utf-8")
    require_markers(agents_text, REQUIRED_AGENTS_MARKERS, "repository instructions")

    if not EVAL_SCENARIOS.is_file() or not EVAL_EXPECTED.is_file() or not EVAL_V022.is_file():
        fail("evaluation files missing")
    scenario_text = EVAL_SCENARIOS.read_text(encoding="utf-8")
    expected_text = EVAL_EXPECTED.read_text(encoding="utf-8")
    v022_eval_text = EVAL_V022.read_text(encoding="utf-8")
    require_markers(scenario_text, REQUIRED_LOGIC_EVAL_MARKERS, "logic eval scenarios")
    require_markers(scenario_text, REQUIRED_LOGIC_REGRESSION_MARKERS, "logic regression scenarios")
    require_markers(scenario_text, REQUIRED_OUTPUT_EVAL_MARKERS, "output eval scenarios")
    require_markers(scenario_text, REQUIRED_OUTPUT_HYGIENE_EVAL_MARKERS, "output hygiene eval scenarios")
    require_markers(scenario_text, REQUIRED_COUNTEREVIDENCE_EVAL_MARKERS, "counterevidence eval scenarios")
    require_markers(v022_eval_text, REQUIRED_V022_EVAL_MARKERS, "v0.2.2 regression scenarios")
    require_markers(
        expected_text,
        {
            "실행 소스 고정 조건",
            "allow_implicit_invocation",
            "추상 법적 논리 시나리오",
            "기본 4단 항목은 모두 Markdown H1",
            "번호 목록이나 일반 텍스트는 H1로 인정하지 않는다",
            "`# 1. 질의요지`",
            "`# 2. 검토결론`",
            "`# 3. 검토이유`",
            "`# 4. 관련 법령 및 자료`",
            "검토결론은 상세 검토이유보다 먼저",
            "서로 독립적으로 판단 가능한 복수의 법적 쟁점",
            "자료 부족 조건",
            "그 응답에서는 초안 작성을 중단",
            "법적 쟁점 매핑 필수 조건",
            "동일 사항의 중복 규율",
            "규율 공백",
            "문제 발생 지점",
            "Answer-first 및 Narrative Coherence 조건",
            "Output Hygiene 조건",
            "법제처 1~3 구조는 사용자가",
            "모든 사용자용 최종 출력은 Markdown",
            "Markdown 인라인 하이퍼링크",
            "[공식 링크 확인 필요]",
            "URL provenance 및 공식자료 조건",
            "끝이 `=`인 미완성 URL",
            "Plugin 명시 호출 조건",
            "explicit-only",
            "자동 선택되는 것을 release gate로 요구하지 않는다",
            "Plugin 행동 PASS로 인정하지 않는다",
            "내부 논리검증 필수 조건",
            "추상 논리 시나리오의 A/B/P/Q",
            "선택지 완전성 자체를 독립 전제",
            "동일한 법률용어의 의미가 양 설 사이에서 달라지면 BLOCK",
            "내부 검증 비노출 조건",
            "논리감사, 형식논리 설명, 검증표 공개",
            "E19는 **정보부족 질문 테스트가 아니라 비노출 테스트**",
            "형식적 타당성 50",
            "전제 명확성 20",
            "근거-결론 연결성 20",
            "개념 일관성·반례 대응력 10",
            "네 항목 점수를 각각 기록한다",
            "타당 85~100",
            "부분 타당 65~84",
            "취약 40~64",
            "부당 0~39",
            "원래 문장 번호",
            "수정 전 문제",
            "수정 원칙",
            "수정 예시",
            "추가가 필요한 전제",
            "내부 검증 흔적은 최종 답변에 노출하지 않는다",
            "Golden Case 조건",
            "E36",
            "E37",
            "E38",
        },
        "expected behavior",
    )
    require_markers(expected_text, REQUIRED_COUNTEREVIDENCE_EXPECTED_MARKERS, "counterevidence expected behavior")

    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    if not PACKAGE_LOCK.is_file():
        fail("package-lock.json missing")

    package_lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    package_version = package.get("version")
    lock_version = package_lock.get("version")
    lock_root_version = (package_lock.get("packages") or {}).get("", {}).get("version")

    if not package_version:
        fail("package.json version missing")
    if lock_version != package_version:
        fail("package-lock.json version must match package.json")
    if lock_root_version != package_version:
        fail('package-lock.json packages[""] version must match package.json')

    version = package.get("dependencies", {}).get("korean-law-mcp")
    if not version:
        fail("korean-law-mcp dependency missing")
    if version.startswith(("^", "~", ">", "<", "*")):
        fail("korean-law-mcp must use an exact pinned version")

    if not PLUGIN_MANIFEST.is_file():
        fail(".codex-plugin/plugin.json missing")
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    if plugin.get("name") != "jdipt":
        fail("plugin name must be jdipt")
    if plugin.get("version") != package.get("version"):
        fail("plugin version must match package.json")
    if plugin.get("skills") != "./skills/":
        fail("plugin skills path must be ./skills/")
    interface = plugin.get("interface") or {}
    if interface.get("displayName") != "JDIPT":
        fail("plugin displayName must be JDIPT")
    if not interface.get("shortDescription"):
        fail("plugin shortDescription missing")
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not prompts:
        fail("plugin defaultPrompt must contain at least one prompt")
    if AGENT_SKILL_DUPLICATE.exists():
        fail("duplicate law-interpretation-request skill found under .agents/skills")
    if not PLUGIN_DOC.is_file():
        fail("docs/plugin-packaging.md missing")

    if not MARKETPLACE.is_file():
        fail(".agents/plugins/marketplace.json missing")
    try:
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Marketplace manifest JSON invalid: {exc}")
    if marketplace.get("name") != "sage1993":
        fail("Marketplace name must be sage1993")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        fail("Marketplace plugins must be an array")
    jdipt_entries = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == "jdipt"]
    if len(jdipt_entries) != 1:
        fail(f"Marketplace must contain exactly one jdipt plugin entry, found {len(jdipt_entries)}")
    jdipt_entry = jdipt_entries[0]
    source = jdipt_entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        fail("Marketplace jdipt source.source must be local")
    if source.get("path") != ".":
        fail("Marketplace jdipt source.path must be .")
    policy = jdipt_entry.get("policy")
    if not isinstance(policy, dict) or policy.get("installation") != "AVAILABLE":
        fail("Marketplace jdipt policy.installation must be AVAILABLE")
    if policy.get("authentication") != "ON_INSTALL":
        fail("Marketplace jdipt policy.authentication must be ON_INSTALL")
    if jdipt_entry.get("category") != "Productivity":
        fail("Marketplace jdipt category must be Productivity")

    codex_text = CODEX.read_text(encoding="utf-8")
    if f"korean-law-mcp@{version}" not in codex_text:
        fail("Codex config MCP version does not match package.json")
    if 'env_vars = ["LAW_OC"]' not in codex_text:
        fail("Codex example must forward LAW_OC with env_vars")
    if "REPLACE_WITH_LOCAL_SECRET" in codex_text:
        fail("Codex example must not embed a LAW_OC placeholder value")

    tracked_files = read_tracked_files()
    tracked_text = "\n".join(file_text for _, file_text in tracked_files)
    if "LAW_OC=REPLACE_WITH_" + "LOCAL_SECRET" in tracked_text:
        fail("secret-like value found in tracked text")
    validate_tracked_secrets()

    print("PASS")
    print(f"skill={SKILL.relative_to(ROOT)}")
    print(f"plugin_manifest={PLUGIN_MANIFEST.relative_to(ROOT)}")
    print(f"marketplace_manifest={MARKETPLACE.relative_to(ROOT)}")
    print(f"korean-law-mcp={version}")
    print(f"required_tools={len(REQUIRED_MCP_TOOLS)}")
    print(f"references={len(REQUIRED_REFERENCES)}")
    print(f"issue_mapping_markers={len(REQUIRED_ISSUE_MAPPING_MARKERS)}")
    print(f"logic_markers={len(REQUIRED_LOGIC_REFERENCE_MARKERS)}")
    print(f"logic_eval_scenarios={len(REQUIRED_LOGIC_EVAL_MARKERS)}")
    print(f"output_eval_scenarios={len(REQUIRED_OUTPUT_EVAL_MARKERS)}")
    print(f"output_hygiene_eval_markers={len(REQUIRED_OUTPUT_HYGIENE_EVAL_MARKERS)}")
    print(f"v022_eval_markers={len(REQUIRED_V022_EVAL_MARKERS)}")
    print(f"skill_invocation_markers={len(REQUIRED_AGENT_CONFIG_MARKERS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
