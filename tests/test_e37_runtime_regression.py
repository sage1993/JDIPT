from pathlib import Path

from scripts.regression_oracles import evaluate_case


ROOT = Path(__file__).resolve().parents[1]

E37_RUNTIME_RESPONSE_20260829_ATTEMPT2 = """# 1. 질의요지

사업계획승인을 받아 건설·공급하는 6층 이상 공동주택의 승용승강기 설치대수를 산정할 때, 「주택건설기준 등에 관한 규칙」의 세대수·주동형식 기준과 「건축물의 설비기준 등에 관한 규칙」의 6층 이상 거실면적 기준을 함께 적용해야 하는지 여부입니다.

# 2. 검토결론

사업승인 대상 공동주택의 승용승강기 설치대수는 원칙적으로 「주택건설기준 등에 관한 규칙」 제4조에 따라 산정하면 되고, 「건축물의 설비기준 등에 관한 규칙」 별표 1의2의 거실면적 기준을 추가로 적용할 필요는 없습니다.

법제처도 동일 쟁점에 대해, 주택건설기준에 따른 세대수 등의 기준만 충족하면 된다고 해석했습니다. [법제처 17-0047 해석례](https://law.go.kr/LSW/expcInfoP.do?expcSeq=331029)

다만 이는 “승용승강기 설치대수 산정기준”에 관한 결론입니다. 승강기의 구조·승강장 구조, 비상용승강기·피난용승강기 등 별도의 건축법상 안전기준까지 배제되는 것은 아닙니다.

# 3. 검토이유

「주택법」 제35조는 사업주체가 건설·공급하는 주택의 구조·설비 및 부대시설 기준을 대통령령으로 정하도록 하고 있습니다. [「주택법」 제35조](https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1033933859)

이에 따라 「주택건설기준 등에 관한 규정」 제15조제1항은 6층 이상 공동주택에 6인승 이상 승용승강기를 설치하도록 하고, 구체적인 설치기준은 국토교통부령으로 정하도록 합니다. [「주택건설기준 등에 관한 규정」 제15조](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1026129119)

그 위임에 따른 「주택건설기준 등에 관한 규칙」 제4조는 공동주택의 유형과 세대수 등을 기준으로 설치대수를 정합니다. [「주택건설기준 등에 관한 규칙」 제4조](https://law.go.kr/lumLsLinkPop.do?lspttninfSeq=130300)

반면 「건축법」 제64조 및 「건축물의 설비기준 등에 관한 규칙」 제5조·별표 1의2는 일반적인 건축물에 대해 6층 이상 거실면적을 기준으로 승용승강기 설치대수를 산정합니다. [「건축법」 제64조](https://law.go.kr/LSW/flDownload.do?bylClsCd=110201&flSeq=61648875&gubun=), [「건축물의 설비기준 등에 관한 규칙」 제5조](https://law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=105273), [별표 1의2](https://law.go.kr/LSW/flDownload.do?bylClsCd=110201&flSeq=61648875&gubun=)

그러나 주택법령은 사업계획승인 공동주택의 승강기 설치대수를 별도로 직접 규율하고 있습니다. 따라서 주택법령이 승용승강기 설치대수를 정하고 있으므로, 같은 사항에 관한 건축법령의 거실면적 기준을 중복 적용할 수는 없습니다.

다만 구조·안전 관련 사항은 별도로 확인해야 합니다.

# 4. 관련 법령 및 자료

- [「주택법」 제35조](https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1033933859)
- [「주택건설기준 등에 관한 규정」 제15조](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1026129119)
- [「주택건설기준 등에 관한 규칙」 제4조](https://law.go.kr/lumLsLinkPop.do?lspttninfSeq=130300)
- [「건축법」 제64조](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1032217999)
- [「건축물의 설비기준 등에 관한 규칙」 제5조](https://law.go.kr/LSW/lsLinkCommonInfo.do?lspttninfSeq=105273)
- [법제처 17-0047 해석례](https://law.go.kr/LSW/expcInfoP.do?expcSeq=331029)
"""


def test_e37_runtime_variant_rejects_incomplete_download_url():
    result = evaluate_case(37, E37_RUNTIME_RESPONSE_20260829_ATTEMPT2)

    assert result["contract_oracle"] == "FAIL"
    assert any("no_unstable_download_links" in failure for failure in result["contract_failures"])


def test_runtime_prompt_names_the_stable_source_link_class():
    policy = (ROOT / "skills/law-interpretation-request/references/source-policy.md").read_text(encoding="utf-8")

    assert "flDownload.do" in policy
    assert "flNm" in policy
    assert "확인 필요" in policy
