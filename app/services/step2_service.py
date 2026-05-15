"""step2 비즈니스 로직: RFP 파싱 및 제안서 검색."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 프로젝트 루트를 sys.path에 추가
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from steps.step2_retrieval_and_rfp_parse.parser import parse_rfp_text


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
) -> list[dict[str, Any]]:
    """임베딩 기반 제안서 청크 검색."""
    from app.services.chroma_index_service import get_retriever

    retriever = get_retriever()
    results = retriever.search(query=query, top_k=top_k)
    return [r.to_dict() for r in results]


def rebuild_index(
    chunks_root_str: str | None = None,
    reset: bool = True,
) -> dict[str, Any]:
    """Step1 청크로 Chroma 인덱스를 재생성한다."""
    from app.services.chroma_index_service import build_index, get_retriever

    chunks_root = Path(chunks_root_str).expanduser().resolve() if chunks_root_str else None
    result = build_index(chunks_root=chunks_root, reset=reset)

    # 싱글턴 검색기 인덱스 갱신
    get_retriever().reload()

    return result
