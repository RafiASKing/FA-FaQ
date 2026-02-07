"""
Generative Engine - Google Gemini API adapters.
Following Siloam convention: app/generative/engine.py

Embedding adapter: uses google-genai SDK (no LangChain wrapper needed).
Chat adapter: uses LangChain ChatGoogleGenerativeAI for structured output support.
"""

from typing import List, Type, TypeVar

from pydantic import BaseModel

from app.ports.embedding_port import EmbeddingPort
from app.ports.llm_port import LLMPort

T = TypeVar('T', bound=BaseModel)


class GeminiEmbeddingAdapter(EmbeddingPort):
    """
    Embedding adapter using Google Gemini API (google-genai SDK).

    Args:
        api_key: Google API key.
        model: Embedding model name (e.g. "models/gemini-embedding-001").
    """

    def __init__(self, api_key: str, model: str = "models/gemini-embedding-001"):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def embed(self, text: str) -> List[float]:
        """Generate embedding vector using Google Gemini."""
        from google.genai import types
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Embedding error: {e}")
            return []


class GeminiChatAdapter(LLMPort):
    """
    Chat adapter using LangChain ChatGoogleGenerativeAI.
    Supports both free-form text and structured (Pydantic) output.

    Args:
        api_key: Google API key.
        model: Chat model name (e.g. "gemini-2.5-flash").
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        self._llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.0,
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate free-form text using Google Gemini via LangChain."""
        from langchain_core.messages import SystemMessage, HumanMessage
        try:
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            response = self._llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"LLM generation error: {e}")
            return ""

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        """
        Generate a validated Pydantic object using with_structured_output().
        No manual JSON parsing — LangChain handles schema enforcement.
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        structured_llm = self._llm.with_structured_output(schema)
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        return structured_llm.invoke(messages)
