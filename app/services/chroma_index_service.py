"""ChromaDB + sentence-transformers 기반 검색 서비스."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from app.services.retrieval_engine import BaseRetriever, RetrievalResult

# 프로젝트 루트를 sys.path에 추가
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_INDEX_DIR = _REPO_ROOT / "local_data" / "step2" / "chroma_index"
_COLLECTION_NAME = "proposal_chunks"

# 임베딩 모델명. 환경변수로 오버라이드 가능.
_EMBED_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2",
)


def _get_chroma_client(persist_dir: Path):  # type: ignore[return]
    import chromadb

    return chromadb.PersistentClient(path=str(persist_dir))


def _get_embedding_function():  # type: ignore[return]
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    return SentenceTransformerEmbeddingFunction(model_name=_EMBED_MODEL)


def build_index(
    chunks_root: Path | None = None,
    index_dir: Path | None = None,
    reset: bool = True,
) -> dict[str, Any]:
    """Step1 청크 파일을 읽어 Chroma 인덱스를 생성/갱신한다.

    Returns:
        {"indexed_count": int, "index_path": str, "model": str}
    """
    if chunks_root is None:
        chunks_root = _REPO_ROOT / "local_data" / "step1" / "chunks"
    if index_dir is None:
        index_dir = Path(os.environ.get("CHROMA_INDEX_DIR", str(_DEFAULT_INDEX_DIR)))

    if not chunks_root.is_dir():
        raise FileNotFoundError(
            f"청크 디렉터리를 찾을 수 없습니다: {chunks_root}\n"
            "step1 스크립트를 먼저 실행해 청크를 생성하세요."
        )

    index_dir.mkdir(parents=True, exist_ok=True)
    client = _get_chroma_client(index_dir)
    ef = _get_embedding_function()

    if reset:
        try:
            client.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=ef,  # type: ignore[arg-type]
        metadata={"hnsw:space": "cosine"},
    )

    chunk_paths = sorted(chunks_root.glob("**/chunk_*.txt"))
    if not chunk_paths:
        return {"indexed_count": 0, "index_path": str(index_dir), "model": _EMBED_MODEL}

    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    ids: list[str] = []

    for path in chunk_paths:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        doc_name = path.parent.name
        chunk_id = path.stem
        uid = f"{doc_name}__{chunk_id}"
        documents.append(text)
        metadatas.append({"document_name": doc_name, "chunk_id": chunk_id})
        ids.append(uid)

    # Chroma는 한 번에 최대 ~5000건 처리 권장 → 배치 분할
    BATCH = 500
    for i in range(0, len(documents), BATCH):
        collection.add(
            documents=documents[i : i + BATCH],
            metadatas=metadatas[i : i + BATCH],
            ids=ids[i : i + BATCH],
        )

    return {
        "indexed_count": len(documents),
        "index_path": str(index_dir),
        "model": _EMBED_MODEL,
    }


class ChromaRetriever(BaseRetriever):
    """영속 Chroma 컬렉션 기반 임베딩 검색기."""

    def __init__(self, index_dir: Path | None = None) -> None:
        self._index_dir = index_dir or Path(
            os.environ.get("CHROMA_INDEX_DIR", str(_DEFAULT_INDEX_DIR))
        )
        self._client = None
        self._collection = None
        self._ef = None

    def _ensure_loaded(self) -> None:
        if self._collection is not None:
            return
        if not self._index_dir.exists():
            return
        try:
            self._ef = _get_embedding_function()
            self._client = _get_chroma_client(self._index_dir)
            self._collection = self._client.get_collection(
                name=_COLLECTION_NAME,
                embedding_function=self._ef,  # type: ignore[arg-type]
            )
        except Exception:
            self._collection = None

    @property
    def index_ready(self) -> bool:
        self._ensure_loaded()
        try:
            return self._collection is not None and self._collection.count() > 0
        except Exception:
            return False

    def reload(self) -> None:
        """인덱스 재생성 후 컬렉션을 다시 로드한다."""
        self._collection = None
        self._client = None
        self._ensure_loaded()

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        self._ensure_loaded()
        if not self.index_ready:
            raise RuntimeError(
                "인덱스가 준비되지 않았습니다. "
                "POST /api/v1/proposals/index/rebuild 를 먼저 호출하세요."
            )
        results = self._collection.query(  # type: ignore[union-attr]
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),  # type: ignore[union-attr]
            include=["documents", "metadatas", "distances"],
        )

        out: list[RetrievalResult] = []
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for text, meta, dist in zip(docs, metas, dists):
            # 코사인 거리(0~2) → 유사도 점수(0.0~1.0) 변환
            score = round(max(0.0, 1.0 - dist / 2.0), 4)
            preview = " ".join(text.split())[:200]
            out.append(
                RetrievalResult(
                    document_name=meta.get("document_name", ""),
                    chunk_id=meta.get("chunk_id", ""),
                    preview=preview,
                    score=score,
                )
            )
        return out


# 앱 전체에서 공유하는 싱글턴 검색기
_retriever: ChromaRetriever | None = None


def get_retriever() -> ChromaRetriever:
    global _retriever
    if _retriever is None:
        _retriever = ChromaRetriever()
    return _retriever
