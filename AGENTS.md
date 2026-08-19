# JDIPT Repository Instructions

## 목적
이 저장소는 대한민국 법령해석요청 업무용 Skills와 `korean-law-mcp` 연동 설정을 관리한다.

## 변경 원칙
- 법령 데이터 조회 기능을 JDIPT 안에 중복 구현하지 않는다. 우선 `korean-law-mcp`의 공개 도구를 사용한다.
- 업스트림 MCP의 내부 API에 직접 결합하지 말고 MCP 도구 인터페이스에 의존한다.
- 법제처 제출용 기본 출력은 1~3 항목만 유지한다.
- 법적 결론보다 조문·출처 정확성을 우선한다.
- 존재를 확인하지 않은 판례번호, 해석례번호, 법령 URL을 생성하지 않는다.
- 최종 법령해석 문안 생성 전 `skills/law-interpretation-request/references/logic-validation.md`의 내부 논리검증 Gate를 반드시 거친다.
- 논리검증 중 원문·확인된 법적 근거에 없는 숨은 전제를 임의로 추가하지 않는다.
- 논리검증 메모·기호화·점수표는 사용자가 요구하지 않는 한 사용자 출력에 노출하지 않는다.
- 비밀값(`LAW_OC`, 토큰 등)은 절대 커밋하지 않는다.

## 변경 후 검증
최소한 다음을 실행한다.

```bash
python scripts/validate_repo.py
```

`package.json` 또는 MCP 버전을 바꾼 경우에는 Node.js 환경에서 추가로 다음을 실행한다.

```bash
npm install
npm run mcp -- --help
```

업스트림 도구명이 바뀌었으면 `skills/law-interpretation-request/SKILL.md`와 `docs/upstream-mcp.md`를 함께 갱신한다.
논리검증 계약을 바꿨으면 `references/logic-validation.md`, `evals/scenarios.md`, `evals/expected-behavior.md`, `scripts/validate_repo.py`를 함께 갱신한다.
