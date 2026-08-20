from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
PACKAGE = ROOT / "package.json"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
PLUGIN_DOC = ROOT / "docs" / "plugin-packaging.md"
CODEX = ROOT / "config" / "codex.example.toml"
REQUEST_FORMAT = SKILL.parent / "references" / "request-format.md"
SOURCE_POLICY = SKILL.parent / "references" / "source-policy.md"
EVAL_SCENARIOS = SKILL.parent / "evals" / "scenarios.md"
EVAL_EXPECTED = SKILL.parent / "evals" / "expected-behavior.md"
AGENT_SKILL_DUPLICATE = ROOT / ".agents" / "skills" / "law-interpretation-request"
REQUIRED_REFERENCES = {
    "baseline-document-policy.md",
    "case-patterns.md",
    "eligibility-checklist.md",
    "interpretation-principles.md",
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
REQUIRED_OUTPUT_SKILL_MARKERS = {
    "모든 사용자용 최종 출력은 Markdown",
    "기본 출력 모드 — 별도 형식 지시가 없을 때",
    "최상위 Markdown 제목은 아래 문자열을 그대로 사용한다",
    "# 1. 요청취지",
    "# 2. 질의 배경 및 사실관계",
    "# 3. 관련 법령 및 조문",
    "# 4. 해석상 쟁점",
    "# 5. 법률검토",
    "# 6. 첨부자료",
    "1번 제목 이전에 별도 서론",
    "결론·검토의견·적용상 유의사항",
    "사용자의 질문",
    "유추",
    "특수 출력 모드 — 사용자가 명시적으로 요청한 경우에만",
    "`법제처 법령해석요청서`",
    "클릭 가능한 Markdown 인라인 하이퍼링크",
}
REQUIRED_REQUEST_FORMAT_MARKERS = {
    "사용자가 별도 형식을 명시하지 않으면",
    "문자열과 순서를 그대로 유지",
    "최상위 1~6 항목은 모두 Markdown H1",
    "1번 항목 이전에는 별도 서론",
    "# 1. 요청취지",
    "# 2. 질의 배경 및 사실관계",
    "# 3. 관련 법령 및 조문",
    "# 4. 해석상 쟁점",
    "# 5. 법률검토",
    "# 6. 첨부자료",
    "결론·검토의견·적용상 유의사항",
    "실제 검토 목적",
    "사용자가 명시적으로 법제처 법령해석요청서",
    "# 1. 질의요지",
    "# 2. 해석대상 법령조문 및 관련 법령",
    "## 가. 해석대상 법령조문",
    "## 나. 관련 법령",
    "# 3. 대립되는 의견 및 이유",
    "## 가. 갑설",
    "## 나. 을설",
    "모든 사용자용 최종 출력은 Markdown",
}
REQUIRED_SOURCE_LINK_MARKERS = {
    "본문의 자료명 자체에 Markdown 인라인 하이퍼링크를 기본",
    "[표시 텍스트](실제로 확인한 공식 URL)",
    "원문 접근은 본문 인라인 링크를 우선",
    "URL 패턴을 추측하지 않는다",
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
    "특정 법률·조문·판례·법제처 해석례·사실관계를 임의로 대응시키거나 만들어내지 않는다",
    "가능한 해석 전부",
    "동일 조문의 동일 용어 `건축물`의 의미가 양 설에서 달라졌다는 점을 BLOCK으로 탐지",
    "추가 질문 없이 기본 1~6 Markdown 형식을 사용",
    "내부 기호·분류명은 기본 출력에 노출하지 않는다",
}
REQUIRED_OUTPUT_EVAL_MARKERS = {
    "E21. 기본 1~6 출력",
    "E22. 명시적 법제처 1~3 출력",
    "E23. Markdown 출력 강제",
    "E24. 공식자료 인라인 하이퍼링크",
    "E25. 요청취지 유추",
    "E26. Plugin 설치 후 자동 Skill 적용",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require_markers(text: str, markers: set[str], scope: str) -> None:
    missing = sorted(marker for marker in markers if marker not in text)
    if missing:
        fail(f"{scope} markers missing: {missing}")


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

    for tool in sorted(REQUIRED_MCP_TOOLS):
        if f"`{tool}`" not in skill_text:
            fail(f"MCP tool reference missing: {tool}")

    require_markers(skill_text, REQUIRED_LOGIC_SKILL_MARKERS, "skill logic")
    require_markers(skill_text, REQUIRED_OUTPUT_SKILL_MARKERS, "skill output")

    ref_dir = SKILL.parent / "references"
    actual = {p.name for p in ref_dir.glob("*.md")}
    missing = REQUIRED_REFERENCES - actual
    if missing:
        fail(f"reference files missing: {sorted(missing)}")

    logic_path = ref_dir / "logic-validation.md"
    logic_text = logic_path.read_text(encoding="utf-8")
    require_markers(logic_text, REQUIRED_LOGIC_REFERENCE_MARKERS, "logic reference")

    request_text = REQUEST_FORMAT.read_text(encoding="utf-8")
    source_text = SOURCE_POLICY.read_text(encoding="utf-8")
    if "다음 1~8 구조" in request_text or "# 6. 질의사항" in request_text:
        fail("legacy default output sections remain in request-format.md")
    require_markers(request_text, REQUIRED_REQUEST_FORMAT_MARKERS, "request format")
    require_markers(source_text, REQUIRED_SOURCE_LINK_MARKERS, "source link policy")

    if not EVAL_SCENARIOS.is_file() or not EVAL_EXPECTED.is_file():
        fail("evaluation files missing")
    scenario_text = EVAL_SCENARIOS.read_text(encoding="utf-8")
    expected_text = EVAL_EXPECTED.read_text(encoding="utf-8")
    require_markers(scenario_text, REQUIRED_LOGIC_EVAL_MARKERS, "logic eval scenarios")
    require_markers(scenario_text, REQUIRED_LOGIC_REGRESSION_MARKERS, "logic regression scenarios")
    require_markers(scenario_text, REQUIRED_OUTPUT_EVAL_MARKERS, "output eval scenarios")
    require_markers(
        expected_text,
        {
            "기본 1~6 항목은 모두 Markdown H1",
            "`1. 요청취지`",
            "실제 검토 목적",
            "별도 `제목` 또는 `질의사항` 항목을 생성하지 않는다",
            "법제처 1~3 구조는 사용자가",
            "모든 사용자용 최종 출력은 Markdown",
            "Markdown 인라인 하이퍼링크",
            "[공식 링크 확인 필요]",
            "Plugin 적용 조건",
            "Skill명이나 `@jdipt`를 명시하지 않은",
            "최상위 제목 문자열·순서·H1 수준 중 하나라도 기본 계약과 다르거나",
            "Plugin 행동 PASS로 인정하지 않는다",
            "내부 논리검증 필수 조건",
            "추상 논리 시나리오의 A/B/P/Q",
            "선택지 완전성 자체를 독립 전제",
            "동일한 법률용어의 의미가 양 설 사이에서 달라지면 BLOCK",
            "내부 검증 비노출 조건",
            "정보부족 질문 테스트가 아니라 비노출 테스트",
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
        },
        "expected behavior",
    )

    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
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

    codex_text = CODEX.read_text(encoding="utf-8")
    if f"korean-law-mcp@{version}" not in codex_text:
        fail("Codex config MCP version does not match package.json")
    if 'env_vars = ["LAW_OC"]' not in codex_text:
        fail("Codex example must forward LAW_OC with env_vars")
    if "REPLACE_WITH_LOCAL_SECRET" in codex_text:
        fail("Codex example must not embed a LAW_OC placeholder value")

    tracked_text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.suffix.lower()
        in {".md", ".json", ".toml", ".yml", ".yaml", ".example", ".gitignore"}
    )
    if "LAW_OC=REPLACE_WITH_LOCAL_SECRET" in tracked_text:
        fail("secret-like value found in tracked text")

    print("PASS")
    print(f"skill={SKILL.relative_to(ROOT)}")
    print(f"plugin_manifest={PLUGIN_MANIFEST.relative_to(ROOT)}")
    print(f"korean-law-mcp={version}")
    print(f"required_tools={len(REQUIRED_MCP_TOOLS)}")
    print(f"references={len(REQUIRED_REFERENCES)}")
    print(f"logic_markers={len(REQUIRED_LOGIC_REFERENCE_MARKERS)}")
    print(f"logic_eval_scenarios={len(REQUIRED_LOGIC_EVAL_MARKERS)}")
    print(f"output_eval_scenarios={len(REQUIRED_OUTPUT_EVAL_MARKERS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
