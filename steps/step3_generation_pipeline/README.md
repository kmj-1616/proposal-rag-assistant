# step3_generation_pipeline

## 목표

RFP 구조화 결과와 유사 제안서 검색 결과를 결합해 섹션별 제안서 초안을 생성한다.

## 핵심 구현 범위

- 목차 자동 구성 로직
  - RFP에 목차 지정이 있으면 우선 반영
  - 목차 지정이 없으면 기본 회사 공통 목차 사용
  - 평가 배점이 높은 항목에 더 많은 분량/우선순위 할당
- 섹션별 생성 파이프라인
  - `RFP 분석 -> 검색 컨텍스트 주입 -> 섹션 생성` 흐름
  - 전체 원샷 생성이 아닌 섹션 단위 생성
- LLM 어댑터
  - `.env`의 `LLM_BASE_URL` / `LLM_MODEL`로 백엔드 전환 (Ollama 기본)
  - OpenAI 호환 엔드포인트 범용 지원 (Ollama / OpenAI 등)

## API 실행 방법

```bash
# 서버 기동
uvicorn app.main:app --reload --port 8000

# 정상 케이스: rfp_text 직접 입력
curl -X POST http://localhost:8000/api/v1/drafts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "프로젝트명: AI 기반 업무 자동화\n발주기관: 한국정보화진흥원\n평가기준: 기술력 40점, 사업이해도 30점",
    "context_top_k": 3
  }'

# 이미 파싱된 요구사항 객체를 직접 전달하는 케이스
curl -X POST http://localhost:8000/api/v1/drafts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_requirements": {
      "project_name": "AI 기반 업무 자동화",
      "organization": "한국정보화진흥원",
      "budget_range": null,
      "purpose_background": null,
      "evaluation_criteria": ["기술력 40점", "사업이해도 30점"],
      "core_requirements": [],
      "authoring_guidelines": [],
      "schedule_constraints": [],
      "must_have_constraints": []
    },
    "context_top_k": 3
  }'
```

## 사전 조건

1. Ollama 설치 및 서버 기동: `ollama serve`
2. 모델 다운로드: `ollama pull qwen2.5:7b`
3. (선택) 검색 인덱스 구축: `POST /api/v1/proposals/index/rebuild`

> OpenAI 등 다른 LLM 사용 시 `.env`의 `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY`를 변경하세요.

## 산출물

- 목차 생성 결과(중간 구조 데이터) — `generation_meta.toc_source`로 확인
- 섹션별 생성 텍스트 — `sections[].content`
- 생성 메타정보 — `generation_meta`

## 완료 기준

- 목차 구성부터 섹션별 생성까지 End-to-End로 동작한다.
- Ollama 미기동/모델 미설치 시 사용자 친화적 에러(503)가 반환된다.
- step2 검색 결과가 프롬프트에 반영되는 흐름이 확인된다.

## 현재 상태

- API 구현 완료 (`POST /api/v1/drafts/generate`)
- OpenAI 호환 LLM 어댑터 구현 완료 (Ollama 기본, 환경변수로 전환)
- 실 실행 검증 진행 중
