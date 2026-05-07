"""API 라우터 - step2 엔드포인트."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.models.step2 import (
    ErrorResponse,
    ProposalSearchRequest,
    ProposalSearchResponse,
    ProposalSearchResult,
    RfpAnalyzeRequest,
    RfpAnalyzeResponse,
    RfpRequirements,
)
from app.services.step2_service import analyze_rfp, search_proposals

router = APIRouter(prefix="/api/v1", tags=["step2"])


@router.post(
    "/rfp/analyze",
    response_model=RfpAnalyzeResponse,
    responses={422: {"model": ErrorResponse}},
    summary="RFP 텍스트 구조화 파싱",
    description=(
        "RFP 전문 텍스트(`rfp_text`) 또는 로컬 파일 경로(`rfp_file_path`)를 받아 "
        "구조화된 요구사항 JSON을 반환합니다."
    ),
)
def rfp_analyze(body: RfpAnalyzeRequest) -> RfpAnalyzeResponse:
    if body.rfp_text is None and body.rfp_file_path is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "MISSING_INPUT",
                "message": "rfp_text 또는 rfp_file_path 중 하나는 필수입니다.",
                "details": None,
            },
        )

    if body.rfp_text is not None:
        text = body.rfp_text
    else:
        file_path = Path(body.rfp_file_path).expanduser().resolve()  # type: ignore[arg-type]
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "FILE_NOT_FOUND",
                    "message": f"파일을 찾을 수 없습니다: {file_path}",
                    "details": {"rfp_file_path": body.rfp_file_path},
                },
            )
        text = file_path.read_text(encoding="utf-8", errors="replace")

    result = analyze_rfp(text)
    return RfpAnalyzeResponse(
        rfp_requirements=RfpRequirements(**result["rfp_requirements"]),
        missing_fields=result["missing_fields"],
    )


@router.post(
    "/proposals/search",
    response_model=ProposalSearchResponse,
    summary="유사 제안서 섹션 검색 (키워드 기반 스텁)",
    description=(
        "질의(`query`)와 유사한 제안서 청크를 반환합니다. "
        "현재는 키워드 빈도 기반 스모크 검색이며, 임베딩 검색은 후속 브랜치에서 구현 예정입니다."
    ),
)
def proposals_search(body: ProposalSearchRequest) -> ProposalSearchResponse:
    raw_results = search_proposals(query=body.query, top_k=body.top_k)
    results = [ProposalSearchResult(**r) for r in raw_results]
    return ProposalSearchResponse(query=body.query, results=results)


@router.get(
    "/health",
    summary="헬스체크",
    response_model=dict,
)
def health() -> dict:
    return {"status": "ok", "service": "proposal-rag-assistant"}
