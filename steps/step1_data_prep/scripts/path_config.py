from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    here = Path(__file__).resolve()
    for anc in [here, *here.parents]:
        if (anc / ".gitignore").is_file() and (anc / "steps").is_dir():
            return anc
    raise RuntimeError("Project root not found from current script path.")


def local_data_root() -> Path:
    env = os.getenv("LOCAL_DATA_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return project_root() / "local_data"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def step1_dir(*parts: str) -> Path:
    base = local_data_root() / "step1"
    return base.joinpath(*parts)
