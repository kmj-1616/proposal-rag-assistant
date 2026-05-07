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
  - `POST /api/v1/proposals/search`: 키워드 기반 스텁 검색 (후속 브랜치에서 교체)
  - `GET /api/v1/health`: 헬스체크
- OpenAPI(`/docs`) 에서 입력/응답 예시 확인 가능

### feature/step2-embedding-retrieval

- 검색 엔진 추상화 계층 추가
  - `app/services/retrieval_engine.py`: `BaseRetriever` 인터페이스
  - `app/services/chroma_index_service.py`: `ChromaRetriever` 구현체 + `build_index()`
- 임베딩 모델: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (로컬 실행)
- Chroma 인덱스 영속 저장: `local_data/step2/chroma_index`
- 신규 엔드포인트
  - `POST /api/v1/proposals/index/rebuild`: Step1 청크 기반 인덱스 재생성
- 검색 엔드포인트 교체
  - `POST /api/v1/proposals/search`: 키워드 스텁 → 코사인 유사도 임베딩 검색
- 헬스체크 응답에 `index_ready` 상태 추가

## 실행 절차

```bash
# 파서 품질 검증 (CLI)
python "steps/step2_retrieval_and_rfp_parse/run_validation_cases.py"

# API 서버 실행
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 인덱스 생성 (step1 청크 준비 후)
curl -X POST http://localhost:8000/api/v1/proposals/index/rebuild \
  -H "Content-Type: application/json" -d '{"reset": true}'
```

## 환경변수

| 변수명 | 기본값 | 설명 |
|---|---|---|
| `LOCAL_DATA_ROOT` | `<repo>/local_data` | 로컬 데이터 루트 |
| `CHROMA_INDEX_DIR` | `local_data/step2/chroma_index` | Chroma 인덱스 저장 경로 |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | 임베딩 모델명 |

## 현재 한계

- 파서는 규칙 기반이며 의미 기반(LLM) 추출은 미구현
- 인증/권한 처리 미포함
- 멀티파일 업로드 및 대용량 파일 처리 미지원

## 검증 체크리스트

- [x] 5개 이상 질의로 검색 관련성 점검
- [x] 필수 RFP 필드 추출 확인
- [x] 비정형/불완전 RFP 처리 방식 문서화
- [x] FastAPI 서버 로컬 기동 확인
- [x] `/rfp/analyze` 텍스트/파일경로 입력 동작 확인
- [x] `/proposals/index/rebuild` 인덱스 생성 확인
- [x] `/proposals/search` 임베딩 기반 응답 확인
- [x] 서버 재시작 후 인덱스 영속성 확인
- [x] OpenAPI `/docs` 스키마 및 예시 확인

## 다음 브랜치 연결점

- 대상 브랜치: `feature/step3-generation-pipeline`
- 연결 범위
  - `/proposals/search` 결과를 step3 생성 파이프라인 입력으로 연결
  - `/drafts/generate` 엔드포인트 구현 (step3)
