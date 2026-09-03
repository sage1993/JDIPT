# Korean Law MCP 연동 정책

업스트림: https://github.com/chrisryugj/korean-law-mcp

현재 JDIPT 고정 버전: `4.12.2`

## 사용 이유

`korean-law-mcp`는 국가법령정보센터 기반 법령·판례·법령해석례 조회와 인용 검증 기능을 제공하므로 JDIPT에서 같은 데이터 접근 계층을 재구현하지 않는다.

## JDIPT가 직접 의존하는 MCP 도구

다음 도구명은 Skill에서 직접 참조하므로 업스트림 업데이트 시 호환성을 확인한다.

- `search_law`
- `get_law_text`
- `search_decisions`
- `get_decision_text`
- `legal_analysis`
- `discover_tools`
- `execute_tool`

필요 시 `legal_research`, `get_annexes`, `ordinance_radar`를 사용할 수 있다.

## 조사 기본 순서

1. `search_law`로 법령과 식별자를 확정한다.
2. `get_law_text`로 인용할 현행 조문을 조회한다.
3. 쟁점과 유사한 결정례는 `search_decisions`로 찾고 `get_decision_text`로 본문을 확인한다.
4. 연혁·특정 도구가 필요하면 `discover_tools`로 적합한 도구를 찾고 `execute_tool`로 실행한다.
5. 최종 문안 직전 `legal_analysis`의 인용 검증 기능을 우선 고려한다.

## 현재 업그레이드 검증 상태

- `korean-law-mcp@4.12.2` exact pin 적용
- 업스트림 4.12.2 변경 범위 검토 완료: `get_law_text` MST fallback 복구, `verify_citations` 연쇄 장애 복구, `get_historical_law` 조문 파싱 보정
- Node.js 최소 버전 `>=20.19.0` 유지 확인
- Korean Law MCP 실제 호출/E2E: **PR 병합 전 재검증 필요**
- Codex 로컬 MCP 설정은 `env_vars = ["LAW_OC"]`로 OS 환경변수만 전달
- 정적 release gate: **PR 병합 전 재검증 필요** — `python scripts/validate_repo.py`, `npm ci`, `npm run mcp -- --help`

## 업그레이드 체크리스트

- [x] npm 패키지 버전과 Node.js 최소 버전 확인
- [ ] STDIO 서버 기동 확인
- [ ] 직접 참조 도구명이 유지되는지 확인
- [ ] `search_law` 검색 결과가 식별자를 반환하는지 확인
- [ ] `get_law_text`가 특정 조문 본문을 반환하는지 확인
- [ ] `legal_analysis(mode=verify_citations)`가 실존 인용을 검증하는지 확인
- [ ] 결정례 검색/본문 도구가 유지되는지 확인
- [ ] `get_historical_law`가 실제 조문·가지번호·항 본문을 반환하는지 확인
- [x] Skill과 문서의 버전 참조 갱신
- [ ] `python scripts/validate_repo.py` 통과

업스트림 변경을 자동으로 무조건 병합하지 않는다. 법률정보 도구는 출력 스키마나 검색 정책 변경이 문안 정확도에 직접 영향을 줄 수 있으므로 검증 후 버전을 올린다.
