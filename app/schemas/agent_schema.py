"""
Agent Schemas - Pydantic models for LLM structured output + API response.
Following Siloam pattern: schemas serve double duty (LLM output + API response).

These schemas are used with LangChain's `llm.with_structured_output(Schema)`
so the LLM returns validated Pydantic objects directly — no manual JSON parsing.

Requires: pip install langchain-google-genai langgraph
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# === LLM STRUCTURED OUTPUT SCHEMAS ===
# Used with: llm.with_structured_output(RerankOutput)

class RerankOutput(BaseModel):
    """Output dari reranking LLM — which FAQs best answer the question."""
    selected_ids: List[str] = Field(
        default_factory=list,
        description="ID dokumen FAQ yang paling relevan, urut dari paling relevan"
    )
    reasoning: str = Field(
        default="",
        description="Alasan singkat pemilihan dokumen"
    )


# === Future: add more structured output schemas here ===
# Example for multi-step agent:
#
# class IntentClassification(BaseModel):
#     intent: Literal['faq_search', 'general'] = Field(...)
#     reasoning: str = Field(default="")
#
# class QueryRefinement(BaseModel):
#     refined_query: str = Field(...)
#     filter_tag: Optional[str] = Field(default=None)
