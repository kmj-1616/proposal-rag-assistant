"""Word 문서 내보내기 서비스: 섹션별 초안 데이터를 .docx 파일로 변환한다."""
from __future__ import annotations

from io import BytesIO
from typing import Any


def build_docx(project_name: str | None, sections: list[dict[str, Any]]) -> bytes:
    """섹션 목록을 받아 Word 문서 바이트를 반환한다.

    Args:
        project_name: 문서 제목으로 사용할 프로젝트명. None이면 기본 제목 사용.
        sections: [{"title": str, "content": str, "priority": int, ...}] 형태의 목록.

    Returns:
        .docx 파일 바이트.
    """
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    title_text = project_name or "제안서 초안"
    title = doc.add_heading(title_text, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    for section in sections:
        section_title = section.get("title", "")
        content = section.get("content", "")
        priority = section.get("priority")

        heading_text = f"{section_title}" if priority is None else f"{section_title}"
        doc.add_heading(heading_text, level=1)

        for paragraph in content.split("\n\n"):
            stripped = paragraph.strip()
            if stripped:
                p = doc.add_paragraph(stripped)
                p.paragraph_format.space_after = Pt(6)

        doc.add_paragraph()

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
