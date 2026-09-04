import yaml
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "law-interpretation-request" / "SKILL.md"
REQUEST_FORMAT = SKILL.parent / "references" / "request-format.md"


def test_e02_detailed_suitability_policy_is_not_duplicated_in_default_prompt():
    data = yaml.safe_load((SKILL.parent / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    prompt = data["interface"]["default_prompt"]

    assert "직접 근거" in prompt
    assert "예외·특례" in prompt
    assert "material proposition" in prompt
    assert "4-H1" in prompt
    assert "명시적 법제처 요청" in prompt
    assert "질문 3~7개" not in prompt


def test_e02_skill_and_request_format_own_objective_reframing_before_questions():
    marker = "객관적 법령 의미·적용범위·요건·근거조항 문제로 재구성할 점을 설명"
    assert marker in SKILL.read_text(encoding="utf-8")
    assert "객관적 법령해석형으로 보정하기 위해 필요한 질문 3~7개만" in REQUEST_FORMAT.read_text(encoding="utf-8")


def test_e18_default_prompt_keeps_only_the_high_level_mode_contract():
    data = yaml.safe_load((SKILL.parent / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    prompt = data["interface"]["default_prompt"]

    assert "일반 법률검토" in prompt
    assert "명시적 법제처 요청" in prompt
    assert "갑설·을설" not in prompt