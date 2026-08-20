# JDIPT Codex 설치 가이드

## 배포 모델

JDIPT 저장소는 저장소 루트 자체가 Codex Plugin이며, `.agents/plugins/marketplace.json`을 통해 repo/team Marketplace로 노출한다.

- Marketplace 이름: `sage1993`
- Plugin 이름: `jdipt`
- Plugin source: 저장소 루트 (`.`)
- 설치 ID: `jdipt@sage1993`

Codex의 Marketplace 로더는 `.agents/plugins/marketplace.json`을 지원하며 local plugin source의 `.` 또는 `./`를 Marketplace 루트로 해석한다. 따라서 `skills/`를 다른 경로로 복제하지 않고 현재 단일 원본 구조를 유지한다.

## GitHub에서 설치

GitHub 저장소에 접근할 수 있는 환경에서는 다음 순서로 설치한다.

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

설치 후에는 **새 Codex thread**를 시작하여 Skill discovery와 자동 적용을 검증한다.

현재 저장소가 private인 동안에는 GitHub 읽기 권한과 Git 인증이 있는 사용자만 Git source로 Marketplace를 추가할 수 있다. 불특정 사용자에게 공개 배포하려면 저장소를 public으로 전환하거나, 사용자들이 접근할 수 있는 별도의 Git remote에 배포해야 한다.

## 로컬 clone에서 설치

개발 중인 로컬 저장소를 Marketplace로 직접 등록할 수도 있다.

```bash
git clone https://github.com/sage1993/JDIPT.git
cd JDIPT
codex plugin marketplace add .
codex plugin add jdipt@sage1993
codex plugin list
```

이미 로컬 clone이 있다면 `git clone` 단계는 생략한다.

## 설치 Smoke Test

새 thread에서 Plugin명이나 Skill명을 명시하지 않고 일반 법령해석 질문을 입력한다.

예시:

```text
기존 건축물 증축 시 대지 안의 공지 규정이 적용되는지 검토해줘.
```

PASS 조건:

1. `codex plugin list`에서 `jdipt@sage1993` 설치 상태가 확인된다.
2. 새 thread에서 `law-interpretation-request` Skill이 discovery 대상이 된다.
3. 사용자가 `@jdipt` 또는 Skill명을 직접 입력하지 않아도 법령해석 요청에서 Skill이 적용된다.
4. 기본 출력 계약인 1~6 Markdown 구조가 유지된다.
5. 일반 비법률 요청에서 Skill이 과도하게 활성화되지 않는다.

정적 패키징 검증과 실제 Codex 설치 Smoke Test는 별개다. 저장소 정적 검증이 PASS하더라도 실제 설치 및 자동 Skill activation을 수행하지 않았다면 E26을 PASS로 판정하지 않는다.

## Korean Law MCP

JDIPT Plugin은 Skill-first 구조이므로 Plugin 설치 자체는 `korean-law-mcp` 없이 가능하다. 법령·판례·해석례 조회 도구를 Codex 로컬에서 사용하려면 저장소의 `config/codex.example.toml` 및 README의 MCP 설정 절차를 별도로 적용한다.

## 배포 전 확인

공개 배포 전 최소 확인 항목:

- `.codex-plugin/plugin.json` 유효성
- `.agents/plugins/marketplace.json` 유효성
- `plugin.json`의 `name`이 `jdipt`인지 확인
- Marketplace entry의 `name`이 `jdipt`인지 확인
- Marketplace 이름이 `sage1993`인지 확인
- `source.path`가 저장소 루트 `.`를 가리키는지 확인
- `policy.installation = AVAILABLE`
- `policy.authentication = ON_INSTALL`
- `category = Productivity`
- `python scripts/validate_repo.py`
- 신규 설치 후 E26 자동 Skill 적용 Smoke Test

## 수동 공개 release gate

공개 전에는 다음 정적 검증과 Node MCP smoke를 실행한다.

```bash
python scripts/validate_repo.py
npm ci
npm run mcp -- --help