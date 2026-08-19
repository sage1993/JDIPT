# JDIPT Repository Instructions

## 목적
이 저장소는 대한민국 법령해석요청 업무용 Skills와 `korean-law-mcp` 연동 설정을 관리한다.

## 변경 원칙
- 법령 데이터 조회 기능을 JDIPT 안에 중복 구현하지 않는다. 우선 `korean-law-mcp`의 공개 도구를 사용한다.
- 업스트림 MCP의 내부 API에 직접 결합하지 말고 MCP 도구 인터페이스에 의존한다.
- 별도 형식 지시가 없는 법령해석·검토 답변은 `1. 제목`부터 `8. 첨부자료`까지의 기본 1~8 구조를 사용한다.
- `법제처 법령해석요청서`, `법제처 제출용`, `질의요지·갑설·을설` 등 전용 형식을 사용자가 명시적으로 요청한 경우에만 법제처 1~3 구조를 사용한다.
- 모든 사용자용 최종 답변은 Markdown으로 작성한다.
- 법령·판례·법령해석례 등 공식자료는 실제 확인한 공식 URL이 있으면 자료명 자체에 Markdown 인라인 하이퍼링크를 우선 적용한다. URL 패턴을 추측하지 않는다.
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
출력 형식 또는 인용정책을 바꿨으면 `SKILL.md`, `references/request-format.md`, `references/source-policy.md`, `evals/*`, `scripts/validate_repo.py`를 함께 갱신한다.
