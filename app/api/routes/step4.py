"""API 라우터 - step4 exports/word 엔드포인트."""
from __future__ import annotations

from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.step4 import WordExportRequest

router = APIRouter(prefix="/api/v1", tags=["step4"])


@router.post(
    "/exports/word",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}},
            "description": "생성된 Word(.docx) 파일",
        }
    },
    summary="제안서 Word 파일 내보내기",
    description=(
        "섹션별 초안 데이터를 Word(.docx) 파일로 변환해 반환합니다.\n\n"
        "`POST /api/v1/drafts/generate` 응답의 `project_name`과 `sections` 값을 그대로 입력으로 사용할 수 있습니다."
    ),
)
def exports_word(body: WordExportRequest) -> StreamingResponse:
    from app.services.word_export_service import build_docx

    sections_data = [s.model_dump() for s in body.sections]
    docx_bytes = build_docx(
        project_name=body.project_name,
        sections=sections_data,
    )

    filename = _safe_filename(body.project_name)
    encoded = quote(filename, safe="")
    content_disposition = f"attachment; filename*=UTF-8''{encoded}"
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": content_disposition},
    )


def _safe_filename(project_name: str | None) -> str:
    """프로젝트명으로 안전한 파일명을 생성한다."""
    if not project_name:
        return "proposal_draft.docx"
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in project_name)
    safe = safe.strip().replace(" ", "_")
    return f"{safe[:50]}.docx"
