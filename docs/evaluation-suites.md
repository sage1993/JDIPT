# JDIPT Evaluation Suites

## 목적

JDIPT는 법적 계약 수와 실제 LLM 실행 수를 분리한다. 과거 regression fixture는 보존하되 모든 PR에서 전부 실행하지 않는다.

## Suite 구성

| Suite | 케이스 수 | 용도 |
|---|---:|---|
| Core | 14 | 기능 PR의 핵심 fail-closed 안정성 검증 |
| Full active | 26 | 릴리스 전 실제 LLM 전체 회귀 |
| Legacy | 20 | 과거 회귀 재현·진단용, 기본 실행 제외 |
| Catalog | 46 | E1~E46 전체 fixture/oracle 추적 |

단일 원본은 `skills/law-interpretation-request/evals/suite-manifest.json`이다.

## 실행

설치된 JDIPT runtime이 현재 저장소의 `SKILL.md`, `agents/openai.yaml`, `references/*.md`와 일치해야 한다.

```powershell
python scripts/plugin_integrity.py
```

Core:

```powershell
python scripts/run_eval_suite.py --suite core
```

Full active:

```powershell
python scripts/run_eval_suite.py --suite full
```

Legacy만 재실행:

```powershell
python scripts/run_eval_suite.py --suite legacy
```

전체 catalog를 진단 목적으로 실행:

```powershell
python scripts/run_eval_suite.py --suite all
```

특정 case만 실행:

```powershell
python scripts/run_eval_suite.py --from-case 43 --to-case 43
```

`--from-case/--to-case`가 지정되면 suite 선택보다 우선한다.

## Release Gate

결정론적 검증만:

```powershell
python scripts/run_release_gate.py
```

결정론적 검증 후 Core stability:

```powershell
python scripts/run_release_gate.py --critical-only
```

전체 release gate:

```powershell
python scripts/run_release_gate.py --full
```

순서:

```text
A. deterministic
→ B. Core stability
→ C. Full active (26 cases, single run must be 26/26)
→ D. package/static
```

### Gate B 반복 정책

LLM 출력 변동성이 실제로 관측된 release-critical case는 단일 성공으로 안정성이 입증된 것으로 보지 않는다.

현재 반복 횟수는 `scripts/run_release_gate.py`의 `REPEAT_CASES`가 단일 원본이다.

- E37: 2회
- E44: 3회 — material date 미확인 상태에서 질문-only로 흔들리지 않는지 검증
- E45: 3회 — 법제처 해석과 대법원 판결의 법적 기능·구속력 차이를 안정적으로 구분하는지 검증
- 나머지 Core case: 1회

따라서 현재 Gate B는 Core 14개에 대해 총 19회 LLM 실행을 수행한다. 각 실행은 process, 환경오류, H1 또는 특수 형식, hygiene, URL, contract oracle을 모두 통과해야 한다.

### 최종 release acceptance

Targeted 재실행 성공만으로 Full 실패를 덮지 않는다. Release-ready 판정에는 다음을 모두 요구한다.

```text
A deterministic: PASS
B Core stability: PASS
  - E44 3/3
  - E45 3/3
C Full active single run: 26/26
D package/static: PASS
```

Oracle이 실제 의미상 동등한 표현을 놓친 false negative는 fixture를 추가하고 oracle을 수정한 뒤 기존 계약을 약화하지 않는 방식으로 처리한다. 반면 동일 입력에서 실제 계약 준수 여부가 달라지는 경우는 모델 변동성으로 보고 Gate B 반복 대상으로 관리한다.

## Legacy 정책

Legacy case는 삭제된 테스트가 아니다. active 대표 시나리오와 deterministic oracle이 동일 계약을 더 적은 LLM 호출로 검증하기 때문에 기본 실행에서 제외된 것이다.

예:

- E21/E23/E33 → E04가 4단 Answer-first/Markdown/hygiene를 함께 검증
- E27/E28/E32/E34 → E36 Golden Case가 정의·분류·본칙·예외·문제 발생 지점·연속논증을 함께 검증
- E29 → E37
- E30 → E38
- E40 → E39
- E42 → E41

정확한 mapping은 `suite-manifest.json`의 `legacy_coverage`를 따른다.

## v0.2.3 신규 behavior

- E43: Temporal lifecycle — 최초 허가·개정법·경과조치·변경허가
- E44: Temporal unknown — material date 미확인 fail-closed
- E45: Authority + precedent versioning
- E46: Claim-level evidence

기존 초안의 E43~E48 여섯 건은 위 네 건으로 통합되었다.
