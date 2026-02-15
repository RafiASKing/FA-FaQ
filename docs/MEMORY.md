# Project Memory - Hospital FAQ Retriever (FA-FaQ) v3.0

> Quick reference for AI coding agents. For full details see `docs/SYSTEM_OVERVIEW.md`.

## Architecture (Siloam-aligned Ports & Adapters)
- **Pattern**: Ports & Adapters (Hexagonal), Siloam AI Research Template
- **Ports** (ABCs): `app/ports/embedding_port.py`, `vector_store_port.py`, `messaging_port.py`, `llm_port.py`
- **Adapters**:
  - `app/generative/engine.py` — GeminiEmbeddingAdapter (google-genai) + GeminiChatAdapter (langchain-google-genai)
  - `config/typesenseDb.py` — TypesenseVectorStoreAdapter
  - `config/messaging.py` — WPPConnectMessagingAdapter (cached all-chats for group names, 5-min TTL)
- **Container**: `config/container.py` — `get_embedding()`, `get_vector_store()`, `get_messaging()`, `get_llm()`, `get_llm_pro()` + `set_*()` for tests
- Services use `from config import container` then `container.get_*()` — no direct dependency on concrete impls
- Routing: `config/routes.py` → `routes/api/v1.py` aggregator
- All shared resources preloaded at startup in lifespan (no cold-start)

## Key Files
- `config/container.py` — swap adapters to change providers
- `config/settings.py` — Pydantic BaseSettings (.env)
- `config/constants.py` — thresholds, model names, limits
- `app/Kernel.py` — FastAPI factory, lifespan (preloads ALL resources incl LLM Pro)
- `app/services/agent_service.py` — LLM grading (7 candidates, full content, tag descriptions)
- `app/services/agent_prompts.py` — Hospital EMR context prompt, Indonesian labels
- `core/bot_config.py` — runtime config (atomic writes via tempfile + os.replace)
- `core/group_config.py` — per-group module whitelist (atomic writes, auto-sync names)
- `core/logger.py` — 10-column failed search CSV + search log CSV

## Search Modes
- **Immediate**: vector top-1, 70% threshold, no waiting msg
- **Agent Flash** (`gemini-3-flash-preview`): LLM grades top 7, "Baik, mohon ditunggu", 30s timeout
- **Agent Pro** (`gemini-3-pro-preview`): LLM grades top 7, "Baik, mohon ditunggu...", 60s timeout
- Confidence threshold configurable for both agent modes (default 0.5)
- `AGENT_CANDIDATE_LIMIT=7`, `AGENT_MIN_SCORE=50.0`, `RELEVANCE_THRESHOLD=70`

## LLM / Agent
- `LLMPort` has `generate()` + `generate_structured()` (Pydantic via `with_structured_output()`)
- Agent prompt: tag descriptions (TagManager), HyDE keywords, full content, [GAMBAR X] tags kept
- `RerankOutput`: reasoning (str), best_id (str, "0" = no match), confidence (float)
- Both `google-genai` (embedding) and `langchain-google-genai` (chat/LLM) in requirements.txt

## Vector DB: Typesense
- Collection: `hospital_faq_kb`, 3072-dim (gemini-embedding-001), cosine distance
- Port: 8108 inside Docker, 8118 from host
- `get_all()`/`get_all_ids()` use pagination (250/page), `query()` uses `multi_search` API

## Deployment (Production)
- AWS Lightsail, Ubuntu 22.04, `faq-assist.cloud`, Nginx + Certbot SSL
- Docker Compose v1 (`docker-compose` command, not `docker compose`)
- 6 containers: typesense, wppconnect, faq-bot, faq-user, faq-admin, faq-web-v2
- `docker-compose restart` does NOT re-read .env — must use `docker-compose up -d`
- WPPConnect v2.8.11: SECRET_KEY synced via `${WA_SESSION_KEY}` in docker-compose.yml
- Webhook URL in `wpp_sessions/config.json` → `http://faq-bot:8000/webhook/whatsapp`

## Safety
- Atomic writes for bot_config.json, group_config.json
- TagManager: mtime-based cache (no disk I/O per query)
- bcrypt auth with plain-text fallback for dev
- Non-root Docker user `fafaq`
- Typed exceptions everywhere (no bare `except:`)

## User Preferences
- No "Future TODO" comments
- Siloam alignment is priority
- Preload everything at startup
- Always use latest model versions
- Class name is `FaqService` (not `FAQService`)

## Gotchas
- Streamlit apps import services directly (not via API)
- Win32 platform locally: use `rm` not `del` in bash tool
- WPPConnect `/chat/{id}` returns 404 on v2.8.11 — use `/all-chats` with cache
- TYPESENSE_PORT: 8108 inside Docker, 8118 from host
- Local dev: `docker compose up typesense -d`, set `TYPESENSE_HOST=localhost`, `TYPESENSE_PORT=8118`

## Documentation Index
- **`docs/SYSTEM_OVERVIEW.md`** — Complete current-state overview (START HERE)
- **`docs/MEMORY.md`** — This file, quick reference for AI agents
- **`docs/REFACTORING_V3.0_RELEASE.md`** — v3.0 changelog (current)
- **`docs/REFACTORING_V2.1-V2.5`** — Historical changelogs
