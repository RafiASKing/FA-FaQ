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
| `CHROMA_HOST` | No | ChromaDB host (comment out for local embedded mode) |
| `CHROMA_PORT` | No | ChromaDB port (comment out for local embedded mode) |
| `WA_BASE_URL` | Bot only | WPPConnect server URL |
| `WA_SESSION_KEY` | Bot only | WPPConnect auth token |
| `BOT_IDENTITIES` | Bot only | Bot phone number JIDs (comma-separated) |

---

## Running Locally (No Docker)

For local dev, **comment out** `CHROMA_HOST` and `CHROMA_PORT` in `.env` so ChromaDB uses embedded mode (PersistentClient at `data/chroma_data/`).

Each command needs its own terminal:

```bash
# API Server (port 8000) — search, FAQ CRUD, agent endpoints
python main.py api

# Web Frontend (port 8080) — HTML/CSS search page
python main.py web

# Admin Console (port 8502)
streamlit run streamlit_apps/admin_app.py --server.port 8502

# User Search App (port 8501)
streamlit run streamlit_apps/user_app.py --server.port 8501
```

Verify:
- API docs: http://localhost:8000/docs
- Web search: http://localhost:8080
- Admin: http://localhost:8502
- User app: http://localhost:8501
- Health check: http://localhost:8000/health

### Dev mode with auto-reload
```bash
python main.py api --reload
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

### Partial stack (tanpa WA)
```bash
docker-compose up chroma-server faq-web-v2 faq-admin faq-user
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

---

## Testing Strategy Summary

| Apa yang ditest | Di mana | Cara |
|---|---|---|
| Search, Embedding, ChromaDB | Local | `python main.py api` + curl/Postman/browser |
| Web UI | Local | `python main.py web` + browser |
| Admin CRUD | Local | `streamlit run streamlit_apps/admin_app.py` |
| Bot logic (parsing, search, response) | Local | curl ke `/webhook/whatsapp` + cek logs |
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
| 8000 | FastAPI API / Bot | `python main.py api` or `bot` |
| 8080 | FastAPI Web V2 | `python main.py web` |
| 8501 | Streamlit User | `streamlit run streamlit_apps/user_app.py` |
| 8502 | Streamlit Admin | `streamlit run streamlit_apps/admin_app.py` |
| 21465 | WPPConnect | Docker only |

Note: API dan Bot share port 8000 — jangan jalankan keduanya bersamaan di local. Kalau butuh keduanya, pakai `--port`:
```bash
python main.py api --port 8000
python main.py bot --port 8005
```
