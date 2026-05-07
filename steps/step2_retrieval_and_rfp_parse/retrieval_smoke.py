"""Simple local retrieval smoke test over step1 chunk files."""
from __future__ import annotations

from pathlib import Path


def load_chunks(chunks_root: Path) -> list[tuple[Path, str]]:
    rows: list[tuple[Path, str]] = []
    for path in sorted(chunks_root.glob("**/chunk_*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.append((path, text))
    return rows


def score(query: str, text: str) -> int:
    q_tokens = [t for t in query.lower().split() if t]
    lower = text.lower()
    return sum(lower.count(tok) for tok in q_tokens)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Keyword retrieval smoke test")
    parser.add_argument("--chunks", required=True, help="Path to local chunk root directory")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    root = Path(args.chunks).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Chunk root not found: {root}")

    rows = load_chunks(root)
    if not rows:
        raise SystemExit(f"No chunks found under: {root}")

    ranked = sorted(((score(args.query, text), path, text) for path, text in rows), reverse=True)
    print(f"Query: {args.query}")
    for rank, (s, path, text) in enumerate(ranked[: args.topk], 1):
        preview = " ".join(text.split())[:120]
        print(f"{rank:02d}. score={s:03d} path={path.name} preview={preview}")


if __name__ == "__main__":
    main()
