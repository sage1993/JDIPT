# JDIPT

**JDIPT (Judicial / Legal Interpretation Prompt Toolkit)**는 대한민국 법령해석요청 업무를 위한 Codex/ChatGPT 플러그인 소스 저장소입니다.

이 저장소는 다음 두 계층을 분리해 관리합니다.

- **작성·판단 계층:** `skills/law-interpretation-request` — 법령해석 대상 적합성, 질의 보정, 문언·체계·목적·연혁 검토, 갑설·을설 작성
- **법령 데이터 계층:** [`korean-law-mcp`](https://github.com/chrisryugj/korean-law-mcp) — 국가법령정보센터 기반 법령·판례·해석례 조회 및 인용 검증

> 원칙: JDIPT는 `korean-law-mcp` 소스를 복제하지 않습니다. 업스트림을 외부 의존성으로 사용하고 버전만 이 저장소에서 관리합니다.

## 현재 범위

### 법제처 법령해석요청서 모드

최종 본문은 다음 1~3만 생성합니다.

1. 질의요지
2. 해석대상 법령조문 및 관련 법령
   - 가. 해석대상 법령조문
   - 나. 관련 법령
3. 대립되는 의견 및 이유
   - 가. 갑설
   - 나. 을설

`4. 해석요청기관의 의견`부터 `8. 법령해석요청 체크리스트`까지는 출력하지 않습니다. 체크리스트의 적합성 기준은 내부 검증에만 사용합니다.

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

### 3. Codex MCP 설정

`config/codex.example.toml` 내용을 사용자 Codex 설정에 반영합니다.

중요: API 키는 저장소에 커밋하지 않습니다.

### 4. Skill 설치

```text
skills/law-interpretation-request/
```

폴더를 사용자 Agent Skills 경로의 `law-interpretation-request/`로 복사합니다.

### 5. 검증

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

자세한 내용은 `docs/upstream-mcp.md`를 참조하십시오.

## 주의

JDIPT가 작성한 결과는 법률자문 확정 의견이 아니라 검토·제출용 초안입니다. 실제 제출 전 사실관계, 현행 법령, 조문 버전, 판례 및 법령해석례 원문을 재확인해야 합니다.
