"""
FAQ Schemas - Pydantic models untuk FAQ operations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class FaqCreate(BaseModel):
    """Schema untuk membuat FAQ baru."""
    tag: str = Field(..., description="Tag/modul (ED, OPD, IPD, dll)")
    judul: str = Field(..., description="Judul FAQ/SOP", min_length=3)
    jawaban: str = Field(..., description="Isi jawaban dengan markdown dan [GAMBAR X]")
    keywords: str = Field(default="", description="Variasi pertanyaan user (HyDE)")
    source_url: str = Field(default="", description="URL sumber referensi")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tag": "ED",
                "judul": "Cara Login EMR ED",
                "jawaban": "1. Buka browser\n2. Akses https://emr.siloam.com\n[GAMBAR 1]\n3. Masukkan username dan password",
                "keywords": "gabisa login, lupa password, emr error",
                "source_url": "https://docs.internal.siloam.com/emr-login"
            }
        }


class FaqUpdate(BaseModel):
    """Schema untuk update FAQ."""
    tag: Optional[str] = None
    judul: Optional[str] = None
    jawaban: Optional[str] = None
    keywords: Optional[str] = None
    source_url: Optional[str] = None
    img_paths: Optional[str] = None


class FaqResponse(BaseModel):
    """Schema untuk response FAQ single item."""
    id: str
    tag: str
    judul: str
    jawaban_tampil: str
    keywords_raw: str
    path_gambar: str
    sumber_url: str
    score: Optional[float] = None
    score_class: Optional[str] = None
    badge_color: Optional[str] = None
    
    class Config:
        from_attributes = True


class FaqListResponse(BaseModel):
    """Schema untuk response list FAQ."""
    total: int
    page: int
    per_page: int
    total_pages: int
    items: List[FaqResponse]
