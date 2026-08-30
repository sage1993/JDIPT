# JDIPT Repository Instructions

## Windows UTF-8 tool I/O

Repository Markdown/YAML/text files are UTF-8. On Windows PowerShell 5.1, never read repository text with bare `Get-Content` or `Select-String`.

- Use `Get-Content -Raw -Encoding UTF8 <path>` for full-file reads.
- Use `Select-String -Encoding UTF8 ...` when searching repository text.
- If output is still mojibake, use Python `Path(...).read_text(encoding="utf-8")`.
- Treat mojibake in Skill/reference content as an environment failure.

## 목적

이 저장소는 대한민국 법령해석요청 업무용 ChatGPT/Codex Plugin, Skill, `korean-law-mcp` 연동 설정을 관리한다.

## Plugin 패키징 원칙

- 저장소 루트 자체가 JDIPT Plugin 패키지다.
- `.codex-plugin/plugin.json`은 필수 진입점이며 Plugin ID는 `jdipt`로 유지한다.
- Plugin에 포함되는 Skill의 단일 원본은 `skills/law-interpretation-request/`다.
- 같은 Skill을 `.agents/skills/law-interpretation-request/`에 복제하지 않는다.
- manifest의 `skills` 경로는 `./skills/`로 유지한다.
- `.codex-plugin/plugin.json`의 `version`은 `package.json`의 `version`과 일치시킨다.
- `korean-law-mcp` 소스를 JDIPT에 vendor하지 않는다.
- 비밀값(`LAW_OC`, 토큰 등)은 커밋하지 않는다.
- `law-interpretation-request`는 **explicit-only Skill**로 유지한다.
- `skills/law-interpretation-request/agents/openai.yaml`의 `allow_implicit_invocation`은 `false`여야 한다.
- 일반 법령 질문에 자동 Skill 선택을 release gate로 요구하지 않는다.

## Explicit Skill runtime precedence

사용자 프롬프트에 `$law-interpretation-request`가 있으면 **응답 모드나 정보 부족 여부를 판단하기 전에** `skills/law-interpretation-request/SKILL.md`를 먼저 읽는다.

- Skill을 읽기 전에 `자료가 부족하므로 질문만 하겠습니다`, `초안 작성을 보류하겠습니다` 같은 응답 경로를 결정하지 않는다.
- Skill을 읽은 뒤 그 runtime priority contract에 따라 일반 법률검토형 / 명시적 법제처 모드 / 질문-only / 추상 fixture 모드를 판정한다.
- Skill description이 skills context budget 때문에 축약되더라도 explicit invocation에서는 `SKILL.md를 먼저 읽는다`는 이 규칙을 따른다.
- 필요한 reference는 모드 판정 후 읽는다.

## 법령해석 처리 순서

기본 처리 순서는 **Legal Issue Mapping → Legal Interpretation → Logic Validation → Answer Rendering**으로 유지한다.

- `skills/law-interpretation-request/references/legal-issue-mapping.md`에서 법적 대상·행위·상태, 적용 규범의 역할, 사실대입과 문제 발생 지점을 먼저 특정한다.
- 관련 규정이 둘 이상이면 동일 사항의 중복 규율, 일반/특별 관계, 누적 적용, 원칙/예외, 적용 제외·준용, 규율 공백, 서로 다른 규율대상을 구분한다.
- 사실과 요건은 확인된 자료에 근거해 `충족`, `불충족`, `확인 필요`로 관리한다.
- 제공되지 않은 사실·정의·요건을 임의로 보충하지 않는다.

### 정보 부족 처리

정보 부족 처리는 **응답 모드 판정 뒤**에 수행한다.

- 일반 법률검토형에서 법적 쟁점과 검토대상 행위·상태·관계가 식별되면 법령명·조문·정확한 날짜·경과조치가 미확인이라는 이유만으로 질문-only로 전환하지 않는다.
- 위 경우에는 기본 4-H1 안에서 확인된 판단구조를 설명하고, 미확인 사항은 `확인 필요`로 표시하며 결론을 조건부 결론으로 낮춘다.
- 과거 허가 → 법 개정 → 후속 변경허가처럼 적용 기준시점이 복수인 구조가 식별되면 날짜 미확인 자체를 질문-only 사유로 사용하지 않는다.
- 이 temporal unknown 상태에서 **조건부 결론은 확률적 우세 판단이 아니다**. 허가일·개정법 시행일·변경허가 신청/처분일·경과조치 중 어느 하나라도 신·구법 선택을 좌우하는데 미확인이면 `가능성이 크`, `가능성이 높`, `대체로`, `통상`, `원칙적으로 신법`, `적용될 것으로 보` 같은 방향성 표현을 사용하지 않는다. `경과조치가 종전 규정 적용을 정하면 종전 기준`, `신법 적용요건이 충족되고 경과조치가 없으면 신법 기준`처럼 분기를 대칭적으로 제시하고 **어느 분기가 성립하는지는 현재 판단할 수 없다**고 명시한다.
- 질문-only는 규정·쟁점·검토대상 자체를 구성할 수 없는 입력에 한정한다. 이 경우에만 필요한 질문 3~7개를 하고 그 응답에서는 초안을 중단한다.
- **명시적 법제처 모드에서는 제출 적합성 보정이 정보 부족 질문보다 먼저**다. 구체적 사실 해당 여부나 처분 위법성을 법제처에 직접 묻는 요청이면 첫 문장에서 `이 요청은 법제처 법령해석 대상으로는 부적합할 수 있습니다.`라고 밝힌 뒤 필요한 질문을 한다.
- **형식상 부적합 + 정보 부족이면 질문-only가 법제처 3-H1보다 우선**한다. 이 경우 **부적합 고지 후 필요한 질문 3~7개만 출력하고 즉시 중단**한다. **이 응답에는 H1 제목, 법제처 1~3 초안, `※ 제출 전 확인`, 출처 링크를 출력하지 않는다**. 후속 작성 방향은 일반 문장 한 줄로만 안내할 수 있다.

### 추상 fixture fail-closed

가상 법률·가상 시행령·가상 시행규칙, A/B/P/Q, 동일 용어 충돌, 미확인 별지·정의는 closed-world fixture로 취급한다.

- 사용자가 제공한 규정·정의·사실만 법적 전제로 사용한다.
- `설립`, `신설`, `전환`, `허가`, `승인` 등 정의되지 않은 용어를 통상적 의미로 새 법적 정의처럼 채우지 않는다.
- fixture에 없는 시설·조직·책임자·운영기준·용도변경·등록·변경승인 등을 새 요건으로 만들지 않는다.
- **미확인 정의·참조자료가 결론을 좌우하면 방향성 가설을 제시하지 않는다.** `가능`, `가능성이`, `여지`, `대체로`, `우세` 같은 표현으로 어느 방향을 암시하지 말고 `제공된 전제만으로는 확정할 수 없다`는 중립 결론을 유지한다.
- **미확인 `신설 / 증설` 의미는 승인 방향을 지지하거나 반박하는 근거가 아니다.** 그 의미·법적 기능·위임관계가 해결되지 않은 동안 `# 2. 검토결론`에서는 **현재 전제만으로 승인 가능 여부를 판단할 수 없다**고만 결론내린다. `승인 가능성을 뒷받침`, `승인 가능성이 높`, `승인받기 어렵`, `승인 가능성은 열려` 같은 비대칭 평가 문구를 사용하지 않는다.
- 별지·서식의 실제 문언이 제공되지 않았고 그 내용이 결론에 영향을 줄 수 있으면 참조자료 미확인 상태 자체로 확정 결론을 BLOCK한다.

### 기본 법률검토형

별도 형식 지시가 없는 법령해석·검토 답변은 아래 정확한 H1 4단 구조를 사용한다.

```markdown
# 1. 질의요지
# 2. 검토결론
# 3. 검토이유
# 4. 관련 법령 및 자료
```

- `# 1. 질의요지` 이전에는 별도 서론·확인질문·Skill 호출문자열을 작성하지 않는다.
- `# 2. 검토결론`은 상세 검토이유보다 먼저 제시한다.
- 확정할 수 없는 사항은 기본 4단 안에서 조건부·중립 결론으로 처리한다.
- 단일 쟁점은 분석 단계별 소제목으로 기계적으로 분리하지 않는다.
- 하위 소제목은 서로 독립적인 복수 쟁점에만 사용한다.

### 법제처 제출용

사용자가 `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설` 등을 명시적으로 요구할 때만 다음 구조를 사용한다. 단, 위 **형식상 부적합 + 정보 부족** 질문-only 예외가 성립하면 이 3-H1 구조를 만들지 않는다.

```markdown
# 1. 질의요지
# 2. 해석대상 법령조문 및 관련 법령
# 3. 대립되는 의견 및 이유
```

- 제목을 임의로 바꾸지 않는다.
- 4~8 항목은 생성하지 않는다.

### Output Hygiene 및 URL provenance

- 모든 사용자용 최종 답변은 Markdown으로 작성한다.
- `$law-interpretation-request`, `@jdipt`, Skill/Plugin 활성화 메타데이터, reference 경로와 내부 validator 이름을 최종 법률검토 문안에 노출하지 않는다.
- 공식자료 링크는 현재 실행에서 실제 확인한 완전한 공식 URL만 사용한다.
- **도구·검색 결과에서 관찰한 URL 문자열을 그대로 사용**한다. 한글 경로 URL을 모델이 직접 percent-encoding하거나 경로를 재조합하지 않는다.
- 관찰된 Unicode URL을 인코딩된 형태로 바꾸고 싶다면 그 변환 결과를 현재 실행에서 다시 검증해야 한다. 검증하지 못하면 원래 관찰한 URL을 그대로 쓰거나 `[공식 링크 확인 필요]`로 처리한다.
- percent-encoded 조각과 원문 한글이 섞인 **혼합 인코딩 URL**을 출력하지 않는다.
- URL 패턴을 추측하지 않는다. 핵심 식별자가 비어 있거나 URL 끝이 `=`이면 출력하지 않는다.
- `law.go.kr/LSW/flDownload.do` + `flNm` 링크는 사용하지 않는다.
- **`lsBylInfoPLinkR.do` + `lsNm` 링크는 사용자 출력에 사용하지 않는다.** 사람용 법령명 query 값을 재인코딩하는 과정에서 혼합 인코딩이 재발할 수 있으므로, 현재 실행에서 확인된 식별자 기반의 안정적인 상위 법령·별표 URL을 사용하고 없으면 `[공식 링크 확인 필요]`로 처리한다.
- 존재를 확인하지 않은 판례번호·해석례번호·URL을 생성하지 않는다.

### 논리검증 및 Rendering Gate

- 최종 문안 생성 전 `skills/law-interpretation-request/references/logic-validation.md`의 내부 논리검증 Gate를 수행한다.
- 동일한 법률용어의 의미·범위가 갑설·을설 사이에서 근거 없이 달라지면 BLOCK한다.
- 추상 fixture의 미확인 전제를 임의 보충하지 않는다.
- 내부 기호화·점수표·오류분류명은 사용자가 명시적으로 요구하지 않는 한 출력하지 않는다.
- 사용자에게 보내기 직전에 **최종 Rendering Gate**를 수행해 H1 문자열·순서·개수, Answer-first, Output Hygiene, URL provenance를 다시 확인한다.
- 하나라도 어긋나면 초안을 폐기하고 재렌더링한다.

## 변경 후 검증

최소한 다음을 실행한다.

```bash
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python -m pytest -q
python scripts/plugin_integrity.py
```

- 논리검증 계약을 바꾸면 `references/logic-validation.md`, `evals/*`, validator를 함께 검토한다.
- Legal Issue Mapping 계약을 바꾸면 `references/legal-issue-mapping.md`, `SKILL.md`, `references/interpretation-principles.md`, `evals/*`를 함께 검토한다.
- 출력 형식·Output Hygiene·URL provenance를 바꾸면 `SKILL.md`, `references/request-format.md`, `references/source-policy.md`, `evals/*`, `scripts/validate_repo.py`, `AGENTS.md`를 함께 검토한다.
- Skill 호출 정책을 바꾸면 `agents/openai.yaml`, `evals/*`, 설치 문서와 validator를 함께 검토한다.
- 행동 검증 전에는 repository와 실제 resolved installed Skill의 integrity가 일치해야 한다.
