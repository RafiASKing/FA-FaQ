"""
LLM Port - Abstract interface for Large Language Model text generation.
Used for agent mode (document reranking, grading, etc).
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class LLMPort(ABC):
    """
    Port for LLM text generation.

    Implementations:
    - GeminiChatAdapter (LangChain ChatGoogleGenerativeAI)
    - Future: OpenAI, Azure, Bedrock, local Ollama, etc.
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate free-form text from a prompt.

        Args:
            prompt: User/task prompt.
            system_prompt: Optional system instruction.

        Returns:
            Generated text response.
        """
        ...

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        """
        Generate a validated Pydantic object from a prompt.

        Uses LangChain's with_structured_output() — the LLM returns
        a validated Pydantic object directly, no manual JSON parsing.

        Args:
            prompt: User/task prompt.
            schema: Pydantic BaseModel subclass defining the output shape.
            system_prompt: Optional system instruction.

        Returns:
            Instance of the given schema, populated by the LLM.
        """
        ...
