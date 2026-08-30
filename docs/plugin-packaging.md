# Plugin packaging

현재 공개 기준 버전은 **v0.2.3**다. v0.2.3은 authority, temporal, claim-level evidence 계약과 Core14/Full26 평가 체계를 포함한다.

## 패키지 기준

JDIPT는 저장소 루트 자체를 하나의 Codex Plugin 패키지로 관리한다.

- Plugin 진입점: `.codex-plugin/plugin.json`
- Marketplace: `.agents/plugins/marketplace.json`
- Skill 단일 원본: `skills/law-interpretation-request/`
- 동일 Skill을 `.agents/skills/`에 복제하지 않는다.
- Plugin manifest는 `skills: "./skills/"`를 유지한다.

## 현재 runtime 계약

Plugin runtime 무결성 비교 대상:

- `SKILL.md`
- `agents/openai.yaml`
- `references/*.md`

저장소와 실제 설치본의 SHA-256이 일치해야 live behavior regression을 시작한다.

```powershell
python scripts/plugin_integrity.py
```

불일치 시 behavior regression은 fail-closed로 중단한다.

## Skill 호출 정책

`law-interpretation-request`는 **explicit-only**다.

```yaml
policy:
  allow_implicit_invocation: false
```

자동 Skill activation은 release gate의 PASS 조건이 아니다. 실제 behavior case는 `$law-interpretation-request`를 명시적으로 호출한다.

## Korean Law MCP 경계

- `korean-law-mcp` 소스는 vendor하지 않는다.
- 현재 고정 의존성: `korean-law-mcp@4.12.1`
- `LAW_OC` 같은 비밀값은 Plugin 패키지에 포함하지 않는다.
- Codex 로컬은 `config/codex.example.toml`의 `env_vars = ["LAW_OC"]` 방식으로 전달한다.
- ChatGPT 웹용 등록 MCP App은 별도 후속 작업이다.

## v0.2.3 평가 구조

과거 E1~E42 fixture는 삭제하지 않고 catalog로 보존한다. 신규 E43~E46을 포함한 전체 catalog는 E1~E46이다.

실제 실행군은 `skills/law-interpretation-request/evals/suite-manifest.json`을 따른다.

| Suite | Cases | 용도 |
|---|---:|---|
| Core | 14 | PR 핵심 fail-closed 안정성 |
| Full active | 26 | 릴리스 전 실제 LLM 회귀 |
| Legacy | 20 | 과거 회귀 재현·진단 |
| Catalog | 46 | 전체 fixture/oracle 추적 |

상세 정책: `docs/evaluation-suites.md`

## 개발 및 검증

### 결정론적 검증

```powershell
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python -m pytest -q
python scripts/plugin_integrity.py
```

### Behavior regression

Core:

```powershell
python scripts/run_eval_suite.py --suite core
```

Full active:

```powershell
python scripts/run_eval_suite.py --suite full
```

Legacy 진단:

```powershell
python scripts/run_eval_suite.py --suite legacy
```

### Release orchestration

```powershell
python scripts/run_release_gate.py
python scripts/run_release_gate.py --critical-only
python scripts/run_release_gate.py --full
```

순서:

```text
A. deterministic
→ B. Core stability
→ C. Full active
→ D. package/static
```

Gate B는 Core 14개를 실행하고 E37만 2회 반복한다. Gate C는 Full active 26개만 실행한다.

## v0.2.2 historical validation

v0.2.2 릴리스 당시에는 E1~E42 전체를 live regression으로 실행했다.

- `validate_repo`: PASS
- pytest: 34 passed
- installed runtime SHA: MATCH
- E1~E42 process: 42/42
- environment: 0/42
- H1: 40/42 (`E2/E3 = SKIP_SPECIAL_FORMAT`)
- hygiene: 42/42
- URL: 42/42
- contract oracle: 42/42
- `npm audit --omit=dev`: 0 vulnerabilities

이 42/42 수치는 **v0.2.2의 역사적 결과**이며 현재 release의 기본 실행 수를 의미하지 않는다.

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
- [ ] `python scripts/validate_authority_temporal_contract.py`
- [ ] `python -m pytest -q`
- [ ] installed runtime integrity PASS
- [ ] Core stability PASS
- [ ] Full active PASS
- [ ] `npm ci`
- [ ] `npm audit --omit=dev`
- [ ] `npm run mcp -- --help`
- [ ] real-law smoke PASS
