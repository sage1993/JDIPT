# Roadmap

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
- [x] E21~E26 출력·인용·Plugin 자동 적용 평가
- [x] OpenAI `.codex-plugin/plugin.json` manifest 및 repo Marketplace 패키징
- [x] Skill 단일 원본을 `skills/`로 확정
- [x] `LAW_OC`를 저장소에 직접 넣지 않고 `env_vars`로 전달
- [x] 로컬/개인 Plugin 설치 smoke test
- [x] 공개 배포 전 v0.1.0 회귀 평가

## v0.2 — Legal Issue Mapping + Answer-first output

### 분석 파이프라인

- [x] Legal Issue Mapping Gate 추가
- [x] 법적 대상·행위·정의·분류 선확인
- [x] 본칙·예외·특례·위임·적용 제외·준용 등 적용 규범 지도
- [x] 동일 사항 중복규율 / 일반·특별 / 누적 적용 / 규율 공백 / 다른 규율대상 구분
- [x] 사실관계와 법적 요건을 `충족` / `불충족` / `확인 필요`로 연결
- [x] 질문 반복이 아닌 실제 문제 발생 지점 특정
- [x] `Legal Issue Mapping → Legal Interpretation → Logic Validation → Answer Rendering` 책임 경계 정립

### 출력 구조

- [x] 기본 법률검토형을 4단 구조로 단순화
  1. 질의요지
  2. 검토결론
  3. 검토이유
  4. 관련 법령 및 자료
- [x] 검토결론을 상세 검토이유보다 먼저 제시하는 Answer-first 계약
- [x] 단일 쟁점의 정의·규정·사안적용·해석을 연속 논증으로 작성하는 Narrative Coherence 계약
- [x] 독립적으로 판단 가능한 복수 쟁점에서만 하위 소제목 사용
- [x] 법제처 제출용 1~3 구조 유지

### 호출 정책

- [x] `law-interpretation-request`를 explicit-only Skill로 전환
- [x] `allow_implicit_invocation: false` 적용
- [x] 자동 Skill 선택을 v0.2 release gate에서 제거
- [x] E26을 설치본 명시 호출 Smoke Test로 전환

### 사례 패턴 및 평가

- [x] 22-0351 법적 분류형 패턴 추가
- [x] 17-0047 중복규율형 패턴 추가
- [x] 20-0604 규율공백형 패턴 추가
- [x] E27~E35 Issue Mapping / Answer-first / Narrative Coherence 평가 정의
- [x] E36~E38 Golden Case 정의
- [ ] E1~E38 새 컨텍스트 명시 호출 행동 회귀 평가
- [ ] E26 설치된 Plugin v0.2.0 명시 호출 Smoke Test
- [ ] `python scripts/validate_repo.py` / `npm ci` / `npm audit --omit=dev` / MCP help 최종 release gate
- [ ] v0.2.0 release 판정 및 배포

### 후속 정교화

- [ ] 현행 조문 → 연혁 → 해석례 → 인용검증 표준 플로우 정교화
- [ ] MCP 오류/빈 결과/부분 결과 처리 규칙 보강
- [ ] 복합질의 분해 기준 평가 케이스 추가

## v0.2.1 — Counterevidence Gate

- [ ] 명시적 제한·규정 부재만으로 가능 결론을 확정하지 않는 Counterevidence 계약
- [ ] 관련 하위법령·별표·별지서식·절차규정의 Source Completeness 확인
- [ ] 별표·별지서식의 소속 법령·위임근거·규범적 기능·상위법 정합성 평가
- [ ] 중대한 미해결 반대근거 발견 시 확정 결론을 조건부 결론 또는 확인 필요로 낮춤
- [x] E39 별지서식 충돌형 및 E40 규정 부재 논증 Counterexample fixture
- [ ] E39/E40 RED 관찰 후 production contract 수정 및 GREEN 검증
- [ ] targeted 15/15 및 full E1~E40 40/40 명시 호출 회귀
- [ ] `python scripts/validate_repo.py`, `npm ci`, `npm audit --omit=dev`, MCP help, `git diff --check`
- [ ] 실제 지식산업센터 질의 smoke 및 URL provenance 확인

## v0.3 — MCP / distribution expansion

- [ ] ChatGPT 웹에서 MCP 도구가 필요한 경우 원격/등록 MCP App 구성
- [ ] 실제 등록 ID 확보 후 `.app.json` 및 manifest `apps` 연결 E2E 검증
- [ ] 공개 Plugin Directory 제출·갱신 절차 정교화
- [ ] release/refresh 운영 문서 자동화

## v0.4 — Modular skills

필요성이 검증되면 다음으로 분리한다.

- 법령해석 대상 적합성 검토
- 법령·해석례 리서치
- 법률해석 논증 구성
- 출처·인용 검증
- 최종 요청서 작성

초기에는 조기 분리를 피하고 하나의 orchestration Skill에서 실제 사용 패턴을 수집한다.
