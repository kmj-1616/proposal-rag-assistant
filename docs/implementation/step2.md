# step2 구현 노트

## 범위

- step1 청크 기반 검색 인덱스 구축
- RFP를 구조화된 요구사항 JSON으로 파싱

## 브랜치별 반영 내용

### feature/step2-rfp-parser-quality

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

검증 결과:

- `case_normal.txt`: PASS
- `case_missing.txt`: PASS (스키마는 통과, `missing_fields`로 누락 확인)
- `case_unstructured.txt`: PASS (비정형 입력에서 일부 필드 누락 가능)

### feature/step2-api-skeleton

- FastAPI 앱 골격 구성 (`app/` 디렉터리)
  - `app/main.py`: FastAPI 앱 진입점
  - `app/api/routes/step2.py`: step2 엔드포인트 라우터
  - `app/models/step2.py`: Pydantic 요청/응답 모델
  - `app/services/step2_service.py`: 파서 및 검색 서비스 레이어
- 구현된 엔드포인트
  - `POST /api/v1/rfp/analyze`: 텍스트 및 파일경로 입력 모두 지원
  - `POST /api/v1/proposals/search`: 키워드 기반 스텁 검색
  - `GET /api/v1/health`: 헬스체크
- OpenAPI(`/docs`) 에서 입력/응답 예시 확인 가능

## 실행 절차

```bash
# 파서 품질 검증 (CLI)
python "steps/step2_retrieval_and_rfp_parse/run_validation_cases.py"

# API 서버 실행
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 현재 한계

- 파서는 규칙 기반이며 의미 기반(LLM) 추출은 미구현
- 검색은 키워드 빈도 기반이며 벡터/임베딩 검색은 미구현
- 인증/권한 처리 미포함
- 멀티파일 업로드 및 대용량 파일 처리 미지원

## 검증 체크리스트

- [x] 5개 이상 질의로 검색 관련성 점검
- [x] 필수 RFP 필드 추출 확인
- [x] 비정형/불완전 RFP 처리 방식 문서화
- [x] FastAPI 서버 로컬 기동 확인
- [x] `/rfp/analyze` 텍스트/파일경로 입력 동작 확인
- [x] `/proposals/search` 스텁 응답 확인
- [x] OpenAPI `/docs` 스키마 및 예시 확인

## 다음 브랜치 연결점

- 대상 브랜치: `feature/step3-generation-pipeline` 또는 `feature/step2-embedding-retrieval`
- 연결 범위
  - ChromaDB 통합 및 임베딩 검색 고도화
  - `/drafts/generate` 엔드포인트 연결 (step3)
