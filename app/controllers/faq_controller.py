"""
FAQ Controller - Handler untuk FAQ CRUD endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.schemas import FaqCreate, FaqUpdate, FaqResponse, FaqListResponse
from app.services import FaqService, SearchService
from config.constants import ITEMS_PER_PAGE


router = APIRouter(prefix="/faq", tags=["FAQ"])


class FaqController:
    """Controller untuk FAQ CRUD operations."""
    
    @staticmethod
    @router.get("", response_model=FaqListResponse)
    async def list_faqs(
        page: int = Query(default=0, ge=0, description="Nomor halaman (0-indexed)"),
        per_page: int = Query(default=ITEMS_PER_PAGE, ge=1, le=100),
        tag: Optional[str] = Query(default=None, description="Filter tag")
    ) -> FaqListResponse:
        """
        Ambil daftar FAQ dengan paginasi.
        
        - **page**: Nomor halaman (mulai dari 0)
        - **per_page**: Jumlah item per halaman
        - **tag**: Filter berdasarkan tag (optional)
        """
        try:
            all_faqs = SearchService.get_all_faqs(tag)
            
            total = len(all_faqs)
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            
            start = page * per_page
            end = start + per_page
            page_items = all_faqs[start:end]
            
            return FaqListResponse(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                items=[
                    FaqResponse(
                        id=item.get('id', ''),
                        tag=item.get('tag', ''),
                        judul=item.get('judul', ''),
                        jawaban_tampil=item.get('jawaban_tampil', ''),
                        keywords_raw=item.get('keywords_raw', ''),
                        path_gambar=item.get('path_gambar', 'none'),
                        sumber_url=item.get('sumber_url', ''),
                        badge_color=item.get('badge_color', '#808080')
                    ) for item in page_items
                ]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    @staticmethod
    @router.get("/{faq_id}", response_model=FaqResponse)
    async def get_faq(faq_id: str) -> FaqResponse:
        """
        Ambil FAQ berdasarkan ID.
        
        - **faq_id**: ID dokumen FAQ
        """
        try:
            faq = FaqService.get_by_id(faq_id)
            
            if not faq:
                raise HTTPException(status_code=404, detail=f"FAQ dengan ID {faq_id} tidak ditemukan")
            
            from core.tag_manager import TagManager
            
            return FaqResponse(
                id=faq.get('id', ''),
                tag=faq.get('tag', ''),
                judul=faq.get('judul', ''),
                jawaban_tampil=faq.get('jawaban_tampil', ''),
                keywords_raw=faq.get('keywords_raw', ''),
                path_gambar=faq.get('path_gambar', 'none'),
                sumber_url=faq.get('sumber_url', ''),
                badge_color=TagManager.get_tag_color(faq.get('tag', ''))
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    @staticmethod
    @router.post("", response_model=FaqResponse, status_code=201)
    async def create_faq(faq: FaqCreate) -> FaqResponse:
        """
        Buat FAQ baru.
        
        - **tag**: Tag/modul (ED, OPD, IPD, dll)
        - **judul**: Judul FAQ
        - **jawaban**: Isi jawaban dengan markdown
        - **keywords**: Variasi pertanyaan user (HyDE)
        - **source_url**: URL sumber referensi
        """
        try:
            new_id = FaqService.upsert(
                tag=faq.tag,
                judul=faq.judul,
                jawaban=faq.jawaban,
                keywords=faq.keywords,
                source_url=faq.source_url
            )
            
            # Fetch created FAQ untuk response
            created = FaqService.get_by_id(new_id)
            
            from core.tag_manager import TagManager
            
            return FaqResponse(
                id=new_id,
                tag=created.get('tag', ''),
                judul=created.get('judul', ''),
                jawaban_tampil=created.get('jawaban_tampil', ''),
                keywords_raw=created.get('keywords_raw', ''),
                path_gambar=created.get('path_gambar', 'none'),
                sumber_url=created.get('sumber_url', ''),
                badge_color=TagManager.get_tag_color(created.get('tag', ''))
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating FAQ: {str(e)}")
    
    @staticmethod
    @router.put("/{faq_id}", response_model=FaqResponse)
    async def update_faq(faq_id: str, faq: FaqUpdate) -> FaqResponse:
        """
        Update FAQ existing.
        
        - **faq_id**: ID dokumen yang akan diupdate
        """
        try:
            # Check existing
            existing = FaqService.get_by_id(faq_id)
            if not existing:
                raise HTTPException(status_code=404, detail=f"FAQ dengan ID {faq_id} tidak ditemukan")
            
            # Merge dengan data existing
            updated_id = FaqService.upsert(
                tag=faq.tag or existing.get('tag', ''),
                judul=faq.judul or existing.get('judul', ''),
                jawaban=faq.jawaban or existing.get('jawaban_tampil', ''),
                keywords=faq.keywords or existing.get('keywords_raw', ''),
                img_paths=faq.img_paths or existing.get('path_gambar', 'none'),
                source_url=faq.source_url or existing.get('sumber_url', ''),
                doc_id=faq_id
            )
            
            # Fetch updated
            updated = FaqService.get_by_id(updated_id)
            
            from core.tag_manager import TagManager
            
            return FaqResponse(
                id=updated_id,
                tag=updated.get('tag', ''),
                judul=updated.get('judul', ''),
                jawaban_tampil=updated.get('jawaban_tampil', ''),
                keywords_raw=updated.get('keywords_raw', ''),
                path_gambar=updated.get('path_gambar', 'none'),
                sumber_url=updated.get('sumber_url', ''),
                badge_color=TagManager.get_tag_color(updated.get('tag', ''))
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating FAQ: {str(e)}")
    
    @staticmethod
    @router.delete("/{faq_id}")
    async def delete_faq(faq_id: str):
        """
        Hapus FAQ beserta gambar terkait.
        
        - **faq_id**: ID dokumen yang akan dihapus
        """
        try:
            # Check existing
            existing = FaqService.get_by_id(faq_id)
            if not existing:
                raise HTTPException(status_code=404, detail=f"FAQ dengan ID {faq_id} tidak ditemukan")
            
            success = FaqService.delete(faq_id)
            
            if success:
                return {"message": f"FAQ {faq_id} berhasil dihapus"}
            else:
                raise HTTPException(status_code=500, detail="Gagal menghapus FAQ")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
