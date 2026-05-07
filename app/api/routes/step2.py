"""API 라우터 - step2 엔드포인트."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.models.step2 import (
    ErrorResponse,
    IndexRebuildRequest,
    IndexRebuildResponse,
    ProposalSearchRequest,
    ProposalSearchResponse,
    ProposalSearchResult,
    RfpAnalyzeRequest,
    RfpAnalyzeResponse,
    RfpRequirements,
)
from app.services.step2_service import analyze_rfp, rebuild_index, search_proposals

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
    responses={503: {"model": ErrorResponse}},
    summary="유사 제안서 섹션 검색 (임베딩 기반)",
    description=(
        "질의(`query`)와 의미적으로 유사한 제안서 청크를 반환합니다. "
        "임베딩 모델: `paraphrase-multilingual-MiniLM-L12-v2`. "
        "인덱스 미생성 시 `POST /api/v1/proposals/index/rebuild`를 먼저 호출하세요."
    ),
)
def proposals_search(body: ProposalSearchRequest) -> ProposalSearchResponse:
    try:
        raw_results = search_proposals(query=body.query, top_k=body.top_k)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "INDEX_NOT_READY",
                "message": str(exc),
                "details": {"hint": "POST /api/v1/proposals/index/rebuild 를 먼저 호출하세요."},
            },
        )
    results = [ProposalSearchResult(**r) for r in raw_results]
    return ProposalSearchResponse(query=body.query, results=results)


@router.post(
    "/proposals/index/rebuild",
    response_model=IndexRebuildResponse,
    responses={400: {"model": ErrorResponse}},
    summary="제안서 검색 인덱스 재생성",
    description=(
        "Step1 청크 디렉터리를 읽어 Chroma 임베딩 인덱스를 재생성합니다. "
        "`reset=true`(기본값)이면 기존 인덱스를 삭제 후 재생성합니다. "
        "처음 실행 또는 step1 데이터 갱신 후 호출하세요."
    ),
)
def index_rebuild(body: IndexRebuildRequest) -> IndexRebuildResponse:
    try:
        result = rebuild_index(
            chunks_root_str=body.chunks_root,
            reset=body.reset,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "CHUNKS_NOT_FOUND",
                "message": str(exc),
                "details": {"chunks_root": body.chunks_root},
            },
        )
    return IndexRebuildResponse(**result)


@router.get(
    "/health",
    summary="헬스체크",
    response_model=dict,
)
def health() -> dict:
    from app.services.chroma_index_service import get_retriever

    retriever = get_retriever()
    return {
        "status": "ok",
        "service": "proposal-rag-assistant",
        "index_ready": retriever.index_ready,
    }
