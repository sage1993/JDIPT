# Plugin packaging

현재 기준 버전: **v0.2.2**

## 기준

JDIPT는 저장소 루트 자체를 하나의 Codex Plugin 패키지로 관리합니다.

Plugin 진입점:

- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

Skill 단일 원본:

- `skills/law-interpretation-request/`

같은 Skill을 `.agents/skills/`나 별도 배포 폴더에 복제하지 않습니다.

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
├─ docs/
├─ scripts/
├─ tests/
├─ run_jdipt_full_regression_v4.py
├─ AGENTS.md
├─ README.md
└─ package.json
```

## Plugin Manifest

`.codex-plugin/plugin.json` 계약:

- Plugin ID: `jdipt`
- version: `0.2.2`
- `package.json` version과 일치
- `skills: "./skills/"`
- 표시명/설명/default prompt 제공

현재 `package.json`과 Plugin manifest는 모두 `0.2.2`입니다.

## Skill 호출 정책

`law-interpretation-request`는 v0.2.0부터 계속 **explicit-only**입니다.

```yaml
policy:
  allow_implicit_invocation: false
```

일반 법령 질문에 자동 선택되는 것을 요구하지 않으며 사용자가 필요할 때 `$law-interpretation-request`로 직접 호출합니다.

자동 Skill activation은 v0.2.2 release gate에 포함하지 않습니다.

## Repo Marketplace

`.agents/plugins/marketplace.json`은 JDIPT를 repo/team Marketplace로 노출합니다.

핵심 계약:

```json
{
  "name": "sage1993",
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

저장소는 현재 **public**입니다. 따라서 공개 Git source로 Marketplace를 등록할 수 있습니다.

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

로컬 clone:

```bash
codex plugin marketplace add .
codex plugin add jdipt@sage1993
```

## Korean Law MCP 경계

Plugin은 **Skill-first**로 유지하며 `korean-law-mcp` 소스를 vendor하지 않습니다.

현재 구분:

- Skill 패키징: 포함
- Codex Marketplace manifest: 포함
- 로컬 Codex용 `korean-law-mcp@4.12.1`: 선택적 외부 연결
- ChatGPT 웹용 등록 MCP App: 미구현, v0.3 후속 대상

이 구조를 유지하는 이유:

1. 업스트림 소스·릴리스 책임 분리
2. `LAW_OC` 같은 비밀값을 Plugin 패키지에 포함하지 않음
3. 로컬 STDIO MCP와 ChatGPT 웹의 연결 방식을 분리
4. 업스트림 보안·기능 업데이트를 별도 의존성 변경으로 관리

## v0.2.2 Runtime 계약

Plugin runtime에는 다음이 포함됩니다.

- `SKILL.md`
- `agents/openai.yaml`
- `references/*.md`

v0.2.2에서는 저장소 runtime과 실제 설치본의 SHA-256 일치를 release precondition으로 검사합니다.

```bash
python scripts/plugin_integrity.py
```

불일치 시 행동 regression을 시작하지 않습니다.

## v0.2.2 Source / Rendering 계약

패키징 자체와 별개로 설치본 Skill은 다음 안정성 계약을 갖습니다.

- 본문이 결론에 중요한 별표·별지서식을 직접 참조하면 실제 원문 확인 또는 unresolved 상태 유지
- unresolved critical reference가 있으면 확정 결론 BLOCK
- 기본 응답 exact 4 H1 Final Rendering Gate
- 빈 critical query parameter 차단
- invalid percent escape 차단
- `law.go.kr/LSW/flDownload.do + flNm` 불안정 직접링크 차단
- same-run verified official URL 우선

## 개발 및 검증

최소 결정론적 검증:

```bash
python scripts/validate_repo.py
python -m pytest -q
python scripts/plugin_integrity.py
```

Release orchestration:

```bash
python scripts/run_release_gate.py
python scripts/run_release_gate.py --critical-only --codex <codex-cli>
python scripts/run_release_gate.py --full --codex <codex-cli>
```

`--full`은 결정론적 gate → critical stability → E1–E42 full regression → package gate 순으로 fail-closed 실행합니다.

## v0.2.2 검증 상태

최종 검증:

- `validate_repo`: PASS
- pytest: 34 passed
- installed runtime SHA: MATCH
- Critical Suite: PASS
- E25: 3/3
- E37: 3/3
- Full E1–E42 process: 42/42
- environment: 0/42
- H1: 40/42 (`E2/E3 = SKIP_SPECIAL_FORMAT`)
- hygiene: 42/42
- URL: 42/42
- contract oracle: 42/42
- `npm audit --omit=dev`: 0 vulnerabilities
- real-law smoke: PASS
- model: `gpt-5.6-luna`

상세 증거: [`validation/v0.2.2-source-rendering.md`](validation/v0.2.2-source-rendering.md)

## 배포 체크리스트

- [ ] `.codex-plugin/plugin.json` / `package.json` version 일치
- [ ] Plugin name `jdipt`
- [ ] Marketplace name `sage1993`
- [ ] `source.path = "."`
- [ ] `policy.installation = AVAILABLE`
- [ ] `policy.authentication = ON_INSTALL`
- [ ] `category = Productivity`
- [ ] `allow_implicit_invocation = false`
- [ ] tracked secret 없음
- [ ] `python scripts/validate_repo.py`
- [ ] `python -m pytest -q`
- [ ] installed runtime integrity PASS
- [ ] Critical stability PASS
- [ ] Full E1–E42 PASS
- [ ] `npm ci`
- [ ] `npm audit --omit=dev`
- [ ] `npm run mcp -- --help`
- [ ] real-law smoke PASS

## 후속

ChatGPT 웹에서 MCP 도구까지 제공하려면 실제 등록 ID를 확보한 뒤 `.app.json` 및 manifest `apps` 연결을 별도 작업으로 진행합니다. 확인되지 않은 App ID나 MCP URL을 저장소에 임의로 추가하지 않습니다.
