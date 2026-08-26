from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
REQUEST_FORMAT = ROOT / "skills" / "law-interpretation-request" / "references" / "request-format.md"
ELIGIBILITY = ROOT / "skills" / "law-interpretation-request" / "references" / "eligibility-checklist.md"
INTERPRETATION = ROOT / "skills" / "law-interpretation-request" / "references" / "interpretation-principles.md"
SOURCE_POLICY = ROOT / "skills" / "law-interpretation-request" / "references" / "source-policy.md"
LOGIC_VALIDATION = ROOT / "skills" / "law-interpretation-request" / "references" / "logic-validation.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_explicit_skill_invocation_reads_skill_before_mode_decision():
    agents = _read(AGENTS)
    assert "$law-interpretation-request" in agents
    assert "응답 모드나 정보 부족 여부를 판단하기 전에" in agents
    assert "SKILL.md를 먼저 읽는다" in agents


def test_general_review_information_shortage_does_not_force_questions_only():
    agents = _read(AGENTS)
    assert "일반 법률검토형에서 법적 쟁점과 검토대상 행위·상태·관계가 식별되면" in agents
    assert "질문-only로 전환하지 않는다" in agents
    assert "법령명·조문·정확한 날짜·경과조치가 미확인" in agents
    assert "조건부 결론" in agents
    assert "법령명·조문·핵심 사실 등 실체결론 또는 초안 작성에 필수적인 정보가 부족하면 필요한 질문 3~7개만" not in agents


def test_explicit_moleg_suitability_precedes_information_shortage_questions():
    agents = _read(AGENTS)
    assert "명시적 법제처 모드에서는 제출 적합성 보정이 정보 부족 질문보다 먼저" in agents
    assert "이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다." in agents


def test_e02_question_only_overrides_moleg_three_h1_draft():
    marker = "형식상 부적합 + 정보 부족이면 질문-only가 법제처 3-H1보다 우선"
    stop_marker = "부적합 고지 후 필요한 질문 3~7개만 출력하고 즉시 중단"
    no_h1_marker = "이 응답에는 H1 제목, 법제처 1~3 초안, `※ 제출 전 확인`, 출처 링크를 출력하지 않는다"
    for path in (AGENTS, SKILL, REQUEST_FORMAT, ELIGIBILITY):
        text = _read(path)
        assert marker in text
        assert stop_marker in text
        assert no_h1_marker in text


def test_e44_unknown_temporal_branching_is_neutral_not_probabilistic():
    marker = "조건부 결론은 확률적 우세 판단이 아니다"
    forbidden_marker = "`가능성이 크`, `가능성이 높`, `대체로`, `통상`, `원칙적으로 신법`, `적용될 것으로 보`"
    branch_marker = "어느 분기가 성립하는지는 현재 판단할 수 없다"
    for path in (AGENTS, SKILL, INTERPRETATION):
        text = _read(path)
        assert marker in text
        assert forbidden_marker in text
        assert branch_marker in text


def test_unresolved_abstract_fixture_must_remain_neutral():
    agents = _read(AGENTS)
    marker = "미확인 정의·참조자료가 결론을 좌우하면 방향성 가설을 제시하지 않는다"
    assert marker in agents
    assert "가능`, `가능성이`, `여지`, `대체로`, `우세`" in agents


def test_e39_unresolved_source_form_cannot_support_or_oppose_approval():
    marker = "미확인 `신설 / 증설` 의미는 승인 방향을 지지하거나 반박하는 근거가 아니다"
    neutral_marker = "현재 전제만으로 승인 가능 여부를 판단할 수 없다"
    forbidden_marker = "`승인 가능성을 뒷받침`, `승인 가능성이 높`, `승인받기 어렵`, `승인 가능성은 열려`"
    for path in (AGENTS, SKILL, LOGIC_VALIDATION):
        text = _read(path)
        assert marker in text
        assert neutral_marker in text
        assert forbidden_marker in text


def test_verified_unicode_url_is_not_manually_reencoded():
    agents = _read(AGENTS)
    assert "관찰한 URL 문자열을 그대로 사용" in agents
    assert "직접 percent-encoding하거나 경로를 재조합하지 않는다" in agents
    assert "혼합 인코딩 URL" in agents


def test_e37_named_annex_link_class_is_never_user_facing():
    marker = "`lsBylInfoPLinkR.do` + `lsNm`"
    for path in (AGENTS, SKILL, SOURCE_POLICY):
        text = _read(path)
        assert marker in text
        assert "사용자 출력에 사용하지 않는다" in text
