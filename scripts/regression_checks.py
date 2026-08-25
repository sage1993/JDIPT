"""Deterministic checks used by the JDIPT regression runner."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlparse

DEFAULT_H1 = [
    "# 1. 질의요지",
    "# 2. 검토결론",
    "# 3. 검토이유",
    "# 4. 관련 법령 및 자료",
]
MOLEG_H1 = [
    "# 1. 질의요지",
    "# 2. 해석대상 법령조문 및 관련 법령",
    "# 3. 대립되는 의견 및 이유",
]
MOLEG_CASES = {1, 7, 22}
SPECIAL_FORMAT_CASES = {2, 3}
QUESTION_ONLY_CASES = {9}
HYGIENE_FORBIDDEN = [
    "$law-interpretation-request",
    "@jdipt",
    "Skill activated",
    "Plugin activated",
    "references/logic-validation.md",
    "references/legal-issue-mapping.md",
    "references/source-policy.md",
    "references/request-format.md",
]
CRITICAL_IDENTIFIER_KEYS = {
    "lsiseq",
    "lsjolnkseq",
    "expcseq",
    "caseSeq".lower(),
    "cs_seq",
    "lsid",
    "id",
    "seq",
    "flseq",
}
PLACEHOLDER_MARKERS = (
    "<placeholder>", "<id>", "<seq>", "your-token", "your_api_key",
    "replace-me", "example.com", "example.org",
)
URL_RE = re.compile(r"https?://[^\s<>()\]]+", re.IGNORECASE)
INVALID_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
SKILL_READ_FAILURE = "JDIPT SKILL.md could not be read during this case"
EXPLICIT_SKILL_UNAVAILABLE = "JDIPT explicit Skill invocation was unavailable during this case"


def first_nonblank_line(answer: str) -> str | None:
    for line in answer.splitlines():
        if line.strip():
            return line.strip()
    return None


def exact_h1_lines(answer: str) -> list[str]:
    return [line.rstrip() for line in answer.splitlines() if re.match(r"^# [^\r\n]+$", line.rstrip())]


def _mode_for_case(case_number: int) -> str:
    if case_number in MOLEG_CASES:
        return "moleg"
    if case_number in SPECIAL_FORMAT_CASES:
        return "skip"
    if case_number in QUESTION_ONLY_CASES:
        return "question_only"
    return "default"


def check_h1(answer: str, case_number: int, expected_mode: str | None = None) -> str:
    mode = expected_mode or _mode_for_case(case_number)
    headings = exact_h1_lines(answer)
    first = first_nonblank_line(answer)
    if mode in {"skip", "special", "special_format"}:
        return "SKIP_SPECIAL_FORMAT"
    if mode == "moleg":
        expected = MOLEG_H1
    elif mode in {"question_only", "questions_only"}:
        return "PASS" if not headings else f"FAIL E9 should stop after questions; H1 found={headings!r}"
    else:
        expected = DEFAULT_H1
    return "PASS" if first == expected[0] and headings == expected else (
        f"FAIL expected={expected!r} actual={headings!r} first={first!r}"
    )


def check_output_hygiene(answer: str) -> tuple[bool, list[str]]:
    found = [token for token in HYGIENE_FORBIDDEN if token in answer]
    return (not found, [f"forbidden output token: {token}" for token in found])


def check_urls(answer: str) -> tuple[bool, list[str]]:
    problems: list[str] = []
    for url in [match.rstrip(".,;:'\"") for match in URL_RE.findall(answer)]:
        if url.endswith("="):
            problems.append(f"incomplete URL ends with '=': {url}")
            continue
        if INVALID_PERCENT_RE.search(url):
            problems.append(f"invalid percent escape: {url}")
            continue
        lowered_url = url.lower()
        if any(marker in lowered_url for marker in PLACEHOLDER_MARKERS):
            problems.append(f"placeholder URL: {url}")
            continue
        try:
            parsed = urlparse(url)
            params = parse_qsl(parsed.query, keep_blank_values=True)
        except ValueError:
            problems.append(f"invalid URL: {url}")
            continue
        if (
            parsed.netloc.lower().endswith("law.go.kr")
            and parsed.path.lower().endswith("/fldownload.do")
            and any(key.lower() == "flnm" for key, _ in params)
        ):
            problems.append(f"unstable flDownload.do + flNm URL: {url}")
            continue
        for key, value in params:
            if value == "" and key.lower() in CRITICAL_IDENTIFIER_KEYS:
                problems.append(f"empty critical identifier '{key}': {url}")
    return (not problems, problems)


def detect_skill_read_status(log_text: str) -> str:
    """Return ``success``, ``failure``, or ``unknown`` for Skill loading."""
    lower = log_text.lower()
    failure_patterns = (
        r"environment_error\s*:\s*jdipt skill\.md could not be read",
        r"(?:failed|failure|could not|unable|denied|rejected|error)[^\n]{0,120}skill\.md",
        r"skill\.md[^\n]{0,120}(?:failed|failure|could not|unable|denied|rejected|error)",
    )
    if any(re.search(pattern, lower) for pattern in failure_patterns):
        return "failure"
    lines = lower.splitlines()
    for index, line in enumerate(lines):
        if "skill.md" in line:
            nearby = "\n".join(lines[index : index + 4])
            if re.search(r"(?:succeed|success|loaded|read ok)", nearby):
                return "success"
    success_patterns = (
        r"skill\.md[^\n]{0,160}(?:succeed|success|loaded|read ok)",
        r"(?:succeed|success|loaded|read ok)[^\n]{0,160}skill\.md",
    )
    if any(re.search(pattern, lower) for pattern in success_patterns):
        return "success"
    return "unknown"


def detect_environment_error(log_text: str) -> str | None:
    lower = log_text.lower()
    status = detect_skill_read_status(log_text)
    if status == "failure":
        return SKILL_READ_FAILURE
    if re.search(
        r"\$law-interpretation-request[^\n]{0,100}(?:사용할 수 없|이용할 수 없|접근할 수 없|unavailable|not available|cannot access|can't access)",
        lower,
    ):
        return EXPLICIT_SKILL_UNAVAILABLE
    if re.search(
        r"(?:사용할 수 없|이용할 수 없|접근할 수 없|unavailable|not available|cannot access|can't access)[^\n]{0,100}\$law-interpretation-request",
        lower,
    ):
        return EXPLICIT_SKILL_UNAVAILABLE
    if status == "success":
        return None
    if "hit your usage limit" in lower:
        return "Codex usage limit prevented regression execution"
    if any(marker in log_text for marker in (
        "apply deny-read ACLs", "Failed to create unified exec process", "helper_unknown_error"
    )):
        return "Codex Windows sandbox/ACL failure prevented reliable Skill file access"
    if "SKILL.md" in log_text and any(marker in log_text for marker in (
        "?ъ슜", "踰뺣", "洹쒖", "吏덈", "�"
    )):
        return "JDIPT UTF-8 Skill/reference content was mojibake"
    return None
