"""
Search Controller - Handler untuk search endpoints.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Query, Request, HTTPException

from app.schemas import SearchRequest, SearchResponse, SearchResultItem
from app.services import SearchService
from config.constants import WEB_TOP_RESULTS
from config.middleware import limiter
from core.exceptions import AppError, AuthError, SearchError
from core.logger import log_error


router = APIRouter(prefix="/search", tags=["Search"])


class SearchController:
    """Controller untuk search operations."""

    @staticmethod
    def _raise_sanitized_error(exc: Exception, default_ref_prefix: str) -> None:
        """Log full error and raise sanitized HTTPException."""
        request_ref = f"{default_ref_prefix}-{uuid.uuid4().hex[:8].upper()}"

        if isinstance(exc, AppError):
            ref_code = exc.ref_code or request_ref
            detail = f"{exc.message} (Ref: {ref_code})"
            log_error(f"SearchController handled AppError ref={ref_code}", exc)
            raise HTTPException(status_code=exc.status_code, detail=detail)

        log_error(f"SearchController unexpected error ref={request_ref}", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Search service unavailable (Ref: {request_ref})"
        )

    @staticmethod
    @router.get("", response_model=SearchResponse)
    @limiter.limit("60/minute")
    async def search_get(
        request: Request,
        q: str = Query(..., description="Query pencarian", min_length=1, max_length=1000),
        tag: Optional[str] = Query(default=None, description="Filter tag"),
        limit: int = Query(default=WEB_TOP_RESULTS, ge=1, le=50)
    ) -> SearchResponse:
        """
        Pencarian semantic via GET request.

        - **q**: Query pencarian (required)
        - **tag**: Filter berdasarkan tag/modul (optional)
        - **limit**: Jumlah hasil maksimal
        """
        try:
            results = SearchService.search_for_web(q, tag, limit)

            return SearchResponse(
                query=q,
                filter_tag=tag,
                total_results=len(results),
                results=[
                    SearchResultItem(
                        id=r.id,
                        tag=r.tag,
                        judul=r.judul,
                        jawaban_tampil=r.jawaban_tampil,
                        path_gambar=r.path_gambar,
                        sumber_url=r.sumber_url,
                        score=r.score,
                        score_class=r.score_class,
                        badge_color=r.badge_color
                    ) for r in results
                ]
            )
        except (SearchError, AuthError, AppError) as e:
            SearchController._raise_sanitized_error(e, "ERR-SRCH")
        except Exception as e:
            SearchController._raise_sanitized_error(e, "ERR-SRCH")

    @staticmethod
    @router.post("", response_model=SearchResponse)
    @limiter.limit("60/minute")
    async def search_post(request: Request, body: SearchRequest) -> SearchResponse:
        """
        Pencarian semantic via POST request.

        Berguna untuk query yang lebih kompleks atau panjang.
        """
        try:
            results = SearchService.search_for_web(
                body.query,
                body.filter_tag,
                body.limit
            )

            return SearchResponse(
                query=body.query,
                filter_tag=body.filter_tag,
                total_results=len(results),
                results=[
                    SearchResultItem(
                        id=r.id,
                        tag=r.tag,
                        judul=r.judul,
                        jawaban_tampil=r.jawaban_tampil,
                        path_gambar=r.path_gambar,
                        sumber_url=r.sumber_url,
                        score=r.score,
                        score_class=r.score_class,
                        badge_color=r.badge_color
                    ) for r in results
                ]
            )
        except (SearchError, AuthError, AppError) as e:
            SearchController._raise_sanitized_error(e, "ERR-SRCH")
        except Exception as e:
            SearchController._raise_sanitized_error(e, "ERR-SRCH")

    @staticmethod
    @router.get("/tags", response_model=List[str])
    async def get_tags() -> List[str]:
        """
        Ambil daftar semua tag yang tersedia.

        Berguna untuk populate dropdown filter.
        """
        try:
            return SearchService.get_unique_tags()
        except (SearchError, AuthError, AppError) as e:
            SearchController._raise_sanitized_error(e, "ERR-TAGS")
        except Exception as e:
            SearchController._raise_sanitized_error(e, "ERR-TAGS")
