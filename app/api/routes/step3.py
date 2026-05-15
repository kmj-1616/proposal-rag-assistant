"""API 라우터 - step3 drafts/generate 엔드포인트."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.models.step2 import ErrorResponse
from app.models.step3 import (
    DraftGenerateRequest,
    DraftGenerateResponse,
    DraftSection,
    GenerationMeta,
)
from app.services.claude_cli_adapter import (
    ClaudeAdapterError,
    ClaudeNotInstalledError,
    ClaudeNotLoggedInError,
    ClaudeTimeoutError,
)

router = APIRouter(prefix="/api/v1", tags=["step3"])


@router.post(
    "/drafts/generate",
    response_model=DraftGenerateResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="제안서 섹션별 초안 생성",
    description=(
        "RFP 요구사항과 유사 제안서 검색 컨텍스트를 결합해 섹션별 제안서 초안을 생성합니다.\n\n"
        "입력 방식 (셋 중 하나):\n"
        "- `rfp_text`: RFP 전문 텍스트 → 내부에서 자동 파싱\n"
        "- `rfp_file_path`: 로컬 RFP .txt 파일 경로 → 읽어서 자동 파싱\n"
        "- `rfp_requirements`: 이미 파싱된 구조화 객체 (`/rfp/analyze` 응답값)\n\n"
        "LLM 백엔드는 `.env`의 `LLM_BASE_URL` / `LLM_MODEL` 환경변수로 결정됩니다.\n"
        "기본값: Ollama (`http://localhost:11434/v1`, 모델: `qwen2.5:7b`).\n"
        "Ollama 미기동 또는 모델 미설치 시 503 반환."
    ),
)
def drafts_generate(body: DraftGenerateRequest) -> DraftGenerateResponse:
    rfp_dict = _resolve_rfp(body)

    try:
        from app.services.step3_generation_service import generate_draft
        result = generate_draft(rfp=rfp_dict, context_top_k=body.context_top_k)
    except ClaudeNotInstalledError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
                "details": exc.details,
            },
        )
    except ClaudeNotLoggedInError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
                "details": exc.details,
            },
        )
    except ClaudeTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
                "details": exc.details,
            },
        )
    except ClaudeAdapterError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
                "details": exc.details,
            },
        )

    sections = [DraftSection(**s) for s in result["sections"]]
    meta = GenerationMeta(**result["generation_meta"])

    return DraftGenerateResponse(
        project_name=result["project_name"],
        sections=sections,
        total_sections=result["total_sections"],
        generation_meta=meta,
    )


def _resolve_rfp(body: DraftGenerateRequest) -> dict:
    """요청에서 RFP dict를 확정한다. rfp_requirements > rfp_text > rfp_file_path 순으로 우선."""
    if body.rfp_requirements is not None:
        return body.rfp_requirements.model_dump()

    if body.rfp_text is None and body.rfp_file_path is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "MISSING_INPUT",
                "message": (
                    "rfp_text, rfp_file_path, rfp_requirements 중 하나는 필수입니다."
                ),
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
        from app.api.routes.step2 import _read_file_text
        text = _read_file_text(file_path, body.rfp_file_path)

    from app.services.step2_service import analyze_rfp
    return analyze_rfp(text)["rfp_requirements"]
