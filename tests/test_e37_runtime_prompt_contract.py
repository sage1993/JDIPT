from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_default_prompt_names_the_stable_source_link_class():
    prompt = next(
        line.split(": ", 1)[1]
        for line in (ROOT / "skills/law-interpretation-request/agents/openai.yaml")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.startswith("  default_prompt:")
    )

    assert "flDownload.do" in prompt
    assert "flNm" in prompt
    assert "공식 링크 확인 필요" in prompt
