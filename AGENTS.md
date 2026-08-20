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
- 별도 형식 지시가 없는 법령해석·검토 답변은 아래 **정확한 H1 1~6 구조**를 사용한다. 제목 문자열·번호·순서·Markdown 수준을 변경하지 않는다.

```markdown
# 1. 요청취지
# 2. 질의 배경 및 사실관계
# 3. 관련 법령 및 조문
# 4. 해석상 쟁점
# 5. 법률검토
# 6. 첨부자료
```

- `# 1. 요청취지` 이전에 별도 서론·요약·검토대상 설명을 작성하지 않는다.
- 기본 출력에는 별도 `제목` 또는 `질의사항` 항목을 생성하지 않는다.
- `사실관계 및 전제`, `관련 법령`, `검토의견`, `검토결론`, `결론`, `적용상 유의사항` 등으로 기본 최상위 제목을 바꾸지 않는다.
- 결론·검토의견·적용상 유의사항은 필요하면 `# 5. 법률검토` 내부의 하위 제목으로 작성한다.
- `1. 요청취지`는 사용자의 질문·사실관계·요구사항을 분석해 실제 검토 목적을 합리적으로 유추한다. 제공되지 않은 사업목적·처분경위·기관입장 등을 사실처럼 추가하지 않는다.
- `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설` 등 전용 형식을 사용자가 명시적으로 요청한 경우에만 법제처 1~3 구조를 사용한다.
- 모든 사용자용 최종 답변은 Markdown으로 작성한다.
- 법령·판례·법령해석례 등 공식자료는 실제 확인한 공식 URL이 있으면 자료명 자체에 Markdown 인라인 하이퍼링크를 우선 적용한다. URL 패턴을 추측하지 않는다.
- 법적 결론보다 조문·출처 정확성을 우선한다.
- 존재를 확인하지 않은 판례번호, 해석례번호, 법령 URL을 생성하지 않는다.
- 최종 법령해석 문안 생성 전 `skills/law-interpretation-request/references/logic-validation.md`의 내부 논리검증 Gate를 반드시 거친다.
- 논리검증 중 원문·확인된 법적 근거에 없는 숨은 전제를 임의로 추가하지 않는다.
- A/B/P/Q 같은 추상 논리 시나리오를 사용자가 제시하지 않은 특정 법률·판례·해석례·개정연혁·사실관계에 임의로 대응시키지 않는다.
- `갑설 아니면 을설`처럼 선택지가 제시되면 가능한 해석을 모두 포괄한다는 전제 자체를 검증하고, 확인되지 않으면 제3의 가능성을 배제하지 않는다.
- 갑설·을설에서 동일한 법률용어의 의미·범위가 근거 없이 달라지면 BLOCK으로 처리하고 공통 개념 기준을 먼저 확정한다.
- 논리검증 메모·기호화·점수표·오류분류명은 사용자가 논리감사나 형식논리 설명을 요구하지 않는 한 사용자 출력에 노출하지 않는다.

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
출력 형식 또는 인용정책을 바꿨으면 `SKILL.md`, `references/request-format.md`, `references/source-policy.md`, `evals/*`, `scripts/validate_repo.py`를 함께 갱신한다.
Plugin 패키징을 바꿨으면 `.codex-plugin/plugin.json`, `docs/plugin-packaging.md`, `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `scripts/validate_repo.py`를 함께 검토한다.
