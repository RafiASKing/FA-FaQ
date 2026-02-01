"""
Test untuk config module.
"""

import pytest
from config.settings import Settings, PathSettings
from config.constants import (
    RELEVANCE_THRESHOLD,
    HIGH_RELEVANCE_THRESHOLD,
    MEDIUM_RELEVANCE_THRESHOLD,
    ITEMS_PER_PAGE,
)


class TestSettings:
    """Test Settings class."""
    
    def test_default_values(self):
        """Pastikan default values tersedia."""
        settings = Settings()
        assert settings.embedding_model is not None
        assert settings.collection_name is not None
    
    def test_path_settings_exists(self):
        """Pastikan PathSettings bisa diakses."""
        paths = PathSettings()
        assert paths.BASE_DIR.exists()


class TestConstants:
    """Test constants values."""
    
    def test_threshold_values(self):
        """Pastikan threshold values masuk akal."""
        assert 0 < RELEVANCE_THRESHOLD < 100
        assert RELEVANCE_THRESHOLD < MEDIUM_RELEVANCE_THRESHOLD
        assert MEDIUM_RELEVANCE_THRESHOLD < HIGH_RELEVANCE_THRESHOLD
    
    def test_pagination(self):
        """Pastikan pagination value positif."""
        assert ITEMS_PER_PAGE > 0
