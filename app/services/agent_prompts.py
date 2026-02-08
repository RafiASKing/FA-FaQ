"""
Agent Prompts - All prompt templates for LLM-powered agent mode.
Following Siloam pattern: prompts separated from service logic.

Prompts are in English for token efficiency. Output instruction tells LLM to
respond in user's language when needed.
"""


# === GRADER PROMPT (NEW - Single Best Selection) ===

GRADER_SYSTEM_PROMPT = """You are a document relevance grader for a Hospital FAQ system.
Your task is to select the SINGLE BEST document that answers the user's question.

RULES:
1. Analyze each candidate's relevance to the question carefully.
2. Consider: topic match, keyword overlap, completeness of answer, specificity.
3. If NO document is relevant to the question, set best_id to "0".
4. A document about a DIFFERENT procedure/module is NOT relevant even if it shares some words.
5. Think step-by-step in your reasoning before making your final decision.

CONFIDENCE SCORING:
- 0.0-0.3: Low (weak match, partial relevance)
- 0.4-0.6: Medium (good match, answers most of the question)
- 0.7-1.0: High (excellent match, directly answers the question)"""


GRADER_USER_PROMPT = """USER QUESTION:
"{query}"

CANDIDATE DOCUMENTS ({count}):
{candidates}

Analyze each candidate, explain your reasoning, then select the BEST document ID or "0" if none are relevant."""


# === LEGACY RERANK PROMPT (kept for backward compatibility) ===

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
