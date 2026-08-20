# Roadmap

## v0.1 — Repository foundation

- [x] 법령해석요청 Skill 저장소화
- [x] `korean-law-mcp` 외부 의존성 고정
- [x] Codex MCP 설정 예시
- [x] 업스트림 버전 관리 정책
- [x] 정적 저장소 검증 스크립트

## v0.2 — MCP-aware + logic-validated Skill

- [x] 내부 논리검증 Gate 설계 및 Skill 강제
- [x] 전건 부정·후건 긍정·거짓 양자택일·전제 누락 등 오류 탐지 규칙
- [x] 형식적 타당성과 건전성/사실성 상태 분리
- [x] 갑설·을설 독립 검증 및 상호 비교
- [x] 항목별 100점 내부 평가와 수정·재검증 절차
- [x] E10~E20 논리검증 평가 시나리오 정의
- [x] 기본 1~6 Markdown 출력 및 요청취지 유추 규칙
- [x] E21~E25 출력·인용 평가 시나리오 정의
- [x] E10~E25 새 컨텍스트 실제 에이전트 회귀 평가
- [x] 실제 MCP 호출 시나리오 평가
- [ ] 현행 조문 → 연혁 → 해석례 → 인용검증 표준 플로우 정교화
- [ ] MCP 오류/빈 결과/부분 결과 처리 규칙 보강
- [ ] 복합질의 분해 기준 평가 케이스 추가

## v0.3 — Plugin packaging

- [x] OpenAI 공식 `.codex-plugin/plugin.json` manifest 추가
- [x] Plugin의 Skill 단일 원본을 `skills/`로 확정
- [x] Plugin ID·표시명·설명·기본 프롬프트 메타데이터 정의
- [x] `package.json`과 Plugin manifest 버전 정합성 검증
- [x] `korean-law-mcp` vendor 금지 및 외부 의존성 경계 문서화
- [x] `LAW_OC`를 저장소/config에 직접 넣지 않고 `env_vars`로 전달하는 로컬 Codex 예시
- [x] Plugin 패키징 문서 추가
- [x] 로컬/개인 Plugin 설치 smoke test
- [x] ChatGPT/Codex 새 컨텍스트에서 Plugin Skill 자동 적용 확인
- [ ] ChatGPT 웹에서 MCP 도구가 필요한 경우 원격/등록 MCP App 구성
- [ ] `.app.json` 및 manifest `apps` 연결 E2E 검증
- [ ] 공개 Plugin Directory 제출 전 심사 요구사항 확인
- [x] 공개 배포 전 최종 회귀 평가

## v0.4 — Modular skills

필요성이 검증되면 다음으로 분리한다.

- 법령해석 대상 적합성 검토
- 법령·해석례 리서치
- 법률해석 논증 구성
- 출처·인용 검증
- 최종 요청서 작성

초기에는 조기 분리를 피하고 하나의 orchestration Skill에서 실제 사용 패턴을 수집한다.
