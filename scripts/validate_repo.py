from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
PACKAGE = ROOT / "package.json"
CODEX = ROOT / "config" / "codex.example.toml"
REQUIRED_REFERENCES = {
    "baseline-document-policy.md",
    "case-patterns.md",
    "eligibility-checklist.md",
    "interpretation-principles.md",
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


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


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

    ref_dir = SKILL.parent / "references"
    actual = {p.name for p in ref_dir.glob("*.md")}
    missing = REQUIRED_REFERENCES - actual
    if missing:
        fail(f"reference files missing: {sorted(missing)}")

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
        if p.is_file() and p.suffix.lower() in {".md", ".json", ".toml", ".yml", ".yaml", ".example", ".gitignore"}
    )
    if "LAW_OC=REPLACE_WITH_LOCAL_SECRET" in tracked_text:
        fail("secret-like value found in tracked text")

    print("PASS")
    print(f"skill={SKILL.relative_to(ROOT)}")
    print(f"korean-law-mcp={version}")
    print(f"required_tools={len(REQUIRED_MCP_TOOLS)}")
    print(f"references={len(REQUIRED_REFERENCES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
