# Next Branch TODO (`feature/step2-api-skeleton`)

## 목표

CLI 중심 step2 구현을 API 골격으로 연결한다.

## 엔드포인트 초안

- `POST /api/v1/rfp/analyze`
  - 입력: RFP 텍스트 또는 파일 참조
  - 출력: `rfp_requirements` JSON + `missing_fields`
- `POST /api/v1/proposals/search`
  - 입력: 검색 질의, top_k
  - 출력: 유사 청크 목록(문서명, 청크 ID, 미리보기, 점수)

## 인터페이스 설계 TODO

- [ ] 요청/응답 Pydantic 스키마 정의
- [ ] `parser.parse_rfp_text()`를 서비스 레이어로 분리
- [ ] `run_validation_cases.py`와 중복되는 로직 공용 모듈화
- [ ] 검색기 인터페이스 분리(현재 키워드 스모크 -> 임베딩 검색 확장)
- [ ] 에러 응답 포맷 통일 (`error_code`, `message`, `details`)

## 수용 기준 (API 브랜치)

- [ ] `/rfp/analyze` 기본 동작 및 스키마 일치
- [ ] `/proposals/search` 스텁 응답 + 향후 검색 구현 포인트 명시
- [ ] OpenAPI 문서에서 요청/응답 확인 가능
