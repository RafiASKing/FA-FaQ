# V2.2 Release Notes — Windows Local Dev + Bot Tester

## Overview

This release focuses on improving local development experience, especially on **Windows**, and adding a **Bot Tester** Streamlit app for testing bot logic without WPPConnect.

---

## What Changed

### 1. ChromaDB Server Mode for Local Dev

**Problem**: Embedded ChromaDB mode (PersistentClient) crashes even with `retry_on_lock` wrapper.

**Solution**: Use ChromaDB server mode for all local development.

```bash
# Start ChromaDB container
docker compose up chroma-server -d

# Configure .env
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

**Files changed**:
- `.env.example` — Now shows server mode as default
- `docs/LOCAL_DEV_GUIDE.md` — Updated instructions
- `docs/MEMORY.md` — Updated gotchas

---

### 2. Dockerfile PYTHONPATH Fix

**Problem**: Streamlit apps in Docker failed with `ModuleNotFoundError: No module named 'app'`.

**Cause**: When Streamlit runs from `streamlit_apps/`, Python doesn't know to look in `/app` for modules.

**Solution**: Added `ENV PYTHONPATH=/app` to Dockerfile.

```dockerfile
WORKDIR /app
ENV PYTHONPATH=/app  # <-- Added
```

**Files changed**:
- `Dockerfile`

---

### 3. Windows: WPPConnect Can't Build

**Problem**: On Windows, Docker can't build from Git URL:
```
failed to evaluate path "https://github.com/wppconnect-team/wppconnect-server.git"
```

**Solution**: Use partial stack on Windows (skip WPPConnect and Bot):
```bash
docker compose up --build -d chroma-server faq-web-v2 faq-admin faq-user
```

**Files changed**:
- `docs/LOCAL_DEV_GUIDE.md` — Added Windows-specific notes

---

### 4. Bot Tester Streamlit App (NEW)

**Problem**: Testing bot logic locally requires:
- Running bot server with `python main.py bot`
- Sending webhook payloads via curl/Postman
- Getting WPPConnect errors in logs (expected but noisy)

**Solution**: Created `streamlit_apps/bot_tester.py` — a visual bot simulator.

Features:
- Toggle Private / Group mode
- Shows if bot would reply (based on `@faq` detection)
- Displays search results with relevance scores
- Previews images that would be attached
- Debug panel with raw data
- **No WPPConnect errors** — calls `SearchService` directly

```powershell
$env:PYTHONPATH="."
streamlit run streamlit_apps/bot_tester.py --server.port 8503
```

**Files added**:
- `streamlit_apps/bot_tester.py`

**Files changed**:
- `docs/LOCAL_DEV_GUIDE.md` — Added Bot Tester section

---

### 5. Repository Renamed

**Change**: Repository renamed from `eighthExperiment` to `FA-FaQ`.

```bash
git remote set-url origin https://github.com/RafiASKing/FA-FaQ.git
```

> Note: Local folder name and Lightsail folder can stay as `eighthExperiment` — git doesn't care about folder names.

**Files changed**:
- `docs/MEMORY.md`
- `docs/REFACTORING_V2.1_PORTS_ADAPTERS.md`
- `docs/COMPLETE_SYSTEM_SPECIFICATION.md`
- `docs/COMPLETE_SYSTEM_SPECIFICATION_V2.md`
- `nginx/notes_nginx.md` — Kept `eighthExperiment` path for Lightsail compatibility

---

## Port Map (Local Dev)

| Port | Service | Command |
|------|---------|---------|
| 8000 | ChromaDB | `docker compose up chroma-server` |
| 8001 | API / Bot | `python main.py api --port 8001` |
| 8080 | Web V2 | `python main.py web` |
| 8501 | User App | `streamlit run streamlit_apps/user_app.py` |
| 8502 | Admin App | `streamlit run streamlit_apps/admin_app.py` |
| 8503 | Bot Tester | `streamlit run streamlit_apps/bot_tester.py` |

---

## Windows Quick Start

```powershell
# 1. Start ChromaDB
docker compose up chroma-server -d

# 2. Activate venv
.\venv\Scripts\activate

# 3. Set PYTHONPATH (required for Streamlit)
$env:PYTHONPATH="."

# 4. Run any app
streamlit run streamlit_apps/bot_tester.py --server.port 8503
python main.py api --port 8001
python main.py web
```

---

## Files Summary

| Action | File |
|--------|------|
| Modified | `Dockerfile` |
| Modified | `.env.example` |
| Modified | `docs/LOCAL_DEV_GUIDE.md` |
| Modified | `docs/MEMORY.md` |
| Modified | `docs/REFACTORING_V2.1_PORTS_ADAPTERS.md` |
| Modified | `docs/COMPLETE_SYSTEM_SPECIFICATION.md` |
| Modified | `docs/COMPLETE_SYSTEM_SPECIFICATION_V2.md` |
| Added | `streamlit_apps/bot_tester.py` |
| Added | `docs/REFACTORING_V2.2_WINDOWS_BOT_TESTER.md` (this file) |
