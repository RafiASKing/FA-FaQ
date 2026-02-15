# Refactoring V2.5: Production Hardening (Batch 1)

> **Date**: 2026-02-15
> **Focus**: Security, Reliability, Architecture Cleanup, Analytics

---

## 1. Summary of Changes (Batch 1)

We successfully implemented **6 out of 6** critical hardening items to move from "Prototype" to "Pilot-Ready".

### ✅ A. Enhanced Logging
- **New Function**: `log_search()` in `core/logger.py` captures detailed metrics.
- **Data Points**: query, score, faq_id, faq_title, mode (immediate/agent), response_ms, source.
- **Storage**: structured CSV at `data/search_log.csv` (instead of raw stdout).
- **Integration**: `webhook_controller.py` calls this for every message (success, low confidence, no result).

### ✅ B. Analytics Dashboard
- **Location**: `admin_app.py` (Tab 5).
- **Features**:
  - **KPIs**: Total queries, Today's count, Avg Score, Avg Latency.
  - **Charts**: Daily traffic bar chart, Relevance score histogram.
  - **Tables**: Top 10 FAQs, Recent Queries (Live), Mode Split (Agent vs Immediate).
  - **Privacy**: No PII logged, just message metrics.

### ✅ C. LLM & System Reliability
- **Timeouts**: Added `timeout=25` (seconds) to `GeminiChatAdapter` and `GeminiEmbeddingAdapter` in `engine.py`. Prevents infinite hangs if Google API stalls.
- **Error Handling**: `webhook_controller` wraps processing in `try/except` to prevent worker crash.

### ✅ D. Security
- **CORS**: Restricted from wildcard `*` to configurable `CORS_ORIGINS` in `.env`.
- **Webhook Sec**: Added `WEBHOOK_SECRET` env var. If set, `webhook_controller` validates `X-Webhook-Secret` header.

### ✅ E. Architecture Cleanup
- **Dead Code**: Removed all references to outdated `ChromaDB` (replaced by Typesense).
- **Deprecated**: Removed `rerank_search()` method (replaced by `grade_search()`).
- **Config**: Removed stale `DB_PATH` from `settings.py`.
- **Fixes**: Corrected `agent_controller.py` to use the new `grade_search` API.

### ✅ F. Web Interface Refresh
- **Architecture**: Deprecated `web_v2/` folder. Moved `templates/` and `static/` to project root for standard FastAPI structure.
- **Templates**: Refreshed `templates/index.html` and `static/style.css`.
- **Style**: Modern dark theme, glassmorphism, Inter font, proper emoji encoding, responsive mobile view.

---

## 2. System Architecture State (Current)

The system follows a strict **Ports & Adapters (Hexagonal)** architecture.

```
[External: WhatsApp/Web] 
       ↓
[Controllers: Webhook/Search]
       ↓
[Services: Search/Agent/FAQ]
       ↓
[Ports: VectorStore/LLM/Embedding]
       ↓
[Adapters: Typesense/Gemini/WPPConnect]
```

### Key Components
- **Kernel.py**: Application factory and dependency injection wiring.
- **Container.py**: Lazy singleton management for adapters.
- **Settings.py**: Pydantic-based configuration (Env vars).

---

## 3. Honest Assessment (Audit)

We performed a "Pre-Sale Audit" to determine if this is enterprise-ready for Siloam.

**Verdict**: 🟢 **Pilot-Ready (70%)** - impressive architecture, but needs boring enterprise features.

| Area | Grade | Notes |
|------|-------|-------|
| **Architecture** | A | Solid patterns, clean separation. |
| **Features** | A | Semantic search + Agent mode is high value. |
| **Testing** | 🔴 D | Only ~5 trivial tests. Needs unit/integration coverage. |
| **Rate Limiting** | 🔴 F | None. Vulnerable to DOS/cost spikes. |
| **Error Handling** | 🟡 C | Basic `print()` logging, needs structured error types. |
| **Input Validation** | 🟡 C | No query length limits or XSS sanitization. |

---

## 4. Next Steps: Hardening Batch 2 (Safe Batch)

We have approved a plan to address the high-priority gaps without risking logic breakage:

1.  **Rate Limiting**: Add `slowapi` to search/webhook endpoints.
2.  **Query Limits**: Cap input length (e.g., 500 chars).
3.  **Dockerfile**: Cleanup, add `HEALTHCHECK`, non-root user.
4.  **Logging**: Switch `print()` to Python's `logging` module (rotating files).
5.  **Exceptions**: Create custom exception hierarchy (`AppError`, `SearchError`).
6.  **Tests**: Write ~30 proper unit tests for services.
7.  **Documentation**: Add a comprehensive `README.md`.

---

> **Note for AI Agents**: This file is the authoritative context for the state of the system as of Feb 2026.
