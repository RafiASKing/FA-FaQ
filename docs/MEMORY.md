# Project Memory - Hospital FAQ Retriever (FA-FaQ) v3.1

> Quick reference for AI coding agents. For complete context, read `docs/SYSTEM_OVERVIEW.md` first.

## Architecture Snapshot
- Pattern: Ports & Adapters (Hexagonal), Siloam AI Research template
- Ports (ABCs):
  - `app/ports/embedding_port.py`
  - `app/ports/vector_store_port.py`
  - `app/ports/llm_port.py`
  - `app/ports/messaging_port.py`
- Main adapters:
  - `app/generative/engine.py` (Gemini embedding + chat)
  - `config/typesenseDb.py` (Typesense vector adapter)
  - `config/messaging.py` (WPPConnect adapter, all-chats cache)
- DI entrypoint: `config/container.py`

## Current Runtime Modes
- Immediate: vector top-1 + threshold 70
- Agent Flash: top-7 + Gemini Flash + confidence threshold
- Agent Pro: top-7 + Gemini Pro + confidence threshold
- Runtime mode source: `data/bot_config.json`

## Security & Hardening (v3.1 docs state)
- API key dependency: `app/dependencies/auth.py`
- Applied at API v1 aggregator: `routes/api/v1.py` (`/api/v1/*`)
- Header: `X-API-Key`
- Env primary key: `APP_API_KEY` (legacy fallback `API_KEY`)
- Search error hardening:
  - Sanitized client message with ref code in `app/controllers/search_controller.py`
  - Internal traceback logging via `core/logger.py` (`log_error`)
  - Custom exceptions in `core/exceptions.py`

## Key Files to Touch First
- `config/settings.py` (env parsing)
- `config/constants.py` (thresholds/models)
- `app/Kernel.py` (lifespan preload)
- `app/services/search_service.py`
- `app/services/agent_service.py`
- `app/controllers/search_controller.py`
- `core/logger.py`
- `core/group_config.py`, `core/bot_config.py`

## Vector & LLM Facts
- Typesense collection: `hospital_faq_kb`
- Embedding dimension: 3072 (`gemini-embedding-001`)
- Scoring function currently: `max(0, (1 - distance) * 100)`
- Agent structured output model: `RerankOutput`

## Testing State
- Latest local validation: `29 passed`
- New focused tests added:
  - `tests/test_services/test_search_service.py`
  - `tests/test_services/test_faq_service.py`
  - `tests/test_core/test_group_config.py`
  - `tests/test_controllers/test_auth_search_api.py`

## Deployment Notes
- Production: AWS Lightsail + Nginx + SSL
- Compose command depends on host:
  - Windows: `docker compose`
  - Lightsail/legacy servers: `docker-compose`
- Env refresh rule: `docker-compose restart` does not reload `.env`; use `up -d`
- WPPConnect 2.8.11: do not rely on `/chat/{id}`; use cached `/all-chats`

## Windows Local Gotchas
- Common partial stack: `typesense + faq-web-v2 + faq-admin + faq-user`
- WPP/bot image build may be skipped on Windows environments
- Healthchecks are now explicitly configured per service in `docker-compose.yml` (correct internal ports)

## Working Preferences (Keep)
- Keep Siloam-aligned architecture
- Do not add speculative “future TODO” comments
- Keep startup preload behavior
- Prefer newest stable model constants
- Use class name `FaqService` (not `FAQService`)

## Doc Index
- `docs/REFACTORING_V3.1_DOCS_UPDATE.md` — v3.1 documentation alignment update
- `docs/SYSTEM_OVERVIEW.md` — full current-state overview (v3.1)
- `docs/MEMORY.md` — this quick reference
- `docs/REFACTORING_V3.0_RELEASE.md` — v3.0 production rollout notes
- `docs/REFACTORING_V2.1*` to `V2.5*` — historical migration logs
