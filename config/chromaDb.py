"""
ChromaDB Vector Store - ChromaDB implementation of VectorStorePort.
Following Siloam convention: config/chromaDb.py (DB connection adapters live in config/).
Includes retry_on_lock logic (SQLite/ChromaDB-specific concern).
"""

import functools
import time
import random
from typing import List, Optional, Dict, Any

from app.ports.vector_store_port import VectorStorePort, VectorSearchResult, VectorDocument


def _retry_on_lock(max_retries: int = 10, base_delay: float = 0.1):
    """
    Decorator untuk menangani error 'Database Locked' pada SQLite.
    Menggunakan Jitter Backoff untuk menghindari thundering herd.

    This is a ChromaDB/SQLite-specific concern and belongs in this adapter,
    not in the service layer.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    err_msg = str(e).lower()
                    if "locked" in err_msg or "busy" in err_msg:
                        retries += 1
                        sleep_time = base_delay * (1 + random.random())
                        time.sleep(sleep_time)
                    else:
                        raise
            raise Exception("Database sedang sibuk (High Traffic), silakan coba lagi sesaat.")
        return wrapper
    return decorator


class ChromaDBVectorStoreAdapter(VectorStorePort):
    """
    Vector store adapter for ChromaDB.
    Supports both server mode (HttpClient) and local mode (PersistentClient).

    Args:
        collection_name: Name of the ChromaDB collection.
        host: ChromaDB server host (for server mode).
        port: ChromaDB server port (for server mode).
        persist_path: Local persistence path (for local mode).
    """

    def __init__(
        self,
        collection_name: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        persist_path: Optional[str] = None,
    ):
        # Force pysqlite3 swap (for Docker/Linux)
        try:
            __import__("pysqlite3")
            import sys
            sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
        except ImportError:
            pass

        import chromadb

        if host and port:
            self._client = chromadb.HttpClient(host=host, port=port)
        else:
            self._client = chromadb.PersistentClient(
                path=persist_path or "./data/chroma_data"
            )

        self._collection = self._client.get_or_create_collection(name=collection_name)

    @_retry_on_lock()
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 50,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Similarity search. Translates ChromaDB response to normalized VectorSearchResult list."""
        raw = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

        results = []
        if raw["ids"] and raw["ids"][0]:
            for i in range(len(raw["ids"][0])):
                results.append(
                    VectorSearchResult(
                        id=raw["ids"][0][i],
                        metadata=raw["metadatas"][0][i] if raw.get("metadatas") else {},
                        distance=raw["distances"][0][i] if raw.get("distances") else 0.0,
                        document=(
                            raw["documents"][0][i]
                            if raw.get("documents") and raw["documents"][0]
                            else ""
                        ),
                    )
                )
        return results

    @_retry_on_lock()
    def get_all(self, include_documents: bool = False) -> List[VectorDocument]:
        """Retrieve all documents from the collection."""
        includes = ["metadatas"]
        if include_documents:
            includes.append("documents")

        data = self._collection.get(include=includes)

        docs = []
        if data["ids"]:
            for i, doc_id in enumerate(data["ids"]):
                docs.append(
                    VectorDocument(
                        id=doc_id,
                        metadata=data["metadatas"][i] if data.get("metadatas") else {},
                        document=(
                            data["documents"][i]
                            if include_documents and data.get("documents")
                            else ""
                        ),
                    )
                )
        return docs

    @_retry_on_lock()
    def get_by_id(
        self,
        doc_id: str,
        include_documents: bool = True,
    ) -> Optional[VectorDocument]:
        """Retrieve a single document by ID."""
        includes = ["metadatas"]
        if include_documents:
            includes.append("documents")

        try:
            data = self._collection.get(ids=[str(doc_id)], include=includes)
            if data["ids"] and len(data["ids"]) > 0:
                return VectorDocument(
                    id=data["ids"][0],
                    metadata=data["metadatas"][0] if data.get("metadatas") else {},
                    document=(
                        data["documents"][0]
                        if include_documents and data.get("documents")
                        else ""
                    ),
                )
        except Exception:
            pass
        return None

    @_retry_on_lock()
    def upsert(
        self,
        doc_id: str,
        embedding: List[float],
        document: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Insert or update a document."""
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

    @_retry_on_lock()
    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            self._collection.delete(ids=[str(doc_id)])
            return True
        except Exception:
            return False

    @_retry_on_lock()
    def get_all_ids(self) -> List[str]:
        """Get all document IDs (lightweight, no metadata)."""
        data = self._collection.get(include=[])
        return data["ids"] if data["ids"] else []
