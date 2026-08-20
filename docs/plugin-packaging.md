# Plugin packaging

## 기준

JDIPT는 OpenAI의 현재 Plugin 패키징 사양을 기준으로 저장소 루트 자체를 하나의 Plugin 패키지로 관리한다.

공식 문서:

- https://developers.openai.com/plugins/build/plugins
- https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex
- https://developers.openai.com/codex/mcp

OpenAI의 현재 사양에서 모든 Plugin은 `.codex-plugin/plugin.json`을 진입점으로 사용하고, Skill을 포함하는 Plugin은 Plugin 루트의 `skills/`를 사용할 수 있다.

## 현재 패키지 구조

```text
JDIPT/
├─ .codex-plugin/
│  └─ plugin.json
├─ skills/
│  └─ law-interpretation-request/
│     ├─ SKILL.md
│     ├─ agents/
│     ├─ references/
│     └─ evals/
├─ config/
│  └─ codex.example.toml
├─ docs/
├─ scripts/
├─ AGENTS.md
├─ README.md
└─ package.json
```

`skills/law-interpretation-request/`가 Plugin에 포함되는 Skill의 단일 원본이다. 같은 Skill을 `.agents/skills/`에 복제하지 않는다.

## Manifest

`.codex-plugin/plugin.json`은 현재 다음 역할만 담당한다.

- Plugin ID: `jdipt`
- Plugin 버전: `package.json`과 동일한 버전
- Plugin 표시명과 설명
- `skills: "./skills/"`를 통한 Skill 등록
- 기본 프롬프트와 설치 화면 메타데이터

Manifest의 경로는 Plugin 루트 기준 상대경로로 유지하고 `./`로 시작한다.

## Korean Law MCP 경계

현재 Plugin 패키지는 **Skill-first 패키지**로 유지하고 `korean-law-mcp`를 Plugin 안에 vendor하지 않는다.

`korean-law-mcp`는 다음 이유로 외부 의존성으로 유지한다.

1. 업스트림 소스와 릴리스 책임을 분리한다.
2. `LAW_OC` 같은 비밀값을 Plugin 패키지에 포함하지 않는다.
3. 현재 업스트림은 로컬 STDIO 실행을 기본으로 하므로 Codex 로컬 환경과 ChatGPT 웹의 MCP 연결 방식을 분리해서 다룬다.

### Codex 로컬

Codex CLI, IDE extension, ChatGPT desktop의 로컬 Codex host에서는 `config/codex.example.toml`을 참고하여 `korean-law-mcp`를 별도로 연결할 수 있다.

실제 API 키는 설정 파일에 기록하지 않고 OS 환경변수 `LAW_OC`로 설정하며, Codex 설정은 `env_vars = ["LAW_OC"]`로 해당 값을 전달한다.

### ChatGPT 웹 / 공개 Plugin

ChatGPT 웹은 로컬 Codex MCP 설정을 읽지 않는다. 공개 Plugin에서 MCP 기반 도구를 함께 제공하려면 OpenAI Plugin에서 사용할 수 있는 원격/등록 MCP 연결을 별도로 구성하고, 실제 등록 ID가 발급된 뒤 `.app.json` 및 manifest의 `apps` 필드를 추가한다.

등록되지 않은 App ID나 확인되지 않은 MCP URL을 저장소에 임의로 넣지 않는다.

따라서 현재 공개 패키징 단계에서는:

- Skill 패키징: 포함
- 로컬 Codex용 `korean-law-mcp`: 선택적 외부 연결
- ChatGPT 웹용 등록 MCP App: 미구현, 후속 검증 대상

으로 구분한다.

## 개발 및 검증

변경 후 최소 정적 검증:

```bash
python scripts/validate_repo.py
```

검증 스크립트는 다음을 확인한다.

- `.codex-plugin/plugin.json` 존재 및 JSON 파싱
- Plugin 이름 `jdipt`
- Plugin 버전과 `package.json` 버전 일치
- `skills` 경로가 `./skills/`
- `skills/law-interpretation-request/SKILL.md` 존재
- `.agents/skills/law-interpretation-request` 중복본 부재
- Plugin 표시명과 기본 프롬프트 존재
- `LAW_OC` 실제 비밀값 미포함
- `config/codex.example.toml`이 `LAW_OC`를 `env_vars`로 전달

정적 검증과 별도로 새 ChatGPT/Codex 컨텍스트에서 E10~E25 행동 회귀평가를 수행해야 한다.

## 배포 전 남은 항목

공개 Plugin Directory 제출 전 다음을 별도로 검증한다.

- 로컬 또는 개인 Plugin 설치 smoke test
- E10~E25 실제 에이전트 회귀평가
- `korean-law-mcp` 실제 조회 E2E
- ChatGPT 웹에서 MCP가 필요한 경우 원격/등록 MCP App 구성
- 공개 저장소 전환 시 라이선스·개인정보·지원정보 최종 확인
- Plugin 제출 포털의 최신 심사 요구사항 재확인
