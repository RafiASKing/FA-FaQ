# Config Package
# Berisi konfigurasi aplikasi yang terpusat

from .settings import settings
from .constants import (
    RELEVANCE_THRESHOLD,
    HIGH_RELEVANCE_THRESHOLD,
    MEDIUM_RELEVANCE_THRESHOLD,
    BOT_TOP_RESULTS,
    WEB_TOP_RESULTS,
    ITEMS_PER_PAGE,
    IMAGE_MAX_WIDTH,
    IMAGE_QUALITY,
    COLLECTION_NAME
)

__all__ = [
    'settings',
    'RELEVANCE_THRESHOLD',
    'HIGH_RELEVANCE_THRESHOLD', 
    'MEDIUM_RELEVANCE_THRESHOLD',
    'BOT_TOP_RESULTS',
    'WEB_TOP_RESULTS',
    'ITEMS_PER_PAGE',
    'IMAGE_MAX_WIDTH',
    'IMAGE_QUALITY',
    'COLLECTION_NAME'
]
