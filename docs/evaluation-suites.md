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
→ B. Core stability (14 cases, E37만 2회)
→ C. Full active (26 cases)
→ D. package/static
```

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
