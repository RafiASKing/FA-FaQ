"""
Typesense Vector Store - Typesense implementation of VectorStorePort.
Following Siloam convention: config/typesenseDb.py (DB connection adapters live in config/).
No retry_on_lock needed — Typesense handles concurrency properly.
"""

from typing import List, Optional, Dict, Any
import typesense
from typesense.exceptions import ObjectNotFound

from app.ports.vector_store_port import VectorStorePort, VectorSearchResult, VectorDocument
from config.constants import EMBEDDING_DIMENSION


class TypesenseVectorStoreAdapter(VectorStorePort):
    """
    Vector store adapter for Typesense.
    
    Args:
        host: Typesense server host.
        port: Typesense server port.
        api_key: Typesense API key.
        collection_name: Name of the collection.
        embedding_dim: Dimension of embedding vectors (default: 768 for Gemini).
    """

    # Schema for FAQ collection
    COLLECTION_SCHEMA = {
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "tag", "type": "string", "facet": True},
            {"name": "judul", "type": "string"},
            {"name": "jawaban_tampil", "type": "string"},
            {"name": "keywords_raw", "type": "string"},
            {"name": "path_gambar", "type": "string"},
            {"name": "sumber_url", "type": "string"},
            {"name": "document", "type": "string"},
            {"name": "embedding", "type": "float[]", "num_dim": EMBEDDING_DIMENSION},
        ]
    }

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        collection_name: str,
        embedding_dim: int = EMBEDDING_DIMENSION,
    ):
        self._client = typesense.Client({
            "nodes": [{
                "host": host,
                "port": str(port),
                "protocol": "http"
            }],
            "api_key": api_key,
            "connection_timeout_seconds": 5
        })
        
        self._collection_name = collection_name
        self._embedding_dim = embedding_dim
        
        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self._client.collections[self._collection_name].retrieve()
        except ObjectNotFound:
            schema = {
                "name": self._collection_name,
                **self.COLLECTION_SCHEMA
            }
            # Update embedding dimension
            for field in schema["fields"]:
                if field["name"] == "embedding":
                    field["num_dim"] = self._embedding_dim
            
            self._client.collections.create(schema)

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 50,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Similarity search by embedding vector using multi_search (POST body)."""
        
        # Build filter string (Typesense uses string-based filtering)
        filter_by = ""
        if where:
            filters = []
            for key, value in where.items():
                # Handle equality filter
                filters.append(f"{key}:={value}")
            filter_by = " && ".join(filters)
        
        # Use multi_search API to avoid URL length limit with large embeddings
        search_request = {
            "searches": [{
                "collection": self._collection_name,
                "q": "*",
                "vector_query": f"embedding:([], k:{n_results})",
                "exclude_fields": "embedding",
            }]
        }
        
        if filter_by:
            search_request["searches"][0]["filter_by"] = filter_by
        
        try:
            # Use multi_search with vector in request body
            response = self._client.multi_search.perform(
                search_request,
                {"vector_query": f"embedding:([{','.join(map(str, query_embedding))}], k:{n_results})"}
            )
            
            # multi_search returns {"results": [...]}
            search_result = response.get("results", [{}])[0]
            
        except Exception as e:
            print(f"Typesense search error: {e}")
            return []
        
        results = []
        for hit in search_result.get("hits", []):
            doc = hit.get("document", {})
            # Typesense returns vector_distance (lower is better)
            # Convert to distance format similar to ChromaDB
            distance = hit.get("vector_distance", 1.0)
            
            results.append(VectorSearchResult(
                id=doc.get("id", ""),
                metadata={
                    "tag": doc.get("tag", ""),
                    "judul": doc.get("judul", ""),
                    "jawaban_tampil": doc.get("jawaban_tampil", ""),
                    "keywords_raw": doc.get("keywords_raw", ""),
                    "path_gambar": doc.get("path_gambar", ""),
                    "sumber_url": doc.get("sumber_url", ""),
                },
                distance=distance,
                document=doc.get("document", ""),
            ))
        
        return results

    def get_all(self, include_documents: bool = False) -> List[VectorDocument]:
        """Retrieve all documents from the collection."""
        try:
            # Use export for getting all documents
            exclude_fields = ["embedding"]
            if not include_documents:
                exclude_fields.append("document")
            
            # Search with wildcard to get all
            search_params = {
                "q": "*",
                "per_page": 250,  # Typesense max per page
                "exclude_fields": ",".join(exclude_fields),
            }
            
            response = self._client.collections[self._collection_name].documents.search(search_params)
            
            docs = []
            for hit in response.get("hits", []):
                doc = hit.get("document", {})
                docs.append(VectorDocument(
                    id=doc.get("id", ""),
                    metadata={
                        "tag": doc.get("tag", ""),
                        "judul": doc.get("judul", ""),
                        "jawaban_tampil": doc.get("jawaban_tampil", ""),
                        "keywords_raw": doc.get("keywords_raw", ""),
                        "path_gambar": doc.get("path_gambar", ""),
                        "sumber_url": doc.get("sumber_url", ""),
                    },
                    document=doc.get("document", "") if include_documents else "",
                ))
            
            return docs
            
        except Exception as e:
            print(f"Typesense get_all error: {e}")
            return []

    def get_by_id(
        self,
        doc_id: str,
        include_documents: bool = True,
    ) -> Optional[VectorDocument]:
        """Retrieve a single document by ID."""
        try:
            doc = self._client.collections[self._collection_name].documents[str(doc_id)].retrieve()
            
            return VectorDocument(
                id=doc.get("id", ""),
                metadata={
                    "tag": doc.get("tag", ""),
                    "judul": doc.get("judul", ""),
                    "jawaban_tampil": doc.get("jawaban_tampil", ""),
                    "keywords_raw": doc.get("keywords_raw", ""),
                    "path_gambar": doc.get("path_gambar", ""),
                    "sumber_url": doc.get("sumber_url", ""),
                },
                document=doc.get("document", "") if include_documents else "",
            )
        except ObjectNotFound:
            return None
        except Exception as e:
            print(f"Typesense get_by_id error: {e}")
            return None

    def upsert(
        self,
        doc_id: str,
        embedding: List[float],
        document: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Insert or update a document."""
        doc = {
            "id": str(doc_id),
            "tag": metadata.get("tag", ""),
            "judul": metadata.get("judul", ""),
            "jawaban_tampil": metadata.get("jawaban_tampil", ""),
            "keywords_raw": metadata.get("keywords_raw", ""),
            "path_gambar": metadata.get("path_gambar", ""),
            "sumber_url": metadata.get("sumber_url", ""),
            "document": document,
            "embedding": embedding,
        }
        
        try:
            # Try update first, then create
            self._client.collections[self._collection_name].documents.upsert(doc)
        except Exception as e:
            print(f"Typesense upsert error: {e}")
            raise

    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            self._client.collections[self._collection_name].documents[str(doc_id)].delete()
            return True
        except ObjectNotFound:
            return False
        except Exception as e:
            print(f"Typesense delete error: {e}")
            return False

    def get_all_ids(self) -> List[str]:
        """Get all document IDs (lightweight, no metadata)."""
        try:
            search_params = {
                "q": "*",
                "per_page": 250,
                "include_fields": "id",
            }
            
            response = self._client.collections[self._collection_name].documents.search(search_params)
            
            return [hit["document"]["id"] for hit in response.get("hits", [])]
            
        except Exception as e:
            print(f"Typesense get_all_ids error: {e}")
            return []
