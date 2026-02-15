# v3.0 Release — Production Deployment & Hardening

> **Date**: 2026-02-15
> **Previous**: v2.5 (Production Hardening batch 1)
> **Deployed to**: AWS Lightsail (`faq-assist.cloud`)

---

## Summary

v3.0 takes the system from local development to **live production** on AWS Lightsail. Major areas: LLM prompt quality, search analytics, production safety, and full Docker deployment with ChromaDB → Typesense migration.

---

## Changes

### 1. LLM Agent Prompt Overhaul
- **Tag descriptions in prompt**: `ED` → `ED (IGD, Emergency, Triage, Ambulans)` via `TagManager.get_tag_description()`
- **Full document content**: Removed 300-char truncation. Now shows entire FAQ content to LLM (reduced candidates from 20 → 7 to compensate token budget)
- **HyDE keywords shown**: Keywords/user variations (`TERKAIT` field) now included in LLM prompt
- **Indonesian labels**: Changed prompt labels from English to Indonesian (MODUL, TOPIK, TERKAIT, ISI KONTEN)
- **Hospital EMR context**: System prompt now explains the domain (Siloam Hospitals, EMR system, department modules)
- **[GAMBAR X] tags kept**: Not stripped — gives LLM context about visual aids in documents
- **Single-candidate bypass removed**: All candidates go through LLM grading (previously top-1 skipped LLM)

### 2. Three Search Modes (was two)
- **Immediate**: Vector top-1, 70% threshold, no waiting message
- **Agent Flash** (`gemini-3-flash-preview`): LLM grades top 7, waiting msg "Baik, mohon ditunggu", 30s timeout
- **Agent Pro** (`gemini-3-pro-preview`): LLM grades top 7, waiting msg "Baik, mohon ditunggu...", 60s timeout
- Confidence threshold configurable in admin UI for both agent modes (was only Flash)

### 3. Search Analytics
- **Search log** (`data/search_log.csv`): All queries logged with score, FAQ hit, mode, response time, source (web/whatsapp)
- **Failed search log** (`data/failed_searches.csv`): Enhanced to 10 columns — includes reason, rejected top-1 info, agent reasoning
- **Rejected candidate diagnostics**: Even when all candidates are below threshold, the rejected top-1 is still fetched (with `min_score=0`) and logged for analysis
- **Web searches now logged**: Previously only WhatsApp logged analytics
- **Admin analytics dashboard**: KPI metrics, daily query chart, score distribution, top FAQs, mode/source split, recent queries table

### 4. Production Safety
- **Atomic file writes**: `bot_config.json` and `group_config.json` use `tempfile.mkstemp()` + `os.replace()` — prevents JSON corruption on concurrent writes
- **bcrypt auth with fallback**: Admin login tries bcrypt hash first, falls back to plain-text for dev environments
- **Typed exceptions**: All bare `except:` replaced with `except Exception:` across 9 files
- **print() → log()**: Replaced all `print()` calls with structured `log()` (engine.py, faq_service.py, tag_manager.py, image_handler.py)
- **Non-root Docker**: Runs as `fafaq` user, only `/app/data` and `/app/images` writable
- **Preloads both LLM models**: Flash + Pro preloaded at startup (was only Flash)

### 5. WPPConnect v2.8.11 Compatibility
- **Group name lookup**: Uses `/api/{session}/all-chats` with 5-minute in-memory cache (the `/chat/{id}` endpoint returns 404 on v2.8.11)
- **Group name auto-sync**: `register_group()` updates group name on every @mention (not just first registration)
- **WA_SESSION_KEY sync**: docker-compose.yml uses `${WA_SESSION_KEY}` variable substitution so WPPConnect's `SECRET_KEY` and bot's `WA_SESSION_KEY` always match
- **Webhook URL**: Configured in `wpp_sessions/config.json` → `http://faq-bot:8000/webhook/whatsapp`

### 6. Web UI
- **Light vibrant theme**: Changed from dark/gloomy CSS to clean light theme with orange gradient header
- **Templates at project root**: `templates/` and `static/` moved to root (was `web_v2/`)

### 7. Docker Deployment
- **6 containers**: typesense, wppconnect, faq-bot, faq-user, faq-admin, faq-web-v2
- **Migration script**: `scripts/migrate_chroma_to_typesense.py` (export from ChromaDB, import to Typesense with re-embedding)
- **`.dockerignore`**: Added `data/`, `docs/`, `scripts/`, `.env.*`
- **`.gitignore`**: Added runtime data files

### 8. Constants Updated
```python
RELEVANCE_THRESHOLD = 70          # was 41
AGENT_CANDIDATE_LIMIT = 7         # was 20
AGENT_MIN_SCORE = 50.0            # was 20.0
AGENT_CONFIDENCE_THRESHOLD = 0.5  # was 0.3
```

---

## Deployment Notes (Lessons Learned)

| Step | Claude's Instruction | What We Actually Did |
|------|---------------------|---------------------|
| Orchestration | `build` then `up -d` all | Database-First: Started typesense & wppconnect first to ensure DB was ready for import |
| Import Method | `docker-compose exec faq-bot ...` | One-off Task: Used `docker-compose run --rm faq-web-v2 ...` to avoid side effects on running bot |
| Missing Files | Assumed files were in image | Volume Mounting: Used `-v "$(pwd):/app"` because migration script was excluded by .dockerignore |
| Code Bug | Assumed `FAQService` name | Code Patching: Used `sed` to change `FAQService` to `FaqService` (case-sensitive match) |
| Webhook Fix | curl or automated | Manual Sync: Fixed `wpp_sessions/config.json` webhook URL to `/webhook/whatsapp` |
| Group IDs | Shell one-liner | Custom Script: Created `get_groups.py` because one-liner failed on server Python version |
| .env Reload | `docker-compose restart` | Must use `docker-compose up -d <service>` — restart does NOT re-read env_file |

---

## Files Changed

### New Files
- `scripts/migrate_chroma_to_typesense.py` — Migration tool
- `templates/` — Jinja2 HTML templates (moved from web_v2/)
- `static/style.css` — Light theme CSS
- `docs/REFACTORING_V3.0_RELEASE.md` — This file

### Deleted Files
- `web_v2/` — Replaced by root `templates/` + `static/`
- `docs/COMPLETE_SYSTEM_SPECIFICATION.md` — Outdated (moved to `docs/referensi/`)
- `docs/COMPLETE_SYSTEM_SPECIFICATION_V2.md` — Outdated (moved to `docs/referensi/`)

### Key Modified Files
- `app/services/agent_service.py` — Full content prompt, tag descriptions, removed single-candidate bypass
- `app/services/agent_prompts.py` — Hospital EMR context, HyDE explanation, Indonesian labels
- `app/controllers/webhook_controller.py` — Waiting messages, failed search diagnostics, agent mode routing
- `config/messaging.py` — Cached all-chats API for group names
- `config/constants.py` — Updated thresholds and limits
- `config/container.py` — Added `get_llm_pro()`, Pro model with 60s timeout
- `core/logger.py` — 10-column failed search log
- `core/bot_config.py` — Atomic writes, confidence threshold default 0.5
- `core/group_config.py` — Auto-sync group name, atomic writes
- `streamlit_apps/admin_app.py` — Analytics dashboard, bcrypt login, confidence slider for both modes
- `routes/web.py` — Search logging, failed search diagnostics
- `app/Kernel.py` — Preload LLM Pro at startup
- `docker-compose.yml` — WA_SESSION_KEY variable substitution
