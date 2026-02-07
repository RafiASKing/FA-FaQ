# FA-FaQ — Fast Cognitive Search System

AI-powered knowledge base for hospital SOPs and FAQs. Uses **semantic vector search** (ChromaDB + Google Gemini) with multi-channel delivery: Web UI, Streamlit apps, and WhatsApp bot.

Built with **Ports & Adapters** (Hexagonal Architecture) for easy swapping of AI providers, databases, and messaging platforms.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Semantic Search** | HyDE-formatted embeddings via Google Gemini for accurate query matching |
| **Multi-Channel** | FastAPI Web, Streamlit Apps, WhatsApp Bot (WPPConnect) |
| **Agent Mode** | LLM-powered reranking with structured output (LangChain) |
| **Admin Console** | CRUD operations with image upload and preview |
| **Pluggable Architecture** | Swap embedding, LLM, vector DB, or messaging provider in one file |

---

## 🏗️ Architecture

```
FA-FaQ/
├── app/
│   ├── Kernel.py              # FastAPI app factory + lifespan
│   ├── ports/                 # Abstract interfaces (EmbeddingPort, VectorStorePort, etc.)
│   ├── generative/engine.py   # Gemini adapters (Embedding + Chat)
│   ├── controllers/           # API route handlers
│   ├── services/              # Business logic (search, FAQ, bot, agent)
│   └── schemas/               # Pydantic models
├── config/
│   ├── container.py           # Dependency wiring (swap adapters here)
│   ├── chromaDb.py            # ChromaDB adapter
│   ├── messaging.py           # WPPConnect adapter
│   ├── settings.py            # Environment variables
│   └── routes.py              # Route registration
├── streamlit_apps/
│   ├── user_app.py            # User search interface
│   ├── admin_app.py           # Admin CRUD console
│   └── bot_tester.py          # Bot logic simulator
├── main.py                    # Unified entry point
└── docker-compose.yml         # Full stack deployment
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Google Gemini API Key

### 1. Setup Environment

```bash
git clone https://github.com/RafiASKing/FA-FaQ.git
cd FA-FaQ

python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
```

### 2. Start ChromaDB

```bash
docker compose up chroma-server -d
```

### 3. Run Apps

```bash
# API Server
python main.py api --port 8001

# Web Frontend
python main.py web

# Streamlit Apps (set PYTHONPATH first on Windows)
$env:PYTHONPATH="."
streamlit run streamlit_apps/user_app.py --server.port 8501
streamlit run streamlit_apps/admin_app.py --server.port 8502
streamlit run streamlit_apps/bot_tester.py --server.port 8503
```

### Access Points

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8001/docs |
| Web Search | http://localhost:8080 |
| User App | http://localhost:8501 |
| Admin Console | http://localhost:8502 |
| Bot Tester | http://localhost:8503 |

---

## 🐳 Docker Deployment

```bash
# Full stack (Linux/Lightsail)
docker compose up --build -d

# Partial stack (Windows - skip WPPConnect)
docker compose up --build -d chroma-server faq-web-v2 faq-admin faq-user
```

---

## 🔌 Swapping Providers

The architecture makes it easy to swap external dependencies:

| To Change | Steps |
|-----------|-------|
| **Embedding Model** | Create adapter in `app/generative/`, update `container.get_embedding()` |
| **LLM Provider** | Create adapter implementing `LLMPort`, update `container.get_llm()` |
| **Vector Database** | Create `config/newDb.py`, update `container.get_vector_store()` |
| **Messaging** | Create adapter implementing `MessagingPort`, update `container.get_messaging()` |

---

## 🤖 WhatsApp Bot

The bot responds to:
- **Private chats**: Always replies
- **Groups**: Only when mentioned with `@faq`

Test bot logic locally without WPPConnect using the **Bot Tester** Streamlit app.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [LOCAL_DEV_GUIDE.md](docs/LOCAL_DEV_GUIDE.md) | Detailed local development instructions |
| [MEMORY.md](docs/MEMORY.md) | Quick reference for project conventions |
| [REFACTORING_V2.1](docs/REFACTORING_V2.1_PORTS_ADAPTERS.md) | Ports & Adapters architecture details |
| [REFACTORING_V2.2](docs/REFACTORING_V2.2_WINDOWS_BOT_TESTER.md) | Windows fixes & Bot Tester |

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn
- **Vector DB**: ChromaDB
- **Embeddings**: Google Gemini (`google-genai`)
- **LLM**: Google Gemini via LangChain (`langchain-google-genai`)
- **Frontend**: Streamlit, Jinja2 Templates
- **Messaging**: WPPConnect (WhatsApp)
- **Deployment**: Docker Compose, AWS Lightsail

---

## 📄 License

MIT

---

Built with ❤️ for hospital knowledge management.