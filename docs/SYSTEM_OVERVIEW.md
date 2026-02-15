# System Overview — FA-FaQ (Hospital EMR FAQ System)

> **Single source of truth** for understanding the entire system.
> **Last Updated**: 2026-02-15 | **Version**: 3.0

---

## What Is This?

A **semantic search FAQ system** for hospital staff using EMR (Electronic Medical Record). Staff ask questions via **WhatsApp** or **Web**, and the system finds the best matching FAQ using vector search + optional LLM grading.

**Target users**: Doctors, nurses, admin staff, cashiers, lab technicians across 42 Siloam Hospitals.

**Live domain**: `https://faq-assist.cloud` (AWS Lightsail, Ubuntu 22.04, Nginx + SSL)

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
│  Typesense 27.1 (vector DB, host:8118 → container:8108) │
│  Google Gemini API (embedding + LLM)                     │
│  WPPConnect 2.8.11 (WhatsApp gateway, port 21465)        │
└──────────────────────────────────────────────────────────┘
```

### Ports & Adapters

| Port (ABC) | Adapter | Library |
|------------|---------|---------|
| `EmbeddingPort` | `GeminiEmbeddingAdapter` | `google-genai` |
| `LLMPort` | `GeminiChatAdapter` | `langchain-google-genai` (ChatGoogleGenerativeAI) |
| `VectorStorePort` | `TypesenseVectorStoreAdapter` | `typesense` |
| `MessagingPort` | `WPPConnectMessagingAdapter` | `requests` |

Swap any adapter via `config/container.py` without touching business logic.

---

## Directory Structure

```
FA-FaQ/
├── main.py                          # Entry: uvicorn main:bot_app / web_app / api_app
├── Dockerfile                       # Python 3.10-slim, non-root user
├── docker-compose.yml               # 6 services (typesense, wppconnect, bot, user, admin, web)
├── config/
│   ├── settings.py                  # Pydantic BaseSettings (.env)
│   ├── constants.py                 # Thresholds, model names, limits
│   ├── container.py                 # DI container (lazy singletons, set_*() for tests)
│   ├── typesenseDb.py               # Typesense vector store adapter
│   ├── messaging.py                 # WPPConnect messaging adapter (cached all-chats)
│   ├── routes.py                    # Centralized route registration
│   └── middleware.py                # CORS, rate limiting, static files
├── core/
│   ├── tag_manager.py               # Tag/module defs (cached with mtime check)
│   ├── content_parser.py            # [GAMBAR X] parsing, WhatsApp formatter
│   ├── image_handler.py             # Image upload, compression, base64
│   ├── logger.py                    # Logging + search analytics (10-col CSV)
│   ├── group_config.py              # Per-group module whitelist (atomic writes)
│   └── bot_config.py                # Runtime bot settings (atomic writes)
├── app/
│   ├── Kernel.py                    # FastAPI factory + lifespan (preloads everything)
│   ├── ports/                       # Abstract interfaces (ABCs)
│   │   ├── embedding_port.py
│   │   ├── llm_port.py              # generate() + generate_structured()
│   │   ├── vector_store_port.py
│   │   └── messaging_port.py
│   ├── generative/
│   │   └── engine.py                # GeminiEmbeddingAdapter + GeminiChatAdapter
│   ├── services/
│   │   ├── embedding_service.py     # HyDE embedding (document + query)
│   │   ├── search_service.py        # Vector search + scoring + tag filtering
│   │   ├── faq_service.py           # FAQ CRUD (FaqService class)
│   │   ├── whatsapp_service.py      # Bot logic facade
│   │   ├── agent_service.py         # LLM-powered document grading
│   │   └── agent_prompts.py         # Grader system/user prompts (hospital EMR context)
│   ├── controllers/
│   │   ├── search_controller.py     # /api/v1/search
│   │   ├── faq_controller.py        # /api/v1/faq (CRUD)
│   │   ├── webhook_controller.py    # /webhook/whatsapp
│   │   └── agent_controller.py      # /api/v1/agent
│   └── schemas/                     # Pydantic request/response models
│       ├── agent_schema.py          # RerankOutput (structured LLM output)
│       ├── faq_schema.py
│       ├── search_schema.py
│       └── webhook_schema.py        # WhatsAppWebhookPayload
├── routes/
│   ├── api/v1.py                    # API route aggregator
│   └── web.py                       # Web HTML routes (Jinja2 templates)
├── streamlit_apps/
│   ├── user_app.py                  # Public search UI
│   ├── admin_app.py                 # Admin console (CRUD, analytics, group/bot settings)
│   └── bot_tester.py                # Test bot without WhatsApp
├── templates/                       # Jinja2 HTML templates for web UI
├── static/                          # CSS/JS for web UI (light theme, orange header)
├── images/                          # Uploaded FAQ images (organized by module)
├── data/
│   ├── tags_config.json             # Department/module definitions
│   ├── group_config.json            # WhatsApp group settings (auto-synced names)
│   ├── bot_config.json              # Runtime config (search_mode, confidence_threshold)
│   ├── failed_searches.csv          # Failed search analytics (10 columns)
│   └── search_log.csv               # All search traffic analytics
├── scripts/
│   └── migrate_chroma_to_typesense.py  # Migration tool (export/import)
└── docs/                            # Documentation
```

---

## Key Technologies

| Component | Technology | Details |
|-----------|-----------|---------|
| **Vector DB** | Typesense 27.1 | Collection: `hospital_faq_kb`, 3072-dim, cosine distance |
| **Embedding** | `gemini-embedding-001` | 3072-dim, asymmetric retrieval (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY) |
| **LLM Flash** | `gemini-3-flash-preview` | Agent mode, ~2-4s, 30s timeout |
| **LLM Pro** | `gemini-3-pro-preview` | Agent Pro mode, ~5-10s, 60s timeout |
| **LLM Framework** | LangChain (`langchain-google-genai`) | `with_structured_output(RerankOutput)` |
| **Web Framework** | FastAPI + Streamlit | API + admin UI |
| **WhatsApp** | WPPConnect 2.8.11 | Self-hosted, build from GitHub source |
| **Tracing** | LangSmith (optional) | Automatic via LangChain env vars |
| **Deployment** | AWS Lightsail | Ubuntu 22.04, Docker Compose, Nginx + Certbot SSL |

---

## Search Modes

### 1. Immediate Mode
```
Query → Embed (RETRIEVAL_QUERY) → Typesense vector search → Top 1 result
Threshold: score >= 70%
Speed: ~200ms
No waiting message sent to user.
```

### 2. Agent Flash Mode
```
Query → Embed → Top 7 candidates (min 50%) → LLM (Flash) grades with full content →
Best match by confidence >= configurable threshold (default 0.5)
Speed: ~2-4s
Waiting message: "Baik, mohon ditunggu"
```

### 3. Agent Pro Mode
```
Query → Embed → Top 7 candidates (min 50%) → LLM (Pro) grades with full content →
Best match by confidence >= configurable threshold (default 0.5)
Speed: ~5-10s
Waiting message: "Baik, mohon ditunggu..."
```

Toggle via admin UI (Bot Settings tab) or `data/bot_config.json`.

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

## Agent LLM Grading

The LLM receives candidates formatted as:
```
[ID: 5]
  MODUL: ED (IGD, Emergency, Triage, Ambulans)
  TOPIK: Bagaimana cara print order laboratory emergency?
  Skor Vektor: 82.3%
  TERKAIT: print lab, cetak lab, order lab ED
  ISI KONTEN: {full content including [GAMBAR X] tags}
```

**Structured output** via `LLMPort.generate_structured(prompt, RerankOutput)`:
```python
class RerankOutput(BaseModel):
    reasoning: str      # Chain-of-thought FIRST
    best_id: str        # Document ID or "0" (no match)
    confidence: float   # 0.0 - 1.0
```

---

## WhatsApp Bot Flow

```
Message in → Webhook (/webhook/whatsapp) → should_reply? → clean_query →
  ├── Group? → get_group_name (cached all-chats API) → register/sync group → get allowed_modules
  └── DM? → all modules
→ check search_mode →
  ├── "immediate" → SearchService.search_for_bot() [no waiting msg]
  ├── "agent"     → "Baik, mohon ditunggu" → AgentService.grade_search(use_pro=False)
  └── "agent_pro" → "Baik, mohon ditunggu..." → AgentService.grade_search(use_pro=True)
→ build response → send text + images via WPPConnect
→ send footer with web link
```

### Group Features
- Groups auto-register on first @bot mention
- Group names auto-sync from WPPConnect `all-chats` API (5-min cache)
- Per-group module whitelist (e.g., group only sees IPD FAQs)
- Configurable via admin UI (Group Settings tab)

---

## Analytics

### Search Log (`data/search_log.csv`)
Columns: `timestamp, query, score, faq_id, faq_title, mode, response_ms, source`

### Failed Search Log (`data/failed_searches.csv`)
10 columns: `timestamp, query, reason, mode, top_score, top_faq_id, top_faq_title, response_ms, source, detail`

Reasons: `no_results`, `below_threshold`, `no_relevant` (agent), `low_confidence` (agent)

Both Web and WhatsApp sources log to the same files. Viewable in admin console Analytics tab.

---

## Configuration

### .env
```env
# Required
GOOGLE_API_KEY=your-gemini-api-key
TYPESENSE_HOST=typesense          # "typesense" in Docker, "localhost" for local dev
TYPESENSE_PORT=8108               # 8108 inside Docker, 8118 from host
TYPESENSE_API_KEY=xyz
TYPESENSE_COLLECTION=hospital_faq_kb
ADMIN_PASSWORD_HASH=bcrypt-hash   # or plain text for dev
WA_BASE_URL=http://wppconnect:21465
WA_SESSION_KEY=your-secret        # must match WPPConnect SECRET_KEY
WA_SESSION_NAME=mysession
BOT_IDENTITIES=6281234567890,6289876543210

# Optional
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=FA-FaQ
CORS_ORIGINS=https://faq-assist.cloud
```

### Runtime Config (`data/bot_config.json`)
```json
{
  "search_mode": "agent_pro",
  "agent_confidence_threshold": 0.5
}
```

### Key Constants (`config/constants.py`)
```python
RELEVANCE_THRESHOLD = 70              # Min score for immediate mode (%)
EMBEDDING_DIMENSION = 3072            # gemini-embedding-001
LLM_MODEL = "gemini-3-flash-preview"  # Agent Flash
LLM_MODEL_PRO = "gemini-3-pro-preview"# Agent Pro (60s timeout)
AGENT_CANDIDATE_LIMIT = 7             # Candidates for LLM (full content shown)
AGENT_MIN_SCORE = 50.0                # Min score for agent candidates (%)
AGENT_CONFIDENCE_THRESHOLD = 0.5      # Default LLM confidence threshold
SEARCH_CANDIDATE_LIMIT = 50           # Raw candidates from Typesense
```

---

## Docker Compose Services

| Service | Container | Port (host:container) | Purpose |
|---------|-----------|----------------------|---------|
| `typesense` | `faq_typesense` | 8118:8108 | Vector database |
| `wppconnect` | `faq_wppconnect` | 21465:21465 | WhatsApp gateway |
| `faq-bot` | `faq_bot_wa` | 8005:8000 | WhatsApp bot (FastAPI) |
| `faq-user` | `faq_user_app` | 8501:8501 | Public search (Streamlit) |
| `faq-admin` | `faq_admin_app` | 8502:8502 | Admin console (Streamlit) |
| `faq-web-v2` | `faq_web_v2` | 8080:8080 | Web search UI (FastAPI + Jinja2) |

All app containers share `env_file: .env` + docker-compose `environment:` overrides for internal Docker networking (TYPESENSE_HOST=typesense, TYPESENSE_PORT=8108).

WPPConnect `SECRET_KEY` and bot's `WA_SESSION_KEY` are synced via `${WA_SESSION_KEY}` variable substitution in docker-compose.yml.

---

## Deployment

**Production**: AWS Lightsail, domain `faq-assist.cloud`
- Nginx reverse proxy with Certbot SSL
- Docker Compose v1 (`docker-compose` command)
- Shared volumes: `./data`, `./images`, `./templates`, `./static`

**Important**: `docker-compose restart` does NOT re-read `.env`. Use `docker-compose up -d <service>` to recreate containers with updated env.

### Migration from ChromaDB
```bash
# Step 1: Export from ChromaDB (on old server)
python scripts/migrate_chroma_to_typesense.py export

# Step 2: Import to Typesense (re-generates embeddings)
docker-compose run --rm faq-web-v2 python -m scripts.migrate_chroma_to_typesense import
```

---

## Safety & Resilience

- **Atomic writes**: `bot_config.json` and `group_config.json` use `tempfile.mkstemp()` + `os.replace()` — no corruption on concurrent writes
- **TagManager cache**: mtime-based cache invalidation — no disk I/O per query
- **WPPConnect chat cache**: in-memory, 5-min TTL — no API call per message
- **bcrypt auth**: with plain-text fallback for dev environments
- **Non-root Docker**: `fafaq` user, only `/app/data` and `/app/images` writable
- **All shared resources preloaded at startup** (no cold-start for first user)
- **Typed exceptions everywhere** (no bare `except:`)

---

## Local Development

```bash
# 1. Start Typesense
docker compose up typesense -d

# 2. Set PYTHONPATH (Windows PowerShell)
$env:PYTHONPATH = "."

# 3. Run API / Bot / Web
python main.py api --port 8001
python main.py bot --port 8000
python main.py web --port 8080

# 4. Run Streamlit apps
streamlit run streamlit_apps/admin_app.py --server.port 8502
streamlit run streamlit_apps/bot_tester.py --server.port 8503
```

---

## Documentation Index

| Doc | What It Covers | Status |
|-----|---------------|--------|
| **SYSTEM_OVERVIEW.md** (this file) | Complete current state v3.0 | Current |
| **MEMORY.md** | Quick reference for AI agents | Current |
| **REFACTORING_V3.0** | v2.5 → v3.0 changes | Current |
| **REFACTORING_V2.5** | Production Hardening | Historical |
| **REFACTORING_V2.3** | ChromaDB → Typesense | Historical |
| **REFACTORING_V2.1** | Ports & Adapters migration | Historical |

> **For a new AI agent**: Read `SYSTEM_OVERVIEW.md` + `MEMORY.md`, then explore the code. That's it.
