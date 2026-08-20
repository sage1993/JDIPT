# JDIPT

**JDIPT (Judicial / Legal Interpretation Prompt Toolkit)**는 대한민국 법령해석요청 업무를 위한 **Codex Plugin** 소스 저장소입니다.

v0.1.0은 Skill-first Codex Plugin으로 배포하며, ChatGPT Plugin Directory 등록 및 ChatGPT 웹용 원격 MCP App은 포함하지 않습니다.

JDIPT는 다음 두 계층을 분리해 관리합니다.

- **작성·판단 계층:** `skills/law-interpretation-request` — 법령해석 대상 적합성, 질의 보정, 문언·체계·목적·연혁 검토, 내부 논리검증, 최종 문안 작성
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

설치 후에는 **새 Codex thread**를 시작하여 Skill discovery와 자동 적용을 검증합니다. Plugin명이나 Skill명을 직접 언급하지 않은 일반 법령해석 요청에서 `law-interpretation-request`가 적용되어야 E26 자동 적용 Smoke Test를 PASS로 판정할 수 있습니다.

상세 설치·Smoke Test 절차는 [`docs/installation.md`](docs/installation.md)를 참조하십시오.

## 출력 정책

모든 사용자용 최종 답변은 **Markdown**으로 작성합니다.

### 기본 출력 — 1~6 법률검토형

사용자가 별도 형식을 지정하지 않으면 다음 구조를 기본으로 사용합니다.

1. 요청취지
2. 질의 배경 및 사실관계
3. 관련 법령 및 조문
4. 해석상 쟁점
5. 법률검토
6. 첨부자료

별도 `제목` 또는 `질의사항` 항목은 생성하지 않습니다.

`1. 요청취지`는 사용자의 질문·사실관계·요구사항을 분석하여 실제 검토 목적을 합리적으로 유추해 작성합니다. 사용자가 제공하지 않은 사업목적, 처분경위, 기관입장 등을 사실처럼 추가하지 않으며, 요청취지의 불확실성이 법적 결론에 영향을 주는 경우 `확인 필요`로 표시합니다.

단순한 `검토해줘`, `법령을 해석해줘`, `질의서 작성해줘`, 일반적인 법령해석요청서 작성 요청은 이 기본 모드를 사용합니다.

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
→ 법적 논증 초안
→ 문장·논증 분해
→ 기호화/표준형 변환
→ 전제 검토
→ 형식적 타당성 검토
→ 오류·전제 누락·반례 탐색
→ 필요시 갑설·을설 상호 비교
→ BLOCK 수정·재검증
→ 출처·현행성 최종 검증
→ Markdown 최종 문안
```

내부 기호화(`P`, `Q`, `R`), 논리 점수, 오류분류명, 반례 탐색표와 수정 과정은 사용자가 논리감사나 형식논리 설명을 별도로 요청하지 않는 한 최종 답변에 표시하지 않습니다.

논리검증은 다음 안전장치를 포함합니다.

- A/B/P/Q 같은 **추상 논리 입력은 추상 상태로 검증**하고, 사용자가 제시하지 않은 실제 법령·판례·해석례·사실관계에 임의 대응시키지 않습니다.
- `갑설 아니면 을설`처럼 선택지가 제시되면 두 선택지가 가능한 해석 전부인지 별도로 확인하며, 확인되지 않으면 제3의 가능성을 배제하지 않습니다.
- 갑설·을설에서 같은 법률용어의 의미·범위가 근거 없이 달라지면 BLOCK으로 처리하고 공통 개념 기준을 먼저 확정합니다.
- 발견한 오류는 내부 분류명을 그대로 노출하지 않고 최종 법률검토 문장에 수정된 논증으로 반영합니다.

## 빠른 시작

### 1. 요구사항

- Python 3.11+ — 저장소 정적 검증
- Node.js `>=20.19.0` — `korean-law-mcp`를 로컬에서 사용할 경우
- 국가법령정보 공동활용 API 키 `LAW_OC` — `korean-law-mcp` 사용 시

### 2. 저장소 검증

```bash
python scripts/validate_repo.py
```

검증에는 Plugin manifest, Marketplace manifest, Skill 구조, 출력·논리검증 계약, MCP 버전, tracked secret 정책이 포함됩니다.

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
- 기본 1~6 / 명시적 법제처 1~3 출력 모드 유지
- 요청취지 유추 규칙 유지
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

정적 공개 release gate는 다음 수동 절차로 수행합니다.

```bash
python scripts/validate_repo.py
npm ci
npm run mcp -- --help
```

ChatGPT 웹용 원격/등록 MCP App, `.app.json`, Plugin Directory 등록·심사는 이 버전에 포함되지 않습니다.

## 주의

JDIPT가 작성한 결과는 법률자문 확정 의견이 아니라 검토·제출용 초안입니다. 실제 제출 전 사실관계, 현행 법령, 조문 버전, 판례 및 법령해석례 원문을 재확인해야 합니다.
