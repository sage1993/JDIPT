# Roadmap

현재 공개 버전: **v0.2.3**

## v0.1 — Repository / Plugin foundation

- [x] 법령해석요청 Skill 저장소화
- [x] `korean-law-mcp` 외부 의존성 고정
- [x] Codex MCP 설정 예시
- [x] 업스트림 버전 관리 정책
- [x] 정적 저장소 검증 스크립트
- [x] 내부 논리검증 Gate 설계 및 Skill 강제
- [x] 전건 부정·후건 긍정·거짓 양자택일·전제 누락 등 오류 탐지 규칙
- [x] 형식적 타당성과 건전성/사실성 상태 분리
- [x] 갑설·을설 독립 검증 및 상호 비교
- [x] E10~E20 논리검증 평가 시나리오
- [x] E21~E26 출력·인용·Plugin 평가
- [x] `.codex-plugin/plugin.json` manifest 및 repo Marketplace 패키징
- [x] Skill 단일 원본을 `skills/`로 확정
- [x] `LAW_OC`를 저장소에 직접 넣지 않고 `env_vars`로 전달
- [x] 로컬/개인 Plugin 설치 smoke test
- [x] 공개 배포 전 v0.1.0 회귀 평가

## v0.2.0 — Legal Issue Mapping + Answer-first output

### 분석 파이프라인

- [x] Legal Issue Mapping Gate 추가
- [x] 법적 대상·행위·정의·분류 선확인
- [x] 본칙·예외·특례·위임·적용 제외·준용 등 적용 규범 지도
- [x] 동일 사항 중복규율 / 일반·특별 / 누적 적용 / 규율 공백 / 다른 규율대상 구분
- [x] 사실관계와 법적 요건을 `충족` / `불충족` / `확인 필요`로 연결
- [x] 질문 반복이 아닌 실제 문제 발생 지점 특정
- [x] `Legal Issue Mapping → Legal Interpretation → Logic Validation → Answer Rendering` 책임 경계 정립

### 출력 구조

- [x] 기본 법률검토형 4단 구조
- [x] Answer-first 계약
- [x] 단일 쟁점 Narrative Coherence 계약
- [x] 독립적 복수 쟁점에서만 하위 소제목 사용
- [x] 명시적 법제처 제출용 1~3 구조 유지

### 호출 정책

- [x] `law-interpretation-request` explicit-only 전환
- [x] `allow_implicit_invocation: false`
- [x] 자동 Skill 선택을 v0.2 release gate에서 제거
- [x] E26 설치본 명시 호출 Smoke Test

### 사례 패턴 및 평가

- [x] 22-0351 법적 분류형
- [x] 17-0047 중복규율형
- [x] 20-0604 규율공백형
- [x] E27~E35 Issue Mapping / Answer-first / Narrative Coherence 평가
- [x] E36~E38 Golden Case
- [x] E1~E38 새 컨텍스트 명시 호출 행동 회귀
- [x] 설치본 명시 호출 Smoke Test
- [x] static / npm / MCP release gate

## v0.2.1 — Source Completeness / Counterevidence Gate

- [x] 명시적 제한·규정 부재만으로 가능 결론을 확정하지 않는 Counterevidence 계약
- [x] 관련 하위법령·별표·별지서식·절차규정의 Source Completeness 확인
- [x] 별표·별지서식의 소속 법령·위임근거·규범적 기능·상위법 정합성 평가
- [x] 중대한 미해결 반대근거 발견 시 조건부 결론 또는 확인 필요로 낮춤
- [x] E39 별지서식 충돌형
- [x] E40 규정 부재 논증 Counterexample
- [x] production contract 수정 및 GREEN 검증
- [x] 실제 지식산업센터 질의 smoke로 Counterevidence gap 재현·후속 개선점 확인

## v0.2.2 — Source Resolution / Rendering / Regression Stabilization

### Referenced Source Resolution

- [x] 본문이 결론에 중요한 별표·별지서식·부록을 직접 참조할 때 실제 원문 확인을 hard gate로 승격
- [x] 참조자료 확인 실패 시 확정 결론 BLOCK
- [x] `지식산업센터 신설`과 물리적 `건축물 신축` 자동 동일시 금지
- [x] 기존 승인사항 변경과 기존 일반 건축물의 최초 전환 자동 동일시 금지
- [x] E41 referenced annex/form resolution BLOCK

### Final Rendering / Source URL

- [x] 기본 모드 첫 비공백 줄 `# 1. 질의요지`
- [x] 정확한 4 H1 구조·순서 Final Rendering Hard Gate
- [x] 렌더링 실패 초안 폐기 후 재검사
- [x] 미완성 query parameter 차단
- [x] invalid percent escape 차단
- [x] `law.go.kr/LSW/flDownload.do + flNm` 불안정 직접링크 차단
- [x] E42 post-research final rendering hard gate

### Regression infrastructure

- [x] `scripts/regression_checks.py` 결정론적 판정 분리
- [x] E1–E42 `machine-oracles.json` contract oracle
- [x] `scripts/regression_oracles.py`
- [x] 설치본 runtime SHA-256 integrity gate
- [x] `scripts/run_release_gate.py` fail-closed orchestration
- [x] E25 환경오류 false-positive 회귀 fixture
- [x] E37 URL 안정성 fixture
- [x] Critical Suite 도입
- [x] E25 3/3 stability
- [x] E37 3/3 stability
- [x] Full E1–E42: process 42/42, environment 0/42, hygiene 42/42, URL 42/42, oracle 42/42
- [x] pytest 34 passed
- [x] 설치본 SHA repo와 일치
- [x] `npm audit --omit=dev`: 0 vulnerabilities
- [x] real-law smoke PASS
- [x] v0.2.2 release gate PASS
- [x] PR #8 병합 및 `main` 반영

검증 문서: [`validation/v0.2.2-source-rendering.md`](validation/v0.2.2-source-rendering.md)

## v0.3 — MCP / distribution expansion

- [ ] ChatGPT 웹에서 MCP 도구가 필요한 경우 원격/등록 MCP App 구성
- [ ] 실제 등록 ID 확보 후 `.app.json` 및 manifest `apps` 연결 E2E 검증
- [ ] 공개 Plugin Directory 제출·갱신 절차 정교화
- [ ] release/refresh 운영 문서 자동화
- [ ] release gate 결과 요약을 배포 문서에 자동 반영하는 워크플로 검토
- [ ] 외부 설치 사용자 기준 fresh-install smoke 절차 표준화

## v0.4 — Modular skills

필요성이 검증되면 다음 책임을 별도 Skill로 분리하는 방안을 검토합니다.

- 법령해석 대상 적합성 검토
- 법령·해석례 리서치
- 법률해석 논증 구성
- 출처·인용 검증
- 최종 요청서 작성

초기에는 조기 분리를 피하고 하나의 orchestration Skill에서 실제 사용 패턴을 계속 수집합니다.
