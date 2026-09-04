from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
REQUEST_FORMAT = SKILL.parent / "references" / "request-format.md"
ELIGIBILITY = SKILL.parent / "references" / "eligibility-checklist.md"
INTERPRETATION = SKILL.parent / "references" / "interpretation-principles.md"
SOURCE_POLICY = SKILL.parent / "references" / "source-policy.md"
LOGIC_VALIDATION = SKILL.parent / "references" / "logic-validation.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_explicit_skill_invocation_reads_skill_before_mode_decision():
    agents = _read(AGENTS)
    assert "$law-interpretation-request" in agents
    assert "응답 모드나 정보 부족 여부를 판단하기 전에" in agents
    assert "SKILL.md를 먼저 읽는다" in agents


def test_agents_is_not_a_second_runtime_contract():
    agents = _read(AGENTS)
    assert "CURRENT_CONFIRMED" not in agents
    assert "mandatory_render_clause" not in agents
    assert "Range/effect coupling hard stop" not in agents
    assert len(agents.splitlines()) <= 6


def test_e02_policy_is_owned_by_skill_and_references():
    marker = "형식상 부적합 + 정보 부족이면 질문-only가 법제처 3-H1보다 우선"
    for path in (SKILL, REQUEST_FORMAT, ELIGIBILITY):
        assert marker in _read(path)


def test_e44_temporal_neutrality_is_owned_by_skill_and_interpretation():
    marker = "조건부 결론은 확률적 우세 판단이 아니다"
    forbidden_marker = "`가능성이 크`, `가능성이 높`, `대체로`, `통상`, `원칙적으로 신법`, `적용될 것으로 보`"
    branch_marker = "어느 분기가 성립하는지는 현재 판단할 수 없다"
    for path in (SKILL, INTERPRETATION):
        text = _read(path)
        assert marker in text
        assert forbidden_marker in text
        assert branch_marker in text


def test_e39_source_form_neutrality_is_owned_by_skill_and_logic():
    marker = "미확인 `신설 / 증설` 의미는 승인 방향을 지지하거나 반박하는 근거가 아니다"
    neutral_marker = "현재 전제만으로 승인 가능 여부를 판단할 수 없다"
    forbidden_marker = "`승인 가능성을 뒷받침`, `승인 가능성이 높`, `승인받기 어렵`, `승인 가능성은 열려`"
    for path in (SKILL, LOGIC_VALIDATION):
        text = _read(path)
        assert marker in text
        assert neutral_marker in text
        assert forbidden_marker in text


def test_e37_url_provenance_is_owned_by_skill_and_source_policy():
    marker = "`lsBylInfoPLinkR.do` + `lsNm`"
    for path in (SKILL, SOURCE_POLICY):
        text = _read(path)
        assert marker in text
        assert "사용자 출력에 사용하지 않는다" in text