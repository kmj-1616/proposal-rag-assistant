# step2 구현 노트

## 범위

- step1 청크 기반 검색 인덱스 구축
- RFP를 구조화된 요구사항 JSON으로 파싱

## 예정 산출물

- 검색 스모크 테스트 스크립트
- RFP 요구사항 스키마 정의
- 파서 모듈 및 검증 결과

## 검증 체크리스트

- [ ] 5개 이상 질의로 검색 관련성 점검
- [ ] 필수 RFP 필드 추출 확인
- [ ] 비정형/불완전 RFP 처리 방식 문서화

## 이번 브랜치 반영 내용

- 파서 고도화
  - 필수 8개 항목 추출 패턴 확장
  - 리스트 필드 중복 제거/정규화
  - `--print-missing` 옵션으로 누락 필드 즉시 확인 가능
- 스키마 검증 파이프라인 추가
  - `schema_validator.py`: 스키마 기반 필드/타입 검증
  - `run_validation_cases.py`: 케이스 일괄 실행 및 리포트 생성
- 샘플 케이스 추가
  - 정상(`case_normal.txt`)
  - 누락(`case_missing.txt`)
  - 비정형(`case_unstructured.txt`)

## 실행 절차

```bash
python "steps/step2_retrieval_and_rfp_parse/run_validation_cases.py"
```

## 검증 결과 요약

- `case_normal.txt`: PASS
- `case_missing.txt`: PASS (스키마는 통과, `missing_fields`로 누락 확인)
- `case_unstructured.txt`: PASS (비정형 입력에서 일부 필드 누락 가능)

## 현재 한계

- 의미 기반 추출은 아직 규칙 기반 파서에 의존
- 검색 계층은 키워드 스모크 테스트 수준
- API 엔드포인트는 아직 미구현

## 다음 브랜치 연결점

- 대상 브랜치: `feature/step2-api-skeleton`
- 연결 범위:
  - `/rfp/analyze` 요청/응답 스키마 연결
  - `/proposals/search` 스켈레톤 및 step2 검색 모듈 바인딩
