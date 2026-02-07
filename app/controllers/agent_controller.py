"""
Agent Controller - LLM-powered FAQ search with reranking.
Following Siloam pattern: class with dependencies at __init__, module-level singleton.

This controller handles "agent mode" — where an LLM grades candidate documents
instead of relying purely on vector distance.
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.schemas import SearchResponse, SearchResultItem
from app.services.agent_service import AgentService
from core.logger import log


router = APIRouter(prefix="/agent", tags=["Agent Search"])


class AgentController:
    """
    Controller untuk agent-mode search.
    Dependencies initialized at startup (singleton pattern).
    """

    def __init__(self):
        self.agent_service = AgentService
        log("AgentController initialized")

    async def search(
        self,
        query: str,
        filter_tag: Optional[str] = None,
        top_n: int = 3,
    ) -> SearchResponse:
        """Agent-mode search: LLM reranks candidate FAQs."""
        try:
            results = self.agent_service.rerank_search(
                query=query,
                filter_tag=filter_tag,
                top_n=top_n,
            )

            return SearchResponse(
                query=query,
                filter_tag=filter_tag,
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
                        badge_color=r.badge_color,
                    )
                    for r in results
                ],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent search error: {str(e)}")


# Singleton — initialized once at import time (like Siloam pattern)
agentController = AgentController()


# === Routes (wired to singleton) ===

@router.get("", response_model=SearchResponse)
async def agent_search(
    q: str = Query(..., description="Query pencarian", min_length=1),
    tag: Optional[str] = Query(default=None, description="Filter tag"),
    limit: int = Query(default=3, ge=1, le=10, description="Max results (1-10)"),
) -> SearchResponse:
    """
    Agent-mode search — LLM reranks candidate FAQs.

    Unlike /search which returns by vector distance, this endpoint
    sends candidates to an LLM that grades which FAQs truly answer the question.
    """
    return await agentController.search(q, tag, limit)
