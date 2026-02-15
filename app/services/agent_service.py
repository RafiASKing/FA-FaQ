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
)
from core.bot_config import BotConfig
from .search_service import SearchService, SearchResult
from .agent_prompts import GRADER_SYSTEM_PROMPT, GRADER_USER_PROMPT
from app.schemas.agent_schema import RerankOutput
from core.logger import log, log_failed_search


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
        use_pro: bool = False,
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
        # 1. Get candidates
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

        # 2. Build grader prompt
        prompt = cls._build_grader_prompt(query, candidates)

        # 3. Ask LLM — structured output, no manual parsing
        try:
            llm = container.get_llm_pro() if use_pro else container.get_llm()
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
        mode = "agent_pro" if use_pro else "agent"
        if result.best_id == "0":
            log("🤖 Agent: LLM says no relevant document")
            log_failed_search(
                query, reason="no_relevant", mode=mode,
                detail=f"Agent reasoning: {result.reasoning[:200]}" if result.reasoning else "",
            )
            return None

        confidence_threshold = BotConfig.get_confidence_threshold()
        if result.confidence < confidence_threshold:
            log(f"🤖 Agent: Confidence too low ({result.confidence:.2f} < {confidence_threshold})")
            # Find the candidate the LLM picked (for diagnostics)
            picked = next((c for c in candidates if c.id == result.best_id), None)
            log_failed_search(
                query, reason="low_confidence", mode=mode,
                top_score=picked.score if picked else 0,
                top_faq_id=result.best_id,
                top_faq_title=picked.judul if picked else "",
                detail=f"confidence={result.confidence:.2f} < {confidence_threshold}; {result.reasoning[:150] if result.reasoning else ''}",
            )
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
            keywords = c.keywords_raw if c.keywords_raw else ""
            line = (
                f"[ID: {c.id}]\n"
                f"  Module: {c.tag}\n"
                f"  Title: {c.judul}\n"
                f"  Vector Score: {c.score:.1f}%\n"
            )
            if keywords:
                line += f"  User Variations (HyDE): {keywords}\n"
            line += f"  Content: {c.jawaban_tampil}\n"
            candidate_lines.append(line)

        return GRADER_USER_PROMPT.format(
            query=query,
            count=len(candidates),
            candidates="\n".join(candidate_lines),
        )


