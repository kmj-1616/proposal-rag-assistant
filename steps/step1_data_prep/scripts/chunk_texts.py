"""Split extracted texts into retrieval-friendly chunks."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from path_config import ensure_dir, step1_dir


@dataclass
class DocSummary:
    source_txt: str
    units: int
    chunks: int
    out_dir: str


DELIM = re.compile(r"^--- (?:Slide (\d+)|PDF Page (\d+)) ---$", re.MULTILINE)
NOISE = re.compile(
    r"^Proprietar.*?\n|Copyright.*?reserved\.?\s*\n|^[\s\d]*Proprietar.*?$",
    re.MULTILINE | re.IGNORECASE,
)


def _safe_name(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r'[<>:"/\\|?*]', "_", stem)
    return stem or "unnamed"


def _parse_units(text: str) -> list[tuple[int, str]]:
    parts = DELIM.split(text)
    if not parts or (parts[0].strip() and not DELIM.search(text)):
        body = NOISE.sub("", text).strip()
        return [(1, body)] if body else []

    units: list[tuple[int, str]] = []
    lead = parts[0].strip()
    i = 1
    while i + 2 < len(parts):
        num = int(parts[i] or parts[i + 1])
        body = NOISE.sub("", parts[i + 2]).strip()
        if body:
            units.append((num, body))
        i += 3
    if lead:
        prefix = NOISE.sub("", lead).strip()
        if prefix:
            units.insert(0, (0, prefix))
    return units


def _merge_units(
    units: list[tuple[int, str]],
    *,
    target_max: int = 3200,
    target_min: int = 500,
    max_units: int = 5,
) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    nums: list[int] = []
    parts: list[str] = []

    def flush() -> None:
        nonlocal nums, parts
        if not parts:
            return
        chunks.append((min(nums), max(nums), "\n\n".join(parts).strip()))
        nums, parts = [], []

    for n, body in units:
        if not parts:
            nums, parts = [n], [body]
            continue
        merged = "\n\n".join(parts + [body])
        if len(merged) > target_max or len(parts) >= max_units:
            flush()
            nums, parts = [n], [body]
        else:
            nums.append(n)
            parts.append(body)
        if len("\n\n".join(parts)) >= target_min and len(parts) >= 2:
            flush()

    flush()
    if not chunks and units:
        chunks.append((units[0][0], units[-1][0], "\n\n".join(b for _, b in units).strip()))
    return chunks


def main() -> int:
    src_dir = step1_dir("extracted_texts")
    out_root = ensure_dir(step1_dir("chunks"))

    if not src_dir.is_dir():
        print(f"Missing extracted text directory: {src_dir}", file=sys.stderr)
        return 1

    txt_files = sorted(p for p in src_dir.glob("*.txt") if p.is_file() and not p.name.startswith("_"))
    if not txt_files:
        print(f"No extracted text files found: {src_dir}", file=sys.stderr)
        return 1

    summaries: list[DocSummary] = []
    for path in txt_files:
        units = _parse_units(path.read_text(encoding="utf-8", errors="replace"))
        if not units:
            continue
        merged = _merge_units(units)
        folder = ensure_dir(out_root / _safe_name(path.name))
        for idx, (lo, hi, body) in enumerate(merged, 1):
            name = f"chunk_{idx:04d}_u{lo:04d}-{hi:04d}.txt"
            header = (
                f"# source_file: {path.name}\n"
                f"# unit_range: {lo}-{hi}\n"
                f"# chunk_index: {idx}\n\n"
            )
            (folder / name).write_text(header + body + "\n", encoding="utf-8", newline="\n")
        summaries.append(
            DocSummary(source_txt=path.name, units=len(units), chunks=len(merged), out_dir=str(folder))
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(src_dir),
        "output_root": str(out_root),
        "documents": [asdict(s) for s in summaries],
    }
    (out_root / "_chunking_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    total_chunks = sum(s.chunks for s in summaries)
    print(f"Chunking done: {len(summaries)} docs, {total_chunks} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
