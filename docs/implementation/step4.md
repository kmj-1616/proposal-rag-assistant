# step4 구현 노트

## 범위

- RFP 입력 → 분석 → 초안 생성 → Word 다운로드 Streamlit UI
- `POST /api/v1/exports/word` Word 내보내기 API 엔드포인트

## 구현 산출물

| 파일 | 역할 |
| --- | --- |
| `steps/step4_ui_and_export/app.py` | Streamlit UI 앱 (4단계 흐름: 입력→분석→생성→다운로드) |
| `app/models/step4.py` | `WordExportRequest` Pydantic 모델 |
| `app/services/word_export_service.py` | 섹션 데이터 → `.docx` 변환 (`python-docx`) |
| `app/api/routes/step4.py` | `POST /api/v1/exports/word` FastAPI 라우터 |

## 실행 방법

### API 서버 + Streamlit UI 동시 실행

```bash
# 터미널 1: API 서버
uvicorn app.main:app --port 8000

# 터미널 2: Streamlit UI
streamlit run steps/step4_ui_and_export/app.py
```

브라우저에서 `http://localhost:8501` 접속

### Word 내보내기 API 단독 테스트

```bash
curl -X POST http://localhost:8000/api/v1/exports/word \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "AI 기반 업무 자동화",
    "sections": [
      {"title": "사업 이해도 및 수행 전략", "content": "본 사업은 ...", "priority": 1},
      {"title": "기술 요구사항 대응방안", "content": "AI 기반 ...", "priority": 2}
    ]
  }' --output proposal.docx
```

## UI 흐름

```
1단계: RFP 텍스트 입력 (text_area)
  └─ [RFP 분석] 버튼 → POST /api/v1/rfp/analyze
2단계: 분석 결과 확인 (프로젝트명·평가기준·요구사항)
  └─ 전체 JSON expander로 확인 가능
3단계: [초안 생성 시작] 버튼 → POST /api/v1/drafts/generate
  └─ LLM 오류 시 친화적 메시지 + 체크리스트 안내
4단계: 섹션별 결과 expander 표시
  └─ [Word(.docx) 생성] → POST /api/v1/exports/word → 다운로드 버튼
```

## 사이드바 설정

- 서버 헬스체크 실시간 표시 (30초 캐시)
- 섹션별 참고 청크 수(`context_top_k`) 슬라이더 (1~10, 기본 3)

## 환경변수 / 전제 조건

| 항목 | 설명 |
| --- | --- |
| API 서버 | `uvicorn app.main:app --port 8000` |
| Ollama | `ollama serve` + `ollama pull qwen2.5:0.5b` |
| (선택) 검색 인덱스 | `POST /api/v1/proposals/index/rebuild` |

## 검증 체크리스트

- [x] `POST /api/v1/exports/word` 200 OK + `.docx` 파일 반환 (36 KB, 2섹션 기준)
- [x] 한글 파일명 RFC 5987 인코딩 적용 (`filename*=UTF-8''...`)
- [x] Streamlit 앱 정상 기동 확인
- [ ] Streamlit UI 전체 흐름 E2E 확인 (LLM 생성 포함)
- [ ] 오류 메시지(서버 미기동, LLM 타임아웃) 노출 확인

## 검증 결과

| 케이스 | 결과 | 비고 |
| --- | --- | --- |
| `POST /api/v1/exports/word` 정상 입력 | 200 OK | 36,875 bytes .docx 반환 확인 |
| 한글 파일명 Content-Disposition | 정상 | RFC 5987 UTF-8 인코딩 적용 |
| Streamlit 앱 기동 | 정상 | `http://localhost:8501` 접속 가능 |

## 한계 및 후속 과제

- Word 서식은 기본 스타일만 적용. 회사 템플릿 반영은 step4 확장 과제.
- PPT 출력은 미구현. `python-pptx`로 추후 `POST /api/v1/exports/ppt` 추가 가능.
- Streamlit은 로컬 단독 실행 전용. 공유/배포 시 인증·세션 관리 별도 고려 필요.
