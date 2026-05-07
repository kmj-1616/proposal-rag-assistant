# proposal-rag-assistant

RFP(제안요청서)를 구조화해서 기존 제안서 스타일을 반영한 초안을 생성하는 step 기반 프로젝트입니다.

## Public Repository Rules

이 저장소는 공개 저장소를 전제로 합니다.

- 실데이터(제안서 원문, RFP 원문) 커밋 금지
- 실데이터 파생 산출물(추출 텍스트, 청크) 커밋 금지
- 런타임 데이터는 반드시 `local_data/` 하위(이미 git ignore 처리)

세부 정책은 `docs/security-data-policy.md`를 따릅니다.

## Step Structure

- `steps/step1_data_prep`: 로컬 제안서 선별/복사, 텍스트 추출, 청킹
- `steps/step2_retrieval_and_rfp_parse`: 검색 인덱스 + RFP 구조화 파서
- `steps/step3_generation_pipeline`: 섹션 단위 초안 생성 파이프라인
- `steps/step4_ui_and_export`: UI와 문서 출력
- `steps/step5_integration_and_demo`: 통합 검증, 리허설, 데모 패키지

## Current Status

- 완료: step1 데이터 파이프라인의 공개 버전 스캐폴드 구축
  - 경로 하드코딩 제거(환경변수 + 상대경로 기반)
  - 민감 데이터 업로드 차단 정책 반영
- 예정: step2~step5 구현 및 검증

## Step1 Quick Start (Local Only)

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

### 3) 산출물 (로컬 전용)

- `local_data/step1/raw_proposals/`
- `local_data/step1/extracted_texts/`
- `local_data/step1/chunks/`

## Path Configuration

지원 환경변수:

- `LOCAL_DATA_ROOT`: 로컬 데이터 루트 경로 (기본값: `<repo>/local_data`)
- `LOCAL_PROPOSAL_SOURCE_DIR`: 원본 제안서 경로 override
- `STEP1_METADATA_CSV`: step1 메타데이터 CSV 경로 override

## Documentation

- `docs/security-data-policy.md`
- `docs/architecture.md`
- `docs/tech-decisions.md`
- `docs/implementation/step1.md`
- `docs/implementation/step2.md`
- `docs/implementation/step3.md`
- `docs/implementation/step4.md`
- `docs/implementation/step5.md`
