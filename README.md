# JDIPT

**JDIPT (Judicial / Legal Interpretation Prompt Toolkit)**는 대한민국 법령해석요청 업무를 위한 **Codex Plugin** 소스 저장소입니다.

현재 공개 버전은 **v0.2.2**입니다. v0.2 계열은 `Legal Issue Mapping → Legal Interpretation → Source Completeness / Counterevidence → Logic Validation → Answer Rendering` 파이프라인, 결론 우선 4단 출력, explicit-only 호출, 참조 별표·별지서식 resolution hard gate, 최종 rendering/source URL hard gate와 결정론적 회귀검증을 제공합니다.

> 현재 배포 상태: **JDIPT v0.2.2 RELEASE GATE = PASS**
> 최종 검증 기준 모델: `gpt-5.6-luna`

## 핵심 구성

JDIPT는 다음 책임을 분리해 관리합니다.

- **작성·판단 계층:** `skills/law-interpretation-request` — 법령해석 대상 적합성, 법적 쟁점 매핑, 문언·체계·목적·연혁 검토, 내부 논리검증, 최종 문안 작성
- **Source Completeness / Counterevidence:** 명시적 제한 부재만으로 가능 결론을 확정하지 않고, 관련 하위법령·별표·별지서식·절차규정의 기능과 위임근거를 확인
- **출처·렌더링 안전장치:** 참조자료 미해결 시 확정 결론 BLOCK, 불완전·손상 URL 차단, 최종 4단 구조 재검증
- **법령 데이터 계층:** [`korean-law-mcp`](https://github.com/chrisryugj/korean-law-mcp) — 국가법령정보센터 기반 법령·판례·해석례 조회 및 인용 검증
- **회귀검증 계층:** E1–E42 contract oracle, installed runtime SHA-256 integrity, critical stability suite, full release gate

`korean-law-mcp` 소스는 저장소에 복제하지 않고 외부 의존성으로 사용합니다. 현재 고정 버전은 `4.12.1`입니다.

## Plugin 패키징

저장소 루트 자체가 하나의 Codex Plugin 패키지입니다.

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
│  ├─ architecture.md
│  ├─ installation.md
│  ├─ plugin-packaging.md
│  ├─ roadmap.md
│  ├─ upstream-mcp.md
│  └─ validation/
├─ scripts/
│  ├─ validate_repo.py
│  ├─ regression_checks.py
│  ├─ regression_oracles.py
│  ├─ plugin_integrity.py
│  └─ run_release_gate.py
├─ tests/
├─ run_jdipt_full_regression_v4.py
├─ AGENTS.md
├─ README.md
└─ package.json
```

Plugin manifest의 `skills` 필드는 `./skills/`를 가리키며, Skill 원본을 `.agents/skills/` 등에 중복 복제하지 않습니다.

- Marketplace: `sage1993`
- Plugin: `jdipt`
- 공개 설치 ID: `jdipt@sage1993`
- 현재 버전: `0.2.2`
- 호출 정책: **explicit-only**
- `allow_implicit_invocation: false`

## 설치

### GitHub 저장소에서 설치

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

JDIPT 저장소는 public이므로 Git source를 통한 Marketplace 등록이 가능합니다.

### 로컬 clone에서 설치

```bash
git clone https://github.com/sage1993/JDIPT.git
cd JDIPT
codex plugin marketplace add .
codex plugin add jdipt@sage1993
codex plugin list
```

설치 또는 refresh 후에는 **새 Codex thread**에서 Skill을 명시 호출합니다.

```text
$law-interpretation-request 이 법령 쟁점을 검토해줘.
```

자동 Skill 선택은 v0.2.2 release gate의 요구사항이 아닙니다.

상세 절차는 [`docs/installation.md`](docs/installation.md)를 참조하십시오.

## 법률검토 파이프라인

```text
사용자 질문
→ 법령해석 대상 적합성 점검
→ Legal Issue Mapping
→ Legal Interpretation
→ Source Completeness / Counterevidence
→ Logic Validation
→ 출처·현행성 검증
→ Answer Rendering
```

### Legal Issue Mapping

- 주체·행위·대상과 법적 상태 또는 분류 확인
- 법정 정의와 상·하위 개념 확인
- 본칙·예외·특례·위임·적용 제외·준용 등 규범 역할 확인
- 동일 사항 중복규율 / 일반·특별 / 누적 적용 / 규율 공백 / 다른 규율대상 구분
- 사실관계를 법적 요건에 `충족` / `불충족` / `확인 필요`로 연결
- 결론을 가르는 실제 문제 발생 지점 특정

### Legal Interpretation

필요한 범위에서 문언 → 정의·참조 → 체계 → 목적 → 연혁 → 다른 법령 → 판례·법령해석례 순으로 검토합니다.

### Source Completeness / Counterevidence

- 명시적 제한 규정이 없다는 이유만으로 가능 결론을 확정하지 않습니다.
- 결론에 중요한 별표·별지서식이 본문에서 직접 참조되면 실제 원문을 확인하거나 미해결 상태를 명시합니다.
- 별표·별지서식의 존재만으로 반대 결론을 자동 확정하지 않고, 위임근거·규범적 기능·상위법과의 정합성을 평가합니다.
- 중대한 반대근거 또는 참조자료가 해결되지 않으면 결론을 조건부 또는 확인 필요로 낮춥니다.

### Logic Validation

논증의 전제, 개념 일관성, 필요·충분조건, 형식적 타당성, 누락 전제와 반례를 내부 검증합니다. A/B/P/Q 같은 추상 fixture는 실제 법령·판례에 임의 대응시키지 않고 closed-world 입력으로 처리합니다.

### Answer Rendering

기본 사용자 답변은 정확히 다음 4단 Markdown 구조를 사용합니다.

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

사용자가 `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설` 등을 명시한 경우에만 법제처 제출용 1~3 구조로 전환합니다.

## 출처 및 URL 정책

- 법령·판례·법제처 해석례는 현재 실행에서 실제 확인한 공식 URL을 우선합니다.
- URL 식별자가 비어 있거나 끝이 `=`인 미완성 URL을 출력하지 않습니다.
- 잘못된 percent escape를 출력하지 않습니다.
- `law.go.kr/LSW/flDownload.do`의 `flNm` 기반 파일명 직접링크는 최종 사용자 링크로 사용하지 않습니다.
- 안정적인 공식 상위 법령/별표 페이지를 확인하지 못한 경우 URL을 추측하지 않고 `[공식 링크 확인 필요]`로 처리합니다.

## 대표 논증 패턴

- **법적 분류형 — 22-0351:** 법적 정의·분류 → 본칙 → 예외 해당 여부
- **중복규율형 — 17-0047:** 두 규정의 규율대상·기능 → 동일 사항 여부 → 특별규정의 배타 적용 여부
- **규율공백형 — 20-0604:** 특별법의 직접 규율 여부 → 규율 공백 → 일반법 보충 적용

## 빠른 시작

### 요구사항

- Python 3.11+
- Node.js `>=20.19.0` — `korean-law-mcp` 사용 시
- 국가법령정보 공동활용 API 키 `LAW_OC` — `korean-law-mcp` 사용 시

### 저장소 정적 검증

```bash
python scripts/validate_repo.py
python -m pytest -q
```

### Korean Law MCP 사용 — 선택

PowerShell:

```powershell
$env:LAW_OC="발급받은_API_KEY"
```

`~/.codex/config.toml` 예시:

```toml
[mcp_servers.korean_law]
command = "npx"
args = ["-y", "korean-law-mcp@4.12.1"]
enabled = true
env_vars = ["LAW_OC"]
```

저장소에서 직접 실행:

```bash
npm ci
npm run mcp -- --help
```

실제 API 키는 저장소나 예제 설정에 커밋하지 않습니다.

## v0.2.2 검증 상태

2026-08-23 기준 release validation 결과:

| Gate | 결과 |
|---|---|
| `python scripts/validate_repo.py` | PASS |
| `python -m pytest -q` | **34 passed** |
| Critical stability | PASS |
| E25 repeated stability | **3/3** |
| E37 repeated stability | **3/3** |
| Full regression process | **42/42** |
| Environment errors | **0/42** |
| H1 | **40/42** — E2/E3는 `SKIP_SPECIAL_FORMAT` |
| Hygiene | **42/42** |
| URL integrity | **42/42** |
| Contract oracle | **42/42** |
| Installed runtime SHA | MATCH |
| `npm audit --omit=dev` | **0 vulnerabilities** |
| Real-law smoke | PASS |

최종 행동 검증 모델은 `gpt-5.6-luna`입니다.

상세 증거는 [`docs/validation/v0.2.2-source-rendering.md`](docs/validation/v0.2.2-source-rendering.md)를 참조하십시오.

## Release gate 실행

결정론적 gate:

```bash
python scripts/run_release_gate.py
```

Critical stability까지:

```bash
python scripts/run_release_gate.py --critical-only --codex <codex-cli>
```

전체 release gate:

```bash
python scripts/run_release_gate.py --full --codex <codex-cli>
```

기본 regression 모델은 `gpt-5.6-luna`입니다.

## 문서

- [Architecture](docs/architecture.md)
- [Installation](docs/installation.md)
- [Plugin packaging](docs/plugin-packaging.md)
- [Roadmap](docs/roadmap.md)
- [Upstream MCP](docs/upstream-mcp.md)
- [v0.2.2 validation](docs/validation/v0.2.2-source-rendering.md)

## 버전 이력 요약

- **v0.1.0:** Plugin/Skill 저장소화, MCP 연동 기반, 초기 논리검증·패키징
- **v0.2.0:** Legal Issue Mapping + Answer-first 4단 출력 + explicit-only 호출
- **v0.2.1:** Source Completeness / Counterevidence Gate
- **v0.2.2:** Referenced Source Resolution / Final Rendering hard gate, URL 안정성, deterministic oracle·runtime integrity·critical stability·release orchestration

상세 계획은 [`docs/roadmap.md`](docs/roadmap.md)를 참조하십시오.

## 주의

JDIPT가 작성한 결과는 법률자문 확정 의견이 아니라 검토·제출용 초안입니다. 실제 제출 전 사실관계, 현행 법령, 조문 버전, 판례 및 법령해석례 원문을 재확인해야 합니다.
