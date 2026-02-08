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
    """
    Grader output - LLM picks the best document from candidates.
    
    Chain-of-thought pattern: reasoning FIRST, then decision.
    This improves accuracy by forcing the LLM to think before answering.
    """
    reasoning: str = Field(
        default="",
        description="Chain of thought: analisis kandidat dan alasan pemilihan dokumen terbaik"
    )
    best_id: str = Field(
        default="0",
        description="ID dokumen terbaik yang menjawab pertanyaan, atau '0' jika tidak ada yang cocok"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Tingkat keyakinan pemilihan (0-1). 0.0-0.3=low, 0.4-0.6=medium, 0.7-1.0=high"
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

