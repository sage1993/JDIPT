from __future__ import annotations

import importlib
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression"


def load_checks():
    try:
        return importlib.import_module("scripts.regression_checks")
    except ModuleNotFoundError as exc:  # pragma: no cover - red characterization on missing module
        pytest.fail(f"scripts.regression_checks is not available yet: {exc}", pytrace=False)


@pytest.fixture(scope="module")
def checks():
    return load_checks()


def read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def line_containing(text: str, needle: str) -> str:
    for line in text.splitlines():
        if needle in line:
            return line
    raise AssertionError(f"missing line containing {needle!r}")


def test_detect_environment_error_ignores_router_error_after_successful_skill_read(checks):
    log_text = read_fixture("e25_skill_read_success_then_router_error.log")

    assert checks.detect_environment_error(log_text) is None


def test_detect_environment_error_reports_failed_skill_read(checks):
    log_text = read_fixture("e25_skill_read_failure.log")

    assert checks.detect_environment_error(log_text) == "JDIPT SKILL.md could not be read during this case"




def test_detect_environment_error_reports_codex_usage_limit(checks):
    log_text = "ERROR: You've hit your usage limit. Upgrade to Pro or try again later."

    assert checks.detect_environment_error(log_text) == "Codex usage limit prevented regression execution"

def test_check_urls_rejects_invalid_percent_escape(checks):
    answer = read_fixture("e37_invalid_percent.md")

    ok, problems = checks.check_urls(answer)

    assert ok is False
    assert problems
    assert any("percent" in problem.lower() or "%" in problem for problem in problems)


def test_check_urls_rejects_flNm_download_even_when_percent_encoded(checks):
    answer = read_fixture("e37_flNm_download.md")

    ok, problems = checks.check_urls(answer)

    assert ok is False
    assert problems
    assert any("flNm" in problem or "flDownload" in problem or "download" in problem.lower() for problem in problems)


def test_check_urls_allows_stable_law_page_and_blank_search_state(checks):
    answer = read_fixture("url_valid_law_page.md")
    stable_line = line_containing(answer, "lsInfoP.do?lsiSeq=287405")
    blank_search_state_line = line_containing(answer, "keyField=&keyWord=")

    stable_ok, stable_problems = checks.check_urls(stable_line)
    blank_ok, blank_problems = checks.check_urls(blank_search_state_line)

    assert stable_ok is True
    assert stable_problems == []
    assert blank_ok is True
    assert blank_problems == []


def test_check_urls_rejects_critical_blank_identifier_query(checks):
    answer = line_containing(read_fixture("url_valid_law_page.md"), "id=&seq=123")

    ok, problems = checks.check_urls(answer)

    assert ok is False
    assert problems
    assert any("empty" in problem.lower() or "blank" in problem.lower() or "incomplete" in problem.lower() for problem in problems)


def test_detect_skill_read_status_distinguishes_success_and_failure(checks):
    assert checks.detect_skill_read_status(
        read_fixture("e25_skill_read_success_then_router_error.log")
    ) == "success"
    assert checks.detect_skill_read_status(
        read_fixture("e25_skill_read_failure.log")
    ) == "failure"


def test_check_output_hygiene_reports_forbidden_metadata(checks):
    assert checks.check_output_hygiene("clean legal answer") == (True, [])
    ok, problems = checks.check_output_hygiene("@jdipt internal marker")
    assert ok is False
    assert problems


def test_check_h1_preserves_default_moleg_and_special_modes(checks):
    default = "\n".join(checks.DEFAULT_H1)
    moleg = "\n".join(checks.MOLEG_H1)
    assert checks.check_h1(default, 4) == "PASS"
    assert checks.check_h1(moleg, 1) == "PASS"
    assert checks.check_h1("draft", 2) == "SKIP_SPECIAL_FORMAT"
    assert checks.check_h1("questions only", 9) == "PASS"
