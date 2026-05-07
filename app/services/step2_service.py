"""step2 비즈니스 로직: RFP 파싱 및 제안서 검색."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# steps 패키지를 임포트 가능하도록 경로 추가
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from steps.step2_retrieval_and_rfp_parse.parser import parse_rfp_text
from steps.step2_retrieval_and_rfp_parse.retrieval_smoke import load_chunks, score


_REQUIRED_FIELDS = [
    "project_name",
    "organization",
    "budget_range",
    "purpose_background",
    "evaluation_criteria",
    "core_requirements",
    "authoring_guidelines",
    "schedule_constraints",
    "must_have_constraints",
]


def analyze_rfp(rfp_text: str) -> dict[str, Any]:
    """텍스트를 구조화된 요구사항 dict로 변환하고 누락 필드를 반환한다."""
    requirements = parse_rfp_text(rfp_text)
    missing: list[str] = []
    for field in _REQUIRED_FIELDS:
        value = requirements.get(field)
        if value is None or value == [] or value == "":
            missing.append(field)
    return {"rfp_requirements": requirements, "missing_fields": missing}


def search_proposals(
    query: str,
    top_k: int = 5,
    chunks_root: Path | None = None,
) -> list[dict[str, Any]]:
    """키워드 기반 제안서 청크 검색. chunks_root 미지정 시 local_data 기본값 사용."""
    if chunks_root is None:
        chunks_root = _REPO_ROOT / "local_data" / "step1" / "chunks"

    if not chunks_root.is_dir():
        return []

    rows = load_chunks(chunks_root)
    if not rows:
        return []

    ranked = sorted(
        ((score(query, text), path, text) for path, text in rows),
        reverse=True,
    )

    results: list[dict[str, Any]] = []
    for s, path, text in ranked[:top_k]:
        preview = " ".join(text.split())[:200]
        results.append(
            {
                "document_name": path.parent.name,
                "chunk_id": path.stem,
                "preview": preview,
                "score": s,
            }
        )
    return results
