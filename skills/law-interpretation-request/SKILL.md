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
- Temporal unknown neutrality hard stop: **조건부 결론은 확률적 우세 판단이 아니다**. If a permit date, amendment effective date, modification application/disposition date, transitional provision, or change scope that can alter old/new-law selection is unresolved, do not say one branch is more likely. Do not use `가능성이 크`, `가능성이 높`, `대체로`, `통상`, `원칙적으로 신법`, `적용될 것으로 보`. State the competing if/then branches neutrally and say **어느 분기가 성립하는지는 현재 판단할 수 없다** until the material dates/transitional provisions/change scope are verified.
- Abstract source-form neutrality hard stop: **미확인 `신설 / 증설` 의미는 승인 방향을 지지하거나 반박하는 근거가 아니다**. Until the meaning, legal function, delegation basis, and relationship to the parent rule are resolved, the outcome sentence is **현재 전제만으로 승인 가능 여부를 판단할 수 없다**. Do not use `승인 가능성을 뒷받침`, `승인 가능성이 높`, `승인받기 어렵`, `승인 가능성은 열려`.
- Authority comparison hard stop: when 법제처 해석례 and 대법원 판결 are compared, explicitly distinguish 법제처 해석례 as 행정부의 공식 해석 from 대법원 판결 as 사법적 판단, and state that 법제처 해석례를 법원 확정판결과 같은 법적 구속력으로 취급하지 않는다. Compare the statutory versions and material wording before carrying an older interpretation forward.
- Abstract or fictional fixtures are closed-world inputs. A self-contained legal inference is also an abstract fixture. Use only supplied premises and sources actually verified in the current run.
- Same-term conflict hard stop: if competing views use the same legal term with different scopes without a supplied or verified common definition, identify the inconsistency and keep the substantive conclusion unresolved. 동일 용어 충돌을 식별한 것 자체가 요청된 법적 관계 검토의 결과일 수 있다.
- Special-rule completeness hard stop: when the question names a specific statutory or regulatory named scheme, program, permit category, use, or facility, finding a general rule is not source-complete. Before synthesis, verify whether a directly governing special rule on the same matter is reasonably implicated by the named context or verified sources, and compare its regulated subject, legal function, conditions, and effect with the general rule. Do not stop merely because the general rule already answers part of the question, but do not exhaustively search unrelated special regimes.
- Context-branching hard stop: when the same legal subject can be governed by materially different rules depending on jurisdiction, regulated program, permit category, subtype, or special statutory status and that selector is unresolved, do not collapse the answer into one universal rule. Identify the unresolved selector, map the material branches supported by verified sources, and preserve those conditional branches without assuming which branch applies. Do not exhaustively enumerate remote or hypothetical regimes that are not reasonably implicated by the question or the sources found.
- Direct defining authority hard stop: when a material conclusion depends on a statutory category, exception, or **specific legal effect** and an **operating standard**, guidance, notice, or summary merely restates that rule, do not treat the restatement as source-complete. Before synthesis, resolve the statute, regulation, ordinance, or rule that **directly defines** the category, exception, or effect when reasonably accessible. If the directly governing **original source** cannot be verified after **bounded** attempts, do not convert the restatement into a generic relaxation or inferred legal effect; preserve that proposition as `확인 필요` or clearly attribute it as guidance-level only. This bounded check ends at the directly defining authority and does not require exhaustive hierarchy search.
- compound-issue coverage hard stop: when the question contains multiple independently outcome-determinative issues, keep an internal issue list through research and synthesis. For each issue, preserve any material main rule, exception or special rule, temporal applicability, unresolved condition, and supporting authority. If an issue depends on a **defined eligibility category**, preserve the category's material boundary and exception rather than leaving the category as an opaque label; do not treat coverage of one issue as coverage of another.
- Synthesis coverage hard stop: if research identifies a main rule and exception, a general rule and directly governing special rule, or current and historical standards that can change the conclusion, preserve that relationship. A material proposition and its **specific legal effect** may not disappear or be reduced to a **generic relaxation** or vague possibility; unresolved applicability remains `확인 필요` or conditional.
- Direct defining authority hard stop: when a category, exception, operating standard, or specific legal effect is material, verify the directly defining original source after bounded attempts. If it cannot be verified, preserve the proposition as `확인 필요` rather than inventing a legal effect.
- Material source dependency closure hard stop: before synthesis, maintain a per-issue ledger for every material proposition. The ledger tracks direct definition, main rule, material boundary, exception condition, required procedure, specific legal effect, direct source, temporal status, and closure status.
- A material field is `OPEN` until its evidence is verified from the directly defining original source; mark it `CLOSED` only when that field is resolved. For each `OPEN` field, run a bounded targeted retrieval retry limited to the directly defining source, exception conditions, and specific legal effect. If it remains unresolved, preserve `확인 필요` in final synthesis and do not convert an OPEN proposition into a confirmed effect.
- Temporal status is one of `CURRENT_CONFIRMED`, `HISTORICAL_CONFIRMED`, or `CURRENT_UNRESOLVED`; a recent title, posting date, or amendment date alone cannot render a proposition current.
- Runtime registry activation (MUST): the first successful bundled `register_material_proposition` write is the authoritative activation record for the exact `session_id` and `turn_id`, and sets `jdipt_active=true`. The registry accepts structured proposition fields only; the model must not supply `mandatory_render_clause`, which is generated deterministically from the registered fields.
- Runtime state isolation (MUST): keep the compact ledger and bounded `repair_count` only under `PLUGIN_DATA/synthesis-runtime/<session_id>/<turn_id>.json`; an unrelated turn with no authoritative record is a no-op and must not activate this Skill. Never store secrets, a transcript, or a full source document in runtime state.
- Synthesis Integrity Gate (MUST): before final answer, use this exact execution order: `Material Proposition Ledger` → `mandatory proposition sentence construction` → `mandatory slots in draft` → `explanatory synthesis` → `proposition-to-draft reconciliation` → `one targeted repair` → `one bounded re-check` → `final rendering`. After the mandatory slots are present, compose the draft synthesis.
- Mandatory Proposition Sentence (MUST): for every material `CLOSED` proposition, construct and insert an independent sentence slot in the final answer before any free-form explanatory synthesis. This is an output slot, not a private checklist: in `# 2. 검토결론` or `# 3. 검토이유`, write the source-equivalent legal-effect sentence first. The legal effect before numbers, ranges, and practical explanation is mandatory.
- Mandatory output gate: even when a specific exception or special effect is only a supporting issue rather than the question's headline, its mandatory sentence must be copied into the final answer. Do not let a headline conclusion or a range summary replace that slot.
- Material Proposition Schema: carry `proposition_id`, `materiality`, `subject / legal actor`, `condition`, `procedure`, `modality`, `legal_action`, `legal_object`, `resulting_status_or_effect`, `polarity`, `relation_to_base_or_exception`, `direct_source`, `evidence_span / source_proposition`, `temporal_status`, `closure_status`, `operative_verb_lexeme`, and `mandatory_render_clause`.
- Source-specific effect preservation (MUST): a relation such as “after the stated condition and procedure, an actor may designate an object as a legal status” must retain its condition-effect relation. The final answer must preserve the source-specific effect: its legal action and resulting status/effect, including approval and exclusion, must remain recoverable; threshold alone is not coverage.
- Exact-effect default path: when a CLOSED material proposition has a specific legal action/effect, use `mandatory_render_clause`, then `source_proposition`, then `evidence_span`, and copy that operative relation into the final answer before writing any free paraphrase. Never replace the operative clause with a weaker generic verb.
- Source-clause extraction (MUST): before drafting any number, range, or practical consequence tied to a CLOSED proposition, extract the verified source sentence that states its operative legal relation and copy the verified operative clause into the proposition record. Preserve the source's operative verb stem when it is unambiguous: do not use `인정` for `지정`, and do not use `완화` for a source-specific legal action. If the clause cannot be verified, keep the proposition OPEN and render `확인 필요`; do not fill the slot with a generic benefit or possibility.
- Mandatory sentence shape: replace each bracketed field from the verified proposition before drafting: `[condition] + [procedure] -> [legal actor] [modality] [legal action] [legal object] -> [resulting legal status/effect]`. If a material field cannot be verified, mark the proposition `OPEN` and write a neutral `확인 필요` statement instead of a confirmed relation.
- Range/effect coupling hard stop: whenever the final answer mentions an exception range, threshold, or other changed practical value, first write the dedicated sentence that states the source-specific condition, procedure, legal object, resulting legal status/effect, and operative legal action. `[range]까지 완화` alone is not a valid mandatory sentence, even when the range is only a supporting issue.
- Base/exception independence (MUST): when a main rule and an exception are both material, use a separate sentence for the base rule and a separate sentence for the exception. The exception sentence must include its procedure and source-specific legal effect and must not be absorbed into a range or threshold. A dedicated sentence or bullet is required for each CLOSED proposition.
- Range-only paraphrase is a material mismatch: a number, threshold, source link, or generic relaxation is not proposition coverage. A range-only paraphrase that omits the source-specific designation/approval/exclusion action must be repaired.
- Every CLOSED material proposition must be represented in the final answer by an equivalent legal relation; a numeric value or generic statement that an exception exists is not coverage. The invariant is written as ``Every `CLOSED` material proposition must be represented``.
- Reconciliation hard stop: after the mandatory slots and explanatory synthesis are composed, check proposition presence, condition, procedure, modality, legal action, legal object, resulting legal status/effect, polarity, and base/exception relation. final rendering is forbidden until every CLOSED material proposition is represented by an equivalent legal relation in the output, not merely in the ledger or explanation plan.
- Repair hard stop: on any material mismatch, perform one targeted repair from `mandatory_render_clause` → `source_proposition` → `evidence_span` → source-equivalent close paraphrase, then one bounded re-check. Do not use a new free-form paraphrase as the first repair.
- Stop-hook bound (MUST): the Codex `Stop` hook may return one `decision: "block"` repair request. If the subsequent Stop event still fails reconciliation, or `stop_hook_active` is already true, return the documented fail-closed stop response; never request unbounded continuation.
- OPEN fail-safe: an OPEN proposition must remain `확인 필요` or a neutral conditional statement and must not be promoted to a confirmed legal effect merely to satisfy coverage.
- MOLEG suitability correction applies only in explicit MOLEG request mode.
- Question-only mode is reserved for an input so incomplete that the legal issue, target rule, and object of review cannot meaningfully be identified. Missing material facts that prevent a definitive conclusion do not by themselves trigger question-only mode in a general legal review.
- **E02 precedence:** 형식상 부적합 + 정보 부족이면 질문-only가 법제처 3-H1보다 우선한다. 부적합 고지 후 객관적 법령 의미·적용범위·요건·근거조항 문제로 재구성할 점을 설명한다. 필요한 질문 3~7개만 출력하고 즉시 중단한다. 이 응답에는 H1 제목, 법제처 1~3 초안, `※ 제출 전 확인`, 출처 링크를 출력하지 않는다.
- Default completed output uses exactly four H1 headings: `# 1. 질의요지`, `# 2. 검토결론`, `# 3. 검토이유`, `# 4. 관련 법령 및 자료`.
- Explicit MOLEG request mode uses exactly three H1 headings: `# 1. 질의요지`, `# 2. 해석대상 법령조문 및 관련 법령`, `# 3. 대립되는 의견 및 이유`, followed by a non-H1 `※ 제출 전 확인`, **except when the E02 question-only precedence rule applies**.
- URLs with empty query-parameter values are incomplete when the blank value is a critical identifier or the URL ends in `=`. Do not reject an otherwise verified official URL solely because a non-identifying optional parameter is blank.
- Every percent sign in a final URL must begin a valid percent escape: `%` followed by exactly two hexadecimal digits.
- `lsBylInfoPLinkR.do` + `lsNm` is an unstable user-facing annex-link class and must not be emitted. Use a verified identifier-based stable source page or `[공식 링크 확인 필요]`.
- Do not output `$law-interpretation-request`, `@jdipt`, Skill/Plugin activation metadata, reference paths, or internal contract names.

## 응답 모드 라우팅

응답 형식은 정보 부족 판단보다 먼저 확정한다.

### 일반 법률검토형

`검토해줘`, `적용되는지`, `어느 기준이 적용되는지`, `어떻게 평가해야 하는지`처럼 법적 의미·적용관계를 묻고 검토대상 행위·상태·관계가 식별되면 일반 법률검토형이다.

**검토 가능한 법적 쟁점이 특정되어 있으면 자료 부족만으로 질문-only 모드로 전환하지 않는다.** 법령명·정확한 날짜·개정 전후 문언·경과조치가 미확인이어도 확인된 구조를 분석하고 `확인 필요` 또는 조건부 결론으로 낮춘다.

건축허가 후 관련 법 변경과 강화기준의 변경허가 적용 여부가 제시되면 법령명·허가일·시행일·신청일이 미확인해도 쟁점이 특정된 것이므로 **질문-only가 아니라 기본 4단** 형식으로 검토한다. 질문 목록만 출력하면 실패하므로 반드시 네 H1을 렌더링한다. **Temporal routing hard stop**에 따라 최초 허가와 변경허가를 분리하고 시행일·경과조치·변경범위를 `확인 필요`로 둔다.

이 temporal unknown 상태에서 **조건부 결론은 확률적 우세 판단이 아니다**. 허가일·개정법 시행일·변경허가 신청/처분일·경과조치·변경범위 중 미확인 사항이 어느 법령 버전이 적용되는지를 바꿀 수 있으면 `가능성이 크`, `가능성이 높`, `대체로`, `통상`, `원칙적으로 신법`, `적용될 것으로 보` 같은 방향성 표현을 쓰지 않는다. `경과조치가 종전 규정 적용을 정하면 종전 기준`, `신법 적용요건이 충족되고 경과조치가 없으면 신법 기준`처럼 조건 분기를 대칭적으로 제시하고 **어느 분기가 성립하는지는 현재 판단할 수 없다**고 명시한다.

### 질문-only 모드

**질문-only 모드는 법적 쟁점·대상·규정 중 무엇을 검토해야 하는지조차 구성할 수 없는 경우에만** 사용한다. 대표 예시는 `이 규정 해석 질의서 써줘`처럼 규정·쟁점·사실이 모두 특정되지 않은 요청이다. 이때 필요한 질문만 3~7개 하고 **질문만 하고 그 응답에서는 중단한다**. 그 응답에서는 초안을 작성하지 않는다.

명시적 법제처 모드에서도 예외적으로 **구체적 사실판단·처분 위법성 판단을 직접 묻는 형식상 부적합 요청이면서 실제 보정 초안에 필요한 법령명·조문·핵심 사실이 부족하면**, **형식상 부적합 + 정보 부족이면 질문-only가 법제처 3-H1보다 우선**한다. 이 경우 **부적합 고지 후 객관적 법령 의미·적용범위·요건·근거조항 문제로 재구성할 점을 설명한다. 부적합 고지 후 필요한 질문 3~7개만 출력하고 즉시 중단**한다. **이 응답에는 H1 제목, 법제처 1~3 초안, `※ 제출 전 확인`, 출처 링크를 출력하지 않는다**.

### 명시적 법제처 모드

사용자가 `법제처 법령해석요청서`, `법제처 제출용`, `법제처에 질의`, `질의요지·갑설·을설`을 명시적으로 요구할 때만 사용한다. 구체적 사실판단·처분 위법성 판단을 직접 요구하면 제출 적합성 문제를 먼저 설명하고 필요한 경우 질의를 객관적 법규범의 의미·범위로 보정한다.

구체적 사실판단·처분 위법성 판단을 직접 요구하면서 필수 정보가 부족한 경우에는 **첫 문장에서 법제처 법령해석 대상으로 부적합할 수 있음을 명시한다**. 이 유형에서는 첫 문장을 반드시 “이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다.”로 작성한다. 이어서 위 E02 질문-only 우선 규칙을 적용하며, 정보가 충분해진 후에만 법제처 1~3 초안을 작성한다.

### 추상 fixture 모드

가상 법령, A/B/P/Q, 동일 용어 충돌, 미확인 요건 상태, 자족적 법적 논증은 제공된 전제 자체를 검토대상으로 본다. 추상 fixture에서 `정보 없음`, `미확인`, `확인 필요`가 제공되면 **미확인 상태 자체를 제공된 전제로 취급한다**. 실제 법령명이나 사건번호가 없다는 이유로 질문-only로 전환하지 않는다.

별지 신청유형이 `신설 / 증설`로만 제시되고 `신설`의 법적 의미·별지의 법적 기능·위임관계가 해결되지 않았다면 **미확인 `신설 / 증설` 의미는 승인 방향을 지지하거나 반박하는 근거가 아니다**. `# 2. 검토결론`은 **현재 전제만으로 승인 가능 여부를 판단할 수 없다**는 중립 문장으로 유지하고 `승인 가능성을 뒷받침`, `승인 가능성이 높`, `승인받기 어렵`, `승인 가능성은 열려` 같은 방향성 표현을 사용하지 않는다.

법제처 해석례·대법원 판결·개정문언의 관계가 제공되면 사건번호·해석례 번호·법률명이 없어도 식별 가능한 추상 fixture로 보고 **식별번호가 없어도 기본 4단 추상 검토**를 작성한다.

## 법적 쟁점 매핑 Gate

`references/legal-issue-mapping.md`를 사용한다.

- 대상·행위·법적 상태 또는 분류를 먼저 특정한다.
- 정의, 본칙, 적용요건, 예외, 특례, 위임, 준용, 적용 제외를 역할별로 정리한다.
- 동일 사항의 중복 규율인지 **규율 공백**인지 구분한다.
- 복수의 독립 판단요소가 있는 질문은 compound-issue coverage를 유지하여 각 issue의 본칙·예외·특례·적용시점·`확인 필요` 상태가 최종 합성에서 누락되지 않게 한다.
- issue가 **defined eligibility category**에 의존하면 그 category의 적용 여부를 바꾸는 material boundary와 exception을 함께 매핑한다.
- 확인한 규정의 **specific legal effect**가 지정·인정·승인·허가·적용제외 등으로 특정되면 이를 단순한 **generic relaxation**이나 막연한 가능성으로 바꾸지 않는다.
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

- 질문이 특정 제도·사업·허가유형·용도·시설을 지칭하면 일반규정 확인으로 조사를 종료하지 않고, 같은 사항을 직접 규율하는 특별규정이 있는지 확인한다.
- 관할·제도·허가유형·세부용도·특별지위에 따라 같은 사항의 적용규정이 달라질 수 있고 그 selector가 미확정이면 하나의 보편 기준으로 단정하지 않고, 현재 자료에서 합리적으로 확인되는 적용경로를 조건부로 분리한다.
- 잠정 결론을 제한할 수 있는 하위법령·위임·준용·**별표**·**별지서식**을 필요한 범위에서 확인한다.
- `명문 제한 없음`, **규정 부재**를 적극 결론의 근거로 삼기 전에 반대 규정과 참조자료를 확인한다.
- 별표·별지서식의 **위임근거**와 **실체·절차·신청양식 기능**을 구분한다.
- 실제 반대자료가 결론을 제한하면 **조건부 결론**으로 낮춘다.

## Fail-closed Hard Gates

1. **Referenced Source Resolution Hard Gate**: 공식 조문이 결론에 영향을 줄 수 있는 별표·별지서식·부표·부록을 직접 참조하면 실제 문언을 확인한다. 확인하지 못하면 `참조자료 확인 실패`로 남기고 확정 결론을 내리지 않는다. 정부24·검색요약은 원문을 대체하지 않는다.
2. **Abstract Fixture Closed-World Hard Gate**: 추상 fixture에서는 제공되지 않은 정의·요건·절차·법적 효과를 만들지 않는다. `설립승인사항 변경`과 `기존 일반 건축물의 최초 전환`, `신설`과 `건축물 신축`을 근거 없이 동일 개념으로 치환하지 않는다. 특히 `신설 / 증설` 관계가 미해결이면 현재 전제만으로 승인 가능 여부를 판단할 수 없다고 유지한다.
3. **최종 Rendering Hard Gate**: 기본 모드의 **첫 비공백 줄**은 `# 1. 질의요지`여야 하며 네 H1의 문자열·순서·개수가 정확해야 한다. 어긋나면 초안을 **폐기**하고 재렌더링한다.

## 내부 논리검증 Gate

최종 답변 전 `references/logic-validation.md`를 사용한다.

- 논증을 전제와 결론으로 분해하고 **BLOCK** 조건을 확인한다.
- `전건 부정`, `후건 긍정`, 거짓 양자택일, 전제 누락을 탐지한다.
- 삼단논법 등에 정확히 맞지 않으면 `비정형 자연어 추론`으로 처리한다.
- 필요조건과 충분조건을 구분하고 **선택지 완전성**을 확인한다.
- 형식적 타당성과 `사실성 미확인`을 분리한다.
- 법제처 모드에서는 **갑설과 을설을 각각 독립 검증**한다.
- 갑설·을설의 **동일한 법률용어** 의미가 근거 없이 달라지면 Same-term conflict hard stop을 적용한다.
- 조사 중 확인한 본칙/예외, 일반/특별, 현행/과거 구분 중 결론에 영향을 주는 material proposition이 최종 문안에서 빠지면 BLOCK하고 재작성한다.
- 조사 중 확인한 specific legal effect가 최종 문안에서 generic relaxation이나 다른 법적 효과로 치환되면 BLOCK하고 원래 효과를 복원한다.
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

사용자가 명시적으로 `법제처 법령해석요청서` 등을 요구할 때만 다음 세 H1을 사용한다. **형식상 부적합 + 정보 부족** 질문-only 예외가 성립하면 이 3-H1 구조를 만들지 않는다.

```markdown
# 1. 질의요지
# 2. 해석대상 법령조문 및 관련 법령
# 3. 대립되는 의견 및 이유
```

법제처 1~3 모드에서는 **4~8 항목을 생성하지 않는다**. 필요하면 `## 가. 해석대상 법령조문`, `## 나. 관련 법령`, `## 가. 갑설`, `## 나. 을설`을 사용한다.

## 인용·URL 정책

`references/source-policy.md`를 따른다.

- 공식자료는 **클릭 가능한 Markdown 인라인 하이퍼링크**로 표시한다.
- 현재 실행에서 실제 확인한 완전한 URL만 사용하고 URL 패턴을 추측하지 않는다.
- `URLs with empty query-parameter values are incomplete` 규칙은 **핵심 식별자가 비어 있거나 URL 끝이 `=`인 경우**에 적용한다.
- `law.go.kr/LSW/flDownload.do` + `flNm` 링크는 사용하지 않는다.
- **`lsBylInfoPLinkR.do` + `lsNm` 링크는 사용자 출력에 사용하지 않는다.** 안정적인 식별자 기반 원문 링크가 현재 실행에서 확인되지 않으면 `[공식 링크 확인 필요]`로 처리한다.
- **Output Hygiene check**: 내부 Skill/Plugin 정보와 reference 경로를 출력하지 않는다.
- **URL provenance check**: 최종 답변 직전에 각 URL의 실제 확인 여부를 검사한다.

## 최종 Rendering Hard Gate

기본 모드에서는 다음을 모두 확인한다.

1. **첫 비공백 줄**이 정확히 `# 1. 질의요지`다.
2. H1은 정확히 네 개이며 위 문자열과 순서 그대로다.
3. `# 2. 검토결론`에 확정 또는 조건부 결론이 있다.
4. Output Hygiene check와 URL provenance check를 통과한다.
5. URL에 `lsBylInfoPLinkR.do` + `lsNm`이 있으면 해당 링크를 제거하거나 현재 실행에서 확인한 안정적인 식별자 기반 링크로 교체한다.
6. 조사·논리검증에서 결론에 사용한 material proposition과 본칙/예외·일반/특별·현행/과거 구분, 그리고 결론을 바꾸는 specific legal effect가 `# 2. 검토결론` 또는 `# 3. 검토이유`에 보존되어 있다.

하나라도 실패하면 **그 초안은 폐기**하고 올바른 구조로 다시 작성한다. **재렌더링한 결과**에도 같은 검사를 다시 적용한다.

위 **형식상 부적합 + 정보 부족** 질문-only 예외는 이 H1 Rendering Gate 대상이 아니다. 해당 예외에서는 H1 자체가 실패다.

## MCP 조사 절차

Korean Law MCP가 연결되어 있으면 공식 법령 데이터 조회를 우선한다.

1. `search_law`로 법령명·식별자를 찾는다.
2. `get_law_text`로 최종 인용 조문을 확인한다.
3. `search_decisions` → `get_decision_text`로 판례·법제처 해석례 본문을 확인한다.
4. material proposition을 식별할 때마다 bundled `register_material_proposition`에 구조화된 필드와 `OPEN`/`CLOSED` 상태를 등록한다. `mandatory_render_clause`는 입력하지 않는다.
5. 필요한 도구가 직접 보이지 않으면 `discover_tools` → `execute_tool`을 사용한다.
6. 질문이 특정 제도·사업·허가유형·용도·시설을 지칭하면 일반규정 확인 후에도 같은 사항을 직접 규율하는 특별규정을 추가 탐색한다.
7. 관할·제도·허가유형·세부용도·특별지위가 미확정이고 검색 중 서로 다른 적용기준이 확인되면 그 차이를 선택하는 selector와 적용경로를 추가 확인한다.
8. 최종 인용은 필요하면 `legal_analysis`로 검증한다.

상세 작성 규칙, 적합성 보정, 사례 패턴은 `references/request-format.md`, `references/eligibility-checklist.md`, `references/case-patterns.md`, `references/baseline-document-policy.md`를 필요한 경우에만 읽는다.
