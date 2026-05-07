"""검색 엔진 추상화 인터페이스 및 팩토리."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RetrievalResult:
    """단일 검색 결과."""

    def __init__(
        self,
        document_name: str,
        chunk_id: str,
        preview: str,
        score: float,
    ) -> None:
        self.document_name = document_name
        self.chunk_id = chunk_id
        self.preview = preview
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_name": self.document_name,
            "chunk_id": self.chunk_id,
            "preview": self.preview,
            "score": self.score,
        }


class BaseRetriever(ABC):
    """검색 엔진 공통 인터페이스."""

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """질의에 대해 상위 top_k 결과를 반환한다."""

    @property
    @abstractmethod
    def index_ready(self) -> bool:
        """인덱스가 검색 가능한 상태인지 반환한다."""
