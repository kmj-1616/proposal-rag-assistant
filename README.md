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
| POST | `/drafts/generate` | 예정 | 섹션별 제안서 초안 생성 |
| POST | `/exports/word` | 예정 | Word 파일 출력 |
| POST | `/exports/ppt` | 예정 | PPT 파일 출력 |
| GET | `/health` | 구현 | 서비스 헬스체크 (인덱스 상태 포함) |

서버 실행:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 최초 실행 또는 step1 데이터 갱신 후: POST /api/v1/proposals/index/rebuild
# OpenAPI 문서: http://localhost:8000/docs
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
- 예정
  - step3 생성 파이프라인
  - step4 UI/출력
  - step5 통합 테스트/데모

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

- `LOCAL_DATA_ROOT`: 로컬 데이터 루트 경로 (기본값: `<repo>/local_data`)
- `LOCAL_PROPOSAL_SOURCE_DIR`: 원본 제안서 경로 오버라이드
- `STEP1_METADATA_CSV`: step1 메타데이터 CSV 경로 오버라이드

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
