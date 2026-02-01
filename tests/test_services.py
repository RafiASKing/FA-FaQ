"""
Test untuk services.
"""

import pytest
from app.services import SearchService, FaqService


class TestSearchService:
    """Test SearchService class."""
    
    def test_calculate_relevance(self):
        """Test relevance calculation."""
        # Distance 0 = 100% relevance
        score = SearchService.calculate_relevance(0.0)
        assert score == 100
        
        # Distance 2 = 0% relevance  
        score = SearchService.calculate_relevance(2.0)
        assert score == 0
        
        # Distance 1 = 50% relevance
        score = SearchService.calculate_relevance(1.0)
        assert score == 50
    
    def test_calculate_relevance_clamp(self):
        """Test bahwa relevance di-clamp ke 0-100."""
        # Negative distance (shouldn't happen but test anyway)
        score = SearchService.calculate_relevance(-0.5)
        assert 0 <= score <= 100


class TestFaqService:
    """Test FaqService class."""
    
    def test_count_by_tag_returns_int(self):
        """Test count_by_tag returns integer."""
        # Ini akan return 0 jika tag tidak ada
        count = FaqService.count_by_tag("NONEXISTENT_TAG_12345")
        assert isinstance(count, int)
        assert count >= 0
