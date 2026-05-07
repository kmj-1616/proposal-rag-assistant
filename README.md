# proposal-rag-assistant

RFP(제안요청서)를 구조화하고, 기존 제안서 스타일을 반영한 초안을 생성하는 step 기반 프로젝트입니다.

## 저장소 운영 규칙

### 1) 브랜치 전략 (라이트 Git Flow)

- `main`: 배포/안정 브랜치
- `develop`: 통합 개발 브랜치
- `feature/<scope>-<topic>`: 기능 작업 브랜치

병합 흐름:

- 기본: `feature/*` -> `develop`
- 릴리즈 반영: `develop` -> `main`

### 2) 커밋 메시지 규칙 (Conventional + 한글 본문)

형식:

`<type>(<scope>): <요약>`

예시:

- `feat(step2): RFP 파서 골격 추가`
- `docs(architecture): 데이터 흐름 문서 한글화`
- `refactor(step1): 경로 설정 유틸 분리`

본문은 변경 이유와 의도를 한글로 작성합니다.

### 3) 공개 저장소 보안 규칙

- 실데이터(제안서 원문, RFP 원문) 커밋 금지
- 실데이터 파생 산출물(추출 텍스트, 청크) 커밋 금지
- 런타임 데이터는 `local_data/` 하위에서만 사용

세부 정책은 `docs/security-data-policy.md`를 따릅니다.

## Step 구조

- `steps/step1_data_prep`: 로컬 제안서 선별/복사, 텍스트 추출, 청킹
- `steps/step2_retrieval_and_rfp_parse`: 검색 인덱스 + RFP 구조화 파서
- `steps/step3_generation_pipeline`: 섹션 단위 초안 생성 파이프라인
- `steps/step4_ui_and_export`: UI 및 문서 출력
- `steps/step5_integration_and_demo`: 통합 검증, 리허설, 데모 패키지

## 현재 상태

- 완료: step1 공개 버전 스캐폴드 구축
  - 경로 하드코딩 제거(환경변수 + 상대경로 기반)
  - 민감 데이터 업로드 차단 정책 반영
- 진행 예정: step2 ~ step5 구현 및 검증

## Step1 빠른 시작 (로컬 전용)

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

## 경로 설정

지원 환경변수:

- `LOCAL_DATA_ROOT`: 로컬 데이터 루트 경로 (기본값: `<repo>/local_data`)
- `LOCAL_PROPOSAL_SOURCE_DIR`: 원본 제안서 경로 오버라이드
- `STEP1_METADATA_CSV`: step1 메타데이터 CSV 경로 오버라이드

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
