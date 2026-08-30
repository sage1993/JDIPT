import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_e02_suitability_contract_is_in_parsed_default_prompt():
    data = yaml.safe_load((ROOT / 'skills/law-interpretation-request/agents/openai.yaml').read_text(encoding='utf-8'))
    prompt = data['interface']['default_prompt']

    assert '법제처 법령해석 대상 부적합' in prompt
    assert '구체적 사실판단' in prompt
    assert '객관적 법령 의미·적용범위·요건·근거조항' in prompt
    assert 'H1 초안' in prompt
    assert '질문 3~7개' in prompt
    assert '질문 전 반드시' in prompt
    assert '설명 후 질문 3~7개' in prompt


def test_e02_skill_contract_explains_objective_reframing_before_questions():
    skill = (ROOT / 'skills/law-interpretation-request/SKILL.md').read_text(encoding='utf-8')

    assert '객관적 법령 의미·적용범위·요건·근거조항 문제로 재구성할 점을 설명' in skill


def test_e18_default_routing_does_not_infer_moleg_from_competing_views():
    data = yaml.safe_load((ROOT / 'skills/law-interpretation-request/agents/openai.yaml').read_text(encoding='utf-8'))
    prompt = data['interface']['default_prompt']

    assert '갑설·을설만으로 법제처 1~3 금지' in prompt
    assert '동일 용어 충돌이면 공통 정의·기준 확인 전 갑설·을설 실체 논거 금지·결론 유보' in prompt
    assert '공통 정의·기준 확인 전' in prompt
