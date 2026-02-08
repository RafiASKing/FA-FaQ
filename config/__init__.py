# Config Package
# Berisi konfigurasi aplikasi yang terpusat

from .settings import settings, paths
from .constants import (
    # Search & Relevance
    RELEVANCE_THRESHOLD,
    HIGH_RELEVANCE_THRESHOLD,
    MEDIUM_RELEVANCE_THRESHOLD,
    # Result Limits
    BOT_TOP_RESULTS,
    WEB_TOP_RESULTS,
    SEARCH_CANDIDATE_LIMIT,
    # Pagination
    ITEMS_PER_PAGE,
    # Image Processing
    IMAGE_MAX_WIDTH,
    IMAGE_QUALITY,
    # Embedding & LLM
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    LLM_MODEL,
    # Color Mappings
    HEX_TO_STREAMLIT_COLOR,
    COLOR_PALETTE,
    DEFAULT_TAGS
)

__all__ = [
    # Settings
    'settings',
    'paths',
    # Search & Relevance
    'RELEVANCE_THRESHOLD',
    'HIGH_RELEVANCE_THRESHOLD',
    'MEDIUM_RELEVANCE_THRESHOLD',
    # Result Limits
    'BOT_TOP_RESULTS',
    'WEB_TOP_RESULTS',
    'SEARCH_CANDIDATE_LIMIT',
    # Pagination
    'ITEMS_PER_PAGE',
    # Image Processing
    'IMAGE_MAX_WIDTH',
    'IMAGE_QUALITY',
    # Embedding & LLM
    'EMBEDDING_MODEL',
    'EMBEDDING_DIMENSION',
    'LLM_MODEL',
    # Color Mappings
    'HEX_TO_STREAMLIT_COLOR',
    'COLOR_PALETTE',
    'DEFAULT_TAGS'
]
