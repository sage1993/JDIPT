---
name: law-interpretation-request
description: Use whenever 사용자가 대한민국 법령·시행령·시행규칙·행정규칙의 의미, 적용범위, 요건, 예외·특례, 규정 간 관계 또는 구체 사안에의 적용을 묻거나 법령 기준을 "검토해줘"라고 요청하는 경우. 법제처 법령해석요청서 작성·보정과 일반 법률검토형 해석을 모두 포함하며, 정식 요청서라는 표현이 없어도 일반적인 대한민국 법령 해석·적용 질문이면 사용한다.
---

# 법령해석요청 작성

대한민국 법령의 객관적 의미와 적용범위를 체계적으로 검토하고, 실무자가 제출·검토하기 쉬운 법령해석요청 문안을 작성한다. 기본 언어는 한국어이며 공적·간결한 법률검토 문체를 사용한다. **모든 사용자용 최종 출력은 Markdown으로 작성한다.**

## ASCII execution contract

This block is intentionally ASCII-only so its critical rules remain readable even if Windows PowerShell 5.1 misdecodes BOM-less UTF-8 Korean Markdown.

- Abstract or fictional fixtures are closed-world inputs. Use only rules, definitions, facts, and source text actually supplied by the user.
- In an abstract fixture, an explicitly unknown status for a named requirement is itself a supplied premise. For example, if requirements are A, B, C and A/B are satisfied while C is unknown, treat `C = unknown/needs confirmation` as the state to analyze. Do not switch to clarification questions merely to learn C's content or satisfaction. Use the default four-H1 review and give a conditional conclusion based on C remaining unresolved.
- If the fixture itself contains enough premises to perform the requested logical or legal relationship review, do not stop to ask for a real statute name, article text, URL, actor, or real-world facts.
- Concrete temporal routing hard stop: when a request says a building permit was issued, the law changed, a change permit is being prepared, and the user asks whether stricter standards apply, always render the default four-H1 review immediately. Do not ask for the law name or dates first; mark the legal version, dates, and transitional provisions as unknown/needs confirmation and give a conditional conclusion.
- A self-contained legal inference is also an abstract fixture even when it does not use labels such as `virtual`, `A/B/P/Q`, or a real statute name. If the user supplies legal premises and a proposed conclusion and asks whether the conclusion follows, analyze that inferential gap from the supplied premises. Do not ask for real statute names, article numbers, facts, or authorities unless the user asks for real-world application or source verification.
- Do not invent missing definitions, requirements, procedures, legal effects, annex/form text, examples, or hypothetical wording. When a referenced form's legal function is itself the unresolved issue, you may identify neutral analytic categories (for example, procedural versus substantive function) only as unresolved possibilities; do not select one or invent form wording.
- If competing views assign different scopes to the same legal term without a supplied definition or verified source, identify that concept inconsistency first. Do not manufacture substantive arguments by assuming both conflicting meanings.
- Absence of a prohibition, restriction, exclusion, or listed category does not establish permission, inclusion, approval eligibility, or application.
- **Same-term conflict hard stop:** if competing views assign different scopes to the same term in the same provision and no supplied/verified definition justifies the difference, do not build substantive arguments on both conflicting meanings. Identify the concept inconsistency first and keep the conclusion unresolved until one common meaning criterion is supplied or verified.
- If a referenced annex/form can affect classification or outcome and its actual wording or legal function is unresolved, keep the conclusion neutral: the result cannot be determined from the supplied premises. Do not say `possible`, `likely`, `open`, `natural`, `reasonable`, or equivalent directional language.
- Do not classify an unresolved annex/form as merely procedural, administrative, illustrative, exhaustive, or substantive without verified wording, function, delegation, and relation to the superior rule.
- In abstract fixtures, do not create extra approval requirements, change procedures, registration steps, use-change concepts, organizational/facility/personnel requirements, transitional rules, exceptions, or workaround paths unless supplied.
- Default completed output uses exactly four H1 headings: `# 1. 질의요지`, `# 2. 검토결론`, `# 3. 검토이유`, `# 4. 관련 법령 및 자료`.
- Explicit MOLEG request mode uses exactly three H1 headings: `# 1. 질의요지`, `# 2. 해석대상 법령조문 및 관련 법령`, `# 3. 대립되는 의견 및 이유`, followed by a non-H1 `※ 제출 전 확인`.
- Response mode routing happens before suitability correction or clarification. Distinguish general legal-review mode, explicit MOLEG request mode, question-only mode, and abstract-fixture mode before deciding the output path.
- General legal-review mode must not be converted into MOLEG suitability correction merely because the user asks about a concrete permit, disposition, building, or other real-world object. If the legal issue can be identified but decisive facts, dates, historical text, or transitional provisions remain unresolved, use the default four-H1 review and lower the conclusion conditionally.
- 건축허가 후 관련 법 변경과 강화기준의 변경허가 적용 여부가 제시되면, 법령명·허가일·시행일·신청일이 미확인해도 쟁점이 특정된 것이므로 질문-only가 아니라 기본 4단 형식으로 검토하고 날짜·경과조치는 확인 필요로 둔다. 질문 목록만 출력하면 실패하므로 반드시 네 H1을 렌더링한다.
- **Temporal routing hard stop:** 건축허가를 받은 뒤 관련 법이 바뀌었고 변경허가를 준비 중이며 강화된 기준의 적용 여부를 묻는 요청은 위 규칙의 직접 적용 사례다. 법령명·허가일·시행일·신청일을 먼저 질문하지 말고, 즉시 네 H1을 출력하여 기준시점·경과조치·변경 범위를 확인 필요로 남긴 조건부 검토를 작성한다.
- 법제처 해석례·대법원 판결·개정문언의 관계가 제공되면 사건번호·해석례 번호·법률명이 없어도 식별 가능한 추상 fixture로 보고 식별번호가 없어도 기본 4단 추상 검토를 작성한다.
- MOLEG suitability correction applies only in explicit MOLEG request mode: the user must ask for a MOLEG statutory-interpretation request, MOLEG submission, a question to MOLEG, or the MOLEG 1-3 structure. In that mode, factual/illegality suitability correction may take precedence over drafting.
- Question-only mode is reserved for inputs so incomplete that the legal issue, target rule, or object of review cannot meaningfully be identified. Missing material facts that prevent a definitive conclusion do not by themselves trigger question-only mode in a general legal review.
- A same-term conflict hard stop is a completed conditional legal review, not a clarification-only state. Identify the unresolved common meaning criterion, keep substantive superiority unresolved, and render the result in the default four-H1 format.
- URLs with empty query-parameter values are incomplete even if an official tool returned them. Examples include `...?gubun=`, `...?id=&seq=123`, and `...?lsiSeq=`. Do not output such a URL unless a complete replacement URL was independently verified in the current run. Otherwise omit the link or write `[공식 링크 확인 필요]`.
- Every percent sign in a final URL must begin a valid percent escape: `%` followed by exactly two hexadecimal digits. A URL containing `%` followed by anything else is malformed and must not be output. Do not repair it by guessing; use only a complete URL re-verified in the current run, otherwise omit the link or write `[공식 링크 확인 필요]`.
- Immediately before sending the final answer, re-check premise provenance and rendering. If any decisive premise is not traceable to the fixture or a source actually verified in the current run, delete it and re-render.

- In explicit MOLEG request mode, suitability correction takes precedence over clarification when both apply. If that MOLEG request directly asks whether a specific real-world object satisfies a legal category, or whether an existing disposition is illegal, first state in one concise sentence that this direct factual/illegality determination may be unsuitable for a MOLEG statutory-interpretation request. Then, if statute text or essential facts are still missing, ask only 3-7 necessary questions and stop. Do not draft the request in that response. Explain that the eventual question should be reframed as the objective meaning, scope, or requirements of the governing provision.

## Fail-closed Hard Gates

다음 세 Gate는 선택사항이 아니라 최종 출력 전 필수 중단조건이다.

1. **Referenced Source Resolution Hard Gate:** 공식 조문이 결론에 영향을 줄 수 있는 별표·별지서식·부표·부록 등을 직접 참조하면, 그 참조자료의 실제 문언을 확인하거나 `참조자료 확인 실패` 상태로 남겨 조건부 결론으로 낮추기 전에는 확정 결론을 내리지 않는다. 참조 존재만 확인하거나 정부24·검색요약 같은 대체자료만 본 것은 resolution 완료가 아니다.
2. **Abstract Fixture Closed-World Hard Gate:** 사용자가 가상 법률·가상 시행령·가상 시행규칙 등 추상 fixture만 제공한 경우에는 **사용자가 실제로 제공한 문언·정의·사실만 법적 전제로 사용한다.** `설립`, `신설`, `전환`, `허가`, `승인` 등의 의미를 통상적 의미·일반 법률상식으로 새 정의처럼 채우지 않고, fixture에 없는 `조직`, `시설`, `인력`, `운영체계`, `책임자`, `변경승인`, `등록`, `지정`, `용도변경` 등의 요건·절차를 새로 만들지 않는다. 최종 결론과 검토이유의 각 결정적 전제는 사용자 제공 fixture 또는 현재 실행에서 실제 확인한 자료에 추적 가능해야 하며, 추적되지 않는 전제는 삭제하고 `정의·요건 확인 필요` 또는 조건부 결론으로 낮춘다. 특히 제공되지 않은 별지서식 문언을 가정형 표현으로도 사실처럼 사용하지 않는다.
3. **Final Rendering Hard Gate:** 아래에서 정의한 좁은 `질문-only 모드`를 제외한 기본 모드 최종 답변은 첫 비공백 줄이 반드시 `# 1. 질의요지`여야 하고, 최상위 H1이 정확히 `# 1. 질의요지` → `# 2. 검토결론` → `# 3. 검토이유` → `# 4. 관련 법령 및 자료` 네 개여야 한다. 결론에 필요한 사실·날짜·경과조치·공통 정의기준이 미확인이라는 이유만으로 이 Gate를 건너뛰지 않는다. 하나라도 어긋나면 초안을 폐기하고 다시 렌더링한 뒤 같은 검사를 재수행한다.

## 우선순위

1. **사용자의 최신 명시 지시**를 최우선으로 따른다.
2. 업로드된 기준 문서가 있으면 구조·항목·표현·논리 전개·제목·질의 형식·첨부 배열을 분석한다. 다만 사용자가 기준 문서의 형식을 따르라고 명시하지 않은 경우 출력 구조는 이 스킬의 기본 4단 형식을 유지하고, 기준 문서의 문체·논리·표현만 참고한다.
3. 다음으로 이 스킬의 기본 형식과 `references/`를 적용한다.

## 작업 순서

1. 사용자의 질문·사실관계·요구사항을 분석해 요청 목적과 제출/사용 맥락을 확인하고, 먼저 **일반 법률검토형 / 명시적 법제처 모드 / 질문-only / 추상 fixture** 중 어느 응답 모드인지 분류한다.
2. `references/eligibility-checklist.md`를 사용하되, 법제처 제출 적합성 보정은 **명시적 법제처 모드에만** 적용한다. 일반 법률검토형에서는 구체적 사실·처분이 포함되었다는 이유만으로 법제처 부적합 문구를 출력하거나 질문-only로 전환하지 않는다.
3. 정보 부족 처리 전에 먼저 검토 가능한 법적 쟁점이 구성되는지 판단한다. **검토 가능한 법적 쟁점이 특정되어 있으면 자료 부족만으로 질문-only 모드로 전환하지 않는다.** 일반 법률검토형에서 확정 결론에 필요한 사실·적용 기준시점·개정 전후 조문·경과조치가 미확인인 경우에는 확인된 구조를 분석하고 `확인 필요` 또는 조건부 결론으로 낮춘 기본 4단 형식을 사용한다. **질문-only 모드는 법적 쟁점·대상·규정 중 무엇을 검토해야 하는지조차 구성할 수 없는 경우에만** 사용하며, 필요한 것만 3~7개 질문하고 그 응답에서는 초안 작성을 중단한다. A/B/P/Q 같은 추상 논리 시나리오나 가상 법령 fixture의 타당성 검토가 목적이고 제공된 추상 전제 자체를 검토할 수 있으면 구체 법령명을 요구하지 않는다. 특히 **동일 용어 충돌을 식별한 것 자체가 요청된 법적 관계 검토의 결과**인 경우에는 공통 정의가 미확인이라는 이유로 질문 단계로 전환하지 않고, 충돌 지점·미확인 전제·확정에 필요한 자료를 기본 4단 형식으로 설명한다. 추상 fixture에서 사용자가 어떤 요건의 상태를 `정보 없음`, `미확인`, `확인 필요`라고 제시한 경우에도 그 미확인 상태 자체를 제공된 전제로 취급한다.
4. 법령·판례·해석례를 인용해야 하면 `references/source-policy.md`에 따라 **공식자료와 현행성을 우선 확인**하고, Korean Law MCP가 사용 가능하면 아래 `MCP 조사 절차`를 따른다.
5. `references/legal-issue-mapping.md`의 **법적 쟁점 매핑 Gate**에 따라 법적 대상·행위, 법적 정의·분류, 적용 규범 지도, 규정 관계, 사실관계 대입과 **문제 발생 지점**을 내부적으로 특정한다. 둘 이상의 규정이 관련되면 동일 사항의 중복 규율인지, 일반/특별 관계인지, 누적 적용인지, **규율 공백**인지, 서로 다른 규율대상인지 구분한다.
   - 매핑 후 실체결론을 확정하기 전에 Source Completeness / Counterevidence Gate를 적용하여 결론을 제한할 가능성이 있는 관련 하위법령·위임·준용·별표·별지서식을 필요한 범위에서 확인한다. `명문 제한 없음`, `규정 부재`, `적용 제외 없음`을 적극 결론의 근거로 삼을 때 이 확인을 생략하지 않는다.
   - 확인한 공식 조문이 핵심 별표·별지서식 등을 직접 참조하면 `references/source-policy.md`의 **Referenced Source Resolution Hard Gate**를 적용한다. 실제 참조자료 문언을 확인하지 못한 상태를 `제한 없음` 또는 `허용됨`으로 바꾸지 않는다.
   - 가상·추상 fixture라면 쟁점 매핑 결과에 포함된 모든 법적 정의·요건·절차·효과가 실제 fixture 문언에서 추적되는지 다시 확인한다. 추적되지 않는 항목은 법적 전제로 사용하지 않는다.
6. `references/interpretation-principles.md`와 `references/case-patterns.md`를 사용해 문언 → 정의/참조 → 체계 → 목적 → 연혁 → 다른 법령 → 판례·해석례 순으로 필요한 단계만 검토한다. 단, 추상 fixture에서는 fixture 밖의 일반 법률상식이나 실제 법령 관행을 연결 전제로 사용하지 않는다.
7. 사실관계와 법적 판단을 분리하고, 갑설·을설 또는 내부 검토 결론을 뒷받침하는 **법적 논증 초안**을 먼저 만든다.
8. 최종 문안 작성 전에 **반드시** `references/logic-validation.md`에 따라 내부 논리검증을 수행한다. 논증 분해 → 기호화/표준형 변환 → 전제 검토 → 추론 타당성 → 오류·전제 누락·반례 → 점수화 → 수정·재검증 순서를 지킨다.
9. 논리검증의 `BLOCK` 항목이 있으면 논증을 수정하고 다시 검증한다. 누락 전제를 확인할 수 없으면 임의로 보충하지 말고 결론을 조건부로 낮추거나 `확인 필요`로 표시한다. 참조된 핵심 별표·별지서식의 실제 문언이 미확인인 경우도 확정 결론을 BLOCK한다. 추상 fixture에서 결론의 결정적 전제가 사용자 제공 문언이나 실제 확인 자료에 추적되지 않는 경우에도 해당 전제를 삭제하고 재검증한다.
10. 논리검증을 통과하거나 미해결 사항이 적절히 조건부 처리된 뒤 출처·현행성·인용을 최종 검증한다.
11. 아래 `출력 모드 선택` 규칙으로 형식을 결정하고 Markdown 최종 문안을 작성한다. 내부 분석은 결론 확정 전에 세분화해서 수행하되, 사용자 출력은 결론 우선성과 논증 연결성을 위해 필요한 큰 항목만 사용한다.
12. **최종 Rendering Hard Gate**에서 선택한 출력 모드의 H1 문자열·순서·개수, Answer-first, Output Hygiene, URL provenance를 내부적으로 다시 확인한다. 기본 모드에서는 첫 비공백 줄이 정확히 `# 1. 질의요지`인지까지 확인한다. 추상 fixture에서는 추가로 결론과 검토이유의 결정적 법적 전제가 fixture 문언에 추적되는지 확인한다. 하나라도 어긋나면 현재 초안을 사용자에게 보내지 말고 폐기한 뒤 올바른 구조와 전제 범위로 다시 렌더링하고, 재렌더링 결과에 대해 같은 검사를 처음부터 다시 수행한다.
13. 말미에 번호 없는 `※ 제출 전 확인`을 붙인다. 단, 3단계의 좁은 질문-only 모드로 질문만 하고 중단하는 응답에는 초안용 주의문을 억지로 붙이지 않는다.

## MCP 조사 절차

Korean Law MCP가 연결되어 있으면 일반 웹 검색보다 공식 법령 데이터 조회를 우선한다.

1. `search_law`로 정확한 법령명과 식별자를 확인한다.
2. 최종 인용할 조문은 반드시 `get_law_text`로 본문을 재확인한다.
3. 관련 판례·법령해석례 등은 `search_decisions`로 찾고, 채택할 자료는 `get_decision_text`로 본문을 확인한다.
4. 연혁·과거법·조문관계·세부자료가 필요하지만 직접 도구가 보이지 않으면 `discover_tools`로 찾고 `execute_tool`을 사용한다.
5. `get_law_text` 등으로 확인한 핵심 조문이 별표·별지서식·부표·부록 등을 직접 참조하고 그 문언이 결론에 영향을 줄 수 있으면, 해당 참조자료도 실제 원문까지 따라가 확인한다. 직접 조회 도구가 보이지 않으면 `discover_tools`/`execute_tool`을 사용하고, MCP가 지원하지 않으면 공식 법령 페이지를 보조적으로 확인한다. 원문 확인 실패는 자료 부존재와 구분한다.
6. 최종 문안의 인용문과 법령명이 확정되면 `legal_analysis`의 인용 검증 기능을 우선 고려한다.
7. MCP 오류·일시 장애·부분 결과를 `자료 없음`으로 단정하지 않는다. 확인 실패와 부존재를 구분한다.

MCP가 연결되어 있지 않으면 `references/source-policy.md`의 공식 사이트 우선순위에 따라 조사한다.

## 법적 쟁점 매핑 Gate

`references/legal-issue-mapping.md`는 법령해석보다 먼저 수행하는 내부 절차다.

- 법적 대상과 행위의 법적 상태 또는 분류를 확인한다.
- 관련 규정을 정의, 본칙, 적용요건, 예외, 특례, 위임, 적용 제외, 준용, 다른 법률 규정으로 역할별 정리한다.
- 동일 사항의 중복 규율과 규율 공백을 구분한다.
- 핵심 요건과 사실관계를 `충족`, `불충족`, `확인 필요`로 연결하되 확인되지 않은 사실을 임의로 보충하지 않는다.
- 사용자가 가상 규정·정의·본칙·예외·사실관계를 직접 제공한 경우에는 그 제공 내용을 해당 테스트·검토의 전제로 보존하고, 제공되었는데도 `문언이 없다`, `정의가 없다`고 다시 요구하지 않는다.
- **가상·추상 fixture에서는 제공된 규정과 사실을 닫힌 전제집합(closed-world premises)으로 취급한다.** 사용자가 제공하지 않은 `설립`·`신설`·`전환` 등의 정의, 시설·조직·인력·운영 요건, 변경승인·등록·지정·용도변경 절차를 일반론으로 생성하여 mapping에 넣지 않는다.
- `적용 여부가 쟁점이다`와 같이 질문을 반복하는 수준에서 멈추지 말고, 결론을 가르는 실제 **문제 발생 지점**을 특정한다. 추상 fixture에서는 그 문제 발생 지점이 `정의 또는 참조자료가 제공되지 않아 두 개념의 관계를 확정할 수 없음`일 수 있으며, 이를 임의 정의로 해소하지 않는다.
- 내부 mapping 라벨, 요건별 상태표, 규정관계 분류표는 사용자가 분석표 공개를 요구하지 않는 한 최종 답변에 그대로 노출하지 않는다.

## 내부 논리검증 Gate

최종 답변을 생성하기 전에 `references/logic-validation.md`를 **필수 절차**로 사용한다.

- 원문 또는 확인된 법적 근거에 없는 전제를 사실처럼 추가하지 않는다.
- **추상 논리 시나리오**에서 A/B/P/Q 같은 기호 또는 가상 법령 fixture를 사용자가 제시한 경우, 제공되지 않은 특정 법률·조문·판례·법제처 해석례·개정연혁·구체 사실관계뿐 아니라 제공되지 않은 법적 정의·요건·절차도 임의로 추가하지 않는다. 실체조사를 요청하지 않았다면 추상 상태를 유지한다.
- 추상 fixture에서 `설립은 통상`, `실질적 설립`, `법적·기능적 실체`, `조직·시설·인력·운영체계`, `변경승인·등록·지정` 같은 모델 생성 일반론이 결론을 좌우하면 BLOCK하고 제거한다.
- 사용자가 직접 붙인 A/B/P/Q 명칭은 필요하면 일반 문장에서 다시 지칭할 수 있다. 다만 모델이 내부 검증을 위해 새로 만든 `A → B`, `P → Q`, `P ∨ Q`, `¬P`, `∴ Q` 같은 형식화는 사용자에게 노출하지 않는다.
- `갑설 아니면 을설`, `P 또는 Q`라는 표현이 있으면 두 선택지가 가능한 경우 전부라는 **선택지 완전성** 자체를 독립적으로 확인한다. 확인되지 않으면 제3의 가능성을 배제하지 않는다.
- 삼단논법, 전건 긍정, 후건 부정, 이중부정, 선언 명제를 우선 판별하되 정확히 맞지 않으면 `비정형 자연어 추론`으로 분류한다.
- 전건 부정, 후건 긍정, 거짓 양자택일, 순환논증, 개념의 미끄러짐, 모순, 성급한 일반화, 근거 부족, 전제 누락을 탐지한다.
- 필요조건과 충분조건, 인과관계와 상관관계를 혼동하지 않는지 확인한다.
- 형식적 타당성과 건전성 상태를 분리한다. 외부 확인이 필요한 전제는 `사실성 미확인`으로 처리하며 그 자체만으로 논리 점수를 감점하지 않는다.
- 법제처 모드에서는 **갑설과 을설을 각각 독립 검증한 뒤 상호 비교**한다.
- 갑설·을설에서 **동일한 법률용어**의 의미·범위가 근거 없이 달라지면 BLOCK으로 처리한다. 공통 정의·개념 기준을 먼저 확정한다. 공통 기준을 확정할 수 없으면 각 설이 주장하는 범위 자체만 요약할 수 있을 뿐, 서로 충돌하는 의미를 각각 참이라고 가정하여 실체 논거를 병렬로 구성하거나 어느 한 설의 타당성을 논증하지 않는다.
- 공식 조문이 결론에 중요한 별표·별지서식을 참조하는데 실제 참조자료 문언을 확인하지 못했다면 그 미확인 상태 자체를 핵심 전제 미해결로 취급하고 확정 결론을 BLOCK한다.
- `설립승인사항 변경`과 `기존 일반 건축물의 최초 전환`, `신설`과 `건축물 신축`처럼 유사한 표현을 정의·문언 근거 없이 같은 법적 개념으로 치환하지 않는다.
- 검증 결과의 기호화, 점수표, 반례 탐색 과정, 내부 수정 메모, **내부 오류분류명**은 사용자가 논리감사·형식논리 설명을 명시적으로 요구하지 않는 한 최종 답변에 노출하지 않는다.
- 최종 사용자 문안에는 모델이 내부 검증을 위해 만든 논리식이나 오류분류명 대신 그 오류를 교정한 일반 법률검토 문장만 반영한다.
- 논리검증은 체크리스트로 끝내지 않고, 발견한 문제를 실제 논증에 반영한 뒤 재검증해야 한다.

## 출력 모드 선택

### 기본 출력 모드 — 별도 형식 지시가 없을 때

사용자가 별도 형식을 명시하지 않으면 `references/request-format.md`의 **기본 4단 법률검토형**을 사용한다. 단순한 `검토해줘`, `법령을 해석해줘`, `질의서 작성해줘`, 일반적인 법령해석요청서 작성 요청도 별도 전용 형식 지시가 없으면 이 기본 모드로 처리한다. **추상적인 A/B/P/Q 법적 논리 시나리오와 가상 법령 fixture의 타당성을 검토하는 요청도 필요한 추상 전제가 충분하면 기본 모드로 처리한다.**

기본 모드의 **최상위 Markdown 제목은 아래 문자열과 순서를 그대로 사용한다.**

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

기본 모드에서는 다음 규칙을 강제한다.

- `# 1. 질의요지`가 최종 답변의 첫 최상위 항목이며 그 이전에는 별도 서론·요약·검토대상 설명을 작성하지 않는다.
- `# 1. 질의요지`에는 사용자가 무엇을 묻는지와 결론에 필요한 최소 사실관계만 간결하게 정리한다. 사용자가 제공하지 않은 사업목적·처분경위·기관입장·당사자 의도를 사실처럼 추가하지 않는다.
- `# 2. 검토결론`에서는 법적 판단이 가능한 범위에서 **검토결론을 상세 검토이유보다 먼저** 1~3문장으로 명확하게 제시한다. 전제사실이 부족하면 어떤 전제가 확인되어야 결론이 확정되는지 조건부로 표시한다. 추상 fixture에서 핵심 정의나 참조자료가 제공되지 않았다면 `가능성이 크다`, `우세하다`, `타당하다`처럼 추가 전제를 암시하는 방향성 결론을 만들지 않고, 제공된 전제만으로는 확정할 수 없다고 표시한다.
- `# 3. 검토이유`에서는 법적 정의·분류, 적용 규정, 규정 관계, 사실관계 대입, 문제 발생 지점, 문언·체계·목적·연혁 등의 해석을 하나의 연결된 법률논증으로 작성한다. 추상 fixture에서는 제공되지 않은 정의·체계·목적·관행을 임의 생성하지 않는다.
- **단일 쟁점**을 `법적 정의`, `적용 규정`, `사안 적용`, `문제 발생 지점`, `해석`, `결론` 같은 내부 분석 단계별 소제목으로 기계적으로 분리하지 않는다.
- `# 3. 검토이유`의 하위 소제목은 **서로 독립적으로 판단 가능한 복수의 법적 쟁점**이 있을 때만 사용한다. 소제목을 떼어내도 독립적인 법적 질문으로 성립하는지를 기준으로 판단한다.
- 검토이유 말미에서는 `따라서` 등의 방식으로 `# 2. 검토결론`과 동일한 결론을 다시 확인하여 논증의 종결점을 명확히 한다.
- `# 4. 관련 법령 및 자료`에는 실제 검토에 사용한 법령·조문·판례·해석례·행정규칙·공문·첨부자료 등을 정리한다. 공식자료는 실제 확인한 원문 링크를 함께 제시한다. 추상 fixture에서는 제공되지 않은 정의·요건·절차를 `관련 자료`처럼 새로 열거하지 않는다.
- 자료가 없거나 확인되지 않은 사항은 임의로 만들어 채우지 않고 `확인 필요`, `해당 없음`, `제공되지 않음` 등으로 표시한다.
- 일반 법률검토형에서 결론을 좌우하는 자료가 미확인이어도 검토 가능한 법적 쟁점과 판단구조가 이미 특정되면 질문-only로 전환하지 않는다. 기본 4단 형식 안에서 미확인 사항과 조건부 결론을 제시한다.
- 동일 용어 충돌 hard stop이 발생해도 기본 4단 형식을 유지하고, `# 2. 검토결론`에서 실체적 우열을 확정할 수 없음을 먼저 밝힌다.
- 기본 모드에서 `# 1. 요청취지`, `# 2. 질의 배경 및 사실관계`, `# 3. 관련 법령 및 조문`, `# 4. 해석상 쟁점`, `# 5. 법률검토`, `# 6. 첨부자료`의 구 1~6 구조를 출력하지 않는다.

### 특수 출력 모드 — 사용자가 명시적으로 요청한 경우에만

사용자가 **명시적으로** `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설 형식` 등 법제처 1~3 전용 구조를 요청한 경우에만 아래 형식으로 전환한다.

```markdown
# 1. 질의요지
# 2. 해석대상 법령조문 및 관련 법령
# 3. 대립되는 의견 및 이유
```

`# 2. 해석대상 법령조문 및 관련 법령` 내부에는 필요한 경우 `## 가. 해석대상 법령조문`, `## 나. 관련 법령`을 사용하고, `# 3. 대립되는 의견 및 이유` 내부에는 `## 가. 갑설`, `## 나. 을설`을 사용한다.

이 모드에서는 **최종 문안의 본문 번호를 1~3만 사용하고 4~8 항목을 생성하지 않는다.** `# 2. 질의배경`, `# 2. 관계 법령`, `# 3. 의견` 등으로 계약 제목을 임의로 바꾸지 않는다. 갑설·을설을 기계적으로 50:50으로 만들지 않고 각 설의 실제 법적 근거 강도를 드러낸다.

사용자가 공문, 민원, 기관 제출 문서 등 다른 형식을 명시적으로 요청하면 그 형식을 따르되, 법제처 1~3 구조는 법제처형 요청이 있을 때만 사용한다.

## 부적합·모호 질의

법제처 제출 적합성 보정은 **명시적 법제처 모드에만** 적용한다. 일반 법률검토형 요청에서는 구체적 건축물·허가·처분 등 실세계 사실이 포함되었다는 이유만으로 `법제처 법령해석 대상으로 부적합`하다고 출력하지 않는다.

명시적 법제처 모드에서 구체적 사실 해당 여부를 직접 묻고 필수 정보가 부족한 경우에는 첫 문장에서 법제처 법령해석 대상으로 부적합할 수 있음을 명시한다. 그 다음에만 필요한 정보 3~7개를 질문하고, 같은 응답에서는 초안 작성을 중단한다.
이 유형에서는 첫 문장을 반드시 “이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다.”로 작성한다. “요구할 수 있습니다”처럼 가능성만 표현하는 완곡한 문장으로 대체하지 않는다.

다음 세 경우를 구분한다.

1. **일반 법률검토형 + 미확인 자료:** 법적 쟁점과 판단구조가 특정되어 있으면 4단 형식으로 조건부 검토한다. 날짜·경과조치·조문 버전 등 미확인 사항은 결론의 조건으로 남긴다.
2. **질문-only 필수 정보 부족:** 규정·쟁점·대상 자체를 구성할 수 없으면 3~7개의 필요한 질문만 하고 그 응답에서는 중단한다. 초안을 병행하지 않는다.
3. **명시적 법제처 모드에서 형식상 부적합하지만 보정 가능한 질의:** 사실과 법적 근거가 충분하지만 구체적 사실판단·처분 위법성 판단 등 법제처 제출 형식상 부적합한 경우에는 설명 우선 병행형으로 쓸 수 있다.

설명 우선 병행형:

1. 부적합 사유와 보완 포인트
2. `참고용 원문형 초안 — 제출 적합성 낮음`
3. `권고 보정 초안 — 제출 권고`

구체적 사실인정·기존 처분의 위법성 판단을 직접 구하는 질문은 가능한 경우 **법규범의 객관적 의미·적용범위**를 묻는 형식으로 보정한다. 병행형 역시 Markdown으로 작성한다.

## 최종 Rendering Hard Gate

최종 사용자 문안을 보내기 직전에 `references/request-format.md`의 Hard Gate를 적용한다. 특히 기본 모드에서는 다음 네 조건을 모두 만족해야 한다.

1. 첫 비공백 줄이 정확히 `# 1. 질의요지`다.
2. 줄 시작이 `# `인 최상위 H1이 정확히 4개다.
3. 그 네 H1은 정확히 `# 1. 질의요지`, `# 2. 검토결론`, `# 3. 검토이유`, `# 4. 관련 법령 및 자료` 순서다.
4. 첫 H1 이전에 `결론적으로`, `검토 결과`, `이유는 다음과 같습니다`, Skill 활성화 설명 등 별도 사용자용 서론이 없다.

하나라도 실패하면 현재 초안을 **폐기**하고 올바른 4단 구조로 새로 렌더링한 뒤 같은 네 조건을 다시 검사한다. 법제처 모드도 동일하게 정확한 1~3 H1만 허용한다.

추가로 다음을 확인한다.

- **Answer-first check:** 기본 모드에서는 상세 해석 전에 `# 2. 검토결론`에서 결론 또는 조건부 결론이 제시되는지 확인한다.
- **Abstract fixture premise provenance check:** 가상·추상 fixture에서는 `# 2. 검토결론`과 `# 3. 검토이유`의 각 결정적 법적 전제가 사용자 제공 fixture 또는 현재 실행에서 실제 확인한 자료에 추적 가능한지 확인한다. 추적되지 않는 `통상적 의미`, `실질`, `조직·시설·인력·운영체계`, `변경승인·등록·지정` 등의 모델 생성 전제가 있으면 초안을 폐기하고 해당 전제를 제거하여 재렌더링한다.
- **Output Hygiene check:** `$law-interpretation-request`, `@jdipt`, `Skill activated`, `Plugin activated`, Skill/reference 파일 경로, 내부 contract 이름 등 실행·활성화 메타데이터가 최종 법률검토 문안에 포함되지 않았는지 확인한다.
- **URL provenance check:** 최종 답변에 포함된 각 URL이 현재 실행에서 MCP·웹·사용자 제공자료를 통해 실제 확인된 완전한 URL인지 하나씩 확인하고, 현행법 결론에 과거 시행본 링크를 현재 근거처럼 사용하지 않는다.

## Markdown 출력 규칙

- 모든 사용자용 최종 출력은 Markdown으로 작성한다.
- 기본 모드의 최상위 4개 항목은 반드시 H1(`#`)을 사용하고, `##`·`###`는 독립적인 복수 쟁점이나 필요한 하위 구조에만 사용한다.
- 특수 법제처 모드의 최상위 1~3 항목도 H1(`#`)을 기본으로 사용하고 하위 항목은 `##`, `###`를 사용한다.
- 표, 목록, 인용은 필요한 경우 Markdown 문법을 사용한다.
- 사용자가 별도 파일 형식이나 비-Markdown 형식을 명시적으로 요구하지 않는 한 HTML 전용 레이아웃이나 일반 텍스트 전용 레이아웃을 기본으로 사용하지 않는다.

## 인용과 링크

법령·판례·법령해석례·헌법재판소 결정례·행정규칙·자치법규 등 참고자료를 제시할 때는 `references/source-policy.md`에 따라 **자료명 또는 법령명·조문 텍스트 자체에 클릭 가능한 Markdown 인라인 하이퍼링크를 우선 적용**한다.

예:

```markdown
[「○○법」 제10조](실제로 확인한 공식 URL)
[법제처 법령해석례 25-0000](실제로 확인한 공식 URL)
```

MCP나 공식 사이트에서 실제로 확인한 URL만 사용한다. 정확한 URL을 확인하지 못한 경우 URL 패턴을 추정하지 말고 `[공식 링크 확인 필요]`라고 표시한다. 각주는 확인일이나 보충 출처정보가 필요한 경우에만 보조적으로 사용할 수 있다. Wikipedia 등 2차 자료는 방법론 참고에만 쓰고 법적 결론의 주된 근거로 삼지 않는다.

## 제출 전 주의문

모든 완성 초안 말미에 번호 없는 `※ 제출 전 확인`을 붙여 다음을 짧게 점검한다.

- 법률자문 확정 의견이 아니라 제출용 초안임
- 사실관계, 해석대상 조문, 최신 개정 여부 재확인
- 법제처 요청이면 소관 중앙행정기관 의견 첨부 필요 여부 확인
- 입증자료·관련 처분서·검토자료 등 첨부 누락 확인
- 구체적 사실판단이나 이미 이루어진 처분의 위법성 판단을 직접 구하는 형식은 법제처 해석 대상에서 제외될 수 있음

상세 원칙과 사례는 필요한 경우에만 `references/`에서 읽는다.

## Source Completeness / Counterevidence Gate

법적 쟁점 매핑 후 실체결론을 확정하기 전에 `references/source-policy.md`의 Source Completeness / Counterevidence Gate를 적용한다.

- 잠정 결론을 제한할 가능성이 있는 관련 하위법령·위임·준용·별표·별지서식을 필요한 범위에서 확인한다.
- `명문 제한 없음`, `규정 부재`, `적용 제외 없음`을 적극 결론의 근거로 사용할 때에는 이 확인을 생략하지 않는다.
- **공식 조문이 결론에 영향을 줄 수 있는 별표·별지서식을 직접 참조하면 그 실제 문언을 확인하거나 확인 실패 상태를 명시적으로 남기기 전에는 source resolution을 완료한 것으로 보지 않는다.**
- 별표·별지서식은 문언만으로 결론을 뒤집지 않고, 소속 법령, 위임근거, 실체·절차·신청양식 기능, 상위법과의 관계 및 실제 제한효과를 평가한다.
- 반대자료가 실제로 발견되면 그 의미와 적용 여부를 논증하고, 해결되지 않으면 조건부 결론 또는 `확인 필요`로 낮춘다.
- 별표·별지서식 직접 조회 도구가 보이지 않으면 기존 MCP 조사 절차의 `discover_tools`로 확인하고, MCP가 지원하지 않으면 도구 한계와 자료 부존재를 구분하여 공식 법령 페이지를 보조적으로 확인한다. 새 도구명을 만들지 않는다.
- 정부24·검색결과 요약·2차 안내자료는 원문 별표·별지서식의 실제 문언을 대체하지 않는다.

이 Gate는 별도의 사용자용 반대 의견 섹션을 만들거나 모든 사건에서 반대근거를 강제하는 규칙이 아니다.

- Never output a `law.go.kr/LSW/flDownload.do` URL when it includes the `flNm` filename parameter, even when that parameter is validly percent-encoded. Prefer a verified stable `lsInfoP.do` or parent page; otherwise write `[공식 링크 확인 필요]`.
