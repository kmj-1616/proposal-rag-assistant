"""step3 초안 생성 서비스: RFP 요구사항 + 검색 컨텍스트 기반 섹션별 제안서 초안 생성."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.services.claude_cli_adapter import ADAPTER_ID, call_claude

# RFP authoring_guidelines에 목차 항목이 없을 때 사용하는 기본 섹션 목록
_DEFAULT_SECTIONS: list[str] = [
    "사업 이해도 및 수행 전략",
    "기술 요구사항 대응방안",
    "수행 조직 및 인력 계획",
    "일정 관리 계획",
    "품질 관리 계획",
    "기대 효과 및 결론",
]

# authoring_guidelines에서 목차 항목으로 판단하는 패턴
_TOC_PATTERNS = [
    re.compile(r"^[0-9]+[.)\s]\s*(.{3,50})$"),
    re.compile(r"^(?:[가나다라마바사아자차카타파하]\.)\s*(.{3,50})$"),
    re.compile(r"^(?:제\s*[0-9]+\s*장|제\s*[0-9]+\s*절)\s+(.{3,50})$"),
]

_SCORE_RE = re.compile(r"(\d+)\s*(?:점|%)")


def _extract_toc(guidelines: list[str]) -> list[str]:
    """authoring_guidelines에서 목차 표기 패턴을 감지해 섹션 제목 목록을 반환한다."""
    found: list[str] = []
    for line in guidelines:
        stripped = line.strip()
        for pat in _TOC_PATTERNS:
            m = pat.match(stripped)
            if m:
                title = m.group(1).strip(" \t-:;,.")
                if title:
                    found.append(title)
                break
    return found


def _parse_score(criterion: str) -> float:
    m = _SCORE_RE.search(criterion)
    return float(m.group(1)) if m else 0.0


def _score_map(sections: list[str], criteria: list[str]) -> dict[str, float]:
    """평가 기준 배점을 섹션 제목과 키워드 매칭으로 연결한다."""
    scores: dict[str, float] = {s: 0.0 for s in sections}
    for criterion in criteria:
        score = _parse_score(criterion)
        if score <= 0:
            continue
        lower = criterion.lower()
        for section in sections:
            keywords = [kw for kw in re.split(r"[\s/·,]", section) if len(kw) >= 2]
            if any(kw in lower for kw in keywords):
                scores[section] = max(scores[section], score)
    return scores


def _plan_sections(rfp: dict[str, Any]) -> tuple[list[str], str]:
    """RFP에서 섹션 목록과 목차 출처('rfp_guidelines' | 'default')를 반환한다."""
    guidelines: list[str] = rfp.get("authoring_guidelines") or []
    toc = _extract_toc(guidelines)
    if toc:
        source = "rfp_guidelines"
        sections = toc
    else:
        source = "default"
        sections = list(_DEFAULT_SECTIONS)

    criteria: list[str] = rfp.get("evaluation_criteria") or []
    score_table = _score_map(sections, criteria)
    sections.sort(key=lambda s: score_table.get(s, 0.0), reverse=True)
    return sections, source


def _build_prompt(
    section_title: str,
    priority: int,
    rfp: dict[str, Any],
    context_chunks: list[str],
) -> str:
    """섹션 생성 프롬프트를 조립한다."""
    project = rfp.get("project_name") or "해당 사업"
    organization = rfp.get("organization") or ""
    purpose = rfp.get("purpose_background") or ""
    core_reqs = rfp.get("core_requirements") or []
    eval_criteria = rfp.get("evaluation_criteria") or []
    must_have = rfp.get("must_have_constraints") or []

    lines: list[str] = [
        f"아래 RFP 정보를 바탕으로 제안서의 **{section_title}** 섹션을 작성하세요.",
        f"(우선순위 {priority}위 섹션 / 500~1500자 / 격식체 한국어)",
        "",
        "## RFP 정보",
        f"- 사업명: {project}",
    ]
    if organization:
        lines.append(f"- 발주처: {organization}")
    if purpose:
        lines.append(f"- 사업 목적: {purpose}")
    if core_reqs:
        lines.append("- 핵심 요구사항:")
        for req in core_reqs[:12]:
            lines.append(f"  * {req}")
    if eval_criteria:
        lines.append("- 평가 기준:")
        for crit in eval_criteria[:8]:
            lines.append(f"  * {crit}")
    if must_have:
        lines.append("- 필수 제약:")
        for item in must_have[:5]:
            lines.append(f"  * {item}")

    if context_chunks:
        lines += ["", "## 유사 제안서 참고 (문체·구성 참고용)"]
        for i, chunk in enumerate(context_chunks, 1):
            body = re.sub(r"^#[^\n]*\n", "", chunk, flags=re.MULTILINE).strip()
            lines.append(f"\n[참고 {i}]\n{body[:500]}")

    return "\n".join(lines)


def generate_draft(
    rfp: dict[str, Any],
    context_top_k: int = 3,
) -> dict[str, Any]:
    """RFP 요구사항을 받아 섹션별 제안서 초안을 생성한다.

    Args:
        rfp: parse_rfp_text() 또는 /rfp/analyze 반환 구조와 동일한 dict.
        context_top_k: 섹션별로 주입할 검색 컨텍스트 청크 수.

    Returns:
        {
            "project_name": str | None,
            "sections": [{"title", "priority", "content", "context_chunks_used"}],
            "total_sections": int,
            "generation_meta": {"generated_at", "adapter", "context_top_k", "toc_source"},
        }
    """
    from app.services.step2_service import search_proposals

    sections, toc_source = _plan_sections(rfp)

    generated_sections: list[dict[str, Any]] = []
    for priority, title in enumerate(sections, 1):
        query = f"{title} {rfp.get('project_name') or ''}".strip()
        try:
            raw_chunks = search_proposals(query=query, top_k=context_top_k)
            context_texts = [r["preview"] for r in raw_chunks]
        except RuntimeError:
            # 인덱스 미구축 상태이면 컨텍스트 없이 생성 진행
            context_texts = []

        prompt = _build_prompt(
            section_title=title,
            priority=priority,
            rfp=rfp,
            context_chunks=context_texts,
        )
        content = call_claude(prompt)

        generated_sections.append(
            {
                "title": title,
                "priority": priority,
                "content": content,
                "context_chunks_used": len(context_texts),
            }
        )

    return {
        "project_name": rfp.get("project_name"),
        "sections": generated_sections,
        "total_sections": len(generated_sections),
        "generation_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "adapter": ADAPTER_ID,
            "context_top_k": context_top_k,
            "toc_source": toc_source,
        },
    }
