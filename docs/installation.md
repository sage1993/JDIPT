# JDIPT Codex 설치 가이드

현재 기준 버전: **v0.2.3**

## 배포 모델

JDIPT 저장소는 저장소 루트 자체가 Codex Plugin이며 `.agents/plugins/marketplace.json`을 통해 repo/team Marketplace로 노출합니다.

- Marketplace 이름: `sage1993`
- Plugin 이름: `jdipt`
- Plugin source: 저장소 루트 (`.`)
- 공개 설치 ID: `jdipt@sage1993`
- 버전: `0.2.3`
- 저장소: public

Skill 원본은 `skills/law-interpretation-request/` 한 곳에서 관리합니다.

## 호출 정책

`law-interpretation-request`는 **explicit-only**입니다.

```yaml
policy:
  allow_implicit_invocation: false
```

일반 법령 질문에 자동 적용되는 것을 요구하지 않습니다. 필요할 때 다음처럼 직접 호출합니다.

```text
$law-interpretation-request 주택건설기준 등에 관한 규정 제27조를 검토해줘.
```

## GitHub에서 설치

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

설치 후에는 새 Codex thread에서 `$law-interpretation-request`를 명시 호출해 설치 상태를 검증합니다.

## 로컬 clone에서 설치

```bash
git clone https://github.com/sage1993/JDIPT.git
cd JDIPT
codex plugin marketplace add .
codex plugin add jdipt@sage1993
codex plugin list
```

이미 clone한 저장소가 있다면 `git clone`은 생략합니다.

개발용 local marketplace를 별도로 사용한다면 설치 ID가 `jdipt@jdipt-local`일 수 있습니다. release validation에서 사용한 개발 설치본도 v0.2.2였습니다.

## 설치본 갱신

새 버전 확인 시:

1. Marketplace/Plugin을 refresh 또는 재설치합니다.
2. `codex plugin list`에서 실제 설치 version/path를 확인합니다.
3. **새 Codex thread**를 시작합니다.
4. 필요 시 저장소와 설치본 runtime SHA-256을 비교합니다.

이전 thread의 Skill 상태를 재사용하면 새 버전의 동작을 정확히 확인하기 어렵습니다.

## v0.2.3 설치본 확인

Windows PowerShell 예시:

```powershell
$jdipt = Join-Path $HOME ".codex\plugins\jdipt"

Get-Content "$jdipt\.codex-plugin\plugin.json" -Raw -Encoding UTF8
Select-String -Path "$jdipt\skills\law-interpretation-request\SKILL.md" -Encoding UTF8 -Pattern '# 2. 검토결론','Final Rendering'
Select-String -Path "$jdipt\skills\law-interpretation-request\agents\openai.yaml" -Encoding UTF8 -Pattern 'allow_implicit_invocation: false'
```

설치 경로는 Codex 버전/Marketplace 방식에 따라 다를 수 있으므로 `codex plugin list`가 표시하는 실제 경로를 우선합니다.

PASS 기준:

- manifest version `0.2.3`
- `SKILL.md` 존재
- 기본 4단 출력 계약 존재
- Final Rendering / Source Resolution hard gate 존재
- `allow_implicit_invocation: false`

## 저장소 ↔ 설치본 SHA-256 무결성 확인

v0.2.2부터 다음 스크립트를 제공합니다.

```bash
python scripts/plugin_integrity.py
```

자동 경로를 찾지 못하는 경우:

```powershell
python scripts/plugin_integrity.py `
  --repo-root F:\2026-PJ\JDIPT `
  --installed-root "$HOME\.codex\plugins\jdipt\skills\law-interpretation-request"
```

비교 범위:

- `SKILL.md`
- `agents/openai.yaml`
- `references/*.md`

PASS:

```text
INSTALLATION_INTEGRITY: PASS
```

mismatch가 있으면 행동 regression을 실행하기 전에 설치본을 갱신합니다.

## 설치 Smoke Test

새 thread에서:

```text
$law-interpretation-request 기존 건축물 증축 시 대지 안의 공지 규정이 적용되는지 검토해줘.
```

PASS 조건:

1. `codex plugin list`에서 JDIPT v0.2.3 설치 확인
2. `allow_implicit_invocation: false`
3. 명시 호출 시 Skill 적용
4. 기본 출력이 정확한 4단 Markdown 구조
5. `# 2. 검토결론`이 검토이유보다 먼저 출력
6. 단일 쟁점에서 내부 분석 단계를 기계적으로 하위제목화하지 않음
7. `$law-interpretation-request`, Plugin activation 문자열 등 실행 메타데이터 비노출
8. 공식자료 링크는 현재 실행에서 실제 확인한 완전한 URL만 사용
9. 빈 critical query / invalid percent escape / `flDownload.do + flNm` 불안정 URL 비출력
10. 내부 논리검증 기호·점수·오류분류 비노출

E26은 설치된 Plugin에서 **명시 호출**이 정상 작동하는지 확인하는 Smoke Test입니다. 자동 Skill 선택은 release gate 대상이 아닙니다.

## Korean Law MCP

Plugin 설치 자체는 `korean-law-mcp` 없이 가능합니다. 법령·판례·해석례 조회를 Codex 로컬에서 사용하려면 별도 MCP 설정이 필요합니다.

현재 고정 버전: `korean-law-mcp@4.12.1`

예시:

```toml
[mcp_servers.korean_law]
command = "npx"
args = ["-y", "korean-law-mcp@4.12.1"]
enabled = true
env_vars = ["LAW_OC"]
```

`LAW_OC` 실제 값은 저장소에 기록하지 않습니다.

## 개발용 정적 검증

```bash
python scripts/validate_repo.py
python -m pytest -q
```

v0.2.2 최종 validation에서는 pytest **34 passed**였습니다.

## Release gate

### A. 결정론적 gate

```bash
python scripts/run_release_gate.py
```

포함 항목:

- `validate_repo`
- pytest
- required Python `py_compile`
- `git diff --check`
- installed runtime integrity

### B. Critical stability

```bash
python scripts/run_release_gate.py --critical-only --codex <codex-cli>
```

Critical cases:

```text
E02 E03 E13 E18 E25 E31 E36 E37 E39 E40 E41 E42
```

E25와 E37은 각각 3회 실행합니다.

### C. Full E1–E42 + package gate

```bash
python scripts/run_release_gate.py --full --codex <codex-cli>
```

v0.2.2 acceptance:

```text
process_ok:          42/42
environment_errors:   0/42
h1_pass:             40/42
hygiene_pass:        42/42
incomplete_url_pass: 42/42
contract_oracle:     42/42
```

E2/E3만 `SKIP_SPECIAL_FORMAT`입니다.

Package gate:

```text
npm ci
npm audit --omit=dev
npm run mcp -- --help
git diff --check
git status --short
```

최종 행동 regression 기본 모델은 `gpt-5.6-luna`입니다.

## v0.2.2 공개 검증 결과

- Critical Suite: PASS
- E25: 3/3
- E37: 3/3
- Full E1–E42: process 42/42
- Environment: 0/42
- Hygiene: 42/42
- URL: 42/42
- Contract oracle: 42/42
- pytest: 34 passed
- npm audit: 0 vulnerabilities
- repository/runtime SHA: MATCH
- real-law smoke: PASS

상세 증거: [`validation/v0.2.2-source-rendering.md`](validation/v0.2.2-source-rendering.md)

## 배포 전 확인

- [ ] `.codex-plugin/plugin.json` version `0.2.3`
- [ ] `package.json` version `0.2.3`
- [ ] Marketplace `sage1993`
- [ ] Plugin `jdipt`
- [ ] `source.path = "."`
- [ ] `policy.installation = AVAILABLE`
- [ ] `policy.authentication = ON_INSTALL`
- [ ] `allow_implicit_invocation = false`
- [ ] `python scripts/validate_repo.py`
- [ ] `python -m pytest -q`
- [ ] installed runtime integrity PASS
- [ ] Critical stability PASS
- [ ] Full E1–E42 PASS
- [ ] package gate PASS
- [ ] real-law smoke PASS
