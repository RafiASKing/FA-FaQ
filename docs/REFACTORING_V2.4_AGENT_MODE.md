# Refactoring V2.4: Agent Mode & Group Whitelist

**Date**: 2026-02-08 ~ 2026-02-09  
**Status**: ✅ Complete

---

## Overview

This version adds two major features:
1. **Group Module Whitelist** — Per-group FAQ filtering
2. **Agent Mode** — LLM-powered document grading for smarter search

Plus critical fixes for embedding task types.

---

## Feature 1: Group Module Whitelist

Allows admins to restrict which FAQ modules are available in specific WhatsApp groups.

### New Files
| File | Description |
|------|-------------|
| `core/group_config.py` | GroupConfig service for managing group settings |
| `data/group_config.json` | Storage for group configurations |

### Modified Files

#### `webhook_controller.py`
- Auto-registers groups on first mention
- Fetches group name from WPPConnect API
- Applies module whitelist filter

#### `app/services/search_service.py`
Added `allowed_modules` parameter:
```python
def search_for_bot(query, top_n=1, allowed_modules=None):
    if allowed_modules and "all" not in allowed_modules:
        candidates = [c for c in candidates if c.tag in allowed_modules]
```

#### `streamlit_apps/admin_app.py`
Added Tab 6: Group Settings
- View registered groups
- Set allowed modules per group
- Delete group registrations

### How It Works
1. User mentions @faq in group
2. Bot auto-registers group with display name
3. Admin sets allowed modules in admin UI
4. Bot only returns FAQs from allowed modules

---

## Feature 2: Agent Mode (LLM Grader)

Uses Gemini 3 Flash to grade search candidates instead of relying purely on vector distance.

### New/Modified Files

| File | Change |
|------|--------|
| `app/schemas/agent_schema.py` | New `RerankOutput` schema with reasoning-first pattern |
| `config/constants.py` | Added `LLM_MODEL`, `AGENT_CANDIDATE_LIMIT`, `AGENT_MIN_SCORE`, `AGENT_CONFIDENCE_THRESHOLD` |
| `app/services/agent_prompts.py` | New `GRADER_SYSTEM_PROMPT` and `GRADER_USER_PROMPT` |
| `app/services/agent_service.py` | New `grade_search()` method |
| `core/bot_config.py` | **NEW** - Global bot config management |
| `data/bot_config.json` | **NEW** - Stores search mode setting |

### Schema Design (Chain-of-Thought)
```python
class RerankOutput(BaseModel):
    reasoning: str      # LLM thinks FIRST
    best_id: str        # "0" = no match, else document ID
    confidence: float   # 0-1 range
```

### Search Modes

| Mode | Speed | Accuracy | Threshold |
|------|-------|----------|-----------|
| **Immediate** | ~200ms | Good | Vector score ≥ 41% |
| **Agent** | ~3-5s | Better | LLM confidence ≥ 30% |

### Webhook Integration
```python
search_mode = BotConfig.get_search_mode()
if search_mode == "agent":
    result = AgentService.grade_search(query, allowed_modules)
else:
    results = SearchService.search_for_bot(query, allowed_modules=allowed_modules)
```

### LangSmith Integration
Automatic tracing via LangChain. Add to `.env`:
```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=FA-FaQ-Dev01
```

---

## Fix: Embedding Task Types

### Problem
All embeddings (documents AND queries) used `RETRIEVAL_DOCUMENT` task type, causing inflated similarity scores for irrelevant queries.

### Solution
Updated to use asymmetric retrieval:
- **Documents**: `RETRIEVAL_DOCUMENT` (for indexing)
- **Queries**: `RETRIEVAL_QUERY` (for searching)

### Files Changed
| File | Change |
|------|--------|
| `app/ports/embedding_port.py` | Added `task_type` parameter |
| `app/generative/engine.py` | `embed()` now accepts `task_type` |
| `app/services/embedding_service.py` | `generate_query_embedding()` uses `RETRIEVAL_QUERY` |

### Result
Irrelevant query scores dropped ~10% (e.g., "nasi padang" from 71% → 61%).

---

## Bug Fixes

### 1. Model Name
```diff
- LLM_MODEL = "gemini-3.0-flash"      # Wrong
+ LLM_MODEL = "gemini-3-flash-preview" # Correct
```

### 2. Threshold Conflict
Agent mode results (20% min score) were being rejected by webhook's 41% threshold check.
```diff
- if score < RELEVANCE_THRESHOLD:
+ if search_mode == "immediate" and score < RELEVANCE_THRESHOLD:
```

### 3. Empty Reasoning Log
```diff
- log(f"Agent reasoning: {result.reasoning[:100]}...")
+ if result.reasoning:
+     log(f"Agent reasoning: {result.reasoning[:100]}...")
```

---

## Testing

### Bot Tester Updates
`streamlit_apps/bot_tester.py` now supports:
- Search mode toggle (Immediate vs Agent)
- Timing display
- Auto-detects global mode setting

### Verified Behavior
| Query | Agent Response |
|-------|----------------|
| "tombol panggil gabisa" | ✅ best_id=16, confidence=1.0 |
| "makan nasi padang yok" | ✅ best_id=0 (rejected) |

---

## Configuration Summary

### `.env` Additions
```env
# LangSmith (optional)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=FA-FaQ-Dev01
```

### `data/bot_config.json`
```json
{
  "search_mode": "immediate",
  "agent_confidence_threshold": 0.3
}
```

### `config/constants.py`
```python
LLM_MODEL = "gemini-3-flash-preview"
LLM_MODEL_PRO = "gemini-3-pro-preview"
AGENT_CANDIDATE_LIMIT = 20
AGENT_MIN_SCORE = 20.0
AGENT_CONFIDENCE_THRESHOLD = 0.3
```

---

## Next Steps (Optional)

- [ ] Test agent mode via WhatsApp in production
- [ ] Monitor LangSmith for cost/latency
- [ ] Consider adjusting confidence threshold based on real usage
