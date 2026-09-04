from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_POLICY = ROOT / "skills" / "law-interpretation-request" / "references" / "source-policy.md"


def test_runtime_source_link_policy_is_owned_by_source_policy():
    policy = SOURCE_POLICY.read_text(encoding="utf-8")
    assert "flDownload.do" in policy
    assert "flNm" in policy
    assert "공식 링크 확인 필요" in policy