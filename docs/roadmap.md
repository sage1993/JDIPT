# Roadmap

## v0.1 — Repository foundation

- [x] 법령해석요청 Skill 저장소화
- [x] `korean-law-mcp` 외부 의존성 고정
- [x] Codex MCP 설정 예시
- [x] 업스트림 버전 관리 정책
- [x] 정적 저장소 검증 스크립트

## v0.2 — MCP-aware Skill

- [ ] 실제 MCP 호출 시나리오 평가
- [ ] 현행 조문 → 연혁 → 해석례 → 인용검증 표준 플로우 정교화
- [ ] MCP 오류/빈 결과/부분 결과 처리 규칙 보강
- [ ] 복합질의 분해 기준 평가 케이스 추가

## v0.3 — Plugin packaging

- [ ] ChatGPT/Codex 플러그인 등록용 메타데이터 정리
- [ ] MCP 앱/앱 템플릿 연결 방식 확정
- [ ] 설치/업데이트 절차 문서화
- [ ] 배포 전 회귀 평가

## v0.4 — Modular skills

필요성이 검증되면 다음으로 분리한다.

- 법령해석 대상 적합성 검토
- 법령·해석례 리서치
- 법률해석 논증 구성
- 출처·인용 검증
- 최종 요청서 작성

초기에는 조기 분리를 피하고 하나의 orchestration Skill에서 실제 사용 패턴을 수집한다.
