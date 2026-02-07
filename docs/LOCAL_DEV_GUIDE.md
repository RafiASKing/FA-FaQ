# Local Development Guide

## Prerequisites

- Python 3.10+
- pip (package manager)
- Docker & Docker Compose (optional, for full stack)
- Google API Key (Gemini)

## Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `fastapi`, `chromadb`, `google-genai`, `langchain-google-genai`, `streamlit`, `pydantic-settings`

## Environment Setup

Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

Required env vars:
| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `ADMIN_PASSWORD_HASH` | Yes | Bcrypt hash for admin login |
| `CHROMA_HOST` | Local dev: Yes | ChromaDB host (`localhost` for local server mode) |
| `CHROMA_PORT` | Local dev: Yes | ChromaDB port (default: `8000`) |
| `WA_BASE_URL` | Bot only | WPPConnect server URL |
| `WA_SESSION_KEY` | Bot only | WPPConnect auth token |
| `BOT_IDENTITIES` | Bot only | Bot phone number JIDs (comma-separated) |

---

## Running Locally (ChromaDB Server Mode - Recommended)

> **Why server mode?** Embedded mode (PersistentClient) has been unreliable — crashes occur even with `retry_on_lock` wrapper. Running ChromaDB as a container provides better stability.

### Step 1: Start ChromaDB Server

```bash
# Start only the ChromaDB container
docker compose up chroma-server -d
```

This starts ChromaDB on **port 8000** with data persisted to `data/chroma_data/`.

### Step 2: Configure .env for Server Mode

Make sure your `.env` has:
```ini
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

### Step 3: Run Python Apps (outside Docker)

Each command needs its own terminal:

```bash
# API Server (port 8000 conflicts with Chroma — use 8001)
python main.py api --port 8001

# Web Frontend (port 8080) — HTML/CSS search page
python main.py web

# Admin Console (port 8502)
streamlit run streamlit_apps/admin_app.py --server.port 8502

# User Search App (port 8501)
streamlit run streamlit_apps/user_app.py --server.port 8501
```

Verify:
- API docs: http://localhost:8001/docs
- Web search: http://localhost:8080
- Admin: http://localhost:8502
- User app: http://localhost:8501
- Health check: http://localhost:8001/health

### Dev mode with auto-reload
```bash
python main.py api --port 8001 --reload
python main.py web --reload
```

---

## Running with Docker Compose

### Full stack (semua service)
```bash
docker-compose up --build
```

Services yang jalan:

| Service | Port | URL |
|---|---|---|
| ChromaDB | 8000 | (internal, no browser UI) |
| WPPConnect | 21465 | http://localhost:21465 |
| Bot Backend | 8005 | http://localhost:8005/docs |
| User Streamlit | 8501 | http://localhost:8501 |
| Admin Streamlit | 8502 | http://localhost:8502 |
| Web V2 | 8080 | http://localhost:8080 |

### Partial stack (tanpa WA — Recommended for Windows)

> **Windows limitation**: WPPConnect can't build from Git URL on Windows. Use partial stack instead.

```bash
docker compose up --build -d chroma-server faq-web-v2 faq-admin faq-user
```

Ini jalankan ChromaDB + Web + Admin + User tanpa WPPConnect dan Bot.

---

## Testing Bot Logic Locally (Tanpa WhatsApp)

### Kenapa WA tidak ditest di local?

1. **Double message**: WhatsApp support multi-device (1 HP + 4 linked devices). Kalau login di WPPConnect lokal DAN Lightsail dengan nomor yang sama, **kedua instance aktif bersamaan** — keduanya terima pesan masuk, keduanya proses, keduanya kirim jawaban. User terima 2x response yang sama.
2. **Ngrok needed**: WPPConnect lokal butuh webhook URL yang accessible dari internet (ngrok/cloudflare tunnel) supaya bisa kirim pesan masuk ke bot backend di laptop kamu.
3. **Solusi**: Test bot logic via curl/API, test WA integration langsung di prod.

### Apakah WPPConnect lokal bentrok dengan Lightsail?

**TIDAK bentrok**, selama kamu **tidak login/scan QR** di WPPConnect lokal. Kamu bisa:
- `docker-compose up` termasuk wppconnect — service jalan tapi idle (belum login)
- WPPConnect Lightsail tetap aktif karena session-nya independent
- Bentrok **HANYA** kalau kedua instance login dengan nomor WA yang sama

### Apa yang terjadi kalau nekat login WA di lokal + pakai ngrok?

Skenario: WPPConnect Lightsail sudah aktif, lalu kamu login WPPConnect lokal dengan nomor yang sama dan pakai ngrok supaya webhook bisa dijangkau.

1. WhatsApp mendaftarkan WPPConnect lokal sebagai **linked device baru** (tidak kick yang lama)
2. Kedua WPPConnect (lokal + Lightsail) **sama-sama menerima** setiap pesan masuk
3. Kedua instance trigger webhook ke masing-masing bot backend
4. Kedua bot proses query yang sama (search, embedding, dll)
5. Kedua bot kirim response ke user
6. **Hasil**: user terima jawaban dobel untuk setiap pertanyaan

Jadi: jangan login WA di lokal. Test bot logic pakai curl ke webhook endpoint (lihat di bawah).

### Cara test bot logic tanpa WA

**Option A: Hit webhook endpoint langsung (simulasi pesan masuk)**

Jalankan bot mode:
```bash
python main.py bot
```

Kirim simulated webhook payload pakai curl:

```bash
# Simulasi pesan private (DM)
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"event\": \"onMessage\", \"data\": {\"body\": \"cara daftar rawat jalan\", \"from\": \"6281234567890@c.us\", \"fromMe\": false, \"sender\": {\"id\": \"6281234567890@c.us\", \"pushname\": \"Test User\"}, \"isGroupMsg\": false, \"mentionedJidList\": []}}"

# Simulasi pesan grup dengan @faq
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d "{\"event\": \"onMessage\", \"data\": {\"body\": \"@faq jadwal dokter spesialis\", \"from\": \"120363XXX@g.us\", \"fromMe\": false, \"sender\": {\"id\": \"6281234567890@c.us\", \"pushname\": \"Test User\"}, \"isGroupMsg\": true, \"mentionedJidList\": []}}"
```

Response HTTP akan `{"status": "success", "message": "Message queued"}` (karena proses di background).
Cek **terminal logs** untuk melihat:
- Query cleaning
- Search results
- Response yang akan dikirim ke WA (send akan gagal karena WPPConnect tidak connected, tapi logic tetap jalan)

**Option B: Test search API langsung (skip WA entirely)**

```bash
# API search (sama dengan yang bot pakai internally)
curl "http://localhost:8000/api/v1/search?q=cara%20daftar%20rawat%20jalan&n_results=3"

# Search dengan filter tag
curl "http://localhost:8000/api/v1/search?q=jadwal%20dokter&tag=OPD&n_results=5"

# Agent rerank
curl -X POST http://localhost:8000/api/v1/agent/rerank \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"cara daftar rawat jalan\", \"top_n\": 3}"
```

Ini langsung test search + embedding + ChromaDB tanpa butuh WA sama sekali.

**Option C: Run pytest**

```bash
pytest tests/ -v
```

**Option D: Bot Tester Streamlit (RECOMMENDED for Windows)**

Gunakan Bot Tester — Streamlit app yang simulasi WhatsApp bot tanpa WPPConnect. **No errors in logs!**

```powershell
# Set PYTHONPATH (required for local Streamlit)
$env:PYTHONPATH="."
streamlit run streamlit_apps/bot_tester.py --server.port 8503
```

Open http://localhost:8503

Features:
- Toggle Private / Group mode
- Shows if bot would reply (based on `@faq` detection)
- Displays search results with relevance scores
- Previews images that would be attached
- Debug panel with raw data

> **Why Bot Tester?** Calls `SearchService` directly, bypassing webhook + WPPConnect. No network errors.

---

## Testing Strategy Summary

| Apa yang ditest | Di mana | Cara |
|---|---|---|
| Search, Embedding, ChromaDB | Local | `python main.py api` + curl/Postman/browser |
| Web UI | Local | `python main.py web` + browser |
| Admin CRUD | Local | `streamlit run streamlit_apps/admin_app.py` |
| Bot logic (parsing, search, response) | Local | **Bot Tester** (`streamlit_apps/bot_tester.py`) ✨ |
| Bot logic (via webhook) | Local | curl ke `/webhook/whatsapp` + cek logs |
| Bot WA send/receive (actual) | Prod (Lightsail) | Deploy, test dengan WA asli |
| Agent reranking (LLM) | Local | curl ke `/api/v1/agent/rerank` |
| Full integration | Prod | `docker-compose up` di Lightsail |

---

## Workflow: Local Dev → Prod

1. **Develop locally** (no Docker, embedded ChromaDB):
   ```bash
   python main.py api --reload
   ```
2. **Test API**: curl/Postman ke `localhost:8000/docs`
3. **Test web**: browser ke `localhost:8080`
4. **Test bot logic**: curl simulasi webhook, cek logs
5. **Commit & push** ke git
6. **Deploy ke Lightsail**:
   ```bash
   git pull
   docker-compose up --build -d
   ```
7. **Test WA** langsung di prod (karena WA session hanya ada di Lightsail)

---

## Port Map (All Modes)

| Port | Service | Mode |
|---|---|---|
| 8000 | ChromaDB (Docker) | `docker compose up chroma-server` |
| 8001 | FastAPI API / Bot | `python main.py api --port 8001` |
| 8080 | FastAPI Web V2 | `python main.py web` |
| 8501 | Streamlit User | `streamlit run streamlit_apps/user_app.py` |
| 8502 | Streamlit Admin | `streamlit run streamlit_apps/admin_app.py` |
| 8503 | Bot Tester | `streamlit run streamlit_apps/bot_tester.py` |
| 21465 | WPPConnect | Docker only (Linux/Lightsail) |

Note: ChromaDB uses port 8000, so API/Bot should use 8001 for local dev:
```bash
python main.py api --port 8001
python main.py bot --port 8001
```

---

## Windows-Specific Notes

1. **WPPConnect can't build on Windows** — use partial stack or run bot logic with Python directly
2. **PYTHONPATH required for Streamlit** — run `$env:PYTHONPATH="."` before `streamlit run`
3. **Use server mode for ChromaDB** — embedded mode crashes even with `retry_on_lock`

