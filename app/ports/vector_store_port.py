"""
Vector Store Port - Abstract interface for vector database operations.
Includes normalized dataclasses so services never depend on provider-specific response shapes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VectorSearchResult:
    """A single result from a vector similarity query."""
    id: str
    metadata: Dict[str, Any]
    distance: float
    document: str = ""


@dataclass
class VectorDocument:
    """A document stored in the vector database."""
    id: str
    metadata: Dict[str, Any]
    document: str = ""


class VectorStorePort(ABC):
    """
    Port for vector database operations.

    Implementations:
    - TypesenseVectorStoreAdapter (config/typesenseDb.py)
    """

    @abstractmethod
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 50,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """
        Similarity search by embedding vector.

        Args:
            query_embedding: The query vector.
            n_results: Maximum number of results to return.
            where: Optional metadata filter dict (e.g. {"tag": "ED"}).

        Returns:
            List of VectorSearchResult, ordered by ascending distance.
        """
        ...

    @abstractmethod
    def get_all(self, include_documents: bool = False) -> List[VectorDocument]:
        """
        Retrieve all documents from the collection.

        Args:
            include_documents: Whether to include the stored document text.

        Returns:
            List of VectorDocument.
        """
        ...

    @abstractmethod
    def get_by_id(
        self,
        doc_id: str,
        include_documents: bool = True,
    ) -> Optional[VectorDocument]:
        """
        Retrieve a single document by ID.

        Args:
            doc_id: Document ID.
            include_documents: Whether to include the stored document text.

        Returns:
            VectorDocument or None if not found.
        """
        ...

    @abstractmethod
    def upsert(
        self,
        doc_id: str,
        embedding: List[float],
        document: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Insert or update a document.

        Args:
            doc_id: Document ID.
            embedding: Vector embedding.
            document: Document text (for retrieval/display).
            metadata: Metadata dict (tag, judul, jawaban_tampil, etc).
        """
        ...

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID.

        Returns:
            True if successfully deleted.
        """
        ...

    @abstractmethod
    def get_all_ids(self) -> List[str]:
        """
        Get all document IDs (lightweight, no metadata).
        Used for ID generation.

        Returns:
            List of document ID strings.
        """
        ...
