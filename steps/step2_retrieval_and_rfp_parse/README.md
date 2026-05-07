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

## 완료 기준

- 자연어 질의 시 관련 청크 검색이 동작한다.
- RFP 업로드 후 구조화 JSON이 안정적으로 생성된다.
- 필수 추출 항목 누락 여부를 검증할 수 있다.

## API 서버 실행 (feature/step2-api-skeleton)

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

### 샘플 요청

**POST /api/v1/rfp/analyze** (텍스트 입력)

```bash
curl -X POST http://localhost:8000/api/v1/rfp/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "프로젝트명: AI 기반 제안서 자동화 시스템\n발주기관: 한국정보화진흥원\n예산: 3억원\n사업 목적: RFP 자동 분석 및 제안서 초안 생성\n평가기준: 기술평가 80점, 가격평가 20점"
  }'
```

**POST /api/v1/rfp/analyze** (파일경로 입력)

```bash
curl -X POST http://localhost:8000/api/v1/rfp/analyze \
  -H "Content-Type: application/json" \
  -d '{"rfp_file_path": "/path/to/local/rfp.txt"}'
```

**POST /api/v1/proposals/search**

```bash
curl -X POST http://localhost:8000/api/v1/proposals/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI 기반 데이터 분석 플랫폼", "top_k": 5}'
```

### 샘플 응답 (/rfp/analyze)

```json
{
  "rfp_requirements": {
    "project_name": "AI 기반 제안서 자동화 시스템",
    "organization": "한국정보화진흥원",
    "budget_range": "3억원",
    "purpose_background": "RFP 자동 분석 및 제안서 초안 생성",
    "evaluation_criteria": ["평가기준: 기술평가 80점, 가격평가 20점"],
    "core_requirements": [],
    "authoring_guidelines": [],
    "schedule_constraints": [],
    "must_have_constraints": []
  },
  "missing_fields": ["core_requirements", "authoring_guidelines", "schedule_constraints", "must_have_constraints"]
}
```

## 현재 상태

- 파서/검색 스모크 테스트 골격 구현 완료
- 파서 품질 강화 완료 (feature/step2-rfp-parser-quality)
- FastAPI API 골격 구현 완료 (feature/step2-api-skeleton)
  - `POST /api/v1/rfp/analyze`: 텍스트/파일경로 입력 지원
  - `POST /api/v1/proposals/search`: 키워드 기반 스텁 검색
  - `GET /api/v1/health`: 헬스체크

## 한계 및 다음 브랜치 연결점

- 검색은 키워드 빈도 기반이며 임베딩 검색은 미구현
- 파서는 규칙 기반이며 의미 기반 추출은 미구현
- 인증/권한 처리 미포함
- 다음 목표: 벡터DB(ChromaDB) 통합 및 임베딩 검색 고도화
