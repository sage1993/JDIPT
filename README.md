# JDIPT

**JDIPT (Judicial / Legal Interpretation Prompt Toolkit)**는 대한민국 법령해석요청 업무를 위한 **Codex Plugin** 소스 저장소입니다.

v0.2.0은 Skill-first Codex Plugin의 법률검토 파이프라인을 `Legal Issue Mapping → Legal Interpretation → Logic Validation → Answer Rendering`으로 확장하고, 기본 답변을 결론 우선 4단 구조로 단순화하는 릴리스입니다. ChatGPT 웹용 원격 MCP App은 별도 구성으로 유지합니다.

JDIPT는 다음 두 계층을 분리해 관리합니다.

- **작성·판단 계층:** `skills/law-interpretation-request` — 법령해석 대상 적합성, 법적 쟁점 매핑, 문언·체계·목적·연혁 검토, 내부 논리검증, 최종 문안 작성
- **법령 데이터 계층:** [`korean-law-mcp`](https://github.com/chrisryugj/korean-law-mcp) — 국가법령정보센터 기반 법령·판례·해석례 조회 및 인용 검증

> 원칙: JDIPT는 `korean-law-mcp` 소스를 복제하지 않습니다. 업스트림을 외부 의존성으로 사용하고 버전을 이 저장소에서 관리합니다.

## Plugin 패키징

JDIPT 저장소 루트 자체가 하나의 Plugin 패키지입니다. OpenAI의 현재 Codex Plugin 패키징 사양에 따라 `.codex-plugin/plugin.json`을 Plugin 진입점으로 사용하고, `.agents/plugins/marketplace.json`을 repo/team Marketplace 진입점으로 사용합니다. Plugin에 포함되는 Skill의 단일 원본은 `skills/`에서 관리합니다.

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
│     │  └─ legal-issue-mapping.md
│     └─ evals/
├─ config/
│  └─ codex.example.toml
├─ docs/
│  ├─ architecture.md
│  ├─ installation.md
│  ├─ plugin-packaging.md
│  ├─ upstream-mcp.md
│  └─ roadmap.md
├─ scripts/
│  └─ validate_repo.py
├─ AGENTS.md
├─ README.md
└─ package.json
```

`skills/law-interpretation-request/`를 `.agents/skills/` 또는 별도 배포 폴더에 중복 복제하지 않습니다. Plugin manifest의 `skills` 필드는 `./skills/`를 가리킵니다.

Marketplace 이름은 `sage1993`, Plugin 이름은 `jdipt`이며 Marketplace의 local source `.`가 저장소 루트 Plugin을 가리킵니다. Codex의 현재 Marketplace 로더는 `.` 또는 `./`를 Marketplace 루트로 해석하므로 Skill 원본을 이동하지 않고 배포할 수 있습니다.

현재 패키지는 **Skill-first Plugin**입니다. `korean-law-mcp`는 vendor하지 않고 Codex 로컬 환경에서 선택적으로 연결합니다. ChatGPT 웹에서 MCP 도구까지 제공하려면 별도의 원격/등록 MCP App 구성이 필요하며, 실제 App ID가 발급되기 전에는 `.app.json`이나 가짜 연결 정보를 만들지 않습니다.

상세 정책은 [`docs/plugin-packaging.md`](docs/plugin-packaging.md)를 참조하십시오.

공식 참고 문서:

- https://github.com/openai/codex/tree/main/codex-rs/skills/src/assets/samples/plugin-creator
- https://developers.openai.com/codex/mcp
- https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex

## Codex 설치

### GitHub 저장소에서 Codex Plugin 설치

공개 GitHub 저장소를 Codex Marketplace source로 등록한 뒤 Plugin을 설치합니다.

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

JDIPT는 공개 저장소이므로 별도의 저장소 읽기 권한 없이 Git source로 Marketplace를 등록할 수 있습니다.

### 로컬 clone에서 설치

```bash
git clone https://github.com/sage1993/JDIPT.git
cd JDIPT
codex plugin marketplace add .
codex plugin add jdipt@sage1993
codex plugin list
```

이미 clone한 저장소가 있다면 `git clone` 단계는 생략합니다.

설치 또는 refresh 후에는 **새 Codex thread**를 시작하여 Skill discovery와 자동 적용을 검증합니다. Plugin명이나 Skill명을 직접 언급하지 않은 일반 법령해석 요청에서 `law-interpretation-request`가 적용되어야 E26 자동 적용 Smoke Test를 PASS로 판정할 수 있습니다.

상세 설치·Smoke Test 절차는 [`docs/installation.md`](docs/installation.md)를 참조하십시오.

## 법률검토 파이프라인

v0.2.0부터 법령해석을 다음 네 계층으로 처리합니다.

```text
사용자 질문
→ Legal Issue Mapping
→ Legal Interpretation
→ Logic Validation
→ Answer Rendering
```

### 1. Legal Issue Mapping

법령해석 전에 질문을 법적으로 구조화합니다.

- 주체·행위·대상과 법적 상태 또는 분류 확인
- 법정 정의와 상·하위 개념 확인
- 본칙·적용요건·예외·특례·위임·적용 제외·준용 등 규범의 역할 확인
- 둘 이상의 규정이 관련될 때 동일 사항 중복규율·일반/특별·누적 적용·규율 공백·서로 다른 규율대상 구분
- 사실관계를 법적 요건에 연결하고 `충족` / `불충족` / `확인 필요`로 관리
- 질문을 반복하는 수준이 아니라 결론을 가르는 실제 **문제 발생 지점** 특정

이 내부 mapping 라벨과 상태표는 사용자가 분석표 공개를 요청하지 않는 한 최종 답변에 그대로 노출하지 않습니다.

### 2. Legal Interpretation

`references/interpretation-principles.md`에 따라 필요한 범위에서 문언 → 정의·참조 → 체계 → 목적 → 연혁 → 다른 법령 → 판례·법령해석례 순으로 검토합니다.

### 3. Logic Validation

`references/logic-validation.md`에서 논증의 전제, 추론 타당성, 개념 일관성, 누락 전제와 반례를 검증합니다. BLOCK이 있으면 수정·재검증하고 확인되지 않은 사실은 임의로 보충하지 않습니다.

### 4. Answer Rendering

내부 분석은 세밀하게 수행하지만 사용자 출력은 결론 우선성과 논증 연결성을 기준으로 단순화합니다.

## 출력 정책

모든 사용자용 최종 답변은 **Markdown**으로 작성합니다.

### 기본 출력 — 4단 Answer-first 법률검토형

사용자가 별도 형식을 지정하지 않으면 다음 구조를 기본으로 사용합니다.

1. 질의요지
2. 검토결론
3. 검토이유
4. 관련 법령 및 자료

`검토결론`에서 상세 이유보다 먼저 사용자가 확인하려는 법적 판단을 제시합니다. 결론이 확인되지 않은 사실에 따라 달라지면 조건부로 표시합니다.

`검토이유`에서는 정의·분류, 적용규정, 규정관계, 사실대입, 문제 발생 지점과 해석을 하나의 연결된 법률논증으로 작성합니다. 단일 쟁점에서는 `법적 정의`, `적용 규정`, `사안 적용`, `문제 발생 지점`, `해석`을 각각 소제목으로 기계적으로 분리하지 않습니다.

하위 소제목은 **서로 독립적으로 판단 가능한 복수의 법적 쟁점**이 있을 때만 사용합니다. 각 쟁점 내부에서는 다시 분석 단계를 과도하게 세분하지 않습니다.

### 법제처 법령해석요청서 — 명시적 요청 시에만

사용자가 `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설` 등 전용 형식을 **명시적으로 요청한 경우에만** 다음 1~3 구조로 전환합니다.

1. 질의요지
2. 해석대상 법령조문 및 관련 법령
   - 가. 해석대상 법령조문
   - 나. 관련 법령
3. 대립되는 의견 및 이유
   - 가. 갑설
   - 나. 을설

이 모드에서는 `4. 해석요청기관의 의견`부터 `8. 법령해석요청 체크리스트`까지 출력하지 않습니다.

### 공식자료 링크

법령·판례·법제처 해석례 등 참고자료는 실제 확인한 공식 URL이 있으면 자료명 자체에 Markdown 인라인 링크를 겁니다.

```markdown
[「○○법」 제10조](실제로 확인한 공식 URL)
[법제처 법령해석례 25-0000](실제로 확인한 공식 URL)
```

공식 URL을 확인할 수 없으면 URL 패턴을 추측하지 않고 `[공식 링크 확인 필요]`로 표시합니다.

## 내부 논리검증

최종 문안 생성 전 `references/logic-validation.md`에 따라 논증을 내부 검증합니다.

```text
법령·해석례 조사
→ 법적 쟁점 매핑
→ 법령해석
→ 법적 논증 초안
→ 문장·논증 분해
→ 기호화/표준형 변환
→ 전제 검토
→ 형식적 타당성 검토
→ 오류·전제 누락·반례 탐색
→ 필요시 갑설·을설 상호 비교
→ BLOCK 수정·재검증
→ 출처·현행성 최종 검증
→ Answer-first Markdown 최종 문안
```

내부 기호화(`P`, `Q`, `R`), 논리 점수, 오류분류명, 반례 탐색표와 수정 과정은 사용자가 논리감사나 형식논리 설명을 별도로 요청하지 않는 한 최종 답변에 표시하지 않습니다.

논리검증은 다음 안전장치를 포함합니다.

- A/B/P/Q 같은 **추상 논리 입력은 추상 상태로 검증**하고, 사용자가 제시하지 않은 실제 법령·판례·해석례·사실관계에 임의 대응시키지 않습니다.
- `갑설 아니면 을설`처럼 선택지가 제시되면 두 선택지가 가능한 해석 전부인지 별도로 확인하며, 확인되지 않으면 제3의 가능성을 배제하지 않습니다.
- 갑설·을설에서 같은 법률용어의 의미·범위가 근거 없이 달라지면 BLOCK으로 처리하고 공통 개념 기준을 먼저 확정합니다.
- 발견한 오류는 내부 분류명을 그대로 노출하지 않고 최종 법률검토 문장에 수정된 논증으로 반영합니다.

## 대표 논증 패턴

v0.2.0은 법제처 해석례에서 확인한 다음 세 패턴을 별도로 구분합니다.

- **법적 분류형 — 22-0351:** 대상의 정의·법적 분류 → 본칙 → 예외 해당 여부
- **중복규율형 — 17-0047:** 두 규정의 규율대상·기능 → 동일 사항 중복규율 여부 → 특별규정의 배타 적용 여부
- **규율공백형 — 20-0604:** 특별법이 구체 사항을 직접 규율하는지 → 규율 공백 → 일반법 보충 적용

중복규율형과 규율공백형을 같은 `특별법 우선` 규칙으로 기계적으로 처리하지 않습니다.

## 빠른 시작

### 1. 요구사항

- Python 3.11+ — 저장소 정적 검증
- Node.js `>=20.19.0` — `korean-law-mcp`를 로컬에서 사용할 경우
- 국가법령정보 공동활용 API 키 `LAW_OC` — `korean-law-mcp` 사용 시

### 2. 저장소 검증

```bash
python scripts/validate_repo.py
```

검증에는 Plugin manifest, Marketplace manifest, Skill 구조, 법적 쟁점 매핑·출력·논리검증 계약, MCP 버전, tracked secret 정책이 포함됩니다.

### 3. Codex 로컬에서 Korean Law MCP 사용 — 선택

`korean-law-mcp`는 실행 프로세스의 환경변수 `LAW_OC`를 읽습니다. 실제 API 키는 GitHub 저장소나 Codex 설정 파일에 기록하지 않습니다.

PowerShell 예시:

```powershell
$env:LAW_OC="발급받은_API_KEY"
```

bash/zsh 예시:

```bash
export LAW_OC="발급받은_API_KEY"
```

그 다음 `config/codex.example.toml`을 사용자 `~/.codex/config.toml`에 병합합니다.

```toml
[mcp_servers.korean_law]
command = "npx"
args = ["-y", "korean-law-mcp@4.12.1"]
enabled = true
env_vars = ["LAW_OC"]
```

또는 CLI에서 직접 등록할 수 있습니다.

```bash
codex mcp add korean_law --env LAW_OC=발급받은_API_KEY -- npx -y korean-law-mcp@4.12.1
codex mcp list
```

CLI의 `--env` 방식은 사용자의 Codex 설정에 값을 기록할 수 있으므로, 비밀값을 config에 남기고 싶지 않으면 OS 환경변수 + `env_vars` 방식을 권장합니다.

### 4. 저장소에서 MCP 직접 실행 — 선택

```bash
npm ci
npm run mcp
```

업스트림 초기 설정이 필요하면:

```bash
npm run mcp:setup
```

`.env.example`은 필요한 환경변수 이름을 기록하기 위한 참고 템플릿이며 JDIPT는 `.env` 자동 로딩을 전제로 하지 않습니다.

## MCP 사용 정책

Skill은 법적 근거를 확인할 때 다음 도구를 우선합니다.

1. `search_law` — 법령 식별
2. `get_law_text` — 현행 조문 원문
3. `search_decisions` / `get_decision_text` — 판례·해석례 등 결정례
4. `legal_analysis` — 인용 검증 등 정밀 검토
5. `discover_tools` → `execute_tool` — 직접 노출되지 않은 연혁·세부 도구가 필요한 경우

검색 결과만으로 조문을 확정하지 않고, 최종 문안에 사용할 조문은 본문 조회로 재확인합니다.

MCP가 연결되지 않은 환경에서는 Skill의 공식자료 우선 정책에 따라 국가법령정보센터 등 공식 출처를 사용합니다.

## 업스트림 관리

`korean-law-mcp`는 이 저장소의 `package.json`에서 정확한 버전으로 고정합니다. Dependabot이 주 1회 업데이트 가능성을 확인합니다. 업스트림 버전 변경 PR은 최소한 다음을 확인한 뒤 반영합니다.

- MCP 서버 기동
- 직접 노출 도구명 변경 여부
- `search_law` / `get_law_text` 동작
- 결정례 검색·본문 조회 동작
- Skill의 도구명 참조 정합성
- 기본 4단 / 명시적 법제처 1~3 출력 모드 유지
- Legal Issue Mapping 및 문제 발생 지점 특정 규칙 유지
- Answer-first / Narrative Coherence 규칙 유지
- 공식자료 인라인 하이퍼링크 정책 유지
- 논리검증 후 출처·현행성 검증 순서 유지
- `.codex-plugin/plugin.json`과 `package.json` 버전 일치

자세한 내용은 `docs/upstream-mcp.md`와 `docs/plugin-packaging.md`를 참조하십시오.

## v0.1.0 공개 상태

JDIPT v0.1.0은 **Codex Plugin 신규 설치, Skill 자동 적용 회귀평가(E10~E26), Korean Law MCP 실제 E2E 검증을 완료한 공개 배포 가능 버전**입니다.

완료된 실제 검증:

- 신규 설치 환경 Plugin smoke test: PASS
- E10~E26 실제 회귀평가: PASS
- Korean Law MCP 실제 E2E: PASS
- `npm audit --omit=dev`: 0 vulnerabilities

## v0.2.0 릴리스 Gate

v0.2.0은 다음 검증을 모두 완료한 뒤 release-ready로 판정합니다.

```bash
python scripts/validate_repo.py
npm ci
npm audit --omit=dev
npm run mcp -- --help
```

행동 검증은 E1~E38을 대상으로 하며 E26 Plugin 자동 적용을 새 컨텍스트에서 3회 반복합니다. E36~E38은 각각 22-0351, 17-0047, 20-0604 패턴을 검증합니다. 실제 검증이 완료되기 전에는 v0.2.0을 PASS로 표시하지 않습니다.

ChatGPT 웹용 원격/등록 MCP App, `.app.json`, Plugin Directory 등록·심사는 별도 작업입니다.

## 주의

JDIPT가 작성한 결과는 법률자문 확정 의견이 아니라 검토·제출용 초안입니다. 실제 제출 전 사실관계, 현행 법령, 조문 버전, 판례 및 법령해석례 원문을 재확인해야 합니다.
