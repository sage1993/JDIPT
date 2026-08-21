# JDIPT Codex 설치 가이드

## 배포 모델

JDIPT 저장소는 저장소 루트 자체가 Codex Plugin이며, `.agents/plugins/marketplace.json`을 통해 repo/team Marketplace로 노출한다.

- Marketplace 이름: `sage1993`
- Plugin 이름: `jdipt`
- Plugin source: 저장소 루트 (`.`)
- 설치 ID: `jdipt@sage1993`

Codex의 Marketplace 로더는 `.agents/plugins/marketplace.json`을 지원하며 local plugin source의 `.` 또는 `./`를 Marketplace 루트로 해석한다. 따라서 `skills/`를 다른 경로로 복제하지 않고 현재 단일 원본 구조를 유지한다.

## GitHub에서 설치

공개 GitHub 저장소를 Marketplace source로 등록한 뒤 Plugin을 설치한다.

```bash
codex plugin marketplace add sage1993/JDIPT
codex plugin add jdipt@sage1993
codex plugin list
```

설치 후에는 **새 Codex thread**를 시작하여 Skill discovery와 자동 적용을 검증한다.

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

## 설치본 갱신

기존 Plugin 설치본에서 새 버전을 확인할 때에는 현재 Plugin Directory/Marketplace가 제공하는 refresh 경로를 우선 사용한다. 로컬 clone 기반 테스트에서는 검증할 branch 또는 commit을 최신 상태로 만든 뒤 새 thread에서 다시 테스트한다.

이전 대화에서 이미 로드된 Skill 상태를 재사용하면 실제 새 버전의 자동 적용 여부를 확인하기 어렵기 때문에 버전 갱신 후에는 반드시 새 컨텍스트를 사용한다.

### v0.2.0 행동검증 전 설치본 확인

E26 또는 설치본을 사용하는 행동검증은 **실제 resolved Plugin/Skill source가 v0.2.0인지 확인한 뒤** 실행한다.

Windows의 기본 설치 경로를 사용하는 경우 예시:

```powershell
$jdipt = Join-Path $HOME ".codex\plugins\jdipt"
Get-Content "$jdipt\.codex-plugin\plugin.json"
Select-String -Path "$jdipt\skills\law-interpretation-request\SKILL.md" -Pattern '# 2. 검토결론','최종 Rendering Gate'
```

PASS 기준:

- 설치본 manifest의 `version`이 `0.2.0`
- 설치본 `SKILL.md`에 `# 2. 검토결론` 존재
- 설치본 `SKILL.md`에 `최종 Rendering Gate` 존재

설치 경로가 다르면 `codex plugin list`가 표시하는 설치 상태와 실제 Plugin 저장 위치를 기준으로 동일 항목을 확인한다.

v0.2.0 설치 여부를 확인할 수 없거나 설치본이 여전히 v0.1.0이면 해당 실행은 v0.2.0의 PASS/FAIL로 계산하지 않는다. 먼저 refresh 또는 재설치로 설치본을 갱신한다.

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
4. 기본 출력 계약이 정확히 다음 4단 Markdown 구조로 나타난다.

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

5. `# 2. 검토결론`이 상세 검토이유보다 먼저 나온다.
6. 단일 쟁점에서 `법적 정의`, `적용 규정`, `사안 적용`, `문제 발생 지점`, `해석`을 각각 하위 제목으로 기계적으로 나누지 않는다.
7. `$law-interpretation-request`, `@jdipt`, Skill/Plugin activation 문자열 등 실행 메타데이터가 사용자 답변에 노출되지 않는다.
8. 공식자료 링크는 현재 실행에서 실제 확인한 완전한 URL만 사용하며 식별자가 비어 있거나 끝이 `=`인 미완성 URL을 출력하지 않는다.
9. 내부 논리검증 기호화·점수·오류분류명을 사용자에게 노출하지 않는다.
10. 일반 비법률 요청에서 Skill이 과도하게 활성화되지 않는다.

정적 패키징 검증과 실제 Codex 설치 Smoke Test는 별개다. 저장소 정적 검증이 PASS하더라도 실제 설치 및 자동 Skill activation을 수행하지 않았다면 E26을 PASS로 판정하지 않는다.

v0.2.0 release gate에서는 E26을 **서로 독립된 새 컨텍스트에서 3회** 실행하며 세 번 모두 직접 Skill 호출 없이 위 계약이 나타나야 PASS다.

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
- 신규 설치 또는 refresh 후 설치본 version/source 확인
- E26 자동 Skill 적용 Smoke Test 3회

## 수동 공개 release gate

공개 전에는 다음 정적 검증과 Node MCP smoke를 실행한다.

```bash
python scripts/validate_repo.py
npm ci
npm audit --omit=dev
npm run mcp -- --help
```

행동 회귀는 E1~E38을 실행한다. E36~E38은 각각 22-0351 법적 분류형, 17-0047 중복규율형, 20-0604 규율공백형을 검증한다.

v0.1.0 공개 검증 결과:

- Plugin fresh install smoke: PASS
- E10~E26 regression: PASS
- Korean Law MCP E2E: PASS
- `npm audit --omit=dev`: 0 vulnerabilities

v0.2.0은 위 release gate와 E1~E38 행동 검증이 실제로 완료되기 전에는 PASS로 표시하지 않는다.
