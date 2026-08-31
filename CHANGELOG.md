# Changelog

JDIPT의 주요 변경사항을 기록합니다.

## [Unreleased]


### v0.2.4 candidate

- ASH-01~ASH-09 안심주택 Oracle과 의미 기반 positive/negative marker evaluator 추가
- 현행성·권위·특별규정·예외·근거·불확실성 Global Hard Gate 6종 추가
- Core 9/9, Stability 27/27 process·26/27 oracle, Critical marker zero-tolerance release gate 추가
- 기존 Core14/Full26 및 E43~E46 계약은 변경 없이 보존

## [0.2.3] - 2026-08-30

### Authority, Temporal, and Evidence Contracts

PR #9에서 법령해석의 적용시점, 해석권위, 근거 추적 및 회귀검증 계약을 강화했습니다.

#### Added

- 적용 기준시점 후보와 최초 허가·변경허가 lifecycle을 분리하는 temporal contract
- 시행일·경과조치·종전법/신법 관계를 확인하는 fail-closed 처리
- 법제처 정부유권해석·판례·헌재결정·소관부처 질의회신의 권위와 법적 기능을 구분하는 authority contract
- Source Claim과 Analytical Inference를 구분하는 claim-level evidence contract
- Core 14 / Full active 26 / Legacy 20 / Catalog 46 평가 체계
- E43–E46 behavior fixture 및 deterministic oracle

#### Fixed

- E02/E03: 법령해석 대상 적합성 고지 후 객관적 법령 의미·적용범위·요건·근거조항 쟁점으로 재구성하는 runtime contract 보강
- E18: 동일 용어의 의미·범위가 충돌하는 경우 공통 기준 확정 전 갑설·을설의 실체 논거 전개 차단 강화
- E37: 빈 query 값, 불완전 download URL 및 식별자 없는 URL 출력 방지
- E44: `최초 건축허가` 등 의미상 동등한 temporal 표현을 허용하면서 변경허가·시행일·경과조치·신구법 관계 요건 유지
- E18/E31/E44 oracle의 의미상 동등 표현 false negative 최소 보정

#### Validation

2026-08-30 PR #9 병합 전·후 검증 결과:

- Gate A deterministic: PASS
- Gate B Core: PASS
- E02/E03/E18/E37/E43/E44/E45: PASS
- Gate C Full active: 26/26 PASS
  - process: 26/26
  - environment errors: 0/26
  - hygiene: 26/26
  - URL: 26/26
  - oracle: 26/26
- Gate D package/static: PASS
- pytest: 108 passed
- `validate_repo.py`: PASS
- `validate_authority_temporal_contract.py`: PASS
- `plugin_integrity.py`: PASS
- `npm ci`: PASS
- `npm audit --omit=dev`: 0 vulnerabilities
- `npm run mcp -- --help`: PASS
- `git diff --check`: content errors 없음

Merge commit: `244b04f1679f51b08d01a8b60a2f74357730ed3b`

#### Compatibility / Non-goals

- Plugin/package version은 `0.2.3`으로 정합화하며, `v0.2.3` 태그는 병합 후 별도로 생성함
- `korean-law-mcp@4.12.1` 유지
- `allow_implicit_invocation: false` 및 explicit-only 정책 유지
- 기본 4단 / 법제처 제출용 1–3 출력 계약 유지
- 기존 E01–E42 fixture 유지

## [0.2.2]

- Referenced Source Resolution / Final Rendering hard gate
- URL 안정성 강화
- deterministic oracle, runtime integrity, critical stability, release orchestration

## [0.2.1]

- Source Completeness / Counterevidence Gate

## [0.2.0]

- Legal Issue Mapping
- Answer-first 4단 출력
- explicit-only 호출

## [0.1.0]

- Plugin/Skill 저장소화
- Korean Law MCP 연동 기반
- 초기 논리검증 및 패키징
