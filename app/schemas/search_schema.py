"""
Search Schemas - Pydantic models untuk search operations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Schema untuk search request."""
    query: str = Field(..., description="Query pencarian", min_length=1, max_length=1000)
    filter_tag: Optional[str] = Field(default=None, description="Filter berdasarkan tag")
    limit: int = Field(default=3, description="Jumlah hasil maksimal", ge=1, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "gimana cara login emr ed",
                "filter_tag": "ED",
                "limit": 3
            }
        }


class SearchResultItem(BaseModel):
    """Schema untuk single search result."""
    id: str
    tag: str
    judul: str
    jawaban_tampil: str
    path_gambar: str
    sumber_url: str
    score: float = Field(..., description="Relevance score (0-100)")
    score_class: str = Field(..., description="CSS class (score-high, score-med, score-low)")
    badge_color: str = Field(..., description="HEX color untuk badge")


class SearchResponse(BaseModel):
    """Schema untuk search response."""
    query: str
    filter_tag: Optional[str]
    total_results: int
    results: List[SearchResultItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "cara login emr",
                "filter_tag": "ED",
                "total_results": 2,
                "results": [
                    {
                        "id": "1",
                        "tag": "ED",
                        "judul": "Cara Login EMR ED",
                        "jawaban_tampil": "1. Buka browser...",
                        "path_gambar": "./images/ED/login_1.jpg",
                        "sumber_url": "https://docs.siloam.com",
                        "score": 85.5,
                        "score_class": "score-high",
                        "badge_color": "#FF4B4B"
                    }
                ]
            }
        }
