# Architecture

## 목표

JDIPT는 **Plugin 패키징**, **법적 쟁점 매핑**, **법령해석**, **논리검증**, **법령 데이터 조회**, **사용자 출력**의 책임을 분리한다. 내부 분석은 세밀하게 유지하되 사용자 출력은 결론 우선성과 논증 연결성을 기준으로 단순화한다.

```text
ChatGPT / Codex
   │
   ▼
JDIPT Plugin
.codex-plugin/plugin.json
   │
   └─ skills: ./skills/
          │
          ▼
law-interpretation-request Skill
   │
   ├─ explicit-only invocation
   ├─ 적합성 점검
   ├─ 질의 보정
   │
   ├───────────── optional ─────────────┐
   │                                    ▼
   │                             Korean Law MCP
   │                             ├─ 현행 법령 조회
   │                             ├─ 결정례/해석례 조회
   │                             ├─ 연혁·관련 규정 탐색
   │                             └─ 인용 검증
   │
   ▼
Legal Issue Mapping Gate
   │
   ├─ 주체·행위·대상 특정
   ├─ 법적 정의·분류
   ├─ 적용 규범 지도
   ├─ 규정 관계 진단
   ├─ 사실관계 ↔ 법적 요건 연결
   └─ 문제 발생 지점 특정
   │
   ▼
Legal Interpretation
   │
   ├─ 문언
   ├─ 정의·참조
   ├─ 체계
   ├─ 목적
   ├─ 연혁
   └─ 판례·법령해석례
   │
   ▼
법적 논증 초안
   │
   ▼
Logic Validation Gate
   │
   ├─ 논증 분해·기호화
   ├─ 전제 명확성·일관성·충분성
   ├─ 형식적 타당성
   ├─ 오류·전제 누락·반례
   ├─ 필요시 갑설·을설 상호 비교
   └─ BLOCK 수정·재검증
   │
   ▼
출처·현행성 최종 검증
   │
   ▼
Answer Rendering
   │
   ├─ 기본 4단 Answer-first Markdown
   └─ 명시적 법제처 1~3 Markdown
```

## Plugin 경계

저장소 루트 자체가 Plugin 패키지다.

- `.codex-plugin/plugin.json`: Plugin 필수 진입점
- `.agents/plugins/marketplace.json`: `jdipt@sage1993` 로컬 Marketplace 설치 계약
- `skills/`: Plugin에 번들되는 Skill의 단일 원본
- `docs/`, `scripts/`, `config/`: 개발·검증·운영 문서와 도구

같은 Skill을 `.agents/skills/`에 복제하지 않는다. Plugin manifest는 `skills: "./skills/"`를 사용한다.

현재 Plugin은 **Skill-first**로 패키징한다. `korean-law-mcp`는 Plugin 내부에 vendor하지 않고 외부 의존성으로 유지한다.

`law-interpretation-request`의 invocation policy는 **explicit-only**다. `skills/law-interpretation-request/agents/openai.yaml`에서 `allow_implicit_invocation: false`를 유지하며 일반 법령 질문에 자동 선택되는 것을 요구하지 않는다. 사용자가 필요할 때 `$law-interpretation-request`로 직접 호출한다.

ChatGPT 웹은 로컬 Codex MCP 설정을 읽지 않으므로, 공개 Plugin에서 MCP 도구까지 제공하려면 별도의 원격/등록 MCP App 구성이 필요하다. 실제 App ID나 원격 MCP 연결이 준비되기 전에는 `.app.json`을 임의로 생성하지 않는다.

## 책임 경계

### JDIPT Plugin

- Plugin identity와 Skill 패키징
- 설치 화면용 메타데이터
- explicit-only 법령해석 Skill 제공
- MCP가 없는 환경에서도 공식자료 우선 정책으로 동작

### Legal Issue Mapping Gate

`skills/law-interpretation-request/references/legal-issue-mapping.md`가 담당한다.

- 질문의 주체·행위·대상과 법적 상태 또는 분류 특정
- 직접 정의와 상·하위 법적 개념 확인
- 정의·본칙·요건·예외·특례·위임·적용 제외·준용 등 규범 역할 분류
- 동일 사항 중복규율·일반/특별·누적 적용·규율 공백·다른 규율대상 구분
- 사용자 사실과 법적 요건을 `충족` / `불충족` / `확인 필요`로 연결
- 서로 다른 결론을 가르는 실제 문제 발생 지점 특정

이 Gate는 법적 결론을 미리 정하지 않는다. 어떤 규범을 어떤 사실에 연결하여 해석해야 하는지 확정하는 역할만 수행한다.

### Legal Interpretation

`references/interpretation-principles.md`와 `references/case-patterns.md`가 담당한다.

- Mapping에서 확정한 법적 대상과 규정 관계를 전제로 규범의 객관적 의미·범위를 해석
- 문언을 우선하고 필요한 경우 정의·참조, 체계, 목적, 연혁, 판례·법령해석례를 추가
- 중복규율형과 규율공백형을 구분하고 단순 `특별법 우선`으로 축약하지 않음
- 예외·특례·침익 규정의 엄격해석 원칙 적용

### Logic Validation Gate

`logic-validation.md`는 법적 결론을 새로 만드는 도구가 아니라 **이미 구성한 논증을 감사(audit)하는 Gate**다.

- 원문 또는 확인된 법적 근거에 없는 전제를 추가하지 않는다.
- 정형화가 가능한 논증만 기호화하며, 억지 정형화가 필요한 경우 `비정형 자연어 추론`으로 남긴다.
- 사실성은 형식논리와 분리한다. 사실성 미확인 전제가 있으면 `건전성 미확정`으로 처리한다.
- BLOCK 오류는 수정 후 재검증하며, 확인할 수 없는 누락 전제는 조건부 결론 또는 확인 필요 상태로 남긴다.
- 내부 기호화·점수·반례 메모는 기본 사용자 출력에서 숨긴다.

### Answer Rendering

분석 완료 후 사용자에게 보여주는 형식만 담당한다.

기본 법률검토형:

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

- `# 2. 검토결론`에서 검증된 결론을 상세 이유보다 먼저 제시한다.
- `# 3. 검토이유`에서는 정의·규정·규정관계·사실대입·해석을 연결된 논증으로 작성한다.
- 단일 쟁점의 내부 분석 단계를 각각 소제목으로 노출하지 않는다.
- 서로 독립적으로 판단 가능한 복수 쟁점만 하위 소제목으로 분리한다.
- 이유 말미의 결론은 앞의 검토결론과 일치해야 한다.

법제처 제출용은 사용자가 명시적으로 요청한 경우에만 기존 1~3 구조를 유지한다.

### law-interpretation-request Skill

- 명시 호출된 법령해석 요청 처리
- 요청 목적과 질의 유형 판단
- 법령해석 대상 적합성 판정
- Legal Issue Mapping, Interpretation, Logic Validation, Rendering 순서 조정
- 필요한 경우 갑설·을설 구성
- 조사 결과를 제출·검토 가능한 Markdown 문안으로 변환

### korean-law-mcp

- 국가법령정보센터 기반 식별·검색·본문 조회
- 판례·법령해석례 등 결정례 조회
- 연혁/시점 비교
- 인용 검증 및 관련 분석

## 대표 논증 패턴

`case-patterns.md`에서 다음 세 패턴을 독립적으로 관리한다.

1. **법적 분류형 — 22-0351**: 법적 정의·분류 → 본칙 → 예외 해당 여부
2. **중복규율형 — 17-0047**: 규정 A/B의 규율대상·기능 → 동일 사항 여부 → 특별규정의 배타 적용 여부
3. **규율공백형 — 20-0604**: 특별법의 직접 규율 여부 → 규율 공백 → 일반법 보충 적용

중복규율형과 규율공백형은 서로 반대 방향의 적용관계를 만들 수 있으므로 같은 규칙으로 처리하지 않는다.

## MCP 의존성 정책

업스트림 MCP 소스는 vendor하지 않는다.

1. 업스트림 보안·성능 수정이 빠르게 반영되는 편이 유리하다.
2. JDIPT의 핵심 자산은 법령해석 워크플로와 문서 품질 규칙이다.
3. 소스 복제 시 동기화 비용과 책임 경계가 불필요하게 커진다.
4. `LAW_OC` 같은 비밀값을 Plugin 패키지에 포함하지 않는다.

따라서 `package.json`에서 검증된 버전을 고정하고 별도 변경으로 업그레이드한다. Codex 로컬에서는 `config/codex.example.toml`의 `env_vars = ["LAW_OC"]` 방식으로 OS 환경변수를 전달한다.

## ChatGPT 웹 MCP 확장 경로

ChatGPT 웹까지 MCP 도구를 제공해야 할 경우 다음을 별도 작업으로 수행한다.

1. OpenAI Plugin에서 사용할 수 있는 원격/등록 MCP 연결 준비
2. 실제 등록 ID 확보
3. `.app.json` 생성
4. `.codex-plugin/plugin.json`의 `apps` 필드 연결
5. ChatGPT 웹 새 컨텍스트에서 도구 호출 E2E 검증

이 단계는 현재 Skill 패키징과 분리하여 진행한다.
