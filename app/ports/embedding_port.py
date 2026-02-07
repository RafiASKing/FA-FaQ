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
    def embed(self, text: str) -> List[float]:
        """
        Convert text to a vector embedding.

        Args:
            text: Raw text to embed.

        Returns:
            List of floats representing the embedding vector.
            Empty list if an error occurred.
        """
        ...
