# proposal-rag-assistant

RFP(제안요청서)를 구조화하고, 기존 제안서 스타일을 반영한 초안을 생성하는 step 기반 프로젝트입니다.

## 프로젝트 목표

이 프로젝트는 아래 흐름을 자동화하는 것을 목표로 합니다.

1. RFP 분석(고객사 RFP 업로드, 요구사항 자동 추출/구조화)
2. 유사 제안서 검색(학습된 기존 제안서에서 참고 내용 탐색)
3. 제안서 초안 생성(RFP 요구사항 + 기존 스타일 기반 섹션별 작성)
4. 파일 출력(Word 또는 PPT 내보내기)

## 아키텍처 개요

현재는 step 기반으로 모듈을 분리해 단계적으로 구현 중입니다.

```text
RFP 입력
  -> Step2 구조화 파싱
  -> Step2 유사 제안서 검색(Step1 청크)
  -> Step3 섹션별 초안 생성
  -> Step4 문서 출력(Word/PPT)
  -> Step5 통합 검증 및 데모
```

step 모듈:

- `steps/step1_data_prep`: 로컬 제안서 선별/복사, 텍스트 추출, 청킹
- `steps/step2_retrieval_and_rfp_parse`: 검색 인덱스 + RFP 구조화 파서
- `steps/step3_generation_pipeline`: 섹션 단위 초안 생성 파이프라인
- `steps/step4_ui_and_export`: UI 및 문서 출력
- `steps/step5_integration_and_demo`: 통합 검증, 리허설, 데모 패키지

## API 엔드포인트

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | 상태 | 설명 |
| --- | --- | --- | --- |
| POST | `/rfp/analyze` | 구현 | RFP 텍스트/파일경로 입력 → 구조화 요구사항 JSON |
| POST | `/proposals/index/rebuild` | 구현 | Step1 청크 기반 Chroma 임베딩 인덱스 재생성 |
| POST | `/proposals/search` | 구현 | 임베딩 유사도 기반 유사 제안서 청크 검색 |
| POST | `/drafts/generate` | 구현 | RFP + 검색 컨텍스트 기반 섹션별 제안서 초안 생성 (Ollama 또는 OpenAI 호환 LLM) |
| POST | `/exports/word` | 구현 | 섹션 초안 → Word(.docx) 파일 내보내기 |
| POST | `/exports/ppt` | 구현 | 섹션 초안 → PowerPoint(.pptx) 파일 내보내기 (표지·목차·섹션 자동 구성) |
| GET | `/health` | 구현 | 서비스 헬스체크 (인덱스 상태 포함) |

서버 실행:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 최초 실행 또는 step1 데이터 갱신 후: POST /api/v1/proposals/index/rebuild
# OpenAPI(Swagger) 문서: http://localhost:8000/docs
```

Streamlit UI 실행 (별도 터미널, API 서버가 켜진 상태에서):

```bash
streamlit run steps/step4_ui_and_export/app.py
# UI: http://localhost:8501
```

## 지원 파일 포맷

### Step1 입력 포맷(구현됨)

| 용도 | 포맷 | 확장자 | 처리 방식 |
| --- | --- | --- | --- |
| 제안서 원본 | PowerPoint | `.pptx` | `python-pptx`로 텍스트 추출 |
| 제안서 원본 | PDF | `.pdf` | PyMuPDF 우선, 실패 시 pdfplumber fallback |
| 메타데이터 | CSV | `.csv` | 선정 파일 목록 기반 복사 |

### Step2 입력 포맷(부분 구현)

| 용도 | 포맷 | 확장자 | 처리 방식 |
| --- | --- | --- | --- |
| RFP 텍스트 | Text | `.txt` | 키워드 기반 구조화 파싱 |

추가 포맷(`.md`, `.docx`)은 추후 필요 시 확장 예정입니다.

## 현재 구현 상태

- 완료
  - step1 스크립트 공개 버전 구성
  - 민감 데이터 로컬 전용 정책 반영
  - step2 RFP 파서 품질 강화 (규칙 기반 추출, 스키마 검증 파이프라인)
  - step2 FastAPI API 골격 구현 (`/rfp/analyze`, `/proposals/search`, `/health`)
  - step2 임베딩 기반 검색 고도화 (`chromadb` + `sentence-transformers`, `/proposals/index/rebuild`)
  - step3 `/drafts/generate` API (OpenAI 호환 LLM 어댑터 기반 섹션별 초안 생성, Ollama/OpenAI 지원)
  - step4 Streamlit UI (RFP 입력 → 분석 → 생성 → 다운로드 흐름)
  - step4 `/exports/word` Word(.docx) 내보내기 API (마크다운 → Word 스타일 자동 변환)
  - step4 `/exports/ppt` PowerPoint 내보내기 API (표지·목차·섹션 슬라이드 자동 생성)
  - step5 데모 런북 및 장애 대응 시나리오 문서화 (`docs/implementation/step5.md`)
  - step5 E2E 통합 검증 완료 (2026-05-14)

## 빠른 시작 (Step1, 로컬 전용)

### 1) 로컬 입력 준비

- `local_data/proposal_collection/`에 로컬 제안서 파일 배치
- `local_data/step1/proposal_candidates.csv` 생성
  - 템플릿: `steps/step1_data_prep/metadata/proposal_candidates_template.csv`

### 2) 실행

```bash
python "steps/step1_data_prep/scripts/copy_selected_to_raw.py"
python "steps/step1_data_prep/scripts/extract_texts.py"
python "steps/step1_data_prep/scripts/chunk_texts.py"
```

### 3) 산출물(로컬 전용)

- `local_data/step1/raw_proposals/`
- `local_data/step1/extracted_texts/`
- `local_data/step1/chunks/`

## 환경변수

프로젝트 루트에 `.env` 파일을 생성해 설정한다. 템플릿: `.env.example`

### LLM 설정 (초안 생성에 필요)

| 변수명 | 기본값 | 설명 |
| --- | --- | --- |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | LLM 엔드포인트 (Ollama 기본) |
| `LLM_MODEL` | `qwen2.5:0.5b` | 사용 모델명 |
| `LLM_API_KEY` | `ollama` | API 키 (Ollama는 임의 문자열 가능) |

**Ollama 사전 조건** (`drafts/generate` API 사용 시 필수):

```bash
# Ollama 설치 후
ollama serve
ollama pull qwen2.5:0.5b   # 약 400 MB, 기본 품질
# ollama pull qwen2.5:3b   # 약 2 GB, 향상된 품질 (RAM 여유 시 권장)
```

> 메모리 가이드: `0.5b` ≈ 400 MB / `3b` ≈ 2 GB / `7b` ≈ 4.5 GB

**OpenAI 전환 시** `.env` 수정:
```
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 데이터 경로 설정

| 변수명 | 기본값 | 설명 |
| --- | --- | --- |
| `LOCAL_DATA_ROOT` | `<repo>/local_data` | 로컬 데이터 루트 경로 |
| `CHROMA_INDEX_DIR` | `local_data/step2/chroma_index` | Chroma 인덱스 저장 경로 |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | 임베딩 모델명 |
| `LOCAL_PROPOSAL_SOURCE_DIR` | — | 원본 제안서 경로 오버라이드 |
| `STEP1_METADATA_CSV` | — | step1 메타데이터 CSV 경로 오버라이드 |

## 에이전트 규칙 요약

- 브랜치 전략: 라이트 Git Flow (`main`, `develop`, `feature/*`)
- 커밋 규칙: Conventional Commits + 한글 본문
- 보안 경계: 실데이터/파생 산출물은 로컬(`local_data/`)에서만 처리
- 문서 정책: `docs` 하위 문서는 한글 유지
- 상세 규칙: `AGENTS.md`

## 문서

- `AGENTS.md` (에이전트/모델 공통 작업 규칙)
- `docs/security-data-policy.md`
- `docs/architecture.md`
- `docs/tech-decisions.md`
- `docs/implementation/step1.md`
- `docs/implementation/step2.md`
- `docs/implementation/step3.md`
- `docs/implementation/step4.md`
- `docs/implementation/step5.md`
