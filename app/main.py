"""FastAPI 앱 진입점."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.step2 import router as step2_router

app = FastAPI(
    title="proposal-rag-assistant API",
    description=(
        "RFP 구조화 파싱 및 유사 제안서 검색 API.\n\n"
        "- `POST /api/v1/rfp/analyze`: RFP 텍스트 → 구조화된 요구사항 JSON\n"
        "- `POST /api/v1/proposals/search`: 키워드 기반 유사 제안서 청크 검색\n"
        "- `GET /api/v1/health`: 헬스체크"
    ),
    version="0.1.0",
)

app.include_router(step2_router)
