# Architecture

## 목표

JDIPT는 **Plugin 패키징**, **법령해석 논증·작성**, **법령 데이터 조회**를 분리하고 최종 문안 생성 전에 독립된 **내부 논리검증 Gate**를 둔다.

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
   ├─ 적합성 점검
   ├─ 요청취지 유추
   ├─ 질의 보정
   ├─ 문언·체계·목적·연혁 분석
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
법적 논증 초안
   │
   ▼
내부 논리검증 Gate
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
기본 1~6 Markdown / 명시적 법제처 1~3 Markdown
```

## Plugin 경계

저장소 루트 자체가 Plugin 패키지다.

- `.codex-plugin/plugin.json`: Plugin 필수 진입점
- `skills/`: Plugin에 번들되는 Skill의 단일 원본
- `docs/`, `scripts/`, `config/`: 개발·검증·운영 문서와 도구

같은 Skill을 `.agents/skills/`에 복제하지 않는다. Plugin manifest는 `skills: "./skills/"`를 사용한다.

현재 Plugin은 **Skill-first**로 패키징한다. `korean-law-mcp`는 Plugin 내부에 vendor하지 않고 외부 의존성으로 유지한다.

ChatGPT 웹은 로컬 Codex MCP 설정을 읽지 않으므로, 공개 Plugin에서 MCP 도구까지 제공하려면 별도의 원격/등록 MCP App 구성이 필요하다. 실제 App ID나 원격 MCP 연결이 준비되기 전에는 `.app.json`을 임의로 생성하지 않는다.

## 책임 경계

### JDIPT Plugin

- Plugin identity와 Skill 패키징
- 설치 화면용 메타데이터
- 법령해석 Skill 제공
- MCP가 없는 환경에서도 공식자료 우선 정책으로 동작

### law-interpretation-request Skill

- 요청 목적과 질의 유형 판단
- 법령해석 대상 적합성 판정
- 사용자의 질문을 기반으로 요청취지 유추
- 법적 쟁점 구조화
- 필요한 경우 갑설·을설 구성
- 자연어 논증의 내부 논리검증
- 형식적 타당성과 건전성 상태 분리
- 문서 형식·문체 통제
- 조사 결과를 제출·검토 가능한 Markdown 문안으로 변환

### korean-law-mcp

- 국가법령정보센터 기반 식별·검색·본문 조회
- 판례·법령해석례 등 결정례 조회
- 연혁/시점 비교
- 인용 검증 및 관련 분석

## 논리검증 경계

`logic-validation.md`는 법적 결론을 새로 만드는 도구가 아니라 **이미 구성한 논증을 감사(audit)하는 Gate**다.

- 원문 또는 확인된 법적 근거에 없는 전제를 추가하지 않는다.
- 정형화가 가능한 논증만 기호화하며, 억지 정형화가 필요한 경우 `비정형 자연어 추론`으로 남긴다.
- 사실성은 형식논리와 분리한다. 사실성 미확인 전제가 있으면 `건전성 미확정`으로 처리한다.
- BLOCK 오류는 수정 후 재검증하며, 확인할 수 없는 누락 전제는 조건부 결론 또는 확인 필요 상태로 남긴다.
- 내부 기호화·점수·반례 메모는 기본 사용자 출력에서 숨긴다.

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
