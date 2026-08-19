from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
PACKAGE = ROOT / "package.json"
CODEX = ROOT / "config" / "codex.example.toml"
EVAL_SCENARIOS = SKILL.parent / "evals" / "scenarios.md"
EVAL_EXPECTED = SKILL.parent / "evals" / "expected-behavior.md"
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
    "BLOCK",
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

    for tool in sorted(REQUIRED_MCP_TOOLS):
        if f"`{tool}`" not in skill_text:
            fail(f"MCP tool reference missing: {tool}")

    require_markers(skill_text, REQUIRED_LOGIC_SKILL_MARKERS, "skill logic")

    ref_dir = SKILL.parent / "references"
    actual = {p.name for p in ref_dir.glob("*.md")}
    missing = REQUIRED_REFERENCES - actual
    if missing:
        fail(f"reference files missing: {sorted(missing)}")

    logic_path = ref_dir / "logic-validation.md"
    logic_text = logic_path.read_text(encoding="utf-8")
    require_markers(logic_text, REQUIRED_LOGIC_REFERENCE_MARKERS, "logic reference")

    if not EVAL_SCENARIOS.is_file() or not EVAL_EXPECTED.is_file():
        fail("evaluation files missing")
    scenario_text = EVAL_SCENARIOS.read_text(encoding="utf-8")
    expected_text = EVAL_EXPECTED.read_text(encoding="utf-8")
    require_markers(scenario_text, REQUIRED_LOGIC_EVAL_MARKERS, "logic eval scenarios")
    require_markers(
        expected_text,
        {
            "내부 논리검증 필수 조건",
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
            "사용자가 요청하지 않는 한 최종 결과에 노출하지 않는다",
        },
        "logic expected behavior",
    )

    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    version = package.get("dependencies", {}).get("korean-law-mcp")
    if not version:
        fail("korean-law-mcp dependency missing")
    if version.startswith(("^", "~", ">", "<", "*")):
        fail("korean-law-mcp must use an exact pinned version")

    codex_text = CODEX.read_text(encoding="utf-8")
    if f"korean-law-mcp@{version}" not in codex_text:
        fail("Codex config MCP version does not match package.json")
    if "REPLACE_WITH_LOCAL_SECRET" not in codex_text:
        fail("Codex example must not contain a real LAW_OC secret")

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
    print(f"korean-law-mcp={version}")
    print(f"required_tools={len(REQUIRED_MCP_TOOLS)}")
    print(f"references={len(REQUIRED_REFERENCES)}")
    print(f"logic_markers={len(REQUIRED_LOGIC_REFERENCE_MARKERS)}")
    print(f"logic_eval_scenarios={len(REQUIRED_LOGIC_EVAL_MARKERS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
