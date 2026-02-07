# Project Memory - Hospital FAQ Retriever (eighthExperiment)

## Architecture (Siloam-aligned Ports & Adapters)
- **Pattern**: Ports & Adapters (Hexagonal Architecture), folder layout aligned to Siloam AI Research Template
- **Ports** (ABCs): `app/ports/embedding_port.py`, `app/ports/vector_store_port.py`, `app/ports/messaging_port.py`, `app/ports/llm_port.py`
- **Adapters**:
  - `app/generative/engine.py` — GeminiEmbeddingAdapter (google-genai) + GeminiChatAdapter (langchain-google-genai ChatGoogleGenerativeAI)
  - `config/chromaDb.py` — ChromaDBVectorStoreAdapter (Siloam convention: `config/*Db.py`)
  - `config/messaging.py` — WPPConnectMessagingAdapter (external service in `config/`)
- **Container**: `config/container.py` — lazy singleton factory, `get_embedding()`, `get_vector_store()`, `get_messaging()`, `get_llm()` + `set_*()` for testing
- **Services** use `from config import container` then `container.get_*()` — no direct dependency on concrete implementations
- `retry_on_lock` lives ONLY in `config/chromaDb.py` (SQLite concern)
- `WhatsAppService` is a thin facade delegating to `container.get_messaging()` + `BotLogicService`
- Routing uses `config/routes.py` `setup_routes(app)` + `routes/api/v1.py` aggregator
- Middleware uses `config/middleware.py` `setup_middleware(app)`
- All shared resources preloaded at startup in lifespan (no lazy cold-start for first user)

## Key Files
- `config/container.py` — swap adapters here to change providers
- `config/routes.py` — centralized route registration (Siloam pattern)
- `config/middleware.py` — middleware setup (Siloam pattern)
- `app/Kernel.py` — app factory, lifespan manager (preloads all shared resources)
- `app/services/` — business logic (embedding HyDE, search, FAQ CRUD, bot logic, agent reranking)
- `app/ports/` — abstract interfaces (EmbeddingPort, VectorStorePort, MessagingPort, LLMPort)
- `app/generative/engine.py` — AI/ML engine adapters (embedding + chat)
- `app/controllers/agent_controller.py` — Siloam-pattern singleton controller for agent mode
- `config/settings.py` — env vars via Pydantic BaseSettings
- `config/constants.py` — magic numbers (thresholds, limits, model names)

## LLM / Agent
- `LLMPort` has `generate()` (free text) + `generate_structured()` (Pydantic output via `with_structured_output()`)
- `GeminiChatAdapter` uses `ChatGoogleGenerativeAI` from `langchain-google-genai` (NOT raw `google-genai`)
- Agent service uses `generate_structured(prompt, RerankOutput)` — no manual JSON parsing
- Agent prompts in `app/services/agent_prompts.py`, schemas in `app/schemas/agent_schema.py`
- `requirements.txt` has both `google-genai` (embedding) and `langchain-google-genai` (chat/LLM)

## User Preferences
- No "Future TODO" comments — if it can be done now, do it now
- Siloam alignment is priority (folder layout, patterns, conventions)
- Preload everything at startup, no cold-start for first user
- Documentation for session continuity: `docs/REFACTORING_V2.1_PORTS_ADAPTERS.md`
- Always use latest model versions (e.g., `gemini-2.5-flash`)

## Gotchas
- Streamlit apps import services directly (not via API)
- Win32 platform: use `rm` not `del` in bash tool
- **Local dev uses ChromaDB server mode** — run `docker compose up chroma-server -d` and set `CHROMA_HOST=localhost`, `CHROMA_PORT=8000` in `.env`
- Embedded ChromaDB mode is NOT recommended — crashes even with `retry_on_lock`
- Old top-level `ports/`, `adapters/`, `container.py` were DELETED
- `config/database.py` was DELETED — absorbed into adapters + container
