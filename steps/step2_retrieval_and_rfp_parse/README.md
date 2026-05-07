# step2_retrieval_and_rfp_parse

## 목표

- step1 청크를 기반으로 유사 제안서 검색 인덱스를 구성한다.
- 업로드된 RFP를 LLM 기반 문맥 이해 방식으로 분석해 구조화 JSON으로 변환한다.

## 핵심 구현 범위

- 벡터 인덱싱
  - 청크 임베딩 생성 및 저장
  - 자연어 질의 기반 검색 스모크 테스트
- RFP 분석 모듈
  - RFP 텍스트에서 요구사항 자동 추출/구조화
  - 파싱 결과를 스키마 기반 JSON으로 출력

## RFP 추출 필수 항목

- 프로젝트명 및 발주 기관
- 예산 범위
- 사업 목적 및 배경
- 평가 기준 및 배점
- 핵심 요구사항(기능, 기술, 인력)
- 제안서 작성 지침(페이지 제한, 목차 지정)
- 납기 및 일정 조건
- 필수 포함 사항 및 제약 조건

## 산출물

- 로컬 검색 인덱스 메타데이터(로컬 전용)
- `rfp_requirements.json` (스키마 준수)
- 검색 품질 스모크 테스트 결과 노트

## 검증 방법

### 1) 단일 파일 파싱

```bash
python "steps/step2_retrieval_and_rfp_parse/parser.py" \
  --input "<local_rfp_txt_path>" \
  --output "<local_output_json_path>" \
  --print-missing
```

### 2) 스키마 일괄 검증

```bash
python "steps/step2_retrieval_and_rfp_parse/run_validation_cases.py"
```

검증 케이스:

- `test_cases/case_normal.txt` (정상 케이스)
- `test_cases/case_missing.txt` (누락 필드 케이스)
- `test_cases/case_unstructured.txt` (비정형 케이스)

검증 결과 파일:

- `validation_results/*.report.json` (로컬 생성)
- 각 리포트에 `valid`, `errors`, `missing_fields` 기록

## 완료 기준

- 자연어 질의 시 관련 청크 검색이 동작한다.
- RFP 업로드 후 구조화 JSON이 안정적으로 생성된다.
- 필수 추출 항목 누락 여부를 검증할 수 있다.

## API 서버 실행

### 사전 준비

```bash
pip install -r requirements.txt
```

### 서버 기동

```bash
# 프로젝트 루트에서 실행
uvicorn app.main:app --reload --port 8000
```

### OpenAPI 문서 확인

브라우저에서 `http://localhost:8000/docs` 접속

### 임베딩 검색 사용 순서

> 처음 실행하거나 step1 데이터 갱신 후에는 인덱스 재생성이 필요합니다.

**1단계: step1 청크로 인덱스 생성**

```bash
curl -X POST http://localhost:8000/api/v1/proposals/index/rebuild \
  -H "Content-Type: application/json" \
  -d '{"reset": true}'
```

샘플 응답:

```json
{
  "indexed_count": 42,
  "index_path": "local_data/step2/chroma_index",
  "model": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

**2단계: 유사 제안서 검색**

```bash
curl -X POST http://localhost:8000/api/v1/proposals/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI 기반 데이터 분석 플랫폼 구축", "top_k": 5}'
```

샘플 응답:

```json
{
  "query": "AI 기반 데이터 분석 플랫폼 구축",
  "results": [
    {
      "document_name": "proposal_A",
      "chunk_id": "chunk_003",
      "preview": "본 제안은 AI 기반 분석 플랫폼 구축을 목표로...",
      "score": 0.8912
    }
  ],
  "note": "임베딩 기반 검색 (paraphrase-multilingual-MiniLM-L12-v2)."
}
```

**RFP 파싱**

```bash
curl -X POST http://localhost:8000/api/v1/rfp/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "프로젝트명: AI 기반 제안서 자동화 시스템\n발주기관: 한국정보화진흥원\n예산: 3억원"
  }'
```

### 환경변수

| 변수명 | 기본값 | 설명 |
|---|---|---|
| `CHROMA_INDEX_DIR` | `local_data/step2/chroma_index` | Chroma 인덱스 저장 경로 |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | sentence-transformers 모델명 |

## 현재 상태

- 파서/검색 스모크 테스트 골격 구현 완료
- 파서 규칙 고도화 및 누락 필드 출력 지원 완료 (feature/step2-rfp-parser-quality)
- 스키마 검증 스크립트/테스트 케이스(정상/누락/비정형) 추가 완료
- FastAPI API 골격 구현 완료 (feature/step2-api-skeleton)
- 임베딩 기반 검색 고도화 완료 (feature/step2-embedding-retrieval)
  - `POST /api/v1/proposals/index/rebuild`: Chroma 인덱스 재생성
  - `POST /api/v1/proposals/search`: 임베딩 유사도 기반 검색

## 한계 및 다음 브랜치 연결점

- 파서가 규칙 기반(정규식 + 키워드)이라 문서 스타일 편차가 큰 경우 누락 가능
- 인증/권한 처리 미포함
- 다음 목표: step3 섹션별 초안 생성 파이프라인
