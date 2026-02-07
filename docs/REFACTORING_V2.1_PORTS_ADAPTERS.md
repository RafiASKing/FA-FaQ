# V2.1 Refactoring — Ports & Adapters + Siloam Alignment + LangChain

## What Changed and Why

### Problem Statement
After V2.0, the app had clean layering (controllers/services/schemas) but all 3 external dependencies — **embedding model** (Google Gemini), **vector database** (ChromaDB), and **messaging provider** (WPPConnect) — were hardcoded into services. Switching any of them meant rewriting multiple files. Additionally, the folder layout didn't match the Siloam AI Research Template, making it harder to onboard team members familiar with that template.

### What We Did (in order)

#### Phase 1: Ports & Adapters Architecture
Created abstract interfaces (Ports) and concrete implementations (Adapters) so swapping external dependencies becomes a one-line change in `container.py`.

**Ports created** (abstract interfaces):
- `EmbeddingPort` — `embed(text) -> List[float]`
- `VectorStorePort` — `query()`, `get_all()`, `get_by_id()`, `upsert()`, `delete()`, `get_all_ids()`
- `MessagingPort` — `initialize()`, `send_text()`, `send_image()`, `send_images()`
- `LLMPort` — `generate()`, `generate_structured()`

**Adapters created** (concrete implementations):
- `GeminiEmbeddingAdapter` — Google Gemini embedding via `google-genai` SDK
- `GeminiChatAdapter` — Google Gemini chat via `langchain-google-genai` (ChatGoogleGenerativeAI)
- `ChromaDBVectorStoreAdapter` — ChromaDB with normalized return types
- `WPPConnectMessagingAdapter` — WPPConnect WhatsApp API

**Container** (`config/container.py`) — lazy singleton factory:
- `get_embedding()`, `get_vector_store()`, `get_messaging()`, `get_llm()`
- `set_*()` overrides for testing
- All config read lazily inside getters (imports `settings` inside functions)

#### Phase 2: Siloam Folder Alignment
Moved files from generic locations to Siloam-convention locations:

| Before (generic) | After (Siloam-aligned) | Convention |
|---|---|---|
| `ports/` (top-level) | `app/ports/` | Domain interfaces in `app/` |
| `adapters/gemini_embedding.py` | `app/generative/engine.py` | AI/ML engines in `app/generative/` |
| `adapters/chroma_vector_store.py` | `config/chromaDb.py` | DB adapters in `config/*Db.py` |
| `adapters/wppconnect_messaging.py` | `config/messaging.py` | External services in `config/` |
| `container.py` (root) | `config/container.py` | Config wiring in `config/` |

#### Phase 3: Routing & Middleware Extraction
Extracted from `Kernel.py` into dedicated files following Siloam pattern:
- `config/routes.py` — `setup_routes(app, include_bot_routes, include_web_routes)`
- `config/middleware.py` — `setup_middleware(app)`

This made `Kernel.py` a clean app factory — just creates FastAPI, calls setup functions, done.

#### Phase 4: Startup Preloading
**Problem**: Lazy initialization means the first user experiences cold-start (slow first request).
**Fix**: Added eager preloading in FastAPI lifespan — all shared resources initialized at startup:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    container.get_vector_store()   # preload
    container.get_embedding()      # preload
    container.get_llm()            # preload
    yield
```

#### Phase 5: Agent Mode Scaffolding
Created LLM-powered document reranking (agent mode) following Siloam patterns:
- `app/services/agent_service.py` — reranking logic (service provides node methods)
- `app/services/agent_prompts.py` — separated prompt templates
- `app/schemas/agent_schema.py` — Pydantic schemas (double duty: LLM structured output + API response)
- `app/controllers/agent_controller.py` — Siloam-pattern singleton controller

#### Phase 6: LangChain Structured Output (google-genai → langchain-google-genai)
**Before**: `GeminiChatAdapter` used raw `google-genai` SDK. Agent service manually parsed JSON from LLM response with regex fallback — brittle and error-prone.
**After**: `GeminiChatAdapter` uses `ChatGoogleGenerativeAI` from `langchain-google-genai`. New `generate_structured()` method uses `with_structured_output(PydanticSchema)` — LLM returns a validated Pydantic object directly.

What was removed:
- `json` and `re` imports from `agent_service.py`
- `_parse_rerank_response()` method (entire manual JSON parser)
- All "Future (LangChain)" TODO comments — it's the present now

What was added:
- `langchain-google-genai` to `requirements.txt`
- `generate_structured()` to `LLMPort` interface
- `with_structured_output()` call in `GeminiChatAdapter`

---

## Files Deleted

| File | Reason |
|---|---|
| `config/database.py` | Logic absorbed by `ChromaDBVectorStoreAdapter` + `GeminiEmbeddingAdapter` + `container.py` |
| `ports/` (top-level) | Moved to `app/ports/` |
| `adapters/` (top-level) | Split into `app/generative/engine.py`, `config/chromaDb.py`, `config/messaging.py` |
| `container.py` (root) | Moved to `config/container.py` |

---

## Current Architecture

```
eighthExperiment/
├── app/
│   ├── Kernel.py                      # App factory + lifespan (preloads resources)
│   ├── ports/                         # Abstract interfaces (ABCs)
│   │   ├── embedding_port.py          # EmbeddingPort
│   │   ├── vector_store_port.py       # VectorStorePort + VectorSearchResult/VectorDocument
│   │   ├── messaging_port.py          # MessagingPort
│   │   └── llm_port.py               # LLMPort (generate + generate_structured)
│   ├── generative/
│   │   └── engine.py                  # GeminiEmbeddingAdapter + GeminiChatAdapter (LangChain)
│   ├── controllers/
│   │   ├── search_controller.py
│   │   ├── faq_controller.py
│   │   ├── webhook_controller.py
│   │   └── agent_controller.py        # Siloam singleton pattern
│   ├── services/
│   │   ├── embedding_service.py       # HyDE logic (uses container.get_embedding())
│   │   ├── search_service.py          # Semantic search (uses container.get_vector_store())
│   │   ├── faq_service.py             # CRUD (uses container.get_vector_store())
│   │   ├── whatsapp_service.py        # WhatsAppService facade + BotLogicService
│   │   ├── agent_service.py           # LLM reranking (uses container.get_llm().generate_structured())
│   │   └── agent_prompts.py           # Separated prompt templates
│   └── schemas/
│       ├── faq_schema.py
│       ├── search_schema.py
│       ├── webhook_schema.py
│       └── agent_schema.py            # RerankOutput (LLM output + API response)
├── config/
│   ├── settings.py                    # Pydantic BaseSettings (env vars)
│   ├── constants.py                   # Magic numbers + model names
│   ├── container.py                   # Dependency wiring (swap adapters here)
│   ├── routes.py                      # setup_routes(app)
│   ├── middleware.py                   # setup_middleware(app)
│   ├── chromaDb.py                    # ChromaDBVectorStoreAdapter
│   └── messaging.py                   # WPPConnectMessagingAdapter
├── routes/
│   └── api/v1.py                      # API router aggregator
├── core/                              # Utilities (unchanged)
├── streamlit_apps/                    # Streamlit UIs (unchanged)
└── docs/
```

---

## How to Swap Dependencies

### Switch embedding model (e.g., to Gemma or OpenAI):
1. Create new adapter in `app/generative/` implementing `EmbeddingPort`
2. Change `container.py` → `get_embedding()` to return new adapter
3. Done. Zero service changes.

### Switch vector database (e.g., to Typesense):
1. Create `config/typesenseDb.py` implementing `VectorStorePort`
2. Change `container.py` → `get_vector_store()` to return new adapter
3. Done. Zero service changes.

### Switch WhatsApp provider (e.g., to WAHA or Meta Cloud API):
1. Create `config/waha_messaging.py` implementing `MessagingPort`
2. Update `app/schemas/webhook_schema.py` for new webhook payload format
3. Change `container.py` → `get_messaging()` to return new adapter
4. Done.

### Switch LLM (e.g., to OpenAI or local Ollama):
1. Create new adapter implementing `LLMPort` (both `generate` and `generate_structured`)
2. Change `container.py` → `get_llm()` to return new adapter
3. Done. Agent service doesn't care which LLM is behind the port.

---

## Problems Encountered

1. **Win32 shell**: `del` command doesn't exist in bash on Windows. Use `rm` instead.
2. **Lazy init cold-start**: First user gets slow response because shared resources initialize on first use. Fixed by preloading in FastAPI lifespan.
3. **ChromaDB embedded vs server mode**: `.env` must have `CHROMA_HOST`/`CHROMA_PORT` commented out for local embedded mode (PersistentClient). Uncomment for Docker/server mode (HttpClient).
4. **Import paths after reorganization**: All `import container` had to become `from config import container` across every service file.
5. **Manual JSON parsing brittleness**: Before LangChain, the agent had to regex-parse JSON from LLM free-text output. `with_structured_output()` eliminates this entirely.
6. **Model name outdated**: `gemini-2.0-flash` → `gemini-2.5-flash` in constants.

---

## Key Design Decisions

### Why Ports & Adapters (not just refactoring services)?
Services should not know or care which embedding model, database, or messaging provider is being used. The port defines *what* is needed (the contract), the adapter provides *how* (the implementation). This is critical for a project that may switch from ChromaDB to Typesense, or from WPPConnect to WAHA.

### Why container module (not a DI framework)?
A simple module with `get_*()` functions is sufficient. No need for `dependency-injector` or similar frameworks. The container is just a few lazy getters — easy to understand, easy to swap.

### Why LangChain for LLM but not for embedding?
Embedding uses `google-genai` directly because `embed_content()` is simple and doesn't benefit from LangChain abstraction. Chat/LLM uses LangChain because `with_structured_output()` eliminates manual JSON parsing and provides type-safe Pydantic responses — a significant benefit for agent mode.

### Why preload at startup instead of lazy init?
Lazy init means the first user pays the initialization cost (cold-start). Since this is a shared service (not serverless/lambda), we want all resources ready before the first request arrives. The lifespan context manager handles this.

### Why Siloam folder layout?
Team alignment. Engineers familiar with the Siloam AI Research Template can navigate this project immediately: `app/generative/` for AI engines, `config/*Db.py` for database adapters, `config/routes.py` for route setup, etc.

---

## What I Learned About the User's Preferences

1. **Siloam alignment is priority** — Folder layout and patterns should match the Siloam AI Research Template as closely as possible. This isn't just cosmetic; it's about team familiarity.
2. **No "future TODO" comments** — If something can be done now (like LangChain structured output), do it now. Don't leave "Future:" comments as placeholders.
3. **Clean is better than clever** — Simple module-level container over DI frameworks. Clean Kernel.py that delegates to setup functions. No over-engineering.
4. **Preload everything** — Don't make the first user suffer cold-start. Initialize shared resources at startup.
5. **Agent mode is a future priority** — The scaffolding (prompts, schemas, service, controller) should be ready so adding LangGraph agents later is straightforward.
6. **Documentation matters for session continuity** — When context is lost (new session), docs should capture enough context that the user doesn't need to re-explain from scratch.
7. **Model names must be current** — Always use the latest model versions (e.g., `gemini-2.5-flash`, not `2.0`).

---

## Dependencies Added

| Package | Purpose |
|---|---|
| `langchain-google-genai` | ChatGoogleGenerativeAI + with_structured_output() for agent mode |

Note: `google-genai` is still used for embedding (GeminiEmbeddingAdapter). Both coexist.

---

## Verification Checklist

- [ ] `pip install -r requirements.txt` — installs `langchain-google-genai`
- [ ] `python main.py api` — API server starts, `/api/v1/search`, `/api/v1/faq`, `/api/v1/agent/rerank` work
- [ ] `python main.py web` — Web mode works, search via browser
- [ ] `python main.py bot` — Bot mode starts, token generation logs appear
- [ ] `streamlit run streamlit_apps/user_app.py` — Streamlit search works
- [ ] `streamlit run streamlit_apps/admin_app.py` — Streamlit admin works
- [ ] Agent endpoint `POST /api/v1/agent/rerank` returns structured `RerankOutput`
