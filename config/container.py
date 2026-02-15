"""
Dependency Container - Wires ports to their concrete adapters.
Single source of truth for which adapter is active.

To swap an adapter, change the import and instantiation in the corresponding
get_*() function. Everything else (services, controllers, Streamlit apps) stays unchanged.
"""

from typing import Optional

from app.ports.embedding_port import EmbeddingPort
from app.ports.vector_store_port import VectorStorePort
from app.ports.messaging_port import MessagingPort
from app.ports.llm_port import LLMPort


# === Singleton Instances (lazily initialized, preloaded at startup via lifespan) ===
_embedding: Optional[EmbeddingPort] = None
_vector_store: Optional[VectorStorePort] = None
_messaging: Optional[MessagingPort] = None
_llm: Optional[LLMPort] = None
_llm_pro: Optional[LLMPort] = None


# === Getters ===

def get_embedding() -> EmbeddingPort:
    """
    Get the active embedding adapter.
    Currently: Google Gemini.
    To swap: change the import and instantiation below.
    """
    global _embedding
    if _embedding is None:
        from config.settings import settings
        from config.constants import EMBEDDING_MODEL
        from app.generative.engine import GeminiEmbeddingAdapter

        _embedding = GeminiEmbeddingAdapter(
            api_key=settings.google_api_key,
            model=EMBEDDING_MODEL,
        )
    return _embedding


def get_vector_store() -> VectorStorePort:
    """
    Get the active vector store adapter.
    Currently: Typesense (Siloam standard).
    To swap: change the import and instantiation below.
    """
    global _vector_store
    if _vector_store is None:
        from config.settings import settings
        from config.typesenseDb import TypesenseVectorStoreAdapter
        from config.constants import EMBEDDING_DIMENSION
        
        _vector_store = TypesenseVectorStoreAdapter(
            host=settings.typesense_host,
            port=settings.typesense_port,
            api_key=settings.typesense_api_key,
            collection_name=settings.typesense_collection,
            embedding_dim=EMBEDDING_DIMENSION,
        )
    return _vector_store


def get_messaging() -> MessagingPort:
    """
    Get the active messaging adapter.
    Currently: WPPConnect.
    To swap: change the import and instantiation below.
    """
    global _messaging
    if _messaging is None:
        from config.settings import settings
        from config.messaging import WPPConnectMessagingAdapter

        _messaging = WPPConnectMessagingAdapter(
            base_url=settings.wa_base_url,
            session_name=settings.wa_session_name,
            secret_key=settings.wa_secret_key,
        )
    return _messaging


def get_llm() -> LLMPort:
    """
    Get the active LLM adapter.
    Currently: Google Gemini Flash.
    To swap: change the import and instantiation below.
    """
    global _llm
    if _llm is None:
        from config.settings import settings
        from config.constants import LLM_MODEL
        from app.generative.engine import GeminiChatAdapter

        _llm = GeminiChatAdapter(
            api_key=settings.google_api_key,
            model=LLM_MODEL,
        )
    return _llm


def get_llm_pro() -> LLMPort:
    """
    Get the Pro LLM adapter for deeper analysis.
    Currently: Google Gemini Pro (slower, more accurate).
    """
    global _llm_pro
    if _llm_pro is None:
        from config.settings import settings
        from config.constants import LLM_MODEL_PRO
        from app.generative.engine import GeminiChatAdapter

        _llm_pro = GeminiChatAdapter(
            api_key=settings.google_api_key,
            model=LLM_MODEL_PRO,
            timeout=60,
        )
    return _llm_pro


# === Overrides (for testing) ===

def set_embedding(adapter: EmbeddingPort):
    """Override embedding adapter (for testing)."""
    global _embedding
    _embedding = adapter


def set_vector_store(adapter: VectorStorePort):
    """Override vector store adapter (for testing)."""
    global _vector_store
    _vector_store = adapter


def set_messaging(adapter: MessagingPort):
    """Override messaging adapter (for testing)."""
    global _messaging
    _messaging = adapter


def set_llm(adapter: LLMPort):
    """Override LLM adapter (for testing)."""
    global _llm
    _llm = adapter


def reset_all():
    """Reset all singletons. Useful for testing."""
    global _embedding, _vector_store, _messaging, _llm, _llm_pro
    _embedding = None
    _vector_store = None
    _messaging = None
    _llm = None
    _llm_pro = None
