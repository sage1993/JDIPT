# JDIPT

**JDIPT (Judicial / Legal Interpretation Prompt Toolkit)**는 대한민국 법령해석요청 업무를 위한 Codex/ChatGPT 플러그인 소스 저장소입니다.

이 저장소는 다음 두 계층을 분리해 관리합니다.

- **작성·판단 계층:** `skills/law-interpretation-request` — 법령해석 대상 적합성, 질의 보정, 문언·체계·목적·연혁 검토, 내부 논리검증, 최종 문안 작성
- **법령 데이터 계층:** [`korean-law-mcp`](https://github.com/chrisryugj/korean-law-mcp) — 국가법령정보센터 기반 법령·판례·해석례 조회 및 인용 검증

> 원칙: JDIPT는 `korean-law-mcp` 소스를 복제하지 않습니다. 업스트림을 외부 의존성으로 사용하고 버전만 이 저장소에서 관리합니다.

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

내부 기호화(`P`, `Q`, `R`), 논리 점수, 반례 탐색표와 수정 과정은 사용자가 별도로 요청하지 않는 한 최종 답변에 표시하지 않습니다.

## 저장소 구조

```text
JDIPT/
├─ README.md
├─ AGENTS.md
├─ package.json
├─ .env.example
├─ .github/
│  └─ dependabot.yml
├─ config/
│  └─ codex.example.toml
├─ docs/
│  ├─ architecture.md
│  ├─ upstream-mcp.md
│  └─ roadmap.md
├─ scripts/
│  └─ validate_repo.py
└─ skills/
   └─ law-interpretation-request/
      ├─ SKILL.md
      ├─ agents/openai.yaml
      ├─ references/
      │  ├─ logic-validation.md
      │  ├─ request-format.md
      │  └─ source-policy.md
      └─ evals/
```

## 빠른 시작

### 1. 요구사항

- Node.js `>=20.19.0`
- Python 3.11+ (저장소 검증용)
- 국가법령정보 공동활용 API 키 `LAW_OC` 권장

### 2. MCP 설치

```bash
npm install
```

직접 실행:

```bash
npm run mcp
```

업스트림 초기 설정:

```bash
npm run mcp:setup
```

### 3. API 키 입력

`korean-law-mcp`는 실행 프로세스의 환경변수 `LAW_OC`를 읽습니다. 실제 API 키는 GitHub 저장소에 커밋하지 않습니다.

#### Codex에서 사용하는 경우 — 권장

Codex는 기본적으로 `~/.codex/config.toml`에 MCP 설정을 저장합니다. Windows에서는 일반적으로 다음 경로입니다.

```text
%USERPROFILE%\.codex\config.toml
```

`config/codex.example.toml`을 참고하여 다음처럼 등록합니다.

```toml
[mcp_servers.korean_law]
command = "npx"
args = ["-y", "korean-law-mcp@4.12.1"]
enabled = true

[mcp_servers.korean_law.env]
LAW_OC = "발급받은_API_KEY"
```

또는 Codex CLI에서 환경변수와 함께 서버를 등록할 수 있습니다.

```bash
codex mcp add korean_law --env LAW_OC=발급받은_API_KEY -- npx -y korean-law-mcp@4.12.1
```

등록 후 다음으로 확인합니다.

```bash
codex mcp list
```

#### 저장소에서 MCP를 직접 실행하는 경우

실행 프로세스에 `LAW_OC` 환경변수를 전달합니다.

PowerShell:

```powershell
$env:LAW_OC="발급받은_API_KEY"
npm run mcp
```

bash/zsh:

```bash
LAW_OC="발급받은_API_KEY" npm run mcp
```

`.env.example`은 필요한 환경변수 이름을 기록하기 위한 참고 템플릿으로 유지합니다. JDIPT는 `.env` 파일의 자동 로딩을 전제로 하지 않습니다.

#### GitHub Actions에서 사용하는 경우

Repository `Settings → Secrets and variables → Actions`에 `LAW_OC` Repository secret을 등록합니다. 워크플로 파일에 실제 키를 직접 쓰지 않습니다.

### 4. Codex MCP 설정

`config/codex.example.toml` 내용을 사용자 Codex 설정에 반영합니다.

### 5. Skill 설치

```text
skills/law-interpretation-request/
```

폴더를 사용자 Agent Skills 경로의 `law-interpretation-request/`로 복사합니다.

### 6. 검증

```bash
python scripts/validate_repo.py
```

## MCP 사용 정책

Skill은 법적 근거를 확인할 때 다음 도구를 우선합니다.

1. `search_law` — 법령 식별
2. `get_law_text` — 현행 조문 원문
3. `search_decisions` / `get_decision_text` — 판례·해석례 등 결정례
4. `legal_analysis` — 인용 검증 등 정밀 검토
5. `discover_tools` → `execute_tool` — 직접 노출되지 않은 연혁·세부 도구가 필요한 경우

검색 결과만으로 조문을 확정하지 않고, 최종 문안에 사용할 조문은 본문 조회로 재확인합니다.

## 업스트림 관리

`korean-law-mcp`는 이 저장소의 `package.json`에서 정확한 버전으로 고정합니다. Dependabot이 주 1회 업데이트 가능성을 확인합니다. 업스트림 버전 변경 PR은 최소한 다음을 확인한 뒤 반영합니다.

- MCP 서버 기동
- 직접 노출 도구명 변경 여부
- `search_law` / `get_law_text` 동작
- 결정례 검색·본문 조회 동작
- Skill의 도구명 참조 정합성
- 기본 1~6 / 명시적 법제처 1~3 출력 모드가 유지되는지
- 요청취지가 사용자 질문에서 합리적으로 유추되는지
- 공식자료 인라인 하이퍼링크 정책이 유지되는지
- 논리검증 후 출처·현행성 검증 순서가 유지되는지

자세한 내용은 `docs/upstream-mcp.md`를 참조하십시오.

## 주의

JDIPT가 작성한 결과는 법률자문 확정 의견이 아니라 검토·제출용 초안입니다. 실제 제출 전 사실관계, 현행 법령, 조문 버전, 판례 및 법령해석례 원문을 재확인해야 합니다.
