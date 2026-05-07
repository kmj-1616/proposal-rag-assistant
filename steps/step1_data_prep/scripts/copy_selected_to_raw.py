"""Copy selected proposal files from local source into step1 raw directory."""
from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path

from path_config import ensure_dir, local_data_root, step1_dir


def source_dir() -> Path:
    env = os.getenv("LOCAL_PROPOSAL_SOURCE_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return local_data_root() / "proposal_collection"


def metadata_csv() -> Path:
    env = os.getenv("STEP1_METADATA_CSV", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return step1_dir("proposal_candidates.csv")


def selected_names(csv_path: Path) -> list[str]:
    picked: list[str] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            flag = (row.get("선정_Y_N") or "").strip().upper()
            if flag not in ("Y", "YES", "O", "ㅇ"):
                continue
            name = (row.get("파일명") or "").strip()
            if name:
                picked.append(name)
    return picked


def main() -> None:
    src_root = source_dir()
    csv_path = metadata_csv()
    out_dir = ensure_dir(step1_dir("raw_proposals"))

    if not src_root.is_dir():
        raise SystemExit(f"Missing source directory: {src_root}")
    if not csv_path.is_file():
        raise SystemExit(f"Missing metadata csv: {csv_path}")

    names = selected_names(csv_path)
    if not names:
        raise SystemExit("No selected rows in metadata csv.")

    copied = 0
    for name in names:
        src = src_root / name
        if not src.is_file():
            raise SystemExit(f"Missing source file: {src}")
        shutil.copy2(src, out_dir / name)
        copied += 1

    print(f"Copied {copied} files to {out_dir}")


if __name__ == "__main__":
    main()
