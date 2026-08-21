# JDIPT Repository Instructions

## 목적
이 저장소는 대한민국 법령해석요청 업무용 ChatGPT/Codex Plugin, Skill, `korean-law-mcp` 연동 설정을 관리한다.

## Plugin 패키징 원칙
- 저장소 루트 자체가 JDIPT Plugin 패키지다.
- `.codex-plugin/plugin.json`은 필수 진입점이며 Plugin ID는 `jdipt`로 유지한다.
- Plugin에 포함되는 Skill의 단일 원본은 `skills/law-interpretation-request/`에서 관리한다.
- 같은 Skill을 `.agents/skills/law-interpretation-request/`에 복제하지 않는다.
- manifest의 `skills` 경로는 `./skills/`로 유지한다.
- `.codex-plugin/plugin.json`의 `version`은 `package.json`의 `version`과 일치시킨다.
- `korean-law-mcp` 소스를 JDIPT에 vendor하지 않는다.
- 현재 Plugin은 Skill-first 패키지다. ChatGPT 웹용 MCP App은 실제 원격/등록 MCP 연결과 App ID가 확보된 뒤에만 `.app.json`과 manifest `apps` 필드를 추가한다.
- 확인되지 않은 App ID, MCP URL, manifest 필드를 임의로 만들지 않는다.
- 비밀값(`LAW_OC`, 토큰 등)은 절대 커밋하지 않는다. 로컬 Codex MCP는 OS 환경변수와 `env_vars = ["LAW_OC"]`를 사용한다.

## 법령해석 변경 원칙
- 법령 데이터 조회 기능을 JDIPT 안에 중복 구현하지 않는다. 우선 `korean-law-mcp`의 공개 도구를 사용한다.
- 업스트림 MCP의 내부 API에 직접 결합하지 말고 MCP 도구 인터페이스에 의존한다.
- 기본 처리 순서는 **Legal Issue Mapping → Legal Interpretation → Logic Validation → Answer Rendering**으로 유지한다.
- `skills/law-interpretation-request/references/legal-issue-mapping.md`에서 법적 대상·행위, 법적 정의·분류, 적용 규범의 역할, 규정 관계, 사실대입과 문제 발생 지점을 먼저 특정한다.
- 관련 규정이 둘 이상이면 동일 사항의 중복 규율인지, 일반/특별 관계인지, 누적 적용인지, 원칙/예외인지, 적용 제외·준용인지, 규율 공백인지, 서로 다른 규율대상인지 구분한다.
- 사실과 요건의 연결은 확인된 자료에 근거해 `충족`, `불충족`, `확인 필요`로 관리하고 확인되지 않은 사실을 임의로 보충하지 않는다.
- 사용자가 가상 규정·정의·본칙·예외·사실을 문장으로 직접 제공한 경우에는 해당 검토 전제로 보존하고 이미 제공된 내용을 다시 없다고 요구하지 않는다.
- `적용 여부가 쟁점이다`처럼 질문을 반복하는 수준에서 멈추지 않고, 서로 다른 결론을 가르는 실제 법적 연결부를 **문제 발생 지점**으로 특정한다.

### 정보 부족 처리
- 법령명·조문·핵심 사실 등 실체결론 또는 초안 작성에 필수적인 정보가 부족하면 필요한 질문 3~7개만 하고 **그 응답에서는 초안 작성을 중단**한다.
- 정보 부족 상태에서 기본 4단 초안, 법제처 원문형 초안, 권고 보정 초안을 함께 만들지 않는다.
- 반대로 정보는 충분하지만 개별 사실판단·처분 위법성 판단처럼 법제처 제출 형식상 부적합한 경우에는 이유 설명과 보정 초안을 병행할 수 있다.

### 기본 법률검토형
- 별도 형식 지시가 없는 법령해석·검토 답변은 아래 **정확한 H1 4단 구조**를 사용한다.

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

- `# 1. 질의요지` 이전에는 별도 서론·요약·검토대상 설명·Skill 호출문자열을 작성하지 않는다.
- `# 1. 질의요지`에는 사용자가 무엇을 묻는지와 결론에 필요한 최소 사실만 정리한다. 제공되지 않은 사업목적·처분경위·기관입장 등을 사실처럼 추가하지 않는다.
- `# 2. 검토결론`에서는 내부 분석과 논리검증으로 확정된 결론을 상세 검토이유보다 먼저 1~3문장으로 제시한다. 결론이 사실 전제에 따라 달라지면 조건부로 표시한다.
- `# 3. 검토이유`에서는 법적 정의·분류, 본칙·예외·특례, 규정 관계, 사실관계 대입, 문제 발생 지점, 문언·체계·목적·연혁 등을 하나의 연결된 법률논증으로 작성한다.
- **단일 쟁점**에서는 `법적 정의`, `적용 규정`, `사안 적용`, `문제 발생 지점`, `해석`, `결론`을 각각 별도 소제목으로 기계적으로 분리하지 않는다.
- `# 3. 검토이유`의 하위 소제목은 서로 독립적으로 판단 가능한 복수의 법적 쟁점이 있을 때만 사용한다. 각 쟁점 내부에서는 다시 분석 단계별 소제목으로 과분할하지 않는다.
- `# 3. 검토이유` 말미의 결론은 `# 2. 검토결론`과 실질적으로 일치해야 한다.
- `# 4. 관련 법령 및 자료`에는 실제 논증에 사용한 법령·조문·판례·법령해석례·행정규칙·첨부자료만 정리한다.
- 기본 모드에서 구 구조 `# 1. 요청취지` → `# 2. 질의 배경 및 사실관계` → `# 3. 관련 법령 및 조문` → `# 4. 해석상 쟁점` → `# 5. 법률검토` → `# 6. 첨부자료`를 사용하지 않는다.

### 법제처 제출용
- `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설` 등 전용 형식을 사용자가 명시적으로 요청한 경우에만 아래 정확한 H1 1~3 구조를 사용한다.

```markdown
# 1. 질의요지
# 2. 해석대상 법령조문 및 관련 법령
# 3. 대립되는 의견 및 이유
```

- `# 2. 질의배경`, `# 2. 관계 법령`, `# 3. 의견` 등으로 계약 제목을 바꾸지 않는다.
- 4~8 항목은 생성하지 않는다.

### Output Hygiene 및 URL provenance
- 모든 사용자용 최종 답변은 Markdown으로 작성한다.
- `$law-interpretation-request`, `@jdipt`, `Skill activated`, `Plugin activated` 같은 호출·활성화 메타데이터를 최종 법률검토 문안에 노출하지 않는다.
- Skill/reference 파일 경로, 내부 contract 이름, validator 메타데이터를 사용자가 구현 설명을 요구하지 않는 한 출력하지 않는다.
- A/B/P/Q 같은 명칭을 사용자가 직접 제공한 경우 그 명칭을 일반 문장에서 다시 언급하는 것은 허용한다. 모델이 내부적으로 생성한 논리식·점수표·오류분류명은 사용자가 공개를 요구하지 않는 한 출력하지 않는다.
- 법령·판례·법령해석례 등 공식자료는 **현재 실행에서 실제 확인한 완전한 공식 URL**이 있을 때만 링크한다.
- URL 패턴을 추측하지 않는다. 식별자가 비어 있거나 끝이 `=`인 미완성 URL은 출력하지 않는다. 정확한 URL provenance를 확인하지 못하면 `[공식 링크 확인 필요]`로 처리한다.
- 법적 결론보다 조문·출처 정확성을 우선한다.
- 존재를 확인하지 않은 판례번호, 해석례번호, 법령 URL을 생성하지 않는다.

### 논리검증 및 Rendering Gate
- 최종 법령해석 문안 생성 전 `skills/law-interpretation-request/references/logic-validation.md`의 내부 논리검증 Gate를 반드시 거친다.
- 논리검증 중 원문·확인된 법적 근거에 없는 숨은 전제를 임의로 추가하지 않는다.
- A/B/P/Q 같은 추상 논리 시나리오를 사용자가 제시하지 않은 특정 법률·판례·해석례·개정연혁·사실관계에 임의로 대응시키지 않는다.
- `갑설 아니면 을설`처럼 선택지가 제시되면 가능한 해석을 모두 포괄한다는 전제 자체를 검증하고, 확인되지 않으면 제3의 가능성을 배제하지 않는다.
- 갑설·을설에서 동일한 법률용어의 의미·범위가 근거 없이 달라지면 BLOCK으로 처리하고 공통 개념 기준을 먼저 확정한다.
- Legal Issue Mapping의 내부 라벨·상태표와 논리검증 메모·기호화·점수표·오류분류명은 사용자가 분석표·논리감사·형식논리 설명을 요구하지 않는 한 사용자 출력에 노출하지 않는다.
- 사용자에게 보내기 직전에 **최종 Rendering Gate**를 수행해 선택한 모드의 H1 문자열·순서, Answer-first, Output Hygiene, URL provenance를 다시 확인한다. 하나라도 어긋나면 보내기 전에 다시 렌더링한다.

## 변경 후 검증
최소한 다음을 실행한다.

```bash
python scripts/validate_repo.py
```

`package.json`, Plugin manifest 또는 MCP 버전을 바꾼 경우에는 버전·경로 정합성을 함께 확인한다.

`package.json` 또는 MCP 버전을 바꾼 경우 Node.js 환경에서 추가로 다음을 실행한다.

```bash
npm install
npm run mcp -- --help
```

업스트림 도구명이 바뀌었으면 `skills/law-interpretation-request/SKILL.md`와 `docs/upstream-mcp.md`를 함께 갱신한다.
논리검증 계약을 바꿨으면 `references/logic-validation.md`, `evals/scenarios.md`, `evals/expected-behavior.md`, `scripts/validate_repo.py`를 함께 갱신하고 **E10~E20을 새 컨텍스트에서 다시 실행**한다.
Legal Issue Mapping 계약을 바꿨으면 `references/legal-issue-mapping.md`, `SKILL.md`, `references/interpretation-principles.md`, `references/case-patterns.md`, `evals/*`, `scripts/validate_repo.py`를 함께 검토한다.
출력 형식·Output Hygiene·URL provenance를 바꿨으면 `SKILL.md`, `references/request-format.md`, `references/source-policy.md`, `evals/*`, `scripts/validate_repo.py`, `AGENTS.md`, `README.md`, `docs/architecture.md`를 함께 갱신한다.
행동 검증 전에는 실제 resolved Skill source가 v0.2.0인지 확인한다. 설치본이 stale하거나 버전을 확인할 수 없으면 v0.2.0 PASS/FAIL로 계산하지 않는다.
이번 v0.2 계약은 E27~E38을 추가로 검증하고, 특히 22-0351·17-0047·20-0604 Golden Case에서 법적 분류형·중복규율형·규율공백형을 서로 구분해야 한다.
Plugin 패키징을 바꿨으면 `.codex-plugin/plugin.json`, `docs/plugin-packaging.md`, `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `scripts/validate_repo.py`를 함께 검토한다.
