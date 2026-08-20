# Plugin packaging

## 기준

JDIPT는 OpenAI의 현재 Codex Plugin 패키징 및 Marketplace 사양을 기준으로 저장소 루트 자체를 하나의 Plugin 패키지로 관리한다.

공식 참고:

- https://github.com/openai/codex/tree/main/codex-rs/skills/src/assets/samples/plugin-creator
- https://developers.openai.com/codex/mcp
- https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex

Plugin 진입점은 `.codex-plugin/plugin.json`이며, repo/team Marketplace 진입점은 `.agents/plugins/marketplace.json`이다.

## 현재 패키지 구조

```text
JDIPT/
├─ .agents/
│  └─ plugins/
│     └─ marketplace.json
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
│  ├─ installation.md
│  └─ plugin-packaging.md
├─ scripts/
├─ AGENTS.md
├─ README.md
└─ package.json
```

`skills/law-interpretation-request/`가 Plugin에 포함되는 Skill의 단일 원본이다. 같은 Skill을 `.agents/skills/`나 별도 배포 폴더에 복제하지 않는다.

## Plugin Manifest

`.codex-plugin/plugin.json`은 다음 역할을 담당한다.

- Plugin ID: `jdipt`
- Plugin 버전: `package.json`과 동일한 버전
- Plugin 표시명과 설명
- `skills: "./skills/"`를 통한 Skill 등록
- 기본 프롬프트와 설치 화면 메타데이터

Manifest의 Plugin 내부 경로는 Plugin 루트 기준 상대경로로 유지한다.

## Repo Marketplace

`.agents/plugins/marketplace.json`은 JDIPT를 repo/team Marketplace로 노출한다.

현재 계약:

```json
{
  "name": "sage1993",
  "interface": {
    "displayName": "sage1993 Plugins"
  },
  "plugins": [
    {
      "name": "jdipt",
      "source": {
        "source": "local",
        "path": "."
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

Codex Marketplace 로더는 local source의 `.` 또는 `./`를 Marketplace 루트로 해석한다. 따라서 현재처럼 저장소 루트가 Plugin 루트인 구조에서는 `source.path = "."`를 사용한다.

이 방식은 `skills/`를 `plugins/jdipt/skills/`에 복제하거나 대규모 이동하지 않고도 단일 원본을 유지할 수 있다는 장점이 있다.

## 설치

GitHub 저장소 접근 권한이 있는 사용자는 다음과 같이 Marketplace와 Plugin을 설치한다.

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

로컬 clone을 직접 Marketplace로 등록하는 경우:

```bash
cd JDIPT
codex plugin marketplace add .
codex plugin add jdipt@sage1993
codex plugin list
```

설치 후 Skill 및 MCP 변경사항을 확실히 반영하려면 새 Codex thread에서 검증한다.

상세 절차와 E26 Smoke Test 조건은 [`installation.md`](installation.md)를 참조한다.

현재 저장소가 private인 동안 Git source 설치는 저장소 읽기 권한과 Git 인증이 있는 사용자에게만 가능하다. 불특정 사용자 대상 공개 배포에는 public 저장소 또는 별도의 접근 가능한 Git remote가 필요하다.

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
- Codex Marketplace manifest: 포함
- 로컬 Codex용 `korean-law-mcp`: 선택적 외부 연결
- ChatGPT 웹용 등록 MCP App: 미구현, 후속 검증 대상

으로 구분한다.

## 개발 및 검증

변경 후 최소 정적 검증:

```bash
python scripts/validate_repo.py
```

기존 검증 스크립트는 다음을 확인한다.

- `.codex-plugin/plugin.json` 존재 및 JSON 파싱
- Plugin 이름 `jdipt`
- Plugin 버전과 `package.json` 버전 일치
- `skills` 경로가 `./skills/`
- `skills/law-interpretation-request/SKILL.md` 존재
- `.agents/skills/law-interpretation-request` 중복본 부재
- Plugin 표시명과 기본 프롬프트 존재
- `LAW_OC` 실제 비밀값 미포함
- `config/codex.example.toml`이 `LAW_OC`를 `env_vars`로 전달

Marketplace에 대해서는 추가로 다음 계약을 확인한다.

- `.agents/plugins/marketplace.json` 존재
- Marketplace 이름 `sage1993`
- Plugin entry 이름 `jdipt`
- local source path `.`
- `policy.installation = AVAILABLE`
- `policy.authentication = ON_INSTALL`
- `category = Productivity`

정적 검증과 실제 Codex 설치는 별개다. E26은 새 설치 환경에서 `jdipt@sage1993`를 실제 설치하고, Plugin명/Skill명을 명시하지 않은 일반 법령해석 요청에서 자동 Skill activation을 확인한 경우에만 PASS로 판정한다.

## 배포 전 남은 항목

현재 Marketplace manifest가 추가되었으므로 다음 단계는 실제 설치 검증이다.

- 로컬 또는 GitHub source에서 Plugin 설치 smoke test
- E10~E25 실제 에이전트 회귀평가
- E26 신규 설치 후 자동 Skill 적용
- `korean-law-mcp` 실제 조회 E2E
- ChatGPT 웹에서 MCP가 필요한 경우 원격/등록 MCP App 구성
- 공개 저장소 전환 시 라이선스·개인정보·지원정보 최종 확인
- Plugin Directory 제출을 진행할 경우 제출 시점의 최신 심사 요구사항 재확인
