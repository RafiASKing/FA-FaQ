"""
Agent Service - LLM-powered document grading.

Mode 2: Instead of returning the top-1 by vector distance,
the LLM grades candidate FAQs and picks the SINGLE BEST answer.

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
from config.constants import (
    AGENT_CANDIDATE_LIMIT,
    AGENT_MIN_SCORE,
    AGENT_CONFIDENCE_THRESHOLD,
)
from .search_service import SearchService, SearchResult
from .agent_prompts import GRADER_SYSTEM_PROMPT, GRADER_USER_PROMPT
from app.schemas.agent_schema import RerankOutput
from core.logger import log


class AgentService:
    """
    Service untuk agent mode — LLM grading hasil pencarian.

    Flow:
    1. SearchService.search() retrieves candidates (lower threshold, more results)
    2. Candidates formatted into prompt
    3. LLM grades via generate_structured() → returns RerankOutput directly
    4. Return single best SearchResult or None
    """

    @classmethod
    def grade_search(
        cls,
        query: str,
        allowed_modules: Optional[List[str]] = None,
    ) -> Optional[SearchResult]:
        """
        LLM-powered document grading - picks the SINGLE BEST document.

        Args:
            query: User question.
            allowed_modules: Module whitelist for group filtering.
                           If None or ["all"], no filtering applied.

        Returns:
            Single best SearchResult, or None if no match.
        """
        # 1. Get candidates (top 20, min 20%)
        candidates = SearchService.search(
            query=query,
            n_results=AGENT_CANDIDATE_LIMIT,
            min_score=AGENT_MIN_SCORE,
        )

        # Apply module whitelist filter
        if allowed_modules and "all" not in allowed_modules:
            candidates = [c for c in candidates if c.tag in allowed_modules]

        if not candidates:
            log("🤖 Agent: No candidates found")
            return None

        # If only 1 candidate, return it directly
        if len(candidates) == 1:
            log(f"🤖 Agent: Single candidate, returning directly (ID: {candidates[0].id})")
            return candidates[0]

        # 2. Build grader prompt
        prompt = cls._build_grader_prompt(query, candidates)

        # 3. Ask LLM — structured output, no manual parsing
        try:
            llm = container.get_llm()
            result: RerankOutput = llm.generate_structured(
                prompt, RerankOutput, system_prompt=GRADER_SYSTEM_PROMPT
            )
            
            log(f"🤖 Agent: LLM graded (best_id={result.best_id}, confidence={result.confidence:.2f})")
            if result.reasoning:
                log(f"🤖 Agent reasoning: {result.reasoning[:100]}...")

        except Exception as e:
            log(f"🤖 Agent: LLM error - {e}")
            # Fallback to top vector result
            return candidates[0] if candidates else None

        # 4. Check if LLM found a match
        if result.best_id == "0":
            log("🤖 Agent: LLM says no relevant document")
            return None

        if result.confidence < AGENT_CONFIDENCE_THRESHOLD:
            log(f"🤖 Agent: Confidence too low ({result.confidence:.2f} < {AGENT_CONFIDENCE_THRESHOLD})")
            return None

        # 5. Find and return the selected document
        for c in candidates:
            if c.id == result.best_id:
                return c

        # Fallback if ID not found (shouldn't happen)
        log(f"🤖 Agent: ID {result.best_id} not found in candidates, using top result")
        return candidates[0]

    @classmethod
    def _build_grader_prompt(cls, query: str, candidates: List[SearchResult]) -> str:
        """Build the grader prompt with candidate details."""
        candidate_lines = []
        for c in candidates:
            preview = c.jawaban_tampil[:300] + "..." if len(c.jawaban_tampil) > 300 else c.jawaban_tampil
            candidate_lines.append(
                f"[ID: {c.id}]\n"
                f"  Module: {c.tag}\n"
                f"  Title: {c.judul}\n"
                f"  Vector Score: {c.score:.1f}%\n"
                f"  Content: {preview}\n"
            )

        return GRADER_USER_PROMPT.format(
            query=query,
            count=len(candidates),
            candidates="\n".join(candidate_lines),
        )


# === Legacy method (kept for backward compatibility) ===
# Can be removed after migration

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
        [DEPRECATED] Use grade_search() instead.
        Kept for backward compatibility with existing API endpoint.
        """
        result = cls.grade_search(query)
        return [result] if result else []
