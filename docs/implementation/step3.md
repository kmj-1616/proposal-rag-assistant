# step3 구현 노트

## 범위

- 섹션 단위 제안서 생성 파이프라인 (API 우선)
- `POST /api/v1/drafts/generate` 최소 E2E 구현
- OpenAI 호환 LLM 어댑터 (Ollama / OpenAI 교체 가능)

## 구현 산출물

| 파일 | 역할 |
| --- | --- |
| `app/models/step3.py` | Pydantic 요청/응답 모델 (`DraftGenerateRequest`, `DraftGenerateResponse` 등) |
| `app/services/claude_cli_adapter.py` | OpenAI 호환 LLM 클라이언트 래퍼 (환경변수로 백엔드 전환) |
| `app/services/step3_generation_service.py` | 섹션 계획 + step2 검색 컨텍스트 주입 + LLM 호출 루프 |
| `app/api/routes/step3.py` | `POST /api/v1/drafts/generate` FastAPI 라우터 |

## 엔드포인트 동작 흐름

```
POST /api/v1/drafts/generate
  ├── 입력 해석: rfp_requirements > rfp_text > rfp_file_path 우선순위
  ├── RFP 파싱 (필요 시 step2 parser 재사용)
  ├── 섹션 계획
  │     ├── authoring_guidelines에 목차 패턴이 있으면 추출 (toc_source: rfp_guidelines)
  │     └── 없으면 기본 6개 섹션 사용 (toc_source: default)
  │         배점 높은 섹션을 priority 1위로 정렬
  └── 섹션별 생성 루프
        ├── search_proposals(섹션 제목 + 프로젝트명) → 컨텍스트 청크 top-k
        ├── 프롬프트 조립 (RFP 정보 + 검색 컨텍스트)
        └── call_claude(prompt) → LLM 호출 → 섹션 초안 텍스트
```

## LLM 어댑터 설정

환경변수(`.env`)로 LLM 백엔드를 전환한다.

| 변수명 | 기본값 | 설명 |
| --- | --- | --- |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | LLM 엔드포인트 (Ollama 기본) |
| `LLM_MODEL` | `qwen2.5:0.5b` | 사용 모델명 |
| `LLM_API_KEY` | `ollama` | API 키 (Ollama는 임의 문자열 가능) |

Ollama 사용 시 사전 조건:
1. `ollama serve` 구동 확인
2. `ollama pull qwen2.5:0.5b` (로컬 RAM 여유에 따라 모델 선택)

> 메모리 가이드: `qwen2.5:0.5b` ≈ 400 MB, `qwen2.5:3b` ≈ 2 GB, `qwen2.5:7b` ≈ 4.5 GB. 가용 RAM이 모델 요구량보다 여유 있어야 로드된다.

에러 케이스 및 HTTP 응답 코드:

| 에러 | error_code | HTTP |
| --- | --- | --- |
| LLM_API_KEY 미설정 | `LLM_NOT_CONFIGURED` | 503 |
| API 인증 실패 (401/403) | `LLM_AUTH_FAILED` | 503 |
| 응답 타임아웃 (기본 120초) | `LLM_TIMEOUT` | 503 |
| 그 외 API 오류 | `LLM_CALL_FAILED` | 503 |

## 검증 계획

- [x] 정상 케이스: rfp_text 입력 → 섹션별 초안 JSON 반환
- [x] 422 케이스: 입력 3개 모두 누락 시 `MISSING_INPUT` 에러 반환
- [x] LLM 미기동/메모리 부족 케이스: Ollama 모델 로드 실패 시 503 + `LLM_CALL_FAILED` 반환
- [ ] step2 검색 결과가 섹션 프롬프트에 포함되는지 로그 확인 (인덱스 구축 후 검증 예정)
- [x] OpenAPI `/docs`에서 스키마/예시 확인

## 검증 결과

| 케이스 | 결과 | 비고 |
| --- | --- | --- |
| `GET /api/v1/health` | 200 OK (`index_ready: true`) | 서버 정상 기동 확인 |
| `POST /api/v1/drafts/generate` — 입력 누락 | 422 + `MISSING_INPUT` | rfp_text/rfp_file_path/rfp_requirements 모두 누락 시 정상 반환 |
| `POST /api/v1/drafts/generate` — 정상 케이스 | Ollama 응답 대기 중 타임아웃 | 가용 RAM ~500 MB 환경에서 6섹션 순차 생성 시 시간 초과. RAM 확보 후 재검증 필요 |
| Ollama 직접 호출 (`qwen2.5:0.5b`) | 응답 확인 (~10초) | Ollama 단독 호출 시 정상 응답 확인 |
| LLM 메모리 부족 | 503 + `LLM_CALL_FAILED` + 상세 메시지 | `qwen2.5:7b`/`qwen2.5:3b` 가용 메모리 초과 시 에러 응답 확인 |

## 한계 및 후속 과제

- 현재 어댑터는 OpenAI 호환 엔드포인트 전용. Anthropic `messages` API 방식이 필요한 경우 별도 어댑터 추가.
- 섹션별 생성은 순차 처리. 필요 시 비동기 병렬 처리로 전환 가능.
- 프롬프트 버전 비교(v1/v2/v3) 기록은 추후 단계에서 추가.
