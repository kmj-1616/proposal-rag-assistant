"""FastAPI 앱 진입점."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.step2 import router as step2_router
from app.api.routes.step3 import router as step3_router
from app.api.routes.step4 import router as step4_router

app = FastAPI(
    title="proposal-rag-assistant API",
    description=(
        "RFP 구조화 파싱 및 유사 제안서 검색, 제안서 초안 생성 API.\n\n"
        "- `POST /api/v1/rfp/analyze`: RFP 텍스트 → 구조화된 요구사항 JSON\n"
        "- `POST /api/v1/proposals/search`: 임베딩 기반 유사 제안서 청크 검색\n"
        "- `POST /api/v1/proposals/index/rebuild`: 검색 인덱스 재생성\n"
        "- `POST /api/v1/drafts/generate`: RFP + 검색 컨텍스트 기반 섹션별 초안 생성\n"
        "- `POST /api/v1/exports/word`: 섹션 초안 → Word(.docx) 파일 내보내기\n"
        "- `GET /api/v1/health`: 헬스체크"
    ),
    version="0.3.0",
)

app.include_router(step2_router)
app.include_router(step3_router)
app.include_router(step4_router)
