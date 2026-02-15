# Project Memory - Hospital FAQ Retriever (FA-FaQ)

## Architecture (Siloam-aligned Ports & Adapters)
- **Pattern**: Ports & Adapters (Hexagonal Architecture), folder layout aligned to Siloam AI Research Template
- **Ports** (ABCs): `app/ports/embedding_port.py`, `app/ports/vector_store_port.py`, `app/ports/messaging_port.py`, `app/ports/llm_port.py`
- **Adapters**:
  - `app/generative/engine.py` — GeminiEmbeddingAdapter (google-genai) + GeminiChatAdapter (langchain-google-genai ChatGoogleGenerativeAI)
  - `config/typesenseDb.py` — TypesenseVectorStoreAdapter (Siloam convention: `config/*Db.py`)
  - `config/messaging.py` — WPPConnectMessagingAdapter (external service in `config/`)
- **Container**: `config/container.py` — lazy singleton factory, `get_embedding()`, `get_vector_store()`, `get_messaging()`, `get_llm()` + `set_*()` for testing
- **Services** use `from config import container` then `container.get_*()` — no direct dependency on concrete implementations
- `WhatsAppService` is a thin facade delegating to `container.get_messaging()` + `BotLogicService`
- Routing uses `config/routes.py` `setup_routes(app)` + `routes/api/v1.py` aggregator
- Middleware uses `config/middleware.py` `setup_middleware(app)`
- All shared resources preloaded at startup in lifespan (no lazy cold-start for first user)

## Key Files
- `config/container.py` — swap adapters here to change providers
- `config/typesenseDb.py` — Typesense vector store adapter
- `config/routes.py` — centralized route registration (Siloam pattern)
- `config/middleware.py` — middleware setup (Siloam pattern)
- `app/Kernel.py` — app factory, lifespan manager (preloads all shared resources)
- `app/services/` — business logic (embedding HyDE, search, FAQ CRUD, bot logic, agent reranking)
- `app/ports/` — abstract interfaces (EmbeddingPort, VectorStorePort, MessagingPort, LLMPort)
- `app/generative/engine.py` — AI/ML engine adapters (embedding + chat)
- `app/controllers/agent_controller.py` — Siloam-pattern singleton controller for agent mode
- `config/settings.py` — env vars via Pydantic BaseSettings
- `config/constants.py` — magic numbers (thresholds, limits, model names)

## Vector Database: Typesense (V2.3+)
- **Why**: Production-grade, no SQLite locks, Siloam standard
- **Collection**: `hospital_faq_kb`
- **Embedding dim**: 3072 (gemini-embedding-001)
- **Port**: 8118 (external) / 8108 (Docker internal)
- **API Key**: Set in `.env` as `TYPESENSE_API_KEY`
- Uses `multi_search` API for large embedding vectors

## LLM / Agent Mode (V2.4)
- `LLMPort` has `generate()` (free text) + `generate_structured()` (Pydantic output via `with_structured_output()`)
- `GeminiChatAdapter` uses `ChatGoogleGenerativeAI` from `langchain-google-genai` (NOT raw `google-genai`)
- Model: `gemini-3-flash-preview` (default), `gemini-3-pro-preview` (high-precision)
- Agent service uses `generate_structured(prompt, RerankOutput)` — no manual JSON parsing
- Agent prompts in `app/services/agent_prompts.py`, schemas in `app/schemas/agent_schema.py`
- `requirements.txt` has both `google-genai` (embedding) and `langchain-google-genai` (chat/LLM)
- **Search modes**: "immediate" (vector top-1, 41% threshold) vs "agent" (LLM grading, 30% confidence)
- **Mode toggle**: `core/bot_config.py` → `data/bot_config.json`, configurable in admin UI
- **LangSmith tracing**: Automatic via `LANGSMITH_*` env vars

## Embedding (V2.4)
- **Single source**: `EmbeddingService._build_document_text()`
- **Method**: `EmbeddingService.build_faq_document()` returns `(embedding, document_text)`
- **Template fields**: `MODUL`, `TOPIK`, `TERKAIT`, `ISI KONTEN`
- **Asymmetric retrieval**: Documents use `RETRIEVAL_DOCUMENT` task type, queries use `RETRIEVAL_QUERY`
- Embedding model: `gemini-embedding-001` (3072-dim)

## Group Module Whitelist (V2.3.1)
- **Feature**: Per-group module filtering for WhatsApp bot
- **Storage**: `data/group_config.json`
- **Service**: `core/group_config.py` — GroupConfig class
- **Auto-registration**: Groups register on first @faq mention (default: all modules)
- **Admin UI**: Tab 6 in admin console (`🏢 Group Settings`)
- **DM behavior**: Always all modules (no filter)
- **WPPConnect enhancement**: `messaging.get_group_name()` fetches name from API

## User Preferences
- No "Future TODO" comments — if it can be done now, do it now
- Siloam alignment is priority (folder layout, patterns, conventions)
- Preload everything at startup, no cold-start for first user
- Always use latest model versions (e.g., `gemini-3-flash-preview`)

## Gotchas
- Streamlit apps import services directly (not via API)
- Win32 platform: use `rm` not `del` in bash tool
- **Local dev uses Typesense** — run `docker compose up typesense -d` and set `TYPESENSE_HOST=localhost`, `TYPESENSE_PORT=8118` in `.env`
- Old top-level `ports/`, `adapters/`, `container.py` were DELETED
- `config/database.py` was DELETED — absorbed into adapters + container
- `config/chromaDb.py` was DELETED (V2.3) — replaced by Typesense
- **Windows: set PYTHONPATH before Streamlit** — `$env:PYTHONPATH=\".\"`
- **Windows: WPPConnect can't build** — use partial stack or run bot with Python
- **Bot Tester** (`streamlit_apps/bot_tester.py`) — test bot logic without WPPConnect

## Documentation Index
- **`docs/SYSTEM_OVERVIEW.md`** — Complete current-state overview (START HERE)
- **`docs/MEMORY.md`** — This file, quick reference for AI agents
- **`docs/REFACTORING_V2.1-V2.4`** — Historical changelogs per version
- **`docs/COMPLETE_SYSTEM_SPECIFICATION*.md`** — ⚠️ OUTDATED (still references ChromaDB)

