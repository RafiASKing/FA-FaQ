"""
Agent Prompts - All prompt templates for LLM-powered agent mode.
Following Siloam pattern: prompts separated from service logic.

Prompts are in English for token efficiency. Output instruction tells LLM to
respond in user's language when needed.
"""


# === RERANKING PROMPT ===

RERANK_SYSTEM_PROMPT = """You are a document relevance grader for a hospital FAQ system.
Your task: given a list of candidate FAQ documents, select which ones BEST ANSWER
the user's question. Return ONLY the IDs of relevant documents.

Rules:
- Select 1 to 3 most relevant documents only.
- If NONE are relevant, return an empty list.
- Order by relevance (most relevant first).
- Consider semantic meaning, not just keyword overlap.
- A document about a DIFFERENT procedure/module is NOT relevant even if it shares some words."""


RERANK_USER_PROMPT = """User's question: "{query}"

Candidate FAQs ({count} documents):
{candidates}

Select the documents that best answer the user's question."""


# === Future prompt templates ===
# Add here as agent capabilities grow:
#
# INTENT_PROMPT = "..."
# QUERY_REFINEMENT_PROMPT = "..."
# ANSWER_SYNTHESIS_PROMPT = "..."
