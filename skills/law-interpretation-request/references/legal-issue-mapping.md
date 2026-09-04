# 법적 쟁점 매핑 Gate

법령해석을 시작하기 전에 사용자의 질문을 법적 대상, 적용 규범, 사실관계와 문제 발생 지점으로 구조화한다. 이 단계는 결론을 미리 정하는 절차가 아니라, 어떤 규범을 어떤 사실에 연결하여 해석해야 하는지를 확정하는 내부 분석 Gate다.

## 1. 질문 요소 특정

사용자가 실제로 제공한 정보만 사용해 다음 요소를 특정한다.

- 주체
- 행위
- 대상
- 법적 상태 또는 분류
- 규모·수치·시점 등 적용기준에 영향을 주는 조건
- 적용 기준시점 후보(허가일·신청일·처분일·행위일·변경허가일·변경승인일 등)
- 관할 또는 적용 규범 범위
- 사용자가 확인하려는 법적 결과

필수 요소가 없고 그 누락이 결론에 영향을 주면 임의로 보충하지 않고 `확인 필요`로 남긴다. 단순 용어 정의만으로 충분한 질문이나 A/B/P/Q 같은 추상 논리 시나리오는 불필요하게 구체 사실관계로 확장하지 않는다.

사용자가 테스트·가상사례를 위해 법적 정의, 본칙, 예외, 사실관계를 **문장으로 직접 제공한 경우에는 그 제공 내용을 해당 검토의 전제로 보존한다.** 이미 제공된 전제를 다시 `자료 없음`, `문언 없음`, `정의 없음`으로 취급하지 않는다. 다만 사용자가 단순히 `필요한 규정은 모두 제공되었다고 전제해`처럼 내용 없이 메타적으로만 말한 경우에는 실제 규정 문언이 제공된 것으로 간주하지 않는다.

## 2. 적용 기준시점 확정

법적 의미·적용범위를 해석하기 전에 **어느 시점의 규범을 적용해야 하는지**를 먼저 확인한다.

- 현재의 법 적용을 묻고 별도의 과거 법적 효과 발생시점이 없으면 현행법을 기본으로 한다.
- 과거 허가·신청·처분·행위의 적법성 또는 법적 효과가 쟁점이면 그 시점에 유효한 법령 버전을 먼저 확인한다.
- 법령이 중간에 개정되었으면 공포일과 시행일을 구분하고, 부칙의 경과조치가 신·구법 적용범위를 달리 정하는지 확인한다.
- 최초 허가·승인과 후속 변경허가·변경승인처럼 서로 다른 시점의 행위가 있으면 하나의 기준시점으로 합치지 않고 각 행위의 적용 기준시점을 분리한다.
- 질문에 여러 날짜가 나오더라도 모든 날짜가 법적 기준시점인 것은 아니다. 해당 법적 효과와 직접 연결되는 시점을 특정한다.
- 적용 기준시점이 결론을 좌우하는데 제공·확인되지 않으면 임의로 현재 시점이나 가장 최근 날짜를 채택하지 않고 `확인 필요`로 관리한다.

추상 fixture에서 사용자가 시점 조건까지 직접 제공했다면 그 조건을 그대로 전제로 사용한다. 실제 법령의 시행일·경과조치를 추가로 검증하라는 요청이 없는 폐쇄형 fixture에서는 fixture 밖의 실제 개정연혁을 끌어오지 않는다.

## 3. 법적 정의·분류 확인

질문의 핵심 대상 또는 행위에 법정 정의가 있는지 먼저 확인하고, 필요한 범위에서 다음 순서로 법적 위치를 확정한다.

1. 직접 정의규정
2. 상위·하위 개념
3. 포함·제외 문구
4. 다른 조문 또는 다른 법령의 참조·분류 연결
5. 질문의 대상이 실제로 어느 법적 범주에 속하는지

정의가 쟁점 해결에 필요하지 않더라도 내부적으로 확인할 수 있다. 다만 최종 사용자 출력에서는 결론을 좌우하지 않는 정의를 장황하게 설명하지 않는다.

## 4. 적용 규범 지도

관련 조문을 단순 나열하지 말고 각 규정의 역할을 구분한다.

- 정의
- 본칙
- 적용요건
- 예외
- 특례
- 위임
- 적용 제외
- 준용
- 다른 법률의 관련 규정

- 신청·승인·신고·등록·변경승인 절차 규정
- 별표·별지서식
- 법정 신청 유형 또는 처분 유형
- 잠정 결론을 제한하거나 반대방향으로 작용할 수 있는 규정·서식

적용 규범 지도는 `## 2. 적용 기준시점 확정`에서 정한 시점에 유효한 법령 버전을 기준으로 작성한다. 현재 조문과 과거 조문을 함께 비교하는 경우에는 어느 문언이 어느 시점에 적용되는지 섞이지 않도록 분리한다.

모든 사건에서 별표·별지서식을 전수조사하지 않는다. 다음 중 하나에 해당하면 결론을 확정하기 전에 우선 확인한다.

- 허가·승인·신고·등록·변경승인 쟁점
- 본문이 하위규정 또는 서식에 세부 절차를 위임한 경우
- 잠정 결론이 명문 제한 없음 또는 규정 부재에 의존하는 경우
- 신설·증설·변경·신규·기존·전환 등의 분류가 결론을 좌우하는 경우

이 확인은 관련성이 예상되는 범위의 자료를 찾는 절차이며, 관련 없는 서식의 전수 확인이나 반대근거의 강제 생성을 뜻하지 않는다.

본칙과 예외, 원칙과 특례를 뒤바꾸지 않는다. 예외·특례는 명시적 근거와 적용요건을 별도로 확인한다.

## 5. 규정 관계 진단

둘 이상의 규정이 관련되면 다음 관계 중 무엇인지 먼저 판단한다.

- 동일 사항의 중복 규율
- 일반규정 / 특별규정
- 누적 적용
- 원칙 / 예외
- 특례 / 특례
- 준용
- 적용 제외
- 규율 공백
- 서로 다른 규율대상

단순히 서로 다른 법률에 규정되어 있다는 이유만으로 특별법 우선 또는 중복 적용을 단정하지 않는다. 각 규정의 규율대상, 법적 기능, 직접 규율 여부와 조문체계를 비교한다.

신·구법이 함께 언급되는 사건에서는 규정 간 관계뿐 아니라 **각 규정이 어느 기간의 법률관계를 규율하는지**를 분리한다. 개정 전 규정과 개정 후 규정이 문언상 충돌한다는 이유만으로 일반/특별 관계로 처리하지 않는다.

## Direct Defining Authority Gate

질문의 결론이 **법정 범주**·정의된 자격·지역·지위·시설 유형 또는 법정 예외의 성립 여부에 의존하고, 행정기관의 **운영기준**·안내·해설자료가 그 범주를 재서술하는 경우에는 최종 합성 전에 그 범주를 **직접 정의**하거나 예외와 효과를 직접 규정한 법률·시행령·조례·규칙의 원문을 합리적으로 가능한 범위에서 확인한다.

- 운영기준은 세부 집행요건과 절차를 확인하는 직접 자료가 될 수 있지만, 상위 규범이 부여한 **법적 효과**를 임의로 다른 효과로 바꾸는 근거가 되지 않는다.
- 직접 정의규정이 `지정`, `인정`, `승인`, `허가`, `적용 제외`처럼 특정 효과를 정하면 그 효과를 원문 동사 수준에서 매핑한다.
- 검색도구 오류나 원문 접근 실패는 `규정 없음`으로 취급하지 않는다. 직접 정의규정의 **원문 확인 실패**가 결론을 바꿀 수 있으면 운영기준의 요약만으로 특정 법적 효과를 재구성하지 않고, 해당 부분을 `확인 필요`로 보존하거나 다른 공식 원문 경로를 제한적으로 재확인한다.
- 이 Gate는 모든 상위규범을 전수조사하라는 의미가 아니다. 현재 issue의 정의·예외·법적 효과를 직접 정하는 규범까지만 추적한다.

## Material Source Dependency Closure Ledger

결론에 영향을 주는 각 issue는 조사 시작부터 최종 합성 직전까지 내부적으로 **material source dependency** 상태를 유지한다. 단순히 관련 조문 하나를 찾았다는 이유만으로 issue를 완료하지 않는다.

각 issue의 ledger에는 필요한 범위에서 다음 필드를 연결한다.

- `issue`
- `direct definition`: 결론에 쓰인 법정 범주·자격·지역·지위·시설 유형을 직접 정의하는 규정
- `main rule`: 해당 issue의 본칙
- `material boundary`: 수치·범위·대상·포함·제외 등 적용경계를 바꾸는 요소
- `exception`: 예외·특례 또는 별도 인정 경로
- `specific legal effect`: 지정·인정·승인·허가·적용제외 등 원문이 부여한 구체적 효과
- `direct source`: 위 명제를 직접 지지하는 공식 원문
- `status`: `OPEN` 또는 `CLOSED`

운영기준·안내·해설자료 또는 일반 적용조문에서 정의된 법적 범주를 발견했는데 그 범주가 다른 조문에서 정의되거나 예외·효과가 별도로 규정될 가능성이 현재 자료에서 합리적으로 드러나면, 그 **dependency를 직접 정의규정까지 추적**한다. 본칙을 확인했더라도 그 본칙이 사용하는 material category의 정의·경계·예외·법적 효과가 미해결이면 해당 issue는 `OPEN`이다.

`CLOSED`는 결론에 필요한 모든 material 필드가 현재 실행에서 직접 근거에 연결되었거나, 확인한 직접 원문상 해당 필드가 문제되지 않음이 확인된 경우에만 부여한다. 적용시점이 결론을 바꿀 수 있는 자료라면 현행성 또는 해당 기준시점도 함께 확인되어야 한다.

`OPEN`인 material 필드가 있으면 최종 합성 전에 누락 필드를 대상으로 **targeted retrieval retry**를 수행한다. 재검색은 누락된 정의·본칙·material boundary·exception·specific legal effect를 직접 규정한 원문까지의 **bounded** 추적으로 제한하며, 관련 없는 상위·하위 규범을 전수조사하지 않는다.

bounded 재확인 후에도 직접 원문을 확보하지 못하면 해당 field와 그 field에 의존하는 결론을 `확인 필요`로 낮춘다. 운영기준의 요약이나 모델의 일반지식·기억으로 `OPEN` 필드를 메워 `CLOSED`로 바꾸지 않는다.

확인된 `specific legal effect`는 최종 합성에서도 원문 동사 수준을 보존한다. 원문이 `지정`, `인정`, `승인`, `허가`, `적용제외`를 규정하면 이를 `완화`, `가능`, `검토 가능` 같은 포괄적 표현만으로 대체하지 않는다.

## Mutable Standard Temporal Status Gate

운영기준·고시·지침·행정규칙처럼 개정 가능한 기준이 면적·거리·도로·인접조건·비율 등 결론을 좌우하는 material proposition을 직접 지지하면, 조사 단계에서 그 기준의 **개정일**, **시행일** 또는 질의 기준일의 **현행성**을 확인 가능한 범위에서 함께 매핑한다.

- 공식 게시이력·첨부문서·개정표시 등에서 현재 적용되는 버전임이 확인되면 최종 합성에서도 `현행`, `질의일 현재`, 검증된 개정일·시행일 등으로 그 current/effective status를 보존한다.
- 문서명이나 URL **링크만으로** 현행성이 자동 증명되었다고 보지 않는다.
- 개정본이라는 사실만 확인되고 시행일 또는 질의일 현재 적용 여부가 확인되지 않으면 `현행성 확인 필요`로 남기고, 그 버전의 수치를 무조건적인 현행 기준으로 승격하지 않는다.
- 반대로 질의 기준일 현재 적용되는 버전이 직접 확인되었다면 불필요하게 `확인 필요`로 낮추지 말고 확인된 버전과 기준을 명시한다.

## Compound-Issue Coverage Gate

사용자 질문에 서로 독립적으로 결론을 바꿀 수 있는 **독립 판단요소**가 둘 이상 있으면 조사 전에 내부 issue 목록으로 분리하고, 최종 합성 직전까지 그 목록을 유지한다.

각 독립 판단요소에 대해 결론을 바꿀 수 있는 다음 항목을 연결한다.

- **본칙**
- **예외·특례**
- **적용시점** 또는 현행·과거 기준의 구분
- 사실관계의 충족·불충족·`확인 필요`
- 직접 근거가 된 규정 또는 자료

한 issue가 법령상 정의된 자격·지역·지위·시설 유형 같은 **defined eligibility category**에 의존하면 그 명칭만 남기지 않는다. 해당 category의 적용 여부를 바꿀 수 있는 **material boundary**와 **exception**을 그 issue의 일부로 매핑하고, 최종 합성에서도 필요한 범위에서 보존한다.

확인된 규정이 `지정·인정·승인`·허가·적용제외처럼 특정한 **specific legal effect**를 부여하면 그 법적 효과를 동사 수준에서 보존한다. 원문이 `지정할 수 있다`고 규정하는 것을 단순한 `완화 가능`과 같은 **generic relaxation**으로 치환하거나, `인정`·`승인`을 막연한 `가능`으로 축약하여 법적 효과를 바꾸지 않는다.

한 issue에서 확인한 본칙·예외·특례·적용시점이 다른 issue의 설명으로 대체되었다고 보지 않는다. 최종 합성 전에 각 독립 판단요소의 material proposition과 specific legal effect, 그리고 결론에 사용한 개정 가능한 기준의 현행성 상태가 결론 또는 검토이유에 반영되었는지 확인한다. 하나라도 누락되면 해당 초안을 완성본으로 취급하지 않고 누락된 issue를 복원한 뒤 다시 합성한다.

## 6. 사실관계와 요건 연결

각 핵심 법적 요건에 사용자 사실을 연결하고 다음 상태로 관리한다.

- `충족`: 제공되거나 확인된 사실로 요건 충족이 확인됨
- `불충족`: 제공되거나 확인된 사실로 요건 불충족이 확인됨
- `확인 필요`: 결론에 필요한 사실이 제공·확인되지 않음

사실관계와 요건을 연결할 때는 적용 기준시점에 유효한 규범의 요건을 사용한다. 최초 허가 당시 요건과 변경허가 당시 요건이 다르면 별개의 연결표로 보아야 하며, 현행 요건을 과거 사실에 자동 대입하지 않는다.

`확인 필요`를 임의 추정으로 `충족` 또는 `불충족`으로 바꾸지 않는다. 확인되지 않은 전제 때문에 결론이 달라질 수 있으면 조건부 결론으로 낮춘다.
`확인 필요`는 분석 실패나 자동 질문 전환 신호가 아니라 **유효한 요건 상태**다. 특히 추상 fixture가 특정 요건을 미확인으로 명시하면 그 상태를 그대로 보존하고, 나머지 충족 상태와 연결해 조건부 결론을 도출한다. 이 경우 미확인 요건의 구체적 내용이나 충족 여부를 알아내기 위한 질문으로 응답을 중단하지 않는다.

## 7. 문제 발생 지점

`적용 여부가 쟁점이다`, `해석이 필요하다`와 같이 결과만 반복하지 않는다. 서로 다른 결론을 가르는 실제 법적 연결부를 한 문장으로 특정한다.

좋은 문제 발생 지점은 다음 중 하나를 명확히 드러낸다.

- 질문의 대상이 본칙과 예외 중 어느 법적 범주에 속하는지
- 두 규정이 동일한 사항을 중복 규율하는지
- 특별규정이 해당 사항을 직접 규율하는지 또는 규율 공백이 있는지
- 특정 요건이 필요조건인지 충분조건인지
- 적용 제외·준용·특례가 실제로 이 사안까지 확장되는지
- 법령 개정 전후의 어느 규정이 최초 허가·승인과 후속 변경허가·변경승인에 각각 적용되는지
- 경과조치가 기존 권리관계 전체를 보호하는지, 특정 신청·행위 또는 변경되는 부분에만 종전 규정을 적용하는지가 결론을 가르는지
- 본문에는 제한 문언이 없지만 하위 규정·별표·별지서식에 다른 분류 문언이 있으면, 그 문언이 상위법의 법적 개념을 실제로 제한하는지 또는 단순 절차·서식상 분류인지가 결론을 가르는지 확인한다.
- 동일하거나 유사한 용어가 법률 본문과 시행규칙·서식에서 다른 수준의 의미로 사용될 가능성이 있으면 그 의미와 기능을 구분한다.

문제 발생 지점을 특정한 뒤 `interpretation-principles.md`의 해석방법을 적용한다.

## 8. 사용자 출력 비노출

이 Gate의 내부 mapping 라벨, 요건별 상태표, 규정관계 분류표, 적용 기준시점 후보표는 사용자가 논리감사나 분석표 공개를 명시적으로 요청하지 않는 한 사용자에게 그대로 노출하지 않는다. 최종 답변에서는 필요한 정의, 규정, 적용시점, 사실대입과 문제 발생 지점을 하나의 자연스러운 법률논증으로 통합한다.
## Material Source Dependency Closure Ledger

For each independent issue, maintain a ledger for the material evidence required before synthesis.

| Evidence slot | Required state |
|---|---|
| direct definition | verified from the authority that directly defines the legal category or effect |
| main rule | verified from the governing rule |
| material boundary | verified where the category scope or eligibility can change the result |
| exception | verified together with its exception conditions |
| condition | verified facts or legal conditions required for the proposition |
| procedure | required review, approval, designation, or other legal procedure |
| specific legal effect | preserved at the source verb level, such as designation, recognition, approval, permission, or exclusion |
| direct source | official original source identified and checked |
| temporal status | `CURRENT_CONFIRMED`, `HISTORICAL_CONFIRMED`, or `CURRENT_UNRESOLVED` |
| closure status | `CLOSED` only when all material fields are verified; otherwise `OPEN` |

Each issue has a `closure status`: `OPEN` while any material evidence slot is missing, ambiguous, or unverified; `CLOSED` only after every required slot is verified. The condition, procedure, and source-specific legal effect are synthesis inputs, not optional review notes. A material proposition with `OPEN` status cannot be treated as source-complete or used for unconditional synthesis.

Temporal status must be carried independently of the source's publication or amendment date. Use `CURRENT_CONFIRMED` only when the question-date applicable version and effective status are verified; use `HISTORICAL_CONFIRMED` for a verified prior version; use `CURRENT_UNRESOLVED` when current applicability, 시행일, repeal, supersession, or transitional treatment remains unresolved. Do not render `현재 적용` or `질의일 현재` from a recent document title alone.

When a slot is `OPEN`, record the missing evidence and perform a bounded targeted retrieval retry for that slot. Limit the retry to the directly defining authority, the relevant exception conditions, or the specific legal effect; do not turn it into unbounded hierarchy exploration. If the retry does not resolve the slot, preserve the proposition as `확인 필요` and lower dependent conclusions conditionally rather than inferring the missing rule. Do not replace a preserved specific effect with a generic relaxation, benefit, or vague possibility during final synthesis.

### Base / Exception Independence

Represent a main rule and its exception as separate propositions even when they concern the same subject:

```text
P1 = base rule
P2 = exception
P3 = P2 is exception-to P1
```

When P1 and P2 are material and `CLOSED`, both propositions and P3's relation are independently preserved in synthesis. Do not merge a base threshold and an exception threshold into one general relaxation, and do not treat coverage of P2 as coverage of P1. If P2's condition, procedure, or specific legal effect is `OPEN`, retain that unresolved state rather than borrowing it from P1.

## Mandatory Proposition Sentence Construction

After the ledger is closed, do not give a material CLOSED proposition to free-form summary first. Construct one mandatory proposition sentence for each material proposition and place those sentences in the draft before optional explanation.

The runtime ledger is activated only by the bundled `register_material_proposition` registry for the exact `session_id` and `turn_id`. Its structured fields are authoritative for the Stop reconciliation path; `render_contract` slot text is generated by the runtime and is not a model-supplied input. A turn without an authoritative registry record is unrelated and remains a no-op.

The sentence preserves the relation:

```text
[condition] + [procedure]
→ [legal actor] + [modality]
→ [legal action] + [legal object]
→ [resulting legal status/effect] + [polarity]
```

Use source/evidence anchors and `render_contract` slots as surface anchors when they are available. Before drafting any number, range, or practical consequence, perform source-clause extraction and copy the verified operative clause into the proposition record. If an equivalent paraphrase is uncertain, use the operative clause from `source_proposition` or `evidence_span` as a dedicated, attributed sentence. Legal effect comes before any number, range, or practical consequence.

The mandatory sentence is not satisfied by a threshold-only or generic-relaxation sentence. In particular, an exception sentence must retain its condition, required procedure, source-specific action, legal object, resulting status/effect, and relation to the base proposition. Explanatory text may add a range or practical meaning only after those slots exist.
