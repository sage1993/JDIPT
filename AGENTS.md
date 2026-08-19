# JDIPT Repository Instructions

## 목적
이 저장소는 대한민국 법령해석요청 업무용 Skills와 `korean-law-mcp` 연동 설정을 관리한다.

## 변경 원칙
- 법령 데이터 조회 기능을 JDIPT 안에 중복 구현하지 않는다. 우선 `korean-law-mcp`의 공개 도구를 사용한다.
- 업스트림 MCP의 내부 API에 직접 결합하지 말고 MCP 도구 인터페이스에 의존한다.
- 법제처 제출용 기본 출력은 1~3 항목만 유지한다.
- 법적 결론보다 조문·출처 정확성을 우선한다.
- 존재를 확인하지 않은 판례번호, 해석례번호, 법령 URL을 생성하지 않는다.
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
