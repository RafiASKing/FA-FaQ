"""
Test untuk core utilities.
"""

import pytest
from core.content_parser import ContentParser
from core.tag_manager import TagManager


class TestContentParser:
    """Test ContentParser class."""
    
    def test_count_image_tags(self):
        """Test counting [GAMBAR X] tags."""
        text = "Hello [GAMBAR 1] world [GAMBAR 2]"
        assert ContentParser.count_image_tags(text) == 2
    
    def test_count_image_tags_empty(self):
        """Test dengan teks tanpa gambar."""
        assert ContentParser.count_image_tags("No images here") == 0
    
    def test_clean_for_embedding(self):
        """Test cleaning text untuk embedding."""
        text = "Langkah:\n[GAMBAR 1]\nSelesai"
        clean = ContentParser.clean_for_embedding(text)
        assert "[GAMBAR" not in clean
    
    def test_get_streamlit_parts(self):
        """Test parsing untuk Streamlit."""
        text = "Before [GAMBAR 1] After"
        parts = ContentParser.get_streamlit_parts(text, "none")
        assert len(parts) >= 1
        # Check types
        types = [p.get('type') for p in parts]
        assert 'text' in types or 'image' in types


class TestTagManager:
    """Test TagManager class."""
    
    def test_load_tags(self):
        """Test loading tags config."""
        tags = TagManager.load_tags()
        assert isinstance(tags, dict)
    
    def test_color_conversion(self):
        """Test hex to streamlit color."""
        color = TagManager.hex_to_streamlit_color("#FF0000")
        assert color in ["red", "orange", "green", "blue", "violet", "gray"]
