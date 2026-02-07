"""
Agent Service - LLM-powered document reranking.

Mode 2: Instead of returning the top-1 by vector distance,
the LLM grades candidate FAQs and picks the best 1-3 answers.

Uses LangChain's with_structured_output(RerankOutput) via LLMPort.generate_structured()
— LLM returns a validated Pydantic object directly, no manual JSON parsing.

Siloam pattern reference:
  - Service provides logic/node methods
  - Controller builds the graph (when using LangGraph)
  - Prompts separated in agent_prompts.py
  - Schemas in agent_schema.py (double duty: LLM output + API response)
"""

from typing import List, Optional

from config import container
from .search_service import SearchService, SearchResult
from .agent_prompts import RERANK_SYSTEM_PROMPT, RERANK_USER_PROMPT
from app.schemas.agent_schema import RerankOutput


class AgentService:
    """
    Service untuk agent mode — LLM reranking hasil pencarian.

    Flow:
    1. SearchService.search() retrieves candidates (lower threshold, more results)
    2. Candidates formatted into prompt
    3. LLM grades via generate_structured() → returns RerankOutput directly
    4. Return selected SearchResults in LLM's order
    """

    @classmethod
    def rerank_search(
        cls,
        query: str,
        filter_tag: Optional[str] = None,
        top_n: int = 3,
        candidate_limit: int = 10,
        min_candidate_score: float = 20.0,
    ) -> List[SearchResult]:
        """
        Search with LLM reranking.

        Args:
            query: User question.
            filter_tag: Tag filter (None = all).
            top_n: Max results to return.
            candidate_limit: Candidates sent to LLM.
            min_candidate_score: Min score for candidates (lower than normal).

        Returns:
            List of SearchResult selected by LLM, ordered by relevance.
        """
        # 1. Get candidates (lower threshold, more results)
        candidates = SearchService.search(
            query=query,
            filter_tag=filter_tag,
            n_results=candidate_limit,
            min_score=min_candidate_score,
        )

        if not candidates:
            return []

        if len(candidates) == 1:
            return candidates

        # 2. Build prompt
        prompt = cls._build_rerank_prompt(query, candidates)

        # 3. Ask LLM — structured output, no manual parsing
        llm = container.get_llm()
        result: RerankOutput = llm.generate_structured(
            prompt, RerankOutput, system_prompt=RERANK_SYSTEM_PROMPT
        )

        if not result.selected_ids:
            return candidates[:1]

        # 4. Return in LLM's order
        id_to_result = {c.id: c for c in candidates}
        results = [id_to_result[sid] for sid in result.selected_ids if sid in id_to_result]

        return results[:top_n]

    @classmethod
    def _build_rerank_prompt(cls, query: str, candidates: List[SearchResult]) -> str:
        """Build the reranking prompt with candidate details."""
        candidate_lines = []
        for c in candidates:
            preview = c.jawaban_tampil[:200] + "..." if len(c.jawaban_tampil) > 200 else c.jawaban_tampil
            candidate_lines.append(
                f"- ID: {c.id} | Tag: {c.tag} | Judul: {c.judul} | "
                f"Score: {c.score:.1f}% | Isi: {preview}"
            )

        return RERANK_USER_PROMPT.format(
            query=query,
            count=len(candidates),
            candidates="\n".join(candidate_lines),
        )
