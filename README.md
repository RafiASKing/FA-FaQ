# FA-FaQ — Hospital EMR FAQ System (v3.1 Docs)

FA-FaQ adalah sistem semantic FAQ untuk lingkungan EMR rumah sakit (Siloam) dengan arsitektur **Ports & Adapters**. Saat ini stack utamanya adalah **Typesense + Gemini + FastAPI/Streamlit + WPPConnect**.

> Status dokumen: **v3.1 (docs refresh)**
> Referensi teknis utama: `docs/SYSTEM_OVERVIEW.md` dan `docs/MEMORY.md`

---

## ✨ Highlights

| Area | Kondisi Terkini |
|------|------------------|
| Search Engine | Typesense vector search (`hospital_faq_kb`, 3072-dim) |
| Search Mode | `immediate`, `agent` (Flash), `agent_pro` (Pro) |
| Agent Prompt | Full content + tag description + HyDE keywords + context EMR |
| Security | API key protection untuk `/api/v1/*` via `X-API-Key` |
| Error Handling | Sanitized HTTP error + internal stack trace logging |
| Analytics | Unified logging untuk web + whatsapp (`search_log.csv`, `failed_searches.csv`) |

---

## 🏗️ Architecture Ringkas

```
Presentation: FastAPI (API/Web) + Streamlit (User/Admin/Bot Tester)
	↓
App Layer: Controllers → Services → Schemas
	↓
Ports: EmbeddingPort, LLMPort, VectorStorePort, MessagingPort
	↓
Adapters: Gemini + Typesense + WPPConnect
```

Semua adapter bisa ditukar lewat `config/container.py` tanpa ubah business logic.

---

## 🚀 Local Run (Windows-friendly)

### 1) Setup Environment

```bash
git clone https://github.com/RafiASKing/FA-FaQ.git
cd FA-FaQ

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
```

Isi minimal `.env`:
- `GOOGLE_API_KEY=...`
- `APP_API_KEY=...` (recommended untuk protect `/api/v1/*`)

### 2) Start layanan inti (tanpa WPP)

```bash
docker compose up --build -d typesense faq-web-v2 faq-admin faq-user
```

> Command note:
> - Windows / Docker Desktop: `docker compose`
> - Lightsail (Docker Compose v1): `docker-compose`

### 3) Jalankan bot tester lokal

```bash
$env:PYTHONPATH="."
streamlit run streamlit_apps/bot_tester.py --server.port 8503
```

### 4) Optional: Run API/Bot/Web via Python

```bash
python main.py api --port 8001
python main.py web --port 8080
python main.py bot --port 8000
```

---

## 🔐 API Security

- Header auth: `X-API-Key`
- Env utama: `APP_API_KEY`
- Fallback legacy: `API_KEY`
- Scope saat ini: seluruh route `/api/v1/*`

Jika key kosong, auth dianggap nonaktif (dev mode).

---

## 🌐 Endpoints Lokal

| Service | URL |
|---------|-----|
| Typesense Health | http://localhost:8118/health |
| Web V2 | http://localhost:8080 |
| User App | http://localhost:8501 |
| Admin App | http://localhost:8502 |
| Bot Tester | http://localhost:8503 |
| API Docs (manual API run) | http://localhost:8001/docs |

---

## 🩺 Container Health

- `docker-compose.yml` now defines per-service healthchecks on correct internal ports:
	- bot: `8000/health`
	- web: `8080/`
	- user: `8501/`
	- admin: `8502/`
- This avoids false `unhealthy` status caused by inherited default healthcheck to port `8000`.

---

## 🧪 Testing Status

Suites mencakup:
- service logic (`SearchService`, `FaqService`)
- core config (`GroupConfig`)
- auth behavior untuk search API

Kondisi terakhir validasi lokal: **29 passed**.

---

## 📚 Documentation

| Dokumen | Fungsi |
|---------|--------|
| [docs/REFACTORING_V3.1_DOCS_UPDATE.md](docs/REFACTORING_V3.1_DOCS_UPDATE.md) | Changelog docs v3.1 (alignment update) |
| [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) | Gambaran sistem lengkap v3.1 |
| [docs/MEMORY.md](docs/MEMORY.md) | Ringkasan cepat untuk coding agents |
| [docs/REFACTORING_V3.0_RELEASE.md](docs/REFACTORING_V3.0_RELEASE.md) | Changelog rilis v3.0 (production rollout) |
| [docs/LOCAL_DEV_GUIDE.md](docs/LOCAL_DEV_GUIDE.md) | Panduan local development detail |

---

## 🛠️ Tech Stack

- Backend: FastAPI, Uvicorn
- Apps: Streamlit
- Vector DB: Typesense
- Embedding: Google Gemini (`google-genai`)
- LLM: Gemini via LangChain (`langchain-google-genai`)
- Messaging: WPPConnect
- Deployment: Docker Compose, AWS Lightsail

---

Built for hospital knowledge retrieval with Siloam-aligned architecture.