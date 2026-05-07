# AGENTS 운영 규칙

이 문서는 이 저장소에서 작업하는 모든 모델/에이전트가 공통으로 따라야 하는 규칙입니다.

## 1) 브랜치 전략 (라이트 Git Flow)

- `main`: 배포/안정 브랜치
- `develop`: 통합 개발 브랜치
- `feature/<scope>-<topic>`: 기능 작업 브랜치

병합 원칙:

- 기본 개발 흐름: `feature/*` -> `develop`
- 배포/릴리즈 반영: `develop` -> `main`

## 2) 커밋 메시지 규칙

Conventional Commits를 사용하고, 본문은 한글로 작성합니다.

형식:

`<type>(<scope>): <요약>`

권장 타입:

- `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

예시:

- `feat(step2): RFP 파서 골격 추가`
- `docs(architecture): 데이터 흐름 문서 한글화`
- `refactor(step1): 경로 설정 유틸 정리`

## 3) 데이터 보안 규칙

공개 저장소 정책을 반드시 준수합니다.

- 실데이터(제안서 원문/RFP 원문) 커밋 금지
- 실데이터 파생 산출물(추출 텍스트/청크) 커밋 금지
- 로컬 데이터는 `local_data/` 하위에서만 사용

상세 규정: `docs/security-data-policy.md`

## 4) 문서 언어 정책

- `docs` 하위 문서는 원칙적으로 한글 작성
- 영문 용어가 필요한 경우 한글 설명을 함께 작성
- README와 docs 간 용어를 일관되게 유지

## 5) 작업 전/후 체크리스트

작업 전:

- 현재 브랜치가 작업 목적에 맞는지 확인
- 민감 데이터 경로가 `.gitignore`에 반영되어 있는지 확인

커밋 전:

- `git status`로 스테이징 파일 점검
- 민감 경로/오피스 바이너리 파일이 포함되지 않았는지 확인
- 커밋 메시지가 규칙을 준수하는지 확인

작업 후:

- README 또는 관련 docs에 변경사항 반영
- 다음 단계 TODO/리스크를 문서에 기록
