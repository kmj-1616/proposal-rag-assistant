# step5 구현 노트

## 범위

- step1~step4 전체 파이프라인 통합 검증
- 데모 실행 런북 및 장애 대응 시나리오 정리

## 데모 시작 전 체크리스트

### 환경 점검

```bash
# 1. Ollama 서버 기동 확인
ollama serve
ollama list   # qwen2.5:0.5b 가 목록에 있어야 함

# 없으면 다운로드
ollama pull qwen2.5:0.5b

# 2. API 서버 기동 (프로젝트 루트)
uvicorn app.main:app --port 8000

# 헬스체크
# Python: python -c "import urllib.request, json; r=urllib.request.urlopen('http://localhost:8000/api/v1/health',timeout=5); print(json.load(r))"

# 3. (선택) 검색 인덱스 준비 — step1 청크가 있을 때만 실행
# Python: python -c "import urllib.request, json; req=urllib.request.Request('http://localhost:8000/api/v1/proposals/index/rebuild', data=json.dumps({'reset': True}).encode(), headers={'Content-Type':'application/json'}, method='POST'); print(json.load(urllib.request.urlopen(req, timeout=60)))"

# 4. Streamlit UI 기동
streamlit run steps/step4_ui_and_export/app.py
```

| 항목 | 확인 방법 | 기대 결과 |
| --- | --- | --- |
| Ollama 기동 | `ollama list` | 모델 목록 표시 |
| API 서버 | `/api/v1/health` | `{"status": "ok", ...}` |
| Streamlit | `http://localhost:8501` | 사이드바 "API 서버 연결됨" |

---

## 데모 실행 시나리오

### A. Streamlit UI 기반 시나리오 (권장)

1. `http://localhost:8501` 접속
2. RFP 텍스트 붙여넣기 → **RFP 분석** 클릭
3. 분석 결과(프로젝트명·평가기준·요구사항) 확인
4. **초안 생성 시작** 클릭 (소요 시간: 모델에 따라 수 분)
5. 섹션별 생성 결과 확인 (expander 펼치기)
6. **Word(.docx) 생성** → **Word 파일 다운로드** 클릭

### B. API 직접 호출 시나리오 (폴백)

Streamlit이 동작하지 않거나 시간이 촉박한 경우 Python 스크립트로 대체한다.

```python
import urllib.request, json

API = "http://localhost:8000/api/v1"

# 1) RFP 분석
rfp_text = """프로젝트명: AI 기반 업무 자동화 시스템
발주기관: 한국정보화진흥원
예산: 5억원
사업 목적: 반복 업무 자동화로 행정 효율화
평가기준: 기술력 40점, 사업이해도 30점, 수행조직 30점
핵심 요구사항: RPA 도입, 문서 처리 자동화, 대시보드 구축"""

req = urllib.request.Request(
    f"{API}/rfp/analyze",
    data=json.dumps({"rfp_text": rfp_text}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
rfp_result = json.load(urllib.request.urlopen(req, timeout=30))
requirements = rfp_result["rfp_requirements"]
print("분석 완료:", requirements.get("project_name"))

# 2) 초안 생성 (시간이 걸림)
req2 = urllib.request.Request(
    f"{API}/drafts/generate",
    data=json.dumps({"rfp_requirements": requirements, "context_top_k": 1}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
draft = json.load(urllib.request.urlopen(req2, timeout=600))
print(f"생성 완료: {draft['total_sections']}개 섹션")
for s in draft["sections"]:
    print(f"  [{s['priority']}] {s['title']}")

# 3) Word 내보내기
req3 = urllib.request.Request(
    f"{API}/exports/word",
    data=json.dumps({"project_name": draft["project_name"], "sections": draft["sections"]}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
docx_bytes = urllib.request.urlopen(req3, timeout=30).read()
with open("demo_output.docx", "wb") as f:
    f.write(docx_bytes)
print("Word 파일 저장: demo_output.docx")
```

---

## 폴백 시나리오 (라이브 장애 대응)

| 장애 상황 | 증상 | 대응 |
| --- | --- | --- |
| Ollama 메모리 부족 | 503 `LLM_CALL_FAILED` + 메모리 오류 메시지 | 다른 앱 종료 후 재시도. 또는 더 작은 모델로 전환: `ollama pull qwen2.5:0.5b` |
| LLM 응답 타임아웃 | 생성 스피너가 멈춤 / 타임아웃 에러 | `context_top_k=1`로 줄이고 재시도. 폴백으로 미리 생성한 샘플 JSON 결과 사용 |
| 검색 인덱스 없음 | 생성은 되나 컨텍스트 청크 0개 | 컨텍스트 없이 생성 진행 가능 (정상 동작). 화면 사이드바에 "검색 인덱스 없음" 경고 표시됨 |
| API 서버 미기동 | Streamlit 사이드바 "연결 불가" | `uvicorn app.main:app --port 8000` 재실행 |
| Streamlit 미기동 | 브라우저 연결 거부 | `streamlit run steps/step4_ui_and_export/app.py` 재실행 |

---

## 현재 구현 한계

| 항목 | 현재 상태 | 비고 |
| --- | --- | --- |
| 생성 속도 | 섹션당 수 분 (CPU 추론) | GPU 환경이면 수 초로 단축 가능 |
| 생성 품질 | `qwen2.5:0.5b` 기준 초안 수준 | 더 큰 모델(3b/7b) 또는 OpenAI 전환 시 개선 |
| RFP 파서 | 규칙 기반, 비정형 RFP 에서 필드 누락 가능 | LLM 기반 파서로 교체 시 정확도 향상 |
| Word 서식 | 기본 스타일 (제목/본문 2단계) | 회사 템플릿 적용은 후속 과제 |
| PPT 출력 | 미구현 | `python-pptx` 기반 추후 추가 가능 |

## E2E 통합 검증 결과 (2026-05-14, develop 병합 후)

| 단계 | 엔드포인트 | 결과 | 비고 |
| --- | --- | --- | --- |
| 헬스체크 | `GET /health` | ✅ `{"status":"ok","index_ready":true}` | - |
| 인덱스 리빌드 | `POST /proposals/index/rebuild` | ✅ 560청크 인덱싱 완료 | 소요 약 44초 |
| 초안 생성 | `POST /drafts/generate` | ✅ 6개 섹션 생성 완료 | 소요 약 8.7분 (CPU, qwen2.5:0.5b) |
| Word 내보내기 | `POST /exports/word` | ✅ 36,848 bytes `.docx` 반환 | RFC 5987 한글 파일명 정상 |

- 테스트 환경: Windows 10, CPU 추론, qwen2.5:0.5b (394 MB), 포트 8001
- 인덱스 모델: `paraphrase-multilingual-MiniLM-L12-v2`

## 검증 체크리스트

- [x] API 서버 헬스체크 정상
- [x] RFP 분석(`/rfp/analyze`) 동작 확인
- [x] 유사 제안서 검색(`/proposals/search`) 동작 확인
- [x] LLM 오류 케이스 503 에러 정상 반환
- [x] Word 내보내기(`/exports/word`) 정상 반환
- [x] Streamlit UI 기동 확인
- [x] E2E 초안 생성 → Word 다운로드 전체 흐름 검증 완료
