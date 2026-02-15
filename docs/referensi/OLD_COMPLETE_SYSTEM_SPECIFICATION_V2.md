# COMPLETE SYSTEM SPECIFICATION V2
## Siloam EMR FAQ Multichannel Application (Refactored Edition)

> **Dokumen ini berisi spesifikasi lengkap untuk merekonstruksi seluruh aplikasi dari nol.**
> **Versi:** 2.0 | **Tanggal:** Februari 2026

---

## DAFTAR ISI

1. [Ringkasan Eksekutif](#1-ringkasan-eksekutif)
2. [Perubahan dari V1](#2-perubahan-dari-v1)
3. [Arsitektur Sistem](#3-arsitektur-sistem)
4. [Teknologi Stack](#4-teknologi-stack)
5. [Struktur Direktori](#5-struktur-direktori)
6. [Konfigurasi Environment](#6-konfigurasi-environment)
7. [Database Schema](#7-database-schema)
8. [Config Layer](#8-config-layer)
9. [Core Layer](#9-core-layer)
10. [App Layer - Services](#10-app-layer---services)
11. [App Layer - Controllers](#11-app-layer---controllers)
12. [App Layer - Schemas](#12-app-layer---schemas)
13. [App Kernel - FastAPI Factory](#13-app-kernel---fastapi-factory)
14. [Routes Layer](#14-routes-layer)
15. [Streamlit Applications](#15-streamlit-applications)
16. [Main Entry Point](#16-main-entry-point)
17. [Docker Deployment](#17-docker-deployment)
18. [UI/UX Specifications](#18-uiux-specifications)
19. [Business Logic Rules](#19-business-logic-rules)
20. [API Endpoints](#20-api-endpoints)
21. [Testing Checklist](#21-testing-checklist)

---

## 1. RINGKASAN EKSEKUTIF

### 1.1 Tujuan Aplikasi

Aplikasi **FAQ Multichannel** untuk staff internal rumah sakit Siloam yang menggunakan sistem EMR (Electronic Medical Record). Target user:
- Dokter
- Perawat (Nurse)
- Staff administrasi
- Kasir
- Petugas laboratorium
- Staff medical record

### 1.2 Problem yang Diselesaikan

1. Staff sering bingung menggunakan EMR
2. Pertanyaan berulang ke tim IT Support
3. Tidak ada knowledge base yang mudah diakses
4. Butuh akses cepat via WhatsApp (channel paling sering digunakan)

### 1.3 Solusi

Sistem FAQ dengan **semantic search** (bukan keyword matching) yang bisa diakses via:
1. **Web App (Streamlit)** - untuk browsing dan pencarian
2. **Web App (FastAPI)** - alternatif UI yang lebih ringan
3. **WhatsApp Bot** - untuk quick query dari HP
4. **Admin Console** - untuk manajemen konten

### 1.4 Key Features

| Feature | Deskripsi |
|---------|-----------|
| **Semantic Search** | Menggunakan Google Gemini embedding untuk pencarian berbasis makna |
| **HyDE Format** | Hypothetical Document Embeddings untuk meningkatkan akurasi |
| **Pre-filtering** | Filter by department sebelum semantic ranking |
| **Inline Images** | Support gambar inline dengan syntax `[GAMBAR X]` |
| **Confidence Score** | Menampilkan persentase relevansi hasil pencarian |
| **Failed Search Analytics** | Mencatat query yang tidak ada hasilnya untuk improvement |
| **Multi-bot Identity** | Support multiple nomor WhatsApp bot |
| **Cascade Delete** | Hapus FAQ otomatis menghapus file gambar terkait |

---

## 2. PERUBAHAN DARI V1

### 2.1 Architectural Changes

| Aspek | V1 (Lama) | V2 (Baru) |
|-------|-----------|-----------|
| **Struktur** | Flat files (`app.py`, `admin.py`, `bot_wa.py`, `src/`) | Layered architecture (`config/`, `core/`, `app/`, `routes/`, `streamlit_apps/`) |
| **Configuration** | Manual `os.getenv()` | Pydantic `BaseSettings` dengan type validation |
| **Services** | Functions tersebar di `database.py` & `utils.py` | Dedicated Service classes per domain |
| **Controllers** | Logic campur di route handlers | Separation of concerns dengan Controllers |
| **Schemas** | Inline dicts | Pydantic models dengan validation |
| **App Factory** | Multiple entry points | Single `Kernel.py` dengan factory pattern |

### 2.2 Benefits of V2

1. **Maintainability** - Setiap komponen punya tanggung jawab jelas
2. **Testability** - Services bisa di-mock dan di-test secara isolated
3. **Type Safety** - Pydantic validation mencegah runtime errors
4. **Reusability** - Services bisa dipakai di Streamlit dan FastAPI
5. **Scalability** - Mudah menambah fitur baru tanpa mengganggu existing code

### 2.3 Migration Map

```
V1 File                    → V2 Location
─────────────────────────────────────────────────────────
src/config.py              → config/settings.py + config/constants.py
src/database.py            → config/database.py + app/services/*
src/utils.py               → core/content_parser.py + core/image_handler.py + core/tag_manager.py
app.py                     → streamlit_apps/user_app.py
admin.py                   → streamlit_apps/admin_app.py
bot_wa.py                  → app/controllers/webhook_controller.py + app/services/whatsapp_service.py
web_v2/main.py             → routes/web.py + app/Kernel.py
```

---

## 3. ARSITEKTUR SISTEM

### 3.1 High-Level Architecture (V2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                               │
│  ┌────────────────┬────────────────┬────────────────┬─────────────────┐ │
│  │   Streamlit    │   Streamlit    │    FastAPI     │     FastAPI     │ │
│  │   User App     │   Admin App    │    Web V2      │     WA Bot      │ │
│  │   :8501        │   :8502        │    :8080       │     :8000       │ │
│  └────────────────┴────────────────┴────────────────┴─────────────────┘ │
│           │                │                │                │          │
│           └────────────────┴────────┬───────┴────────────────┘          │
└─────────────────────────────────────┼───────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────┐
│                          APP LAYER (app/)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         Kernel.py                                    ││
│  │              (FastAPI App Factory + Lifespan Manager)                ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────┬─────────────────┬─────────────────────────────────┐│
│  │   Controllers   │    Services     │         Schemas                 ││
│  │   (Handlers)    │ (Business Logic)│    (Validation Models)          ││
│  └─────────────────┴─────────────────┴─────────────────────────────────┘│
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────┐
│                          CORE LAYER (core/)                              │
│  ┌─────────────────┬─────────────────┬─────────────────────────────────┐│
│  │  TagManager     │  ContentParser  │      ImageHandler               ││
│  │  (Tag Config)   │ ([GAMBAR X])    │   (Upload/Compress)             ││
│  └─────────────────┴─────────────────┴─────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                           Logger                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────┐
│                        CONFIG LAYER (config/)                            │
│  ┌─────────────────┬─────────────────┬─────────────────────────────────┐│
│  │    settings.py  │   database.py   │       constants.py              ││
│  │ (Pydantic Env)  │ (DB Factory)    │    (Magic Numbers)              ││
│  └─────────────────┴─────────────────┴─────────────────────────────────┘│
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────┐
│                           DATA LAYER                                     │
│  ┌─────────────────────────────┬────────────────────────────────────────┐│
│  │         ChromaDB            │        Google Gemini API               ││
│  │       (Vector Store)        │          (Embeddings)                  ││
│  │        Port: 8000           │        768-dimensional                 ││
│  └─────────────────────────────┴────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| **Presentation** | UI rendering, user input, response formatting |
| **App Layer** | Request handling, business orchestration, validation |
| **Core Layer** | Reusable utilities, shared logic, cross-cutting concerns |
| **Config Layer** | Configuration, environment, database connections |
| **Data Layer** | Persistent storage, external APIs |

### 3.3 Data Flow - Search

```
User Input (Query + Filter Tag)
         │
         ▼
┌─────────────────────────────┐
│  SearchController           │  ← Receives HTTP request
│  (app/controllers/)         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SearchService.search()     │  ← Business logic
│  (app/services/)            │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  EmbeddingService           │  ← Generate query embedding
│  .generate_query_embedding()│     via Google Gemini API
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  DatabaseFactory            │  ← Get ChromaDB collection
│  .get_collection()          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  ChromaDB.query()           │  ← Vector similarity search
│  with WHERE clause          │     (L2 Euclidean Distance)
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Score Calculation          │
│  score = (1 - distance) × 100
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Filter & Transform         │
│  - score > 41%              │
│  - Create SearchResult DTOs │
│  - Add badge colors         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Return List[SearchResult]  │
└─────────────────────────────┘
```

### 3.4 Data Flow - WhatsApp Bot

```
WhatsApp Message
         │
         ▼
┌─────────────────────────────┐
│  WPPConnect Gateway         │
│  Webhook → POST /webhook    │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  WebhookController          │
│  .whatsapp_webhook()        │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  WhatsAppWebhookPayload     │  ← Pydantic validation
│  (app/schemas/)             │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  payload.should_process()?  │
│  - Not from self            │
│  - Valid event type         │
│  - Not status broadcast     │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  BackgroundTask:            │
│  WebhookController          │
│  .process_message()         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  WhatsAppService            │
│  .should_reply_to_message() │
│  - DM: Always YES           │
│  - Group: Only if @faq or   │
│    bot is mentioned         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  WhatsAppService            │
│  .clean_query()             │
│  - Remove @faq              │
│  - Remove @mentions         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SearchService              │
│  .search_for_bot()          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  ContentParser              │
│  .to_whatsapp()             │
│  Convert [GAMBAR X] tags    │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  WhatsAppService            │
│  .send_text() + .send_images()
└─────────────────────────────┘
```

---

## 4. TEKNOLOGI STACK

### 4.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.10 | Core language |
| **Web Framework (User)** | Streamlit | 1.51.0 | User & Admin UI |
| **Web Framework (API)** | FastAPI | latest | WhatsApp bot, Web V2, REST API |
| **Vector Database** | ChromaDB | 1.3.4 | Semantic search storage |
| **Embedding Model** | Google Gemini | embedding-001 | 768-dim vectors |
| **Template Engine** | Jinja2 | latest | HTML rendering |
| **ASGI Server** | Uvicorn | latest | FastAPI server |
| **Configuration** | Pydantic Settings | latest | Type-safe env config |

### 4.2 Supporting Libraries

| Library | Purpose |
|---------|---------|
| `pandas` | DataFrame operations |
| `python-dotenv` | Environment variable loading |
| `pydantic-settings` | Type-safe configuration |
| `requests` | HTTP client for WhatsApp API |
| `bcrypt` | Password hashing |
| `Pillow` | Image processing & compression |
| `markdown` | Markdown to HTML conversion |
| `pysqlite3-binary` | Enhanced SQLite for Linux/Docker |
| `python-multipart` | File upload handling |
| `pytest` | Testing framework |

### 4.3 External Services

| Service | Purpose |
|---------|---------|
| **Google Gemini API** | Generate embeddings |
| **WPPConnect** | WhatsApp gateway (self-hosted) |

---

## 5. STRUKTUR DIREKTORI

```
FA-FaQ/
│
├── main.py                             # Unified entry point for all apps
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Container image definition
├── docker-compose.yml                  # Multi-service orchestration
├── .env                                # Environment variables (SENSITIVE)
│
├── config/                             # Configuration Layer
│   ├── __init__.py                     # Package exports
│   ├── settings.py                     # Pydantic BaseSettings
│   ├── constants.py                    # Magic numbers & defaults
│   └── database.py                     # Database connection factory
│
├── core/                               # Core Utilities Layer
│   ├── __init__.py                     # Package exports
│   ├── tag_manager.py                  # Tag/module configuration
│   ├── content_parser.py               # [GAMBAR X] parsing
│   ├── image_handler.py                # Image upload/compression
│   └── logger.py                       # Logging utilities
│
├── app/                                # Application Layer
│   ├── __init__.py                     # Package marker
│   ├── Kernel.py                       # FastAPI app factory
│   │
│   ├── services/                       # Business Logic
│   │   ├── __init__.py                 # Service exports
│   │   ├── embedding_service.py        # Embedding generation
│   │   ├── search_service.py           # Search operations
│   │   ├── faq_service.py              # FAQ CRUD
│   │   └── whatsapp_service.py         # WhatsApp integration
│   │
│   ├── controllers/                    # Request Handlers
│   │   ├── __init__.py                 # Controller exports
│   │   ├── search_controller.py        # Search endpoints
│   │   ├── faq_controller.py           # FAQ CRUD endpoints
│   │   └── webhook_controller.py       # WhatsApp webhook
│   │
│   └── schemas/                        # Pydantic Models
│       ├── __init__.py                 # Schema exports
│       ├── search_schema.py            # Search request/response
│       ├── faq_schema.py               # FAQ request/response
│       └── webhook_schema.py           # WhatsApp webhook payload
│
├── routes/                             # Route Registrations
│   ├── __init__.py                     # Package exports
│   └── web.py                          # HTML template routes
│
├── streamlit_apps/                     # Streamlit Applications
│   ├── user_app.py                     # User-facing search app
│   └── admin_app.py                    # Admin console
│
├── web_v2/                             # Web V2 Assets
│   ├── templates/
│   │   └── index.html                  # Jinja2 template
│   └── static/
│       └── style.css                   # CSS styling
│
├── data/                               # Persistent Data
│   ├── chroma_data/                    # ChromaDB vector storage
│   ├── tags_config.json                # Department/tag definitions
│   └── failed_searches.csv             # Failed search analytics
│
├── images/                             # Uploaded Images
│   ├── ED/                             # Emergency Department
│   ├── OPD/                            # Outpatient Department
│   ├── IPD/                            # Inpatient Department
│   └── ...                             # Other departments
│
├── wpp_sessions/                       # WhatsApp session data
│   └── config.json
│
├── wpp_tokens/                         # WhatsApp tokens
│
├── tests/                              # Test files
│
├── docs/                               # Documentation
│   ├── COMPLETE_SYSTEM_SPECIFICATION.md    # V1 spec
│   └── COMPLETE_SYSTEM_SPECIFICATION_V2.md # This file
│
└── .streamlit/                         # Streamlit config
    └── config.toml
```

---

## 6. KONFIGURASI ENVIRONMENT

### 6.1 File .env (Template)

```env
# === API KEYS ===
GOOGLE_API_KEY=AIzaSy...your_gemini_api_key_here

# === ADMIN AUTH ===
# Generate dengan: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
ADMIN_PASSWORD_HASH=$2b$12$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# === CHROMA DB (Production/Docker) ===
CHROMA_HOST=chroma-server
CHROMA_PORT=8000
# Kosongkan CHROMA_HOST & CHROMA_PORT untuk mode local file

# === WHATSAPP BOT ===
WA_BASE_URL=http://wppconnect:21465
WA_SESSION_KEY=THISISMYSECURETOKEN
WA_SESSION_NAME=mysession
BOT_IDENTITIES=6281234567890,6289876543210

# === BOT BEHAVIOR (Optional) ===
BOT_MIN_SCORE=80.0
BOT_MIN_GAP=10.0

# === WEB CONFIG ===
WEB_V2_URL=https://faq-assist.cloud/
WA_SUPPORT_NUMBER=6289635225253
```

### 6.2 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | **YES** | - | API key dari Google AI Studio |
| `ADMIN_PASSWORD_HASH` | NO | "admin" | bcrypt hash password admin |
| `CHROMA_HOST` | NO | - | Host ChromaDB server (kosong = local mode) |
| `CHROMA_PORT` | NO | - | Port ChromaDB server |
| `WA_BASE_URL` | YES* | http://wppconnect:21465 | URL WPPConnect API |
| `WA_SESSION_KEY` | YES* | THISISMYSECURETOKEN | Secret key untuk WPPConnect |
| `WA_SESSION_NAME` | NO | mysession | Nama session WhatsApp |
| `BOT_IDENTITIES` | YES* | - | Nomor HP bot (comma-separated) |
| `BOT_MIN_SCORE` | NO | 80.0 | Threshold confidence score |
| `BOT_MIN_GAP` | NO | 10.0 | Gap minimum antara hasil #1 dan #2 |
| `WEB_V2_URL` | NO | https://faq-assist.cloud/ | URL web untuk footer bot |
| `WA_SUPPORT_NUMBER` | NO | 6289635225253 | Nomor WA support |

*Required hanya jika menggunakan WhatsApp Bot

---

## 7. DATABASE SCHEMA

### 7.1 ChromaDB Collection

**Collection Name:** `faq_universal_v1`

### 7.2 Document Structure

```python
{
    "id": "42",  # String numeric ID (auto-increment)

    "documents": [
        """DOMAIN: ED (IGD, Emergency)
DOKUMEN: Cara Login EMR ED
VARIASI PERTANYAAN USER: gabisa login, lupa password, autentikasi gagal
ISI KONTEN: Buka browser, masuk ke https://emr.siloam.com..."""
    ],  # HyDE formatted text for embedding

    "embeddings": [[0.123, 0.456, ...]],  # 768-dimensional vector

    "metadatas": [{
        "tag": "ED",                      # Department category
        "judul": "Cara Login EMR ED",     # FAQ title
        "jawaban_tampil": "**Langkah 1:**\nBuka browser...[GAMBAR 1]",
        "keywords_raw": "gabisa login, lupa pwd, autentikasi gagal",
        "path_gambar": "./images/ED/cara_login_ED_1_a9k2q.jpg;./images/ED/cara_login_ED_2_b3m1x.jpg",
        "sumber_url": "https://confluence.siloam.com/emr/login"
    }]
}
```

### 7.3 HyDE Embedding Format

**Struktur teks yang di-embed:**

```
DOMAIN: {tag} ({tag_description})
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keywords_raw}
ISI KONTEN: {clean_jawaban}
```

**Contoh:**

```
DOMAIN: ED (IGD, Emergency)
DOKUMEN: Cara Registrasi Pasien Baru di IGD
VARIASI PERTANYAAN USER: daftar pasien baru, registrasi igd, pasien baru emergency
ISI KONTEN: Untuk mendaftarkan pasien baru di IGD, ikuti langkah berikut...
```

### 7.4 Tags Configuration (tags_config.json)

```json
{
    "ED": {
        "color": "#FF4B4B",
        "desc": "IGD, Emergency, Triage, Ambulans"
    },
    "OPD": {
        "color": "#2ECC71",
        "desc": "Rawat Jalan, Poli, Dokter Spesialis"
    },
    "IPD": {
        "color": "#3498DB",
        "desc": "Rawat Inap, Bangsal, Bed, Visite"
    },
    "Umum": {
        "color": "#808080",
        "desc": "General Info, IT Support"
    }
}
```

### 7.5 Failed Searches Log (failed_searches.csv)

```csv
Timestamp,Query User
2024-01-18 10:15:23,Bagaimana cara edit resep di farmasi
2024-01-18 10:20:45,Gimana bikin pasien baru di IPD
```

---

## 8. CONFIG LAYER

### 8.1 config/settings.py

**Purpose:** Centralized configuration menggunakan Pydantic BaseSettings dengan type validation.

```python
"""
Centralized Settings menggunakan Pydantic BaseSettings.
Semua environment variables dikelola di sini.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application Settings - Single Source of Truth untuk semua konfigurasi.
    Nilai diambil dari environment variables atau menggunakan default.
    """

    # === API KEYS & AUTH ===
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    admin_password_hash: str = Field(default="admin", alias="ADMIN_PASSWORD_HASH")

    # === CHROMA DB ===
    chroma_host: str | None = Field(default=None, alias="CHROMA_HOST")
    chroma_port: int | None = Field(default=None, alias="CHROMA_PORT")

    # === WHATSAPP BOT ===
    wa_base_url: str = Field(default="http://wppconnect:21465", alias="WA_BASE_URL")
    wa_secret_key: str = Field(default="THISISMYSECURETOKEN", alias="WA_SESSION_KEY")
    wa_session_name: str = Field(default="mysession", alias="WA_SESSION_NAME")
    bot_identities: str = Field(default="", alias="BOT_IDENTITIES")

    # === BOT LOGIC THRESHOLDS ===
    bot_min_score: float = Field(default=80.0, alias="BOT_MIN_SCORE")
    bot_min_gap: float = Field(default=10.0, alias="BOT_MIN_GAP")

    # === WEB CONFIG ===
    web_v2_url: str = Field(default="https://faq-assist.cloud/", alias="WEB_V2_URL")
    wa_support_number: str = Field(default="6289635225253", alias="WA_SUPPORT_NUMBER")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars

    @property
    def bot_identity_list(self) -> List[str]:
        """Parse BOT_IDENTITIES string menjadi list."""
        if not self.bot_identities:
            return []
        return [x.strip() for x in self.bot_identities.split(",") if x.strip()]

    @property
    def is_chroma_server_mode(self) -> bool:
        """Cek apakah menggunakan ChromaDB server mode."""
        return bool(self.chroma_host and self.chroma_port)


class PathSettings:
    """
    Path Configuration - Semua path dikelola di sini.
    Tidak menggunakan Pydantic karena path perlu dihitung dari BASE_DIR.
    """

    def __init__(self):
        # Base directory (root project)
        self.BASE_DIR = Path(__file__).parent.parent.resolve()

        # Data paths
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DB_PATH = self.DATA_DIR / "chroma_data"
        self.TAGS_FILE = self.DATA_DIR / "tags_config.json"
        self.FAILED_SEARCH_LOG = self.DATA_DIR / "failed_searches.csv"

        # Assets paths
        self.IMAGES_DIR = self.BASE_DIR / "images"

        # Web V2 paths
        self.WEB_V2_DIR = self.BASE_DIR / "web_v2"
        self.TEMPLATES_DIR = self.WEB_V2_DIR / "templates"
        self.STATIC_DIR = self.WEB_V2_DIR / "static"

        # Ensure directories exist
        self._setup_directories()

    def _setup_directories(self):
        """Membuat folder yang diperlukan jika belum ada."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.IMAGES_DIR.mkdir(exist_ok=True)
        self.DB_PATH.mkdir(exist_ok=True)


# Singleton instances
settings = Settings()
paths = PathSettings()
```

### 8.2 config/constants.py

**Purpose:** Semua magic numbers terpusat di satu file.

```python
"""
Application Constants - Magic Numbers Terpusat.
"""

# === SEARCH & RELEVANCE ===
RELEVANCE_THRESHOLD = 41          # Minimum score untuk hasil dianggap relevan (%)
HIGH_RELEVANCE_THRESHOLD = 80     # Score >= ini dianggap sangat relevan
MEDIUM_RELEVANCE_THRESHOLD = 50   # Score >= ini dianggap cukup relevan

# === RESULT LIMITS ===
BOT_TOP_RESULTS = 5               # Jumlah hasil untuk WhatsApp Bot
WEB_TOP_RESULTS = 3               # Jumlah top hasil untuk Web search mode
SEARCH_CANDIDATE_LIMIT = 50       # Kandidat hasil dari ChromaDB sebelum filtering

# === PAGINATION ===
ITEMS_PER_PAGE = 10               # Jumlah item per halaman

# === IMAGE PROCESSING ===
IMAGE_MAX_WIDTH = 1024            # Max width gambar setelah resize (px)
IMAGE_QUALITY = 70                # JPEG quality (0-100)

# === DATABASE ===
COLLECTION_NAME = "faq_universal_v1"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# === RETRY LOGIC ===
MAX_RETRIES = 10                  # Max retry untuk database lock
RETRY_BASE_DELAY = 0.1            # Base delay untuk retry (seconds)

# === STREAMLIT COLOR MAPPING ===
HEX_TO_STREAMLIT_COLOR = {
    "#FF4B4B": "red",      # Merah (ED)
    "#2ECC71": "green",    # Hijau (OPD)
    "#3498DB": "blue",     # Biru (IPD/MR/Rehab)
    "#FFA500": "orange",   # Orange (Cashier)
    "#9B59B6": "violet",   # Ungu (Farmasi)
    "#808080": "gray",     # Abu (Umum)
    "#333333": "gray"      # Dark Gray
}

# === COLOR PALETTE (untuk Admin) ===
COLOR_PALETTE = {
    "Merah":             {"hex": "#FF4B4B", "name": "red"},
    "Hijau":             {"hex": "#2ECC71", "name": "green"},
    "Biru":              {"hex": "#3498DB", "name": "blue"},
    "Orange":            {"hex": "#FFA500", "name": "orange"},
    "Ungu":              {"hex": "#9B59B6", "name": "violet"},
    "Abu-abu":           {"hex": "#808080", "name": "gray"},
    "Pelangi (Special)": {"hex": "#333333", "name": "rainbow"}
}

# === DEFAULT TAGS ===
DEFAULT_TAGS = {
    "ED": {"color": "#FF4B4B", "desc": "IGD, Emergency, Triage, Ambulans"},
    "OPD": {"color": "#2ECC71", "desc": "Rawat Jalan, Poli, Dokter Spesialis"},
    "IPD": {"color": "#3498DB", "desc": "Rawat Inap, Bangsal, Bed, Visite"},
    "Umum": {"color": "#808080", "desc": "General Info, IT Support"}
}
```

### 8.3 config/database.py

**Purpose:** Factory pattern untuk database connections.

```python
"""
Database Connection Factory - ChromaDB Client Management.
"""

# --- FORCE USE NEW SQLITE (Wajib Paling Atas untuk Docker/Linux) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb
from google import genai
from google.genai import types

from .settings import settings, paths
from .constants import COLLECTION_NAME, EMBEDDING_MODEL


class DatabaseFactory:
    """
    Factory class untuk membuat koneksi database.
    Mendukung dua mode:
    - Server Mode: Menggunakan ChromaDB HTTP Client (untuk Docker/Production)
    - Local Mode: Menggunakan PersistentClient (untuk development)
    """

    _db_client = None
    _ai_client = None

    @classmethod
    def get_db_client(cls):
        """
        Mendapatkan ChromaDB client.
        Auto-detect mode berdasarkan environment variables.
        """
        if cls._db_client is None:
            if settings.is_chroma_server_mode:
                # Client-Server Mode (Production/Docker)
                cls._db_client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port
                )
            else:
                # Local Mode (Development)
                cls._db_client = chromadb.PersistentClient(
                    path=str(paths.DB_PATH)
                )
        return cls._db_client

    @classmethod
    def get_ai_client(cls):
        """Mendapatkan Google Gemini AI client."""
        if cls._ai_client is None:
            cls._ai_client = genai.Client(api_key=settings.google_api_key)
        return cls._ai_client

    @classmethod
    def get_collection(cls):
        """Mendapatkan ChromaDB collection."""
        client = cls.get_db_client()
        return client.get_or_create_collection(name=COLLECTION_NAME)

    @classmethod
    def reset_clients(cls):
        """Reset semua client (useful untuk testing)."""
        cls._db_client = None
        cls._ai_client = None


def generate_embedding(text: str) -> list:
    """
    Generate embedding vector menggunakan Google Gemini.

    Args:
        text: Teks yang akan di-embed

    Returns:
        List of float (768 dimensions) atau empty list jika error
    """
    client = DatabaseFactory.get_ai_client()
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Error Embedding AI: {e}")
        return []
```

### 8.4 config/__init__.py

**Purpose:** Package exports untuk clean imports.

```python
# Config Package
from .settings import settings, paths
from .constants import (
    # Search & Relevance
    RELEVANCE_THRESHOLD,
    HIGH_RELEVANCE_THRESHOLD,
    MEDIUM_RELEVANCE_THRESHOLD,
    # Result Limits
    BOT_TOP_RESULTS,
    WEB_TOP_RESULTS,
    SEARCH_CANDIDATE_LIMIT,
    # Pagination
    ITEMS_PER_PAGE,
    # Image Processing
    IMAGE_MAX_WIDTH,
    IMAGE_QUALITY,
    # Database
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    # Retry Logic
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    # Color Mappings
    HEX_TO_STREAMLIT_COLOR,
    COLOR_PALETTE,
    DEFAULT_TAGS
)

__all__ = [
    'settings', 'paths',
    'RELEVANCE_THRESHOLD', 'HIGH_RELEVANCE_THRESHOLD', 'MEDIUM_RELEVANCE_THRESHOLD',
    'BOT_TOP_RESULTS', 'WEB_TOP_RESULTS', 'SEARCH_CANDIDATE_LIMIT',
    'ITEMS_PER_PAGE', 'IMAGE_MAX_WIDTH', 'IMAGE_QUALITY',
    'COLLECTION_NAME', 'EMBEDDING_MODEL',
    'MAX_RETRIES', 'RETRY_BASE_DELAY',
    'HEX_TO_STREAMLIT_COLOR', 'COLOR_PALETTE', 'DEFAULT_TAGS'
]
```

---

## 9. CORE LAYER

### 9.1 core/tag_manager.py

**Purpose:** Mengelola konfigurasi tag/modul dengan caching.

```python
"""
Tag Manager - Mengelola konfigurasi tag/modul.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List

from config.settings import paths
from config.constants import DEFAULT_TAGS, HEX_TO_STREAMLIT_COLOR, COLOR_PALETTE


class TagManager:
    """
    Manager untuk tag/modul configuration.
    Menangani:
    - Load/save tags dari JSON
    - Mapping warna
    - Validasi tag
    """

    _cache: Dict = None
    _cache_file_mtime: float = 0

    @classmethod
    def load_tags(cls, force_reload: bool = False) -> Dict:
        """
        Load konfigurasi tag dari JSON file.
        Menggunakan cache untuk performa.
        """
        tags_file = paths.TAGS_FILE

        # Check if cache is valid
        if not force_reload and cls._cache is not None:
            try:
                current_mtime = tags_file.stat().st_mtime
                if current_mtime == cls._cache_file_mtime:
                    return cls._cache
            except FileNotFoundError:
                pass

        # Load from file or create default
        if not tags_file.exists():
            cls.save_tags(DEFAULT_TAGS)
            cls._cache = DEFAULT_TAGS.copy()
            cls._cache_file_mtime = tags_file.stat().st_mtime
            return cls._cache

        try:
            with open(tags_file, "r", encoding="utf-8") as f:
                cls._cache = json.load(f)
                cls._cache_file_mtime = tags_file.stat().st_mtime
                return cls._cache
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading tags config: {e}")
            return DEFAULT_TAGS.copy()

    @classmethod
    def save_tags(cls, tags_dict: Dict) -> bool:
        """Simpan konfigurasi tag ke JSON file."""
        tags_file = paths.TAGS_FILE

        try:
            tags_file.parent.mkdir(parents=True, exist_ok=True)

            with open(tags_file, "w", encoding="utf-8") as f:
                json.dump(tags_dict, f, indent=4, ensure_ascii=False)

            cls._cache = tags_dict.copy()
            cls._cache_file_mtime = tags_file.stat().st_mtime
            return True
        except IOError as e:
            print(f"⚠️ Error saving tags config: {e}")
            return False

    @classmethod
    def get_tag_info(cls, tag_name: str) -> Dict:
        """Dapatkan info untuk tag tertentu."""
        tags = cls.load_tags()
        return tags.get(tag_name, {"color": "#808080", "desc": ""})

    @classmethod
    def get_tag_color(cls, tag_name: str) -> str:
        """Dapatkan warna HEX untuk tag."""
        return cls.get_tag_info(tag_name).get("color", "#808080")

    @classmethod
    def get_tag_description(cls, tag_name: str) -> str:
        """Dapatkan deskripsi untuk tag."""
        return cls.get_tag_info(tag_name).get("desc", "")

    @classmethod
    def get_streamlit_color_name(cls, tag_name: str) -> str:
        """Convert tag color ke nama warna Streamlit."""
        hex_code = cls.get_tag_color(tag_name).upper()
        return HEX_TO_STREAMLIT_COLOR.get(hex_code, "gray")

    @classmethod
    def add_tag(cls, name: str, color: str, description: str = "") -> bool:
        """Tambah atau update tag."""
        tags = cls.load_tags()
        tags[name] = {"color": color, "desc": description}
        return cls.save_tags(tags)

    @classmethod
    def delete_tag(cls, name: str) -> bool:
        """Hapus tag."""
        tags = cls.load_tags()
        if name in tags:
            del tags[name]
            return cls.save_tags(tags)
        return False

    @classmethod
    def get_all_tag_names(cls) -> List[str]:
        """Dapatkan list semua nama tag."""
        return list(cls.load_tags().keys())

    @classmethod
    def invalidate_cache(cls):
        """Invalidate cache."""
        cls._cache = None
        cls._cache_file_mtime = 0
```

### 9.2 core/content_parser.py

**Purpose:** Unified parser untuk konten FAQ dengan syntax `[GAMBAR X]`.

```python
"""
Unified Content Parser - Menangani parsing [GAMBAR X] dan format konten.
"""

import re
import os
import markdown
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ParsedImage:
    """Representasi gambar yang sudah diparsing."""
    index: int          # 1-based index
    path: str           # Path file gambar
    exists: bool        # Apakah file ada


class ContentParser:
    """
    Parser terpusat untuk konten FAQ.
    Menangani:
    - Parsing tag [GAMBAR X]
    - Konversi ke berbagai format output (Streamlit, HTML, WhatsApp)
    - Pembersihan teks untuk embedding
    """

    IMAGE_TAG_PATTERN = re.compile(r'\[GAMBAR\s*(\d+)\]', re.IGNORECASE)

    @classmethod
    def parse_image_paths(cls, path_string: str) -> List[str]:
        """Parse string path gambar dari database (semicolon-separated)."""
        if not path_string or str(path_string).lower() == 'none':
            return []

        paths = []
        for p in path_string.split(';'):
            clean = p.strip().replace("\\", "/")
            if clean:
                paths.append(clean)
        return paths

    @classmethod
    def clean_for_embedding(cls, text: str) -> str:
        """Membersihkan teks untuk embedding AI (hapus tag [GAMBAR X])."""
        if not text:
            return ""
        clean = cls.IMAGE_TAG_PATTERN.sub('', text)
        return " ".join(clean.split())

    @classmethod
    def count_image_tags(cls, text: str) -> int:
        """Hitung jumlah tag [GAMBAR X] dalam teks."""
        return len(cls.IMAGE_TAG_PATTERN.findall(text))

    @classmethod
    def to_html(cls, text: str, image_paths: str, base_image_url: str = "/images") -> str:
        """Convert konten ke HTML untuk web_v2."""
        if not text:
            return ""

        # Fix markdown format
        text = cls._fix_markdown_format(text)

        # Convert markdown to HTML
        try:
            html_content = markdown.markdown(
                text,
                extensions=['nl2br', 'extra', 'sane_lists']
            )
        except Exception:
            html_content = markdown.markdown(text)

        # Parse image paths
        img_list = cls.parse_image_paths(image_paths)

        # Fix paths untuk web
        web_img_list = []
        for p in img_list:
            if p.startswith("./images"):
                p = p[1:]  # Hapus titik
            web_img_list.append(p)

        # Replace [GAMBAR X] dengan HTML img
        def replace_match(match):
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(web_img_list):
                    return f'''
                    <div class="img-container">
                        <img src="{web_img_list[idx]}" alt="Gambar {idx+1}" loading="lazy">
                    </div>
                    '''
                return ""
            except:
                return ""

        html_content = cls.IMAGE_TAG_PATTERN.sub(replace_match, html_content)

        # Fallback gallery
        if "[GAMBAR" not in text.upper() and web_img_list:
            html_content += "<hr><div class='gallery-grid'>"
            for img in web_img_list:
                html_content += f'<div class="img-card"><img src="{img}"></div>'
            html_content += "</div>"

        return html_content

    @classmethod
    def to_whatsapp(cls, text: str, image_paths: str) -> Tuple[str, List[str]]:
        """Convert konten untuk WhatsApp."""
        img_list = cls.parse_image_paths(image_paths)
        images_to_send = []

        def replace_tag(match):
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_list):
                    images_to_send.append(img_list[idx])
                    return f"*(Lihat Gambar {idx+1})*"
                return ""
            except:
                return ""

        processed_text = cls.IMAGE_TAG_PATTERN.sub(replace_tag, text)

        # Jika tidak ada tag tapi ada gambar, kirim semua
        if not images_to_send and img_list:
            images_to_send = img_list

        return processed_text, images_to_send

    @classmethod
    def get_streamlit_parts(cls, text: str, image_paths: str) -> List[dict]:
        """Parse konten untuk rendering Streamlit."""
        img_list = cls.parse_image_paths(image_paths)
        parts = re.split(r'(\[GAMBAR\s*\d+\])', text, flags=re.IGNORECASE)

        result = []
        for part in parts:
            match = cls.IMAGE_TAG_PATTERN.search(part)
            if match:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_list):
                    path = cls._fix_path_for_ui(img_list[idx])
                    result.append({
                        'type': 'image',
                        'index': idx + 1,
                        'path': path,
                        'exists': path and os.path.exists(path)
                    })
                else:
                    result.append({'type': 'missing_image', 'index': idx + 1})
            else:
                if part.strip():
                    result.append({'type': 'text', 'content': part})

        # Fallback gallery
        if len(result) == 1 and result[0].get('type') == 'text' and img_list:
            result.append({'type': 'divider'})
            for idx, p in enumerate(img_list):
                path = cls._fix_path_for_ui(p)
                result.append({
                    'type': 'gallery_image',
                    'index': idx,
                    'path': path,
                    'exists': path and os.path.exists(path)
                })

        return result

    @staticmethod
    def _fix_markdown_format(text: str) -> str:
        """Memperbaiki format markdown."""
        if not text:
            return ""
        text = re.sub(r'([^\n])\n(\d+\.\s)', r'\1\n\n\2', text)
        text = re.sub(r'([^\n])\n(-\s)', r'\1\n\n\2', text)
        return text

    @staticmethod
    def _fix_path_for_ui(db_path: str) -> Optional[str]:
        """Normalisasi path gambar untuk UI."""
        clean = str(db_path).strip('"').strip("'")
        if clean.lower() == "none":
            return None
        clean = clean.replace("\\", "/")
        return clean
```

### 9.3 core/image_handler.py

**Purpose:** Mengelola upload, kompresi, dan path gambar.

```python
"""
Image Handler - Mengelola upload, kompresi, dan path gambar.
"""

import os
import re
import random
import string
import base64
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image

from config.settings import paths
from config.constants import IMAGE_MAX_WIDTH, IMAGE_QUALITY


class ImageHandler:
    """
    Handler untuk operasi gambar.
    """

    @staticmethod
    def sanitize_filename(text: str) -> str:
        """Membersihkan nama file dari karakter tidak valid."""
        return re.sub(r'[^\w\-_]', '', text.replace(" ", "_"))[:30]

    @classmethod
    def save_uploaded_images(
        cls,
        uploaded_files: List,
        judul: str,
        tag: str,
        images_dir: Path = None
    ) -> str:
        """
        Simpan dan kompres gambar yang diupload.
        Returns: String path yang dipisahkan semicolon, atau "none"
        """
        if not uploaded_files:
            return "none"

        if images_dir is None:
            images_dir = paths.IMAGES_DIR

        saved_paths = []
        clean_judul = cls.sanitize_filename(judul)
        target_dir = Path(images_dir) / tag
        target_dir.mkdir(parents=True, exist_ok=True)

        # Get resampling method
        resample_module = getattr(Image, "Resampling", None)
        resample_method = resample_module.LANCZOS if resample_module else getattr(Image, "LANCZOS", Image.BICUBIC)

        for i, file in enumerate(uploaded_files):
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            filename = f"{clean_judul}_{tag}_{i+1}_{suffix}.jpg"
            full_path = target_dir / filename

            try:
                if hasattr(file, "seek"):
                    file.seek(0)

                image = Image.open(file)

                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")

                if image.width > IMAGE_MAX_WIDTH:
                    ratio = IMAGE_MAX_WIDTH / float(image.width)
                    new_height = int(float(image.height) * ratio)
                    image = image.resize((IMAGE_MAX_WIDTH, new_height), resample_method)

                image.save(str(full_path), "JPEG", quality=IMAGE_QUALITY, optimize=True)

            except Exception as e:
                print(f"⚠️ Gagal compress gambar: {e}")
                if hasattr(file, "seek"):
                    file.seek(0)
                with open(full_path, "wb") as f:
                    f.write(file.getbuffer() if hasattr(file, 'getbuffer') else file.read())
            finally:
                if hasattr(file, "seek"):
                    file.seek(0)

            rel_path = f"./images/{tag}/{filename}"
            saved_paths.append(rel_path)

        return ";".join(saved_paths)

    @staticmethod
    def fix_path_for_ui(db_path: str) -> Optional[str]:
        """Normalisasi path gambar dari database untuk UI."""
        if not db_path:
            return None
        clean = str(db_path).strip('"').strip("'")
        if clean.lower() == "none":
            return None
        clean = clean.replace("\\", "/")
        return clean

    @staticmethod
    def get_base64_image(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Convert gambar ke base64 string (untuk WhatsApp API)."""
        try:
            clean_path = file_path.replace("\\", "/")
            if not os.path.exists(clean_path):
                return None, None

            mime_type, _ = mimetypes.guess_type(clean_path)
            if not mime_type:
                mime_type = "image/jpeg"

            with open(clean_path, "rb") as image_file:
                raw_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            return f"data:{mime_type};base64,{raw_base64}", os.path.basename(clean_path)
        except Exception:
            return None, None

    @classmethod
    def delete_images(cls, path_string: str) -> List[str]:
        """Hapus file gambar dari disk."""
        deleted = []

        if not path_string or path_string.lower() == 'none':
            return deleted

        paths_list = path_string.split(';')
        for p in paths_list:
            clean_path = p.strip().replace("\\", "/")
            if os.path.exists(clean_path):
                try:
                    os.remove(clean_path)
                    deleted.append(clean_path)
                except Exception as e:
                    print(f"⚠️ Gagal hapus file {clean_path}: {e}")

        return deleted
```

### 9.4 core/logger.py

**Purpose:** Centralized logging utilities.

```python
"""
Logger - Centralized logging utilities.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import paths


def log(message: str, flush: bool = True):
    """Simple logging function dengan timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=flush)


def log_failed_search(query: str, log_file: Path = None) -> bool:
    """Mencatat pencarian yang gagal ke CSV."""
    if log_file is None:
        log_file = paths.FAILED_SEARCH_LOG

    log_file = Path(log_file)
    file_exists = log_file.exists()

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(["Timestamp", "Query User"])

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                query
            ])
        return True
    except Exception as e:
        print(f"⚠️ Gagal mencatat log: {e}")
        return False


def clear_failed_search_log(log_file: Path = None) -> bool:
    """Hapus file log pencarian gagal."""
    if log_file is None:
        log_file = paths.FAILED_SEARCH_LOG

    try:
        if os.path.exists(log_file):
            os.remove(log_file)
        return True
    except Exception as e:
        print(f"⚠️ Gagal menghapus log: {e}")
        return False
```

---

## 10. APP LAYER - SERVICES

### 10.1 app/services/embedding_service.py

**Purpose:** Embedding generation dengan HyDE format dan retry logic.

```python
"""
Embedding Service - Mengelola generasi embedding vector.
"""

import functools
import time
import random
from typing import List, Optional

from config.database import DatabaseFactory, generate_embedding
from config.constants import MAX_RETRIES, RETRY_BASE_DELAY
from core.content_parser import ContentParser
from core.tag_manager import TagManager


def retry_on_lock(max_retries: int = MAX_RETRIES, base_delay: float = RETRY_BASE_DELAY):
    """
    Decorator untuk menangani error 'Database Locked' pada SQLite.
    Menggunakan Jitter Backoff.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    err_msg = str(e).lower()
                    if "locked" in err_msg or "busy" in err_msg:
                        retries += 1
                        sleep_time = base_delay * (1 + random.random())
                        time.sleep(sleep_time)
                    else:
                        raise e
            raise Exception("Database sedang sibuk, silakan coba lagi.")
        return wrapper
    return decorator


class EmbeddingService:
    """Service untuk mengelola embedding generation dengan HyDE format."""

    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """Generate embedding vector untuk teks."""
        return generate_embedding(text)

    @classmethod
    def generate_faq_embedding(
        cls,
        tag: str,
        judul: str,
        jawaban: str,
        keywords: str
    ) -> List[float]:
        """Generate embedding untuk dokumen FAQ menggunakan format HyDE."""
        clean_jawaban = ContentParser.clean_for_embedding(jawaban)

        try:
            tag_desc = TagManager.get_tag_description(tag)
        except:
            tag_desc = ""

        domain_str = f"{tag} ({tag_desc})" if tag_desc else tag

        text_embed = f"""DOMAIN: {domain_str}
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keywords}
ISI KONTEN: {clean_jawaban}"""

        return cls.generate_embedding(text_embed)

    @staticmethod
    def generate_query_embedding(query: str) -> List[float]:
        """Generate embedding untuk query pencarian."""
        return generate_embedding(query)
```

### 10.2 app/services/search_service.py

**Purpose:** Search logic dengan scoring dan filtering.

```python
"""
Search Service - Mengelola logika pencarian semantic.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from config.database import DatabaseFactory
from config.constants import (
    RELEVANCE_THRESHOLD, HIGH_RELEVANCE_THRESHOLD, MEDIUM_RELEVANCE_THRESHOLD,
    SEARCH_CANDIDATE_LIMIT, WEB_TOP_RESULTS, BOT_TOP_RESULTS
)
from core.tag_manager import TagManager
from .embedding_service import EmbeddingService, retry_on_lock


@dataclass
class SearchResult:
    """Representasi hasil pencarian."""
    id: str
    tag: str
    judul: str
    jawaban_tampil: str
    keywords_raw: str
    path_gambar: str
    sumber_url: str
    score: float
    score_class: str  # high, med, low
    badge_color: str

    @property
    def is_relevant(self) -> bool:
        return self.score > RELEVANCE_THRESHOLD


class SearchService:
    """Service untuk pencarian semantic."""

    @staticmethod
    def calculate_relevance(distance: float) -> float:
        """Hitung score relevance dari Euclidean distance."""
        return max(0, (1 - distance) * 100)

    @staticmethod
    def get_score_class(score: float) -> str:
        """Tentukan class CSS berdasarkan score."""
        if score > HIGH_RELEVANCE_THRESHOLD:
            return "score-high"
        elif score > MEDIUM_RELEVANCE_THRESHOLD:
            return "score-med"
        else:
            return "score-low"

    @classmethod
    @retry_on_lock()
    def search(
        cls,
        query: str,
        filter_tag: Optional[str] = None,
        n_results: int = SEARCH_CANDIDATE_LIMIT,
        min_score: float = RELEVANCE_THRESHOLD
    ) -> List[SearchResult]:
        """Pencarian semantic di database."""
        query_vector = EmbeddingService.generate_query_embedding(query)

        if not query_vector:
            return []

        where_clause = None
        if filter_tag and filter_tag != "Semua Modul":
            where_clause = {"tag": filter_tag}

        collection = DatabaseFactory.get_collection()
        raw_results = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where_clause
        )

        results = []

        if raw_results['ids'][0]:
            for i in range(len(raw_results['ids'][0])):
                doc_id = raw_results['ids'][0][i]
                meta = raw_results['metadatas'][0][i]
                distance = raw_results['distances'][0][i]

                score = cls.calculate_relevance(distance)

                if score > min_score:
                    tag = meta.get('tag', 'Umum')
                    results.append(SearchResult(
                        id=doc_id,
                        tag=tag,
                        judul=meta.get('judul', ''),
                        jawaban_tampil=meta.get('jawaban_tampil', ''),
                        keywords_raw=meta.get('keywords_raw', ''),
                        path_gambar=meta.get('path_gambar', 'none'),
                        sumber_url=meta.get('sumber_url', ''),
                        score=score,
                        score_class=cls.get_score_class(score),
                        badge_color=TagManager.get_tag_color(tag)
                    ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    @classmethod
    def search_for_web(cls, query: str, filter_tag: Optional[str] = None,
                       top_n: int = WEB_TOP_RESULTS) -> List[SearchResult]:
        """Pencarian untuk Web UI (Top N hasil)."""
        results = cls.search(query, filter_tag)
        return results[:top_n]

    @classmethod
    def search_for_bot(cls, query: str, filter_tag: Optional[str] = None,
                       top_n: int = BOT_TOP_RESULTS) -> List[SearchResult]:
        """Pencarian untuk WhatsApp Bot."""
        results = cls.search(query, filter_tag, n_results=top_n)
        return results[:1]  # Bot hanya return 1 hasil terbaik

    @classmethod
    @retry_on_lock()
    def get_all_faqs(cls, filter_tag: Optional[str] = None) -> List[Dict]:
        """Ambil semua FAQ (untuk browse mode)."""
        collection = DatabaseFactory.get_collection()
        data = collection.get(include=['metadatas'])

        results = []
        if data['ids']:
            for i, doc_id in enumerate(data['ids']):
                meta = data['metadatas'][i]

                if filter_tag and filter_tag != "Semua Modul":
                    if meta.get('tag') != filter_tag:
                        continue

                try:
                    id_num = int(doc_id)
                except:
                    id_num = 0

                tag = meta.get('tag', 'Umum')
                meta['id'] = doc_id
                meta['id_num'] = id_num
                meta['badge_color'] = TagManager.get_tag_color(tag)
                results.append(meta)

        results.sort(key=lambda x: x.get('id_num', 0), reverse=True)
        return results

    @classmethod
    @retry_on_lock()
    def get_unique_tags(cls) -> List[str]:
        """Ambil daftar tag unik dari database."""
        collection = DatabaseFactory.get_collection()
        data = collection.get(include=['metadatas'])

        unique_tags = set()
        if data['metadatas']:
            for meta in data['metadatas']:
                if meta and meta.get('tag'):
                    unique_tags.add(meta['tag'])

        return sorted(list(unique_tags))
```

### 10.3 app/services/faq_service.py

**Purpose:** CRUD operations untuk FAQ.

```python
"""
FAQ Service - Mengelola CRUD operasi untuk FAQ.
"""

import pandas as pd
from typing import Dict, Optional, List

from config.database import DatabaseFactory
from core.image_handler import ImageHandler
from .embedding_service import EmbeddingService, retry_on_lock


class FaqService:
    """Service untuk operasi CRUD pada FAQ."""

    @classmethod
    def _get_next_id(cls, collection) -> str:
        """Generate ID baru untuk FAQ (auto-increment)."""
        data = collection.get(include=[])
        existing_ids = data['ids']

        if not existing_ids:
            return "1"

        numeric_ids = [int(x) for x in existing_ids if x.isdigit()]

        if not numeric_ids:
            return "1"

        return str(max(numeric_ids) + 1)

    @classmethod
    @retry_on_lock()
    def upsert(
        cls,
        tag: str,
        judul: str,
        jawaban: str,
        keywords: str,
        img_paths: str = "none",
        source_url: str = "",
        doc_id: Optional[str] = None
    ) -> str:
        """Create atau Update FAQ."""
        collection = DatabaseFactory.get_collection()

        final_id = str(doc_id) if doc_id and doc_id != "auto" else cls._get_next_id(collection)

        vector = EmbeddingService.generate_faq_embedding(
            tag=tag, judul=judul, jawaban=jawaban, keywords=keywords
        )

        from core.content_parser import ContentParser
        from core.tag_manager import TagManager

        clean_jawaban = ContentParser.clean_for_embedding(jawaban)
        tag_desc = TagManager.get_tag_description(tag)
        domain_str = f"{tag} ({tag_desc})" if tag_desc else tag

        text_embed = f"""DOMAIN: {domain_str}
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keywords}
ISI KONTEN: {clean_jawaban}"""

        collection.upsert(
            ids=[final_id],
            embeddings=[vector],
            documents=[text_embed],
            metadatas=[{
                "tag": tag,
                "judul": judul,
                "jawaban_tampil": jawaban,
                "keywords_raw": keywords,
                "path_gambar": img_paths,
                "sumber_url": source_url
            }]
        )

        return final_id

    @classmethod
    @retry_on_lock()
    def delete(cls, doc_id: str) -> bool:
        """Hapus FAQ beserta gambar terkait (cascade delete)."""
        collection = DatabaseFactory.get_collection()

        try:
            data = collection.get(ids=[str(doc_id)], include=['metadatas'])

            if data['metadatas'] and len(data['metadatas']) > 0:
                meta = data['metadatas'][0]
                img_str = meta.get('path_gambar', 'none')

                if img_str and img_str.lower() != 'none':
                    ImageHandler.delete_images(img_str)

            collection.delete(ids=[str(doc_id)])
            return True

        except Exception as e:
            print(f"⚠️ Error deleting FAQ {doc_id}: {e}")
            return False

    @classmethod
    @retry_on_lock()
    def get_by_id(cls, doc_id: str) -> Optional[Dict]:
        """Ambil FAQ berdasarkan ID."""
        collection = DatabaseFactory.get_collection()

        try:
            data = collection.get(ids=[str(doc_id)], include=['metadatas', 'documents'])

            if data['ids'] and len(data['ids']) > 0:
                meta = data['metadatas'][0]
                meta['id'] = data['ids'][0]
                meta['document'] = data['documents'][0] if data['documents'] else ""
                return meta

            return None
        except Exception:
            return None

    @classmethod
    @retry_on_lock()
    def get_all_as_dataframe(cls) -> pd.DataFrame:
        """Ambil semua FAQ sebagai DataFrame."""
        collection = DatabaseFactory.get_collection()
        data = collection.get(include=['metadatas', 'documents'])

        if not data['ids']:
            return pd.DataFrame()

        rows = []
        for i, doc_id in enumerate(data['ids']):
            meta = data['metadatas'][i]
            rows.append({
                "ID": doc_id,
                "Tag": meta.get('tag'),
                "Judul": meta.get('judul'),
                "Jawaban": meta.get('jawaban_tampil'),
                "Keyword": meta.get('keywords_raw'),
                "Gambar": meta.get('path_gambar'),
                "Source": meta.get('sumber_url'),
                "AI Context": data['documents'][i] if data['documents'] else ""
            })

        df = pd.DataFrame(rows)
        df['ID_Num'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0)
        df = df.sort_values('ID_Num', ascending=False).drop(columns=['ID_Num'])

        return df

    @classmethod
    def count_by_tag(cls, tag: str) -> int:
        """Hitung jumlah FAQ dengan tag tertentu."""
        df = cls.get_all_as_dataframe()
        if df.empty:
            return 0
        return len(df[df['Tag'] == tag])
```

### 10.4 app/services/whatsapp_service.py

**Purpose:** WhatsApp integration via WPPConnect.

```python
"""
WhatsApp Service - Mengelola integrasi dengan WPPConnect API.
"""

import requests
import time
import re
from typing import Optional, List, Dict

from config.settings import settings
from core.logger import log
from core.image_handler import ImageHandler


class WhatsAppService:
    """Service untuk integrasi WhatsApp via WPPConnect."""

    _current_token: Optional[str] = None

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Get HTTP headers dengan auth token."""
        if not cls._current_token:
            cls.generate_token()

        return {
            "Authorization": f"Bearer {cls._current_token}",
            "Content-Type": "application/json"
        }

    @classmethod
    def generate_token(cls) -> bool:
        """Generate authentication token dari WPPConnect."""
        try:
            url = f"{settings.wa_base_url}/api/{settings.wa_session_name}/{settings.wa_secret_key}/generate-token"
            r = requests.post(url, timeout=10)

            if r.status_code in [200, 201]:
                resp = r.json()
                token = resp.get("token") or resp.get("session")

                if not token and "full" in resp:
                    token = resp["full"].split(":")[-1]

                if token:
                    cls._current_token = token
                    log("✅ Berhasil Generate Token.")
                    return True
        except Exception as e:
            log(f"❌ Error Auth: {e}")

        return False

    @classmethod
    def send_text(cls, phone: str, message: str) -> bool:
        """Kirim pesan teks ke WhatsApp."""
        if not phone or str(phone) == "None":
            return False

        url = f"{settings.wa_base_url}/api/{settings.wa_session_name}/send-message"
        is_group = "@g.us" in str(phone)

        payload = {
            "phone": phone,
            "message": message,
            "isGroup": is_group,
            "linkPreview": False
        }

        try:
            r = requests.post(url, json=payload, headers=cls.get_headers(), timeout=30)

            if r.status_code == 401:
                cls.generate_token()
                r = requests.post(url, json=payload, headers=cls.get_headers(), timeout=30)

            return r.status_code in [200, 201]
        except Exception as e:
            log(f"❌ Error Kirim Text: {e}")
            return False

    @classmethod
    def send_image(cls, phone: str, file_path: str, caption: str = "") -> bool:
        """Kirim gambar ke WhatsApp."""
        if not phone:
            return False

        base64_str, filename = ImageHandler.get_base64_image(file_path)
        if not base64_str:
            return False

        url = f"{settings.wa_base_url}/api/{settings.wa_session_name}/send-image"
        is_group = "@g.us" in str(phone)

        payload = {
            "phone": phone,
            "base64": base64_str,
            "caption": caption,
            "isGroup": is_group
        }

        try:
            r = requests.post(url, json=payload, headers=cls.get_headers(), timeout=60)
            return r.status_code in [200, 201]
        except Exception as e:
            log(f"❌ Error Kirim Image: {e}")
            return False

    @classmethod
    def send_images(cls, phone: str, file_paths: List[str], delay: float = 0.5) -> int:
        """Kirim multiple gambar dengan delay."""
        success_count = 0
        for i, path in enumerate(file_paths):
            if cls.send_image(phone, path, caption=f"Lampiran {i+1}"):
                success_count += 1
            time.sleep(delay)
        return success_count

    @classmethod
    def start_session(cls, webhook_url: str) -> bool:
        """Start WhatsApp session dan register webhook."""
        try:
            url = f"{settings.wa_base_url}/api/{settings.wa_session_name}/start-session"
            r = requests.post(url, json={"webhook": webhook_url}, headers=cls.get_headers(), timeout=30)
            return r.status_code in [200, 201]
        except Exception as e:
            log(f"⚠️ Gagal start session: {e}")
            return False

    @classmethod
    def should_reply_to_message(cls, is_group: bool, message_body: str, mentioned_list: List[str]) -> bool:
        """
        Tentukan apakah bot harus membalas pesan.
        - Private chat: Selalu balas
        - Group: Hanya jika di-mention atau ada keyword @faq
        """
        if not is_group:
            return True

        if "@faq" in message_body.lower():
            return True

        my_identities = settings.bot_identity_list

        if mentioned_list:
            for mentioned_id in mentioned_list:
                for my_id in my_identities:
                    if str(my_id) in str(mentioned_id):
                        return True

        return False

    @classmethod
    def clean_query(cls, message_body: str) -> str:
        """Bersihkan query dari mention dan keyword."""
        clean = message_body.replace("@faq", "")

        for identity in settings.bot_identity_list:
            clean = clean.replace(f"@{identity}", "")

        clean = re.sub(r'@\d+', '', clean)

        return clean.strip()
```

### 10.5 app/services/__init__.py

```python
# Services Package
from .embedding_service import EmbeddingService
from .search_service import SearchService
from .faq_service import FaqService
from .whatsapp_service import WhatsAppService

__all__ = ['EmbeddingService', 'SearchService', 'FaqService', 'WhatsAppService']
```

---

## 11. APP LAYER - CONTROLLERS

### 11.1 app/controllers/search_controller.py

```python
"""
Search Controller - Handler untuk search endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.schemas import SearchRequest, SearchResponse, SearchResultItem
from app.services import SearchService
from config.constants import WEB_TOP_RESULTS


router = APIRouter(prefix="/search", tags=["Search"])


class SearchController:

    @staticmethod
    @router.get("", response_model=SearchResponse)
    async def search_get(
        q: str = Query(..., description="Query pencarian", min_length=1),
        tag: Optional[str] = Query(default=None, description="Filter tag"),
        limit: int = Query(default=WEB_TOP_RESULTS, ge=1, le=50)
    ) -> SearchResponse:
        """Pencarian semantic via GET request."""
        try:
            results = SearchService.search_for_web(q, tag, limit)

            return SearchResponse(
                query=q,
                filter_tag=tag,
                total_results=len(results),
                results=[
                    SearchResultItem(
                        id=r.id, tag=r.tag, judul=r.judul,
                        jawaban_tampil=r.jawaban_tampil,
                        path_gambar=r.path_gambar, sumber_url=r.sumber_url,
                        score=r.score, score_class=r.score_class,
                        badge_color=r.badge_color
                    ) for r in results
                ]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

    @staticmethod
    @router.post("", response_model=SearchResponse)
    async def search_post(request: SearchRequest) -> SearchResponse:
        """Pencarian semantic via POST request."""
        try:
            results = SearchService.search_for_web(
                request.query, request.filter_tag, request.limit
            )

            return SearchResponse(
                query=request.query,
                filter_tag=request.filter_tag,
                total_results=len(results),
                results=[
                    SearchResultItem(
                        id=r.id, tag=r.tag, judul=r.judul,
                        jawaban_tampil=r.jawaban_tampil,
                        path_gambar=r.path_gambar, sumber_url=r.sumber_url,
                        score=r.score, score_class=r.score_class,
                        badge_color=r.badge_color
                    ) for r in results
                ]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

    @staticmethod
    @router.get("/tags", response_model=List[str])
    async def get_tags() -> List[str]:
        """Ambil daftar semua tag yang tersedia."""
        try:
            return SearchService.get_unique_tags()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

### 11.2 app/controllers/webhook_controller.py

```python
"""
Webhook Controller - Handler untuk WhatsApp webhook.
"""

import time
from fastapi import APIRouter, Request, BackgroundTasks

from app.schemas import WebhookResponse, WhatsAppWebhookPayload
from app.services import WhatsAppService, SearchService
from core.content_parser import ContentParser
from core.logger import log, log_failed_search
from config.settings import settings
from config.constants import RELEVANCE_THRESHOLD


router = APIRouter(prefix="/webhook", tags=["Webhook"])


class WebhookController:

    @staticmethod
    async def process_message(
        remote_jid: str, sender_name: str, message_body: str,
        is_group: bool, mentioned_list: list
    ):
        """Background task untuk memproses pesan masuk."""
        log(f"⚙️ Memproses Pesan: '{message_body}' dari {sender_name}")

        should_reply = WhatsAppService.should_reply_to_message(
            is_group, message_body, mentioned_list
        )

        if not should_reply:
            return

        clean_query = WhatsAppService.clean_query(message_body)

        if not clean_query:
            WhatsAppService.send_text(remote_jid, f"Halo {sender_name}, silakan ketik pertanyaan Anda.")
            return

        try:
            results = SearchService.search_for_bot(clean_query)
        except Exception as e:
            log(f"❌ Database error: {e}")
            WhatsAppService.send_text(remote_jid, "Maaf, database sedang gangguan.")
            return

        web_url = settings.web_v2_url

        if not results:
            log_failed_search(clean_query)
            fail_msg = f"Maaf, tidak ditemukan hasil untuk: '{clean_query}'\n\nSilakan cari di: {web_url}"
            WhatsAppService.send_text(remote_jid, fail_msg)
            return

        top_result = results[0]
        score = top_result.score

        if score < RELEVANCE_THRESHOLD:
            log_failed_search(clean_query)
            msg = f"Maaf, belum ada data yang cocok.\n\nCek FaQs di: {web_url}"
            WhatsAppService.send_text(remote_jid, msg)
            return

        # Build response
        header = f"Relevansi: {score:.0f}%\n" if score >= 60 else f"[Relevansi Rendah: {score:.0f}%]\n"

        processed_text, images_to_send = ContentParser.to_whatsapp(
            top_result.jawaban_tampil, top_result.path_gambar
        )

        final_text = f"{header}\n*{top_result.judul}*\n\n{processed_text}"

        sumber = str(top_result.sumber_url).strip() if top_result.sumber_url else ""
        if len(sumber) > 3:
            final_text += f"\n\n\nSumber: {sumber}" if "http" in sumber.lower() else f"\n\n\nNote: {sumber}"

        WhatsAppService.send_text(remote_jid, final_text)

        if images_to_send:
            WhatsAppService.send_images(remote_jid, images_to_send)

        time.sleep(0.5)
        footer_text = f"-----\nJika bukan ini jawaban yang dimaksud:\n1. Cek: {web_url}\n2. Gunakan kalimat spesifik"
        WhatsAppService.send_text(remote_jid, footer_text)

    @staticmethod
    @router.post("/whatsapp", response_model=WebhookResponse)
    async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
        """Endpoint untuk menerima webhook dari WPPConnect."""
        try:
            body = await request.json()
            payload = WhatsAppWebhookPayload(**body)

            if not payload.should_process():
                return WebhookResponse(status="ignored", message="Event ignored")

            remote_jid = payload.get_remote_jid()
            message_body = payload.get_message_body()
            sender_name = payload.get_sender_name()
            is_group = payload.is_group_message()
            mentioned_list = payload.get_mentioned_list()

            if not remote_jid:
                return WebhookResponse(status="ignored", message="No remote JID")

            background_tasks.add_task(
                WebhookController.process_message,
                remote_jid, sender_name, message_body, is_group, mentioned_list
            )

            return WebhookResponse(status="success", message="Message queued")

        except Exception as e:
            log(f"❌ Webhook Error: {e}")
            return WebhookResponse(status="error", message=str(e))
```

---

## 12. APP LAYER - SCHEMAS

### 12.1 app/schemas/search_schema.py

```python
"""
Search Schemas - Pydantic models untuk search operations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Query pencarian", min_length=1)
    filter_tag: Optional[str] = Field(default=None)
    limit: int = Field(default=3, ge=1, le=50)


class SearchResultItem(BaseModel):
    id: str
    tag: str
    judul: str
    jawaban_tampil: str
    path_gambar: str
    sumber_url: str
    score: float
    score_class: str
    badge_color: str


class SearchResponse(BaseModel):
    query: str
    filter_tag: Optional[str]
    total_results: int
    results: List[SearchResultItem]
```

### 12.2 app/schemas/faq_schema.py

```python
"""
FAQ Schemas - Pydantic models untuk FAQ operations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class FaqCreate(BaseModel):
    tag: str = Field(..., description="Tag/modul")
    judul: str = Field(..., min_length=3)
    jawaban: str = Field(...)
    keywords: str = Field(default="")
    source_url: str = Field(default="")


class FaqUpdate(BaseModel):
    tag: Optional[str] = None
    judul: Optional[str] = None
    jawaban: Optional[str] = None
    keywords: Optional[str] = None
    source_url: Optional[str] = None
    img_paths: Optional[str] = None


class FaqResponse(BaseModel):
    id: str
    tag: str
    judul: str
    jawaban_tampil: str
    keywords_raw: str
    path_gambar: str
    sumber_url: str
    score: Optional[float] = None
    score_class: Optional[str] = None
    badge_color: Optional[str] = None


class FaqListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    items: List[FaqResponse]
```

### 12.3 app/schemas/webhook_schema.py

```python
"""
Webhook Schemas - Pydantic models untuk WhatsApp webhook.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WhatsAppWebhookPayload(BaseModel):
    event: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    fromMe: Optional[bool] = Field(default=False, alias="fromMe")
    from_: Optional[str] = Field(default=None, alias="from")
    chatId: Optional[str] = None
    body: Optional[str] = None
    content: Optional[str] = None
    isGroupMsg: Optional[bool] = False
    mentionedJidList: Optional[List[str]] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        extra = "allow"

    def get_message_body(self) -> str:
        if self.data:
            return self.data.get("body") or self.data.get("content") or ""
        return self.body or self.content or ""

    def get_remote_jid(self) -> Optional[str]:
        if self.data:
            return self.data.get("from") or self.data.get("chatId")
        return self.from_ or self.chatId

    def get_sender_name(self) -> str:
        if self.data:
            return self.data.get("sender", {}).get("pushname", "User")
        return "User"

    def is_group_message(self) -> bool:
        remote_jid = self.get_remote_jid()
        if self.data:
            is_group = self.data.get("isGroupMsg", False)
        else:
            is_group = self.isGroupMsg or False
        return is_group or (remote_jid and "@g.us" in str(remote_jid))

    def get_mentioned_list(self) -> List[str]:
        if self.data:
            return self.data.get("mentionedJidList", [])
        return self.mentionedJidList or []

    def is_from_me(self) -> bool:
        if self.data:
            return self.data.get("fromMe", False) is True
        return self.fromMe is True

    def should_process(self) -> bool:
        if self.is_from_me():
            return False
        remote_jid = self.get_remote_jid()
        if not remote_jid or "status@broadcast" in str(remote_jid):
            return False
        valid_events = ["onMessage", "onAnyMessage", "onmessage"]
        if self.event and self.event not in valid_events:
            return False
        return True


class WebhookResponse(BaseModel):
    status: str
    message: Optional[str] = None
```

---

## 13. APP KERNEL - FASTAPI FACTORY

### 13.1 app/Kernel.py

**Purpose:** FastAPI app factory dengan lifespan manager.

```python
"""
Application Kernel - FastAPI App Factory dengan Lifespan Manager.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings, paths
from core.logger import log
from app.services import WhatsAppService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager untuk startup dan shutdown events."""
    # === STARTUP ===
    log("🚀 Application Starting...")

    if hasattr(app.state, 'is_bot_mode') and app.state.is_bot_mode:
        log(f"🤖 Bot Mode: Identities Loaded: {len(settings.bot_identity_list)}")
        WhatsAppService.generate_token()

        webhook_url = "http://faq-bot:8000/webhook/whatsapp"
        WhatsAppService.start_session(webhook_url)

    log("✅ Application Ready!")

    yield

    # === SHUTDOWN ===
    log("👋 Application Shutting Down...")


def create_app(
    title: str = "Hospital FAQ API",
    description: str = "Semantic Search Knowledge Base for Hospital EMR",
    version: str = "2.0.0",
    include_bot_routes: bool = False,
    include_web_routes: bool = False
) -> FastAPI:
    """Factory function untuk membuat FastAPI application."""

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.state.is_bot_mode = include_bot_routes

    # === CORS Middleware ===
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # === Static Files ===
    app.mount("/images", StaticFiles(directory=str(paths.IMAGES_DIR)), name="images")

    # === Register Routes ===
    from app.controllers.search_controller import router as search_router
    from app.controllers.faq_controller import router as faq_router

    app.include_router(search_router, prefix="/api/v1")
    app.include_router(faq_router, prefix="/api/v1")

    if include_bot_routes:
        from app.controllers.webhook_controller import router as webhook_router
        app.include_router(webhook_router)

    if include_web_routes:
        from routes.web import router as web_router
        app.include_router(web_router)
        app.mount("/static", StaticFiles(directory=str(paths.STATIC_DIR)), name="static")

    # === Health Check ===
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": version}

    @app.get("/", tags=["Root"])
    async def root():
        return {"name": title, "version": version, "docs": "/docs"}

    return app


# Pre-configured app factories
def create_api_app() -> FastAPI:
    return create_app(title="Hospital FAQ API", include_bot_routes=False, include_web_routes=False)

def create_bot_app() -> FastAPI:
    return create_app(title="Hospital FAQ Bot", include_bot_routes=True, include_web_routes=False)

def create_web_app() -> FastAPI:
    return create_app(title="Hospital FAQ Web", include_bot_routes=False, include_web_routes=True)
```

---

## 14. ROUTES LAYER

### 14.1 routes/web.py

**Purpose:** HTML template routes untuk Web V2.

```python
"""
Web Routes - HTML template routes untuk Web V2.
"""

import math
import re
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config.settings import paths
from config.constants import ITEMS_PER_PAGE, WEB_TOP_RESULTS
from app.services import SearchService
from core.content_parser import ContentParser
from core.tag_manager import TagManager


router = APIRouter(tags=["Web"])

templates = Jinja2Templates(directory=str(paths.TEMPLATES_DIR))


def process_content_to_html(text_markdown: str, img_path_str: str) -> str:
    return ContentParser.to_html(text_markdown, img_path_str)


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: str = "", tag: str = "Semua Modul", page: int = 0):
    """Main page - Search dan Browse FAQ."""
    results = []
    total_pages = 1
    is_search_mode = False

    try:
        db_tags = SearchService.get_unique_tags()
    except:
        db_tags = []
    all_tags = ["Semua Modul"] + (db_tags if db_tags else [])

    # === SEARCH MODE ===
    if q.strip():
        is_search_mode = True
        search_results = SearchService.search_for_web(q, tag if tag != "Semua Modul" else None, WEB_TOP_RESULTS)

        for r in search_results:
            results.append({
                'id': r.id, 'tag': r.tag, 'judul': r.judul,
                'jawaban_tampil': r.jawaban_tampil,
                'path_gambar': r.path_gambar, 'sumber_url': r.sumber_url,
                'score': int(r.score), 'score_class': r.score_class,
                'badge_color': r.badge_color
            })

    # === BROWSE MODE ===
    else:
        raw_all = SearchService.get_all_faqs(tag if tag != "Semua Modul" else None)

        total_docs = len(raw_all)
        total_pages = math.ceil(total_docs / ITEMS_PER_PAGE) if total_docs > 0 else 1

        page = max(0, min(page, total_pages - 1))

        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        sliced_data = raw_all[start:end]

        for meta in sliced_data:
            tag_name = meta.get('tag', 'Umum')
            results.append({
                'id': meta.get('id', ''), 'tag': tag_name,
                'judul': meta.get('judul', ''),
                'jawaban_tampil': meta.get('jawaban_tampil', ''),
                'path_gambar': meta.get('path_gambar', 'none'),
                'sumber_url': meta.get('sumber_url', ''),
                'score': None,
                'badge_color': TagManager.get_tag_color(tag_name)
            })

    # === PROCESS CONTENT ===
    for item in results:
        item['html_content'] = process_content_to_html(
            item.get('jawaban_tampil', ''), item.get('path_gambar', '')
        )

    return templates.TemplateResponse("index.html", {
        "request": request,
        "results": results,
        "query": q,
        "current_tag": tag,
        "all_tags": all_tags,
        "page": page,
        "total_pages": total_pages,
        "is_search_mode": is_search_mode,
        "total_items": len(results)
    })
```

---

## 15. STREAMLIT APPLICATIONS

### 15.1 streamlit_apps/user_app.py

Streamlit User Application untuk pencarian FAQ. Menggunakan:
- `SearchService` untuk search operations
- `TagManager` untuk badge colors
- `ContentParser` untuk rendering [GAMBAR X]

Key features:
- Search mode (semantic search, top 3 results)
- Browse mode (paginated, sorted by ID desc)
- Relevance score indicators
- Inline image rendering
- Failed search logging

### 15.2 streamlit_apps/admin_app.py

Streamlit Admin Console dengan 5 tabs:
1. **Database** - View all FAQs in DataFrame
2. **New FAQ** - Smart editor dengan:
   - Auto-increment [GAMBAR X] button
   - Preview mode sebelum publish
   - Image compression
3. **Edit/Delete** - Update existing FAQs dengan cascade delete
4. **Config Tags** - Manage department tags dan colors
5. **Analytics** - View failed search logs

---

## 16. MAIN ENTRY POINT

### 16.1 main.py

```python
"""
Main Entry Point - Bootstrap untuk semua aplikasi.
"""

import sys
import uvicorn

from app.Kernel import create_api_app, create_bot_app, create_web_app


# Pre-created app instances untuk uvicorn
api_app = create_api_app()
bot_app = create_bot_app()
web_app = create_web_app()


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    uvicorn.run("main:api_app", host=host, port=port, reload=reload)

def run_bot(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    uvicorn.run("main:bot_app", host=host, port=port, reload=reload)

def run_web(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    uvicorn.run("main:web_app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Usage: python main.py <api|bot|web> [--reload] [--port N]")
        sys.exit(0)

    command = args[0].lower()
    reload = "--reload" in args

    port = None
    for i, arg in enumerate(args):
        if arg == "--port" and i + 1 < len(args):
            try:
                port = int(args[i + 1])
            except ValueError:
                pass

    if command == "api":
        run_api(port=port or 8000, reload=reload)
    elif command == "bot":
        run_bot(port=port or 8000, reload=reload)
    elif command == "web":
        run_web(port=port or 8080, reload=reload)
```

---

## 17. DOCKER DEPLOYMENT

### 17.1 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501 8502 8000 8080

CMD ["streamlit", "run", "streamlit_apps/user_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 17.2 docker-compose.yml

```yaml
version: '3'

services:
  chroma-server:
    image: chromadb/chroma:latest
    container_name: faq_chroma_server
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./data/chroma_data:/data
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=False

  wppconnect:
    container_name: faq_wppconnect
    build: https://github.com/wppconnect-team/wppconnect-server.git
    restart: always
    ports:
      - "21465:21465"
    environment:
      SECRET_KEY: admin123
    volumes:
      - ./wpp_tokens:/home/wppconnect/tokens
      - ./wpp_sessions:/home/wppconnect/userData

  faq-bot:
    build: .
    container_name: faq_bot_wa
    restart: always
    ports:
      - "8005:8000"
    depends_on:
      - chroma-server
      - wppconnect
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
      - WA_BASE_URL=http://wppconnect:21465
    volumes:
      - ./data:/app/data
      - ./images:/app/images
    command: uvicorn main:bot_app --host 0.0.0.0 --port 8000

  faq-user:
    build: .
    container_name: faq_user_app
    restart: always
    ports:
      - "8501:8501"
    depends_on:
      - chroma-server
    volumes:
      - ./data:/app/data
      - ./images:/app/images
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
    command: streamlit run streamlit_apps/user_app.py --server.port=8501 --server.address=0.0.0.0

  faq-admin:
    build: .
    container_name: faq_admin_app
    restart: always
    ports:
      - "8502:8502"
    depends_on:
      - chroma-server
    volumes:
      - ./data:/app/data
      - ./images:/app/images
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
    command: streamlit run streamlit_apps/admin_app.py --server.port=8502 --server.address=0.0.0.0

  faq-web-v2:
    build: .
    container_name: faq_web_v2
    restart: always
    ports:
      - "8080:8080"
    depends_on:
      - chroma-server
    volumes:
      - ./data:/app/data
      - ./web_v2:/app/web_v2
      - ./images:/app/images
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
    command: uvicorn main:web_app --host 0.0.0.0 --port 8080
```

### 17.3 Service Ports

| Service | Internal Port | External Port | URL |
|---------|--------------|---------------|-----|
| ChromaDB | 8000 | 8000 | http://localhost:8000 |
| WPPConnect | 21465 | 21465 | http://localhost:21465 |
| FAQ Bot | 8000 | 8005 | http://localhost:8005 |
| FAQ User | 8501 | 8501 | http://localhost:8501 |
| FAQ Admin | 8502 | 8502 | http://localhost:8502 |
| FAQ Web V2 | 8080 | 8080 | http://localhost:8080 |

---

## 18. UI/UX SPECIFICATIONS

### 18.1 Color Palette

| Color Name | HEX | Streamlit | Usage |
|------------|-----|-----------|-------|
| Red | #FF4B4B | red | ED (Emergency) |
| Green | #2ECC71 | green | OPD (Outpatient) |
| Blue | #3498DB | blue | IPD, MR, Rehab |
| Orange | #FFA500 | orange | Lab, Cashier, MCU |
| Violet | #9B59B6 | violet | Pharmacy |
| Gray | #808080 | gray | Umum, Default |

### 18.2 Score Indicators

| Score Range | Class | Color | Label |
|-------------|-------|-------|-------|
| > 80% | score-high | Green | Sangat Relevan |
| 50-80% | score-med | Light Green | Cukup Relevan |
| 41-50% | score-low | Orange | Kurang Relevan |
| < 41% | - | - | Tidak Ditampilkan |

---

## 19. BUSINESS LOGIC RULES

### 19.1 Search Rules

1. **Minimum Score Threshold**: 41%
2. **Score Calculation**: `score = (1 - L2_distance) × 100`
3. **Pre-filtering**: Filter by tag di ChromaDB WHERE clause (sebelum semantic ranking)
4. **Result Limits**:
   - Web UI: Top 3 results
   - Bot: Top 1 result only
   - Browse mode: Paginated (10 per page)

### 19.2 WhatsApp Bot Rules

1. **DM (Private Chat)**: Selalu reply
2. **Group Chat**: Reply hanya jika:
   - Message contains `@faq`
   - Bot is mentioned (in mentionedJidList)
3. **Response Format**:
   - Text message with answer
   - Images (if any)
   - Footer with guidance

### 19.3 Image Handling

1. **Upload**: Compress to JPEG, max 1024px width, 70% quality
2. **Storage**: `./images/{tag}/{sanitized_judul}_{tag}_{index}_{random}.jpg`
3. **Inline Syntax**: `[GAMBAR 1]`, `[GAMBAR 2]`, etc.
4. **Cascade Delete**: Hapus FAQ = hapus gambar terkait

---

## 20. API ENDPOINTS

### 20.1 Search API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/search?q=...&tag=...&limit=...` | Search FAQs |
| POST | `/api/v1/search` | Search FAQs (body) |
| GET | `/api/v1/search/tags` | Get all unique tags |

### 20.2 FAQ API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/faq` | List FAQs (paginated) |
| GET | `/api/v1/faq/{id}` | Get FAQ by ID |
| POST | `/api/v1/faq` | Create new FAQ |
| PUT | `/api/v1/faq/{id}` | Update FAQ |
| DELETE | `/api/v1/faq/{id}` | Delete FAQ |

### 20.3 Webhook API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/whatsapp` | WPPConnect webhook |

### 20.4 Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |

---

## 21. TESTING CHECKLIST

### 21.1 Unit Tests

- [ ] `TagManager.load_tags()` returns valid dict
- [ ] `TagManager.add_tag()` persists to JSON
- [ ] `ContentParser.parse_image_paths()` handles semicolons
- [ ] `ContentParser.to_whatsapp()` extracts images correctly
- [ ] `EmbeddingService.generate_embedding()` returns 768-dim vector
- [ ] `SearchService.calculate_relevance()` returns 0-100

### 21.2 Integration Tests

- [ ] Search returns results above threshold
- [ ] Search pre-filters by tag correctly
- [ ] FAQ CRUD operations work
- [ ] Cascade delete removes images
- [ ] WhatsApp webhook processes messages

### 21.3 E2E Tests

- [ ] User app search works
- [ ] Admin app can create/edit/delete FAQ
- [ ] Web V2 renders correctly
- [ ] WhatsApp bot responds to DM
- [ ] WhatsApp bot responds to group mention

### 21.4 Docker Tests

- [ ] All containers start successfully
- [ ] ChromaDB accessible from other containers
- [ ] Volumes persist data correctly
- [ ] Environment variables loaded correctly

---

## APPENDIX: Requirements.txt

```
streamlit==1.51.0
chromadb==1.3.4
pandas
google-genai
python-dotenv
pydantic-settings
fastapi
uvicorn
requests
pysqlite3-binary; sys_platform == 'linux'
watchdog
jinja2
python-multipart
markdown
bcrypt
Pillow
pytest
```

---

**END OF DOCUMENT**

*Dokumen ini dapat digunakan untuk merekonstruksi seluruh sistem dari awal dengan fitur dan arsitektur yang identik.*
