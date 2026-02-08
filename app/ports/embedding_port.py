"""
Embedding Port - Abstract interface for text-to-vector embedding.
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingPort(ABC):
    """
    Port for converting text to embedding vectors.

    Implementations:
    - GeminiEmbeddingAdapter (Google Gemini API)
    - Future: OpenAI, Cohere, local Gemma 300M, etc.
    """

    @abstractmethod
    def embed(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Convert text to a vector embedding.

        Args:
            text: Raw text to embed.
            task_type: "RETRIEVAL_DOCUMENT" for indexing, "RETRIEVAL_QUERY" for searching

        Returns:
            List of floats representing the embedding vector.
            Empty list if an error occurred.
        """
        ...
