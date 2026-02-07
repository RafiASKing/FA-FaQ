"""
Ports Package - Abstract interfaces (ABCs) for external dependencies.
Defines contracts that adapters must implement.
"""

from .embedding_port import EmbeddingPort
from .vector_store_port import VectorStorePort, VectorSearchResult, VectorDocument
from .messaging_port import MessagingPort
from .llm_port import LLMPort

__all__ = [
    'EmbeddingPort',
    'VectorStorePort',
    'VectorSearchResult',
    'VectorDocument',
    'MessagingPort',
    'LLMPort',
]
