"""RFP 텍스트를 구조화 JSON으로 변환하는 파서."""
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


SCALAR_PATTERNS = {
    "project_name": [
        # 라벨 명시형: "프로젝트명: XXX"
        r"(?:프로젝트명|사업명|과업명)\s*[:：]\s*(.+)",
        r"(?:사업\s*개요|과업\s*개요)\s*[:：]\s*(.+)",
        # RFP 표준 헤더 형식: 발주처/발주기관 바로 위 독립 제목 줄
        r"^([^\n:]{5,80})\n+(?:발주처|발주기관|수요기관)\s*[:：]",
        # 구분선(═, ─, =) 직후 제목 줄
        r"[═=─\-]{5,}\n+([^\n:]{5,80})\n+(?:발주처|발주기관|수요기관)\s*[:：]",
    ],
    "organization": [
        r"(?:발주기관|수요기관|발주처|의뢰기관)\s*[:：]\s*(.+)",
        r"(?:기관명|고객사)\s*[:：]\s*(.+)",
    ],
    "budget_range": [
        # 라벨 명시형: "예산: XXX"
        r"(?:예산|사업비|총\s*사업비)\s*[:：]\s*(.+)",
        r"(?:금액|계약금액)\s*[:：]\s*(.+)",
        # 본문 서술형: "총 예산은 VAT 별도 2억 5천만 원 이내로 한다"
        r"총\s*예산은[^.。\n]{0,20}?((?:\d+억\s*)?(?:\d+천만\s*)?(?:\d+만\s*)?원[^\n.。]*)",
        r"예산[은는]\s*(?:VAT\s*별도\s*)?((?:\d+억\s*)?(?:\d+천만\s*)?(?:\d+만\s*)?원[^\n.。]*)",
    ],
    "purpose_background": [
        # 라벨 명시형
        r"(?:사업\s*목적|과업\s*목적)\s*[:：]\s*(.+)",
        r"(?:추진\s*배경|도입\s*배경)\s*[:：]\s*(.+)",
        # 본문 서술형: "이에 ... 구축하고자 한다" 문장
        r"(이에\s+[가-힣A-Za-z\s,·]+(?:구축|개선|강화|확보|마련)하[고자려]{1,3}\s+한다\.?)",
    ],
}


SECTION_HINTS = {
    "evaluation_criteria": ["평가 기준", "평가항목", "배점", "심사 기준"],
    "core_requirements": ["핵심 요구사항", "요구사항", "기능 요구", "기술 요구", "인력 요구"],
    "authoring_guidelines": ["작성 지침", "제안서 작성", "목차", "분량", "페이지 제한"],
    "schedule_constraints": ["일정", "납기", "수행 기간", "마감"],
    "must_have_constraints": ["필수", "제약", "금지", "제외", "의무"],
}


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _clean_value(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" \t-:;,.")
    return value or None


def _extract_first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean_value(match.group(1))
    return None


def _dedup_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _normalize_list_item(line: str) -> str | None:
    line = re.sub(r"^\s*(?:[-*•·]|[0-9]+[.)])\s*", "", line)
    line = _clean_value(line)
    if not line or len(line) < 2:
        return None
    return line


def _collect_section_lines(lines: list[str], section_hints: list[str]) -> list[str]:
    out: list[str] = []
    in_section = False
    heading_pattern = re.compile(r"^(?:[0-9]+[.)]?\s*)?.{0,30}$")

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        is_heading_like = bool(heading_pattern.match(line))
        if any(hint in line for hint in section_hints) and is_heading_like:
            in_section = True
            continue
        if in_section and is_heading_like and not any(hint in line for hint in section_hints):
            in_section = False
        if in_section:
            item = _normalize_list_item(line)
            if item:
                out.append(item)
    return out


def _collect_lines_by_keywords(lines: list[str], words: list[str]) -> list[str]:
    out: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if any(word in line for word in words):
            item = _normalize_list_item(line) or line
            cleaned = _clean_value(item)
            if cleaned:
                out.append(cleaned)
    return out


def _build_list_field(lines: list[str], key: str) -> list[str]:
    from_section = _collect_section_lines(lines, SECTION_HINTS[key])
    by_keyword = _collect_lines_by_keywords(lines, KEYWORDS[key])
    merged = _dedup_keep_order(from_section + by_keyword)
    return merged[:25]


def parse_rfp_text(text: str) -> dict[str, Any]:
    text = _normalize_whitespace(text)
    lines = text.splitlines()

    parsed: dict[str, Any] = {
        "project_name": _extract_first(SCALAR_PATTERNS["project_name"], text),
        "organization": _extract_first(SCALAR_PATTERNS["organization"], text),
        "budget_range": _extract_first(SCALAR_PATTERNS["budget_range"], text),
        "purpose_background": _extract_first(SCALAR_PATTERNS["purpose_background"], text),
        "evaluation_criteria": _build_list_field(lines, "evaluation_criteria"),
        "core_requirements": _build_list_field(lines, "core_requirements"),
        "authoring_guidelines": _build_list_field(lines, "authoring_guidelines"),
        "schedule_constraints": _build_list_field(lines, "schedule_constraints"),
        "must_have_constraints": _build_list_field(lines, "must_have_constraints"),
    }
    return parsed


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse local RFP text into structured JSON")
    parser.add_argument("--input", required=True, help="Path to local RFP .txt file")
    parser.add_argument("--output", required=True, help="Path to output .json file")
    parser.add_argument(
        "--print-missing",
        action="store_true",
        help="Print missing scalar/empty list fields summary",
    )
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
    if args.print_missing:
        missing = [k for k, v in parsed.items() if v is None or (isinstance(v, list) and not v)]
        print(f"Missing fields: {', '.join(missing) if missing else '(none)'}")


if __name__ == "__main__":
    main()
