"""
API Routes v1 - Aggregator untuk semua API endpoints versi 1.
"""

from fastapi import APIRouter

from app.controllers.search_controller import router as search_router
from app.controllers.faq_controller import router as faq_router
from app.controllers.agent_controller import router as agent_router


router = APIRouter(prefix="/api/v1")

# Include sub-routers
router.include_router(search_router)
router.include_router(faq_router)
router.include_router(agent_router)


@router.get("/info")
async def api_info():
    """Informasi tentang API v1."""
    return {
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/v1/search",
            "agent": "/api/v1/agent",
            "faq": "/api/v1/faq",
            "tags": "/api/v1/search/tags"
        }
    }
