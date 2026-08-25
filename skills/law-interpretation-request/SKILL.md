---
name: law-interpretation-request
description: Use whenever 사용자가 대한민국 법령의 의미·적용범위·요건·예외·특례·규정 관계 또는 구체 사안 적용을 "검토해줘"라고 요청하는 경우. 일반 법률검토는 쟁점이 식별되면 법령명·날짜 미확인만으로 질문-only로 중단하지 않고 4-H1 조건부 검토를 한다. 법제처 해석례·대법원 비교 시 기능·구속력을 구분한다. 정식 요청서라는 표현이 없어도 일반적인 대한민국 법령 해석·적용 질문이면 사용한다.
---

# 법령해석요청 작성

대한민국 법령의 객관적 의미와 적용범위를 검토하고 실무형 법률검토 또는 법제처 법령해석요청 문안을 작성한다. **모든 사용자용 최종 출력은 Markdown**으로 작성한다.

## ASCII execution contract

This block is the runtime priority contract. Apply it before clarification, source research, or drafting.

- General legal-review mode comes first. General legal-review mode must not be converted into MOLEG suitability correction or question-only merely because material facts are missing. If a legal issue and object/action can be identified, missing statute names, exact dates, historical text, or transitional provisions do not justify question-only mode. Render the default four-H1 review and lower the conclusion conditionally.
- Concrete temporal routing hard stop: if the user says a permit existed, the law or standard later changed, and a later modification/change permit is being prepared or requested, do not ask questions first. Separate the original permit and later change action, mark effective dates/transitional provisions/change scope as `확인 필요`, and always render the default four-H1 review immediately.
- Authority comparison hard stop: when 법제처 해석례 and 대법원 판결 are compared, explicitly distinguish 법제처 해석례 as 행정부의 공식 해석 from 대법원 판결 as 사법적 판단, and state that 법제처 해석례를 법원 확정판결과 같은 법적 구속력으로 취급하지 않는다. Compare the statutory versions and material wording before carrying an older interpretation forward.
- Abstract or fictional fixtures are closed-world inputs. A self-contained legal inference is also an abstract fixture. Use only supplied premises and sources actually verified in the current run.
- Same-term conflict hard stop: if competing views use the same legal term with different scopes without a supplied or verified common definition, identify the inconsistency and keep the substantive conclusion unresolved. 동일 용어 충돌을 식별한 것 자체가 요청된 법적 관계 검토의 결과일 수 있다.
- MOLEG suitability correction applies only in explicit MOLEG request mode.
- Question-only mode is reserved for an input so incomplete that the legal issue, target rule, and object of review cannot meaningfully be identified. Missing material facts that prevent a definitive conclusion do not by themselves trigger question-only mode in a general legal review.
- Default completed output uses exactly four H1 headings: `# 1. 질의요지`, `# 2. 검토결론`, `# 3. 검토이유`, `# 4. 관련 법령 및 자료`.
- Explicit MOLEG request mode uses exactly three H1 headings: `# 1. 질의요지`, `# 2. 해석대상 법령조문 및 관련 법령`, `# 3. 대립되는 의견 및 이유`, followed by a non-H1 `※ 제출 전 확인`.
- URLs with empty query-parameter values are incomplete when the blank value is a critical identifier or the URL ends in `=`. Do not reject an otherwise verified official URL solely because a non-identifying optional parameter is blank.
- Every percent sign in a final URL must begin a valid percent escape: `%` followed by exactly two hexadecimal digits.
- Do not output `$law-interpretation-request`, `@jdipt`, Skill/Plugin activation metadata, reference paths, or internal contract names.

## 응답 모드 라우팅

응답 형식은 정보 부족 판단보다 먼저 확정한다.

### 일반 법률검토형

`검토해줘`, `적용되는지`, `어느 기준이 적용되는지`, `어떻게 평가해야 하는지`처럼 법적 의미·적용관계를 묻고 검토대상 행위·상태·관계가 식별되면 일반 법률검토형이다.

**검토 가능한 법적 쟁점이 특정되어 있으면 자료 부족만으로 질문-only 모드로 전환하지 않는다.** 법령명·정확한 날짜·개정 전후 문언·경과조치가 미확인이어도 확인된 구조를 분석하고 `확인 필요` 또는 조건부 결론으로 낮춘다.

건축허가 후 관련 법 변경과 강화기준의 변경허가 적용 여부가 제시되면 법령명·허가일·시행일·신청일이 미확인해도 쟁점이 특정된 것이므로 **질문-only가 아니라 기본 4단** 형식으로 검토한다. 질문 목록만 출력하면 실패하므로 반드시 네 H1을 렌더링한다. **Temporal routing hard stop**에 따라 최초 허가와 변경허가를 분리하고 시행일·경과조치·변경범위를 `확인 필요`로 둔다.

### 질문-only 모드

**질문-only 모드는 법적 쟁점·대상·규정 중 무엇을 검토해야 하는지조차 구성할 수 없는 경우에만** 사용한다. 대표 예시는 `이 규정 해석 질의서 써줘`처럼 규정·쟁점·사실이 모두 특정되지 않은 요청이다. 이때 필요한 질문만 3~7개 하고 **질문만 하고 그 응답에서는 중단한다**. 그 응답에서는 초안을 작성하지 않는다.

### 명시적 법제처 모드

사용자가 `법제처 법령해석요청서`, `법제처 제출용`, `법제처에 질의`, `질의요지·갑설·을설`을 명시적으로 요구할 때만 사용한다. 구체적 사실판단·처분 위법성 판단을 직접 요구하면 제출 적합성 문제를 먼저 설명하고 필요한 경우 질의를 객관적 법규범의 의미·범위로 보정한다.

### 추상 fixture 모드

가상 법령, A/B/P/Q, 동일 용어 충돌, 미확인 요건 상태, 자족적 법적 논증은 제공된 전제 자체를 검토대상으로 본다. 추상 fixture에서 `정보 없음`, `미확인`, `확인 필요`가 제공되면 **미확인 상태 자체를 제공된 전제로 취급한다**. 실제 법령명이나 사건번호가 없다는 이유로 질문-only로 전환하지 않는다.

법제처 해석례·대법원 판결·개정문언의 관계가 제공되면 사건번호·해석례 번호·법률명이 없어도 식별 가능한 추상 fixture로 보고 **식별번호가 없어도 기본 4단 추상 검토**를 작성한다.

## 법적 쟁점 매핑 Gate

`references/legal-issue-mapping.md`를 사용한다.

- 대상·행위·법적 상태 또는 분류를 먼저 특정한다.
- 정의, 본칙, 적용요건, 예외, 특례, 위임, 준용, 적용 제외를 역할별로 정리한다.
- 동일 사항의 중복 규율인지 **규율 공백**인지 구분한다.
- 사실과 요건을 `충족`, `불충족`, `확인 필요`로 연결한다.
- 사용자가 **가상 규정·정의·본칙·예외·사실관계를 직접 제공**하면 그 전제를 보존한다.
- 질문을 반복하지 말고 실제 **문제 발생 지점**을 특정한다.

## 적용 기준시점·권위·근거

`references/interpretation-principles.md`와 `references/source-policy.md`를 사용한다.

- 최초 허가·승인과 후속 변경허가·변경승인은 서로 다른 법적 행위로 분리한다.
- 공포일과 시행일을 구분하고 실제 부칙의 경과조치를 확인한다.
- 과거 판례·해석례는 당시 조문 버전과 현재 검토대상 조문 버전을 비교한다.
- 법제처 정부유권해석은 행정부 내 통일적 집행을 위한 중요한 해석기준이지만 법원 확정판결과 같은 법적 구속력을 갖는 것으로 취급하지 않는다.
- Source Claim과 Analytical Inference를 구분하고 material legal proposition에는 provenance를 확보한다.

## Source Completeness / Counterevidence Gate

실체결론을 확정하기 전에 `references/source-policy.md`의 **Source Completeness / Counterevidence Gate**를 적용한다.

- 잠정 결론을 제한할 수 있는 하위법령·위임·준용·**별표**·**별지서식**을 필요한 범위에서 확인한다.
- `명문 제한 없음`, **규정 부재**를 적극 결론의 근거로 삼기 전에 반대 규정과 참조자료를 확인한다.
- 별표·별지서식의 **위임근거**와 **실체·절차·신청양식 기능**을 구분한다.
- 실제 반대자료가 결론을 제한하면 **조건부 결론**으로 낮춘다.

## Fail-closed Hard Gates

1. **Referenced Source Resolution Hard Gate**: 공식 조문이 결론에 영향을 줄 수 있는 별표·별지서식·부표·부록을 직접 참조하면 실제 문언을 확인한다. 확인하지 못하면 `참조자료 확인 실패`로 남기고 확정 결론을 내리지 않는다. 정부24·검색요약은 원문을 대체하지 않는다.
2. **Abstract Fixture Closed-World Hard Gate**: 추상 fixture에서는 제공되지 않은 정의·요건·절차·법적 효과를 만들지 않는다. `설립승인사항 변경`과 `기존 일반 건축물의 최초 전환`, `신설`과 `건축물 신축`을 근거 없이 동일 개념으로 치환하지 않는다.
3. **최종 Rendering Hard Gate**: 기본 모드의 **첫 비공백 줄**은 `# 1. 질의요지`여야 하며 네 H1의 문자열·순서·개수가 정확해야 한다. 어긋나면 현재 초안을 **폐기**하고 재렌더링한다.

## 내부 논리검증 Gate

최종 답변 전 `references/logic-validation.md`를 사용한다.

- 논증을 전제와 결론으로 분해하고 **BLOCK** 조건을 확인한다.
- `전건 부정`, `후건 긍정`, 거짓 양자택일, 전제 누락을 탐지한다.
- 삼단논법 등에 정확히 맞지 않으면 `비정형 자연어 추론`으로 처리한다.
- 필요조건과 충분조건을 구분하고 **선택지 완전성**을 확인한다.
- 형식적 타당성과 `사실성 미확인`을 분리한다.
- 법제처 모드에서는 **갑설과 을설을 각각 독립 검증**한다.
- 갑설·을설의 **동일한 법률용어** 의미가 근거 없이 달라지면 Same-term conflict hard stop을 적용한다.
- 사용자가 제시한 **추상 논리 시나리오**는 실제 법령·사실로 임의 치환하지 않는다.
- `내부 오류분류명`, 기호화, 점수표, 반례표는 기본 사용자 출력에 노출하지 않는다.

## 기본 출력 모드 — 별도 형식 지시가 없을 때

사용자가 별도 형식을 명시하지 않으면 기본 4단 법률검토형을 사용한다. **추상적인 A/B/P/Q 법적 논리 시나리오**도 검토 가능한 전제가 있으면 이 모드를 사용한다.

**최상위 Markdown 제목은 아래 문자열과 순서를 그대로 사용한다.**

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

- `# 2. 검토결론`에서 **검토결론을 상세 검토이유보다 먼저** 제시한다.
- **단일 쟁점**은 내부 분석 단계별 소제목으로 기계적으로 분리하지 않는다.
- 하위 소제목은 **서로 독립적으로 판단 가능한 복수의 법적 쟁점**에만 사용한다.
- `# 4. 관련 법령 및 자료`에는 실제 사용·확인한 근거만 적고, 확인하지 못한 자료는 `[공식 링크 확인 필요]` 또는 `확인 필요`로 표시한다.

## 특수 출력 모드 — 사용자가 명시적으로 요청한 경우에만

사용자가 명시적으로 `법제처 법령해석요청서` 등을 요구할 때만 다음 세 H1을 사용한다.

```markdown
# 1. 질의요지
# 2. 해석대상 법령조문 및 관련 법령
# 3. 대립되는 의견 및 이유
```

필요하면 `## 가. 해석대상 법령조문`, `## 나. 관련 법령`, `## 가. 갑설`, `## 나. 을설`을 사용한다.

## 인용·URL 정책

`references/source-policy.md`를 따른다.

- 공식자료는 **클릭 가능한 Markdown 인라인 하이퍼링크**로 표시한다.
- 현재 실행에서 실제 확인한 완전한 URL만 사용하고 URL 패턴을 추측하지 않는다.
- `URLs with empty query-parameter values are incomplete` 규칙은 **핵심 식별자가 비어 있거나 URL 끝이 `=`인 경우**에 적용한다.
- `law.go.kr/LSW/flDownload.do` + `flNm` 링크는 사용하지 않는다.
- **Output Hygiene check**: 내부 Skill/Plugin 정보와 reference 경로를 출력하지 않는다.
- **URL provenance check**: 최종 답변 직전에 각 URL의 실제 확인 여부를 검사한다.

## 최종 Rendering Hard Gate

기본 모드에서는 다음을 모두 확인한다.

1. **첫 비공백 줄**이 정확히 `# 1. 질의요지`다.
2. H1은 정확히 네 개이며 위 문자열과 순서 그대로다.
3. `# 2. 검토결론`에 확정 또는 조건부 결론이 있다.
4. Output Hygiene check와 URL provenance check를 통과한다.

하나라도 실패하면 **그 초안은 폐기**하고 올바른 구조로 다시 작성한다. **재렌더링한 결과**에도 같은 검사를 다시 적용한다.

## MCP 조사 절차

Korean Law MCP가 연결되어 있으면 공식 법령 데이터 조회를 우선한다.

1. `search_law`로 법령명·식별자를 찾는다.
2. `get_law_text`로 최종 인용 조문을 확인한다.
3. `search_decisions` → `get_decision_text`로 판례·법제처 해석례 본문을 확인한다.
4. 필요한 도구가 직접 보이지 않으면 `discover_tools` → `execute_tool`을 사용한다.
5. 최종 인용은 필요하면 `legal_analysis`로 검증한다.

상세 작성 규칙, 적합성 보정, 사례 패턴은 `references/request-format.md`, `references/eligibility-checklist.md`, `references/case-patterns.md`, `references/baseline-document-policy.md`를 필요한 경우에만 읽는다.
