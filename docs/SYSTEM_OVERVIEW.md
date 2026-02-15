# System Overview — FA-FaQ (Hospital EMR FAQ System)

> **Single source of truth** for understanding the entire system.  
> **Last Updated**: 2026-02-15 | **Version**: 2.5

---

## What Is This?

A **semantic search FAQ system** for hospital staff using EMR (Electronic Medical Record). Staff ask questions via **WhatsApp** or **Web**, and the system finds the best matching FAQ using vector search + optional LLM grading.

**Target users**: Doctors, nurses, admin staff, cashiers, lab technicians.

---

## Architecture

```
Ports & Adapters (Hexagonal) — Siloam AI Research Template

┌────────────────────── PRESENTATION ──────────────────────┐
│  Streamlit User App (:8501)    │  FastAPI Web V2 (:8080) │
│  Streamlit Admin App (:8502)   │  FastAPI WA Bot (:8000) │
│  Streamlit Bot Tester (:8503)  │                         │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────── APP LAYER (app/) ────────────────────┐
│  Controllers  →  Services  →  Schemas (Pydantic)        │
│  Ports (ABCs) →  Adapters (concrete implementations)    │
│  Kernel.py (FastAPI factory + lifespan)                  │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────── CORE LAYER (core/) ──────────────────┐
│  TagManager │ ContentParser │ ImageHandler │ Logger      │
│  GroupConfig │ BotConfig                                 │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────── CONFIG LAYER (config/) ──────────────┐
│  settings.py (Pydantic)  │  constants.py  │  container.py│
│  typesenseDb.py │ messaging.py │ routes.py │ middleware.py│
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────── EXTERNAL SERVICES ───────────────────┐
│  Typesense (vector DB, port 8118)                        │
│  Google Gemini API (embedding + LLM)                     │
│  WPPConnect (WhatsApp gateway, port 21465)               │
└──────────────────────────────────────────────────────────┘
```

### Ports & Adapters

| Port (ABC) | Adapter | Library |
|------------|---------|---------|
| `EmbeddingPort` | `GeminiEmbeddingAdapter` | `google-genai` |
| `LLMPort` | `GeminiChatAdapter` | `langchain-google-genai` |
| `VectorStorePort` | `TypesenseVectorStoreAdapter` | `typesense` |
| `MessagingPort` | `WPPConnectMessagingAdapter` | `requests` |

Swap any adapter via `config/container.py` without touching business logic.

---

## Directory Structure

```
FA-FaQ/
├── main.py                          # Entry point (API / admin / bot-tester)
├── config/
│   ├── settings.py                  # Pydantic BaseSettings (.env)
│   ├── constants.py                 # Thresholds, model names, limits
│   ├── container.py                 # Dependency injection (lazy singletons)
│   ├── typesenseDb.py               # Typesense vector store adapter
│   ├── messaging.py                 # WPPConnect messaging adapter
│   ├── routes.py                    # Centralized route registration
│   └── middleware.py                # CORS, static files
├── core/
│   ├── tag_manager.py               # Tag/module definitions
│   ├── content_parser.py            # [GAMBAR X] parsing, WhatsApp formatter
│   ├── image_handler.py             # Image upload, compression, path fixing
│   ├── logger.py                    # Logging + failed search analytics
│   ├── group_config.py              # Per-group module whitelist
│   └── bot_config.py                # Global bot settings (search mode)
├── app/
│   ├── Kernel.py                    # FastAPI app factory + lifespan
│   ├── ports/                       # Abstract interfaces
│   │   ├── embedding_port.py
│   │   ├── llm_port.py
│   │   ├── vector_store_port.py
│   │   └── messaging_port.py
│   ├── generative/
│   │   └── engine.py                # Gemini embedding + chat adapters
│   ├── services/
│   │   ├── embedding_service.py     # HyDE embedding (document + query)
│   │   ├── search_service.py        # Vector search + scoring
│   │   ├── faq_service.py           # FAQ CRUD operations
│   │   ├── whatsapp_service.py      # Bot logic + WA facade
│   │   ├── agent_service.py         # LLM-powered document grading
│   │   └── agent_prompts.py         # Grader system/user prompts
│   ├── controllers/
│   │   ├── search_controller.py     # /api/v1/search
│   │   ├── faq_controller.py        # /api/v1/faq (CRUD)
│   │   ├── webhook_controller.py    # /webhook (WhatsApp)
│   │   └── agent_controller.py      # /api/v1/agent
│   └── schemas/                     # Pydantic request/response models
├── streamlit_apps/
│   ├── user_app.py                  # Public search UI
│   ├── admin_app.py                 # Admin console (CRUD + settings + full analytics dashboard)
│   └── bot_tester.py                # Test bot without WhatsApp
├── data/
│   ├── tags_config.json             # Department definitions
│   ├── group_config.json            # WhatsApp group settings
│   ├── bot_config.json              # Global bot config (search mode)
│   ├── failed_searches.csv          # Analytics (Misses)
│   └── search_log.csv               # Analytics (All Traffic)
├── web_v2/                          # [DEPRECATED] - Templates now in root templates/
├── images/                          # Uploaded FAQ images (by module)
└── docs/                            # Documentation
```

---

## Key Technologies

| Component | Technology | Details |
|-----------|-----------|---------|
| **Vector DB** | Typesense 27.1 | Collection: `hospital_faq_kb`, port 8118 |
| **Embedding** | `gemini-embedding-001` | 3072-dim, asymmetric retrieval |
| **LLM (Agent)** | `gemini-3-flash-preview` | Via LangChain structured output |
| **Web Framework** | FastAPI + Streamlit | API + admin UI |
| **WhatsApp** | WPPConnect | Self-hosted gateway |
| **Tracing** | LangSmith | Automatic via LangChain env vars |

---

## Search Modes

### 1. Immediate Mode (Default)
```
Query → Embed (RETRIEVAL_QUERY) → Typesense vector search → Top 1 result
Filter: score ≥ 41%
Speed: ~200ms
```

### 2. Agent Mode (LLM Grader)
```
Query → Embed → Top 20 candidates (min 20%) → LLM grades all →
Best match by confidence (≥ 30%)
Speed: ~3-5s
```

Toggle via admin UI (Bot Settings) or `data/bot_config.json`.

---

## Embedding Template

**Single source**: `EmbeddingService._build_document_text()`

```
MODUL: {tag} ({tag_description})
TOPIK: {judul}
TERKAIT: {keywords}
ISI KONTEN: {clean_jawaban}
```

**Asymmetric retrieval**:
- Documents indexed with `RETRIEVAL_DOCUMENT` task type
- Queries use `RETRIEVAL_QUERY` task type

---

## WhatsApp Bot Flow

```
Message → Webhook → should_reply? → clean_query →
  ├── Group? → auto-register → get allowed_modules
  └── DM? → all modules
→ check search_mode →
  ├── "immediate" → SearchService.search_for_bot()
  └── "agent" → AgentService.grade_search()
→ build response → send via WPPConnect
```

---

## Agent Mode Schema

```python
class RerankOutput(BaseModel):
    reasoning: str      # Chain-of-thought FIRST
    best_id: str        # Document ID or "0" (no match)
    confidence: float   # 0.0 - 1.0
```

---

## Configuration

### .env
```env
GOOGLE_API_KEY=...
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8118
TYPESENSE_API_KEY=xyz
TYPESENSE_COLLECTION=hospital_faq_kb
ADMIN_PASSWORD_HASH=...
WA_BASE_URL=http://wppconnect:21465
WA_SESSION_KEY=THISISMYSECURETOKEN
BOT_IDENTITIES=6281234567890

# Optional: LangSmith
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=FA-FaQ-Dev01

# Security
CORS_ORIGINS=https://faq-assist.cloud,http://localhost:3000
WEBHOOK_SECRET=your-secret-token-here
```

### Key Constants (`config/constants.py`)
```python
RELEVANCE_THRESHOLD = 41              # Min score for immediate mode
EMBEDDING_DIMENSION = 3072            # gemini-embedding-001
LLM_MODEL = "gemini-3-flash-preview"  # Agent mode LLM
AGENT_CANDIDATE_LIMIT = 20            # Candidates for LLM grading
AGENT_MIN_SCORE = 20.0                # Min score for agent candidates
AGENT_CONFIDENCE_THRESHOLD = 0.3      # Min LLM confidence
```

---

## Local Development

```bash
# 1. Start Typesense
docker compose up typesense -d

# 2. Set PYTHONPATH (Windows)
$env:PYTHONPATH = "."

# 3. Run API
python main.py api --port 8001

# 4. Run Admin
streamlit run streamlit_apps/admin_app.py --server.port 8502

# 5. Run Bot Tester
streamlit run streamlit_apps/bot_tester.py --server.port 8503
```

---

## Documentation Index

| Doc | What It Covers | Status |
|-----|---------------|--------|
| **SYSTEM_OVERVIEW.md** (this file) | Complete current state | ✅ Current |
| **MEMORY.md** | Quick reference for AI agents | ✅ Current |
| **REFACTORING_V2.1** | Ports & Adapters migration | 📋 Historical |
| **REFACTORING_V2.2** | Windows + Bot Tester | 📋 Historical |
| **REFACTORING_V2.3** | ChromaDB → Typesense migration | 📋 Historical |
| **REFACTORING_V2.4** | Agent Mode + Group Whitelist | 📋 Historical |
| **REFACTORING_V2.5** | Production Hardening (Batch 1) | ✅ Current Context |
| **COMPLETE_SYSTEM_SPECIFICATION** V1/V2 | ⚠️ OUTDATED — still references ChromaDB | ❌ Outdated |

> **For a new AI**: Read `SYSTEM_OVERVIEW.md` + `MEMORY.md`. That's it.  
> The REFACTORING docs are changelog history, not required reading.
