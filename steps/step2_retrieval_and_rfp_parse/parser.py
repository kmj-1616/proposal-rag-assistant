"""RFP parser skeleton: converts plain text to structured requirements JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


KEYWORDS = {
    "evaluation_criteria": ["평가", "배점", "심사", "평가기준"],
    "core_requirements": ["요구사항", "기능", "기술", "인력", "범위"],
    "authoring_guidelines": ["작성", "분량", "페이지", "목차", "제출형식"],
    "schedule_constraints": ["일정", "납기", "기간", "마감"],
    "must_have_constraints": ["필수", "제약", "제외", "금지", "조건"]
}


def _extract_first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return (match.group(1) or "").strip() or None
    return None


def _collect_lines_by_keywords(text: str, words: list[str]) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(word in s for word in words):
            out.append(s)
    return out[:20]


def parse_rfp_text(text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {
        "project_name": _extract_first(
            [r"프로젝트명[:\s]+(.+)", r"사업명[:\s]+(.+)"],
            text,
        ),
        "organization": _extract_first(
            [r"발주기관[:\s]+(.+)", r"수요기관[:\s]+(.+)"],
            text,
        ),
        "budget_range": _extract_first(
            [r"예산[:\s]+(.+)", r"사업비[:\s]+(.+)"],
            text,
        ),
        "purpose_background": _extract_first(
            [r"사업\s*목적[:\s]+(.+)", r"추진\s*배경[:\s]+(.+)"],
            text,
        ),
        "evaluation_criteria": _collect_lines_by_keywords(text, KEYWORDS["evaluation_criteria"]),
        "core_requirements": _collect_lines_by_keywords(text, KEYWORDS["core_requirements"]),
        "authoring_guidelines": _collect_lines_by_keywords(text, KEYWORDS["authoring_guidelines"]),
        "schedule_constraints": _collect_lines_by_keywords(text, KEYWORDS["schedule_constraints"]),
        "must_have_constraints": _collect_lines_by_keywords(text, KEYWORDS["must_have_constraints"]),
    }
    return parsed


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse local RFP text into structured JSON")
    parser.add_argument("--input", required=True, help="Path to local RFP .txt file")
    parser.add_argument("--output", required=True, help="Path to output .json file")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    text = input_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_rfp_text(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote parsed requirements to {output_path}")


if __name__ == "__main__":
    main()
