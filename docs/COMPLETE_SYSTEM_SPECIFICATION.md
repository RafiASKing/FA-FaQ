# COMPLETE SYSTEM SPECIFICATION
## Siloam EMR FAQ Multichannel Application

> **Dokumen ini berisi spesifikasi lengkap untuk merekonstruksi seluruh aplikasi dari nol.**
> **Versi:** 1.0 | **Tanggal:** Februari 2026

---

## DAFTAR ISI

1. [Ringkasan Eksekutif](#1-ringkasan-eksekutif)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Teknologi Stack](#3-teknologi-stack)
4. [Struktur Direktori](#4-struktur-direktori)
5. [Konfigurasi Environment](#5-konfigurasi-environment)
6. [Database Schema](#6-database-schema)
7. [Core Module: src/config.py](#7-core-module-srcconfigpy)
8. [Core Module: src/utils.py](#8-core-module-srcutilspy)
9. [Core Module: src/database.py](#9-core-module-srcdatabasepy)
10. [User Application: app.py](#10-user-application-apppy)
11. [Admin Application: admin.py](#11-admin-application-adminpy)
12. [WhatsApp Bot: bot_wa.py](#12-whatsapp-bot-bot_wapy)
13. [Web V2: FastAPI Application](#13-web-v2-fastapi-application)
14. [Docker Deployment](#14-docker-deployment)
15. [UI/UX Specifications](#15-uiux-specifications)
16. [Business Logic Rules](#16-business-logic-rules)
17. [API Endpoints](#17-api-endpoints)
18. [Testing Checklist](#18-testing-checklist)

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

## 2. ARSITEKTUR SISTEM

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│  ┌──────────────┬──────────────┬──────────────┬───────────────┐ │
│  │  Streamlit   │  Streamlit   │   FastAPI    │   FastAPI     │ │
│  │  User App    │  Admin App   │   Web V2     │   WA Bot      │ │
│  │  :8501       │  :8502       │   :8080      │   :8000       │ │
│  └──────────────┴──────────────┴──────────────┴───────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      SERVICE LAYER (src/)                       │
│  ┌─────────────────┬─────────────────┬────────────────────────┐ │
│  │   database.py   │    utils.py     │      config.py         │ │
│  │   (Vector DB)   │   (Helpers)     │   (Configuration)      │ │
│  └─────────────────┴─────────────────┴────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌─────────────────────────┬──────────────────────────────────┐ │
│  │       ChromaDB          │      Google Gemini API           │ │
│  │    (Vector Store)       │      (Embeddings)                │ │
│  │    Port: 8000           │      768-dimensional             │ │
│  └─────────────────────────┴──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow - Search

```
User Input (Query + Filter Tag)
         │
         ▼
┌─────────────────────────────┐
│  1. Generate Query Embedding │  ← Google Gemini API
│     (768 dimensions)         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  2. Pre-filter by Tag       │  ← ChromaDB WHERE clause
│     (if tag selected)        │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  3. Vector Similarity Search │  ← ChromaDB query()
│     (L2 Euclidean Distance)  │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  4. Score Calculation        │
│     score = (1 - distance) × 100
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  5. Filter: score > 41%      │
│     Keep Top 3 results       │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  6. Render Results           │
│     - Badge warna department │
│     - Score indicator        │
│     - Inline images          │
└─────────────────────────────┘
```

### 2.3 Data Flow - WhatsApp Bot

```
WhatsApp Message
         │
         ▼
┌─────────────────────────────┐
│  Fonnte/WPPConnect Gateway   │
│  Webhook → POST /webhook     │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Parse Message:              │
│  - remote_jid (sender)       │
│  - message_body              │
│  - is_group                  │
│  - mentionedJidList          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Should Reply?               │
│  - DM: Always YES            │
│  - Group: Only if @faq or    │
│    bot is mentioned          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Clean Query:                │
│  - Remove @faq               │
│  - Remove @mentions          │
│  - Trim whitespace           │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  search_faq_for_bot()        │
│  (Raw function, no cache)    │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Score Check:                │
│  - score > 41%: Send answer  │
│  - score ≤ 41%: Log failed + │
│    send "tidak ditemukan"    │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Send Response:              │
│  1. Text message (answer)    │
│  2. Images (if any)          │
│  3. Footer guidance          │
└─────────────────────────────┘
```

---

## 3. TEKNOLOGI STACK

### 3.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.10 | Core language |
| **Web Framework (User)** | Streamlit | 1.51.0 | User & Admin UI |
| **Web Framework (API)** | FastAPI | latest | WhatsApp bot, Web V2 |
| **Vector Database** | ChromaDB | 1.3.4 | Semantic search storage |
| **Embedding Model** | Google Gemini | embedding-001 | 768-dim vectors |
| **Template Engine** | Jinja2 | latest | HTML rendering |
| **ASGI Server** | Uvicorn | latest | FastAPI server |

### 3.2 Supporting Libraries

| Library | Purpose |
|---------|---------|
| `pandas` | DataFrame operations |
| `python-dotenv` | Environment variable loading |
| `requests` | HTTP client for WhatsApp API |
| `bcrypt` | Password hashing |
| `Pillow` | Image processing & compression |
| `markdown` | Markdown to HTML conversion |
| `pysqlite3-binary` | Enhanced SQLite for Linux/Docker |
| `watchdog` | File system monitoring |

### 3.3 External Services

| Service | Purpose |
|---------|---------|
| **Google Gemini API** | Generate embeddings |
| **WPPConnect** | WhatsApp gateway (self-hosted) |
| **Fonnte** | Alternative WhatsApp gateway (SaaS) |

---

## 4. STRUKTUR DIREKTORI

```
eighthExperiment/
│
├── app.py                          # Streamlit User Application
├── admin.py                        # Streamlit Admin Console
├── bot_wa.py                       # FastAPI WhatsApp Bot
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image definition
├── docker-compose.yml              # Multi-service orchestration
├── .env                            # Environment variables (SENSITIVE)
├── .env.example                    # Template for .env
├── .gitignore                      # Git ignore rules
│
├── src/                            # Core Business Logic
│   ├── __init__.py                 # Package marker
│   ├── config.py                   # Configuration management
│   ├── database.py                 # Vector DB operations
│   └── utils.py                    # Utility functions
│
├── web_v2/                         # FastAPI Web Application
│   ├── __init__.py                 # Package marker
│   ├── main.py                     # FastAPI routes
│   ├── templates/
│   │   └── index.html              # Jinja2 template
│   └── static/
│       └── style.css               # CSS styling
│
├── data/                           # Persistent Data
│   ├── chroma_data/                # ChromaDB vector storage
│   ├── tags_config.json            # Department/tag definitions
│   └── failed_searches.csv         # Failed search analytics
│
├── images/                         # Uploaded Images
│   ├── ED/                         # Emergency Department
│   ├── OPD/                        # Outpatient Department
│   ├── IPD/                        # Inpatient Department
│   ├── Lab/                        # Laboratory
│   ├── MR/                         # Medical Records
│   ├── Rehab/                      # Rehabilitation
│   ├── EMR Cashier/                # Cashier Module
│   ├── MCU/                        # Medical Check Up
│   ├── OOT/                        # Out of Topic
│   ├── Warning/                    # Alert items
│   └── Internal Bithealth/         # Company internal
│
├── wpp_sessions/                   # WhatsApp session data
│   └── config.json
│
├── wpp_tokens/                     # WhatsApp tokens (ephemeral)
│
├── .streamlit/                     # Streamlit config (optional)
│   └── config.toml
│
└── docs/                           # Documentation
    └── COMPLETE_SYSTEM_SPECIFICATION.md  # This file
```

---

## 5. KONFIGURASI ENVIRONMENT

### 5.1 File .env (Template)

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
BOT_IDENTITIES=6281234567890,6289876543210

# === BOT BEHAVIOR (Optional) ===
BOT_MIN_SCORE=80.0
BOT_MIN_GAP=10.0
```

### 5.2 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | **YES** | - | API key dari Google AI Studio |
| `ADMIN_PASSWORD_HASH` | YES | "admin" | bcrypt hash password admin |
| `CHROMA_HOST` | NO | - | Host ChromaDB server (kosong = local mode) |
| `CHROMA_PORT` | NO | - | Port ChromaDB server |
| `WA_BASE_URL` | YES* | - | URL WPPConnect API |
| `WA_SESSION_KEY` | YES* | - | Secret key untuk WPPConnect |
| `BOT_IDENTITIES` | YES* | - | Nomor HP bot (comma-separated) |
| `BOT_MIN_SCORE` | NO | 80.0 | Threshold confidence score |
| `BOT_MIN_GAP` | NO | 10.0 | Gap minimum antara hasil #1 dan #2 |

*Required hanya jika menggunakan WhatsApp Bot

---

## 6. DATABASE SCHEMA

### 6.1 ChromaDB Collection

**Collection Name:** `faq_universal_v1`

### 6.2 Document Structure

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
        "jawaban_tampil": "**Langkah 1:**\nBuka browser...[GAMBAR 1]",  # User-facing answer (with markdown & image tags)
        "keywords_raw": "gabisa login, lupa pwd, autentikasi gagal",   # HyDE variations
        "path_gambar": "./images/ED/cara_login_ED_1_a9k2q.jpg;./images/ED/cara_login_ED_2_b3m1x.jpg",  # Semicolon-delimited paths
        "sumber_url": "https://confluence.siloam.com/emr/login"  # Reference source
    }]
}
```

### 6.3 HyDE Embedding Format

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
ISI KONTEN: Untuk mendaftarkan pasien baru di IGD, ikuti langkah berikut. Pertama, buka modul Registration. Kedua, pilih New Patient...
```

**Kenapa pakai HyDE?**
- Menjembatani "semantic gap" antara bahasa panik user ("gak bisa masuk!") dengan dokumentasi formal ("Gagal Autentikasi")
- Format terstruktur membantu AI memahami konteks
- Universal dan bisa dipakai untuk domain lain

### 6.4 Tags Configuration (tags_config.json)

```json
{
    "ED": {
        "color": "#FF4B4B",
        "desc": "IGD, Emergency"
    },
    "OPD": {
        "color": "#2ECC71",
        "desc": "Rawat Jalan, Poli"
    },
    "IPD": {
        "color": "#3498DB",
        "desc": "Rawat Inap, Bangsal"
    },
    "MR": {
        "color": "#3498DB",
        "desc": "Medical Record"
    },
    "Rehab": {
        "color": "#3498DB",
        "desc": "Fisioterapi, Rehab Medik"
    },
    "Lab": {
        "color": "#FFA500",
        "desc": "Laboratorium"
    },
    "EMR Cashier": {
        "color": "#9B59B6",
        "desc": ""
    },
    "OOT": {
        "color": "#333333",
        "desc": "Out of Topic"
    },
    "Warning": {
        "color": "#9B59B6",
        "desc": ""
    },
    "Internal Bithealth": {
        "color": "#FFA500",
        "desc": "Peraturan Company"
    },
    "MCU": {
        "color": "#FFA500",
        "desc": "Medical Check Up, Pemeriksaan Kesehatan Rutin"
    }
}
```

### 6.5 Failed Searches Log (failed_searches.csv)

```csv
Timestamp,Query User
2024-01-18 10:15:23,Bagaimana cara edit resep di farmasi
2024-01-18 10:20:45,Gimana bikin pasien baru di IPD
2024-01-18 11:05:12,Error saat print barcode
```

---

## 7. CORE MODULE: src/config.py

### 7.1 Purpose
Mengelola semua konfigurasi aplikasi dari environment variables dan paths.

### 7.2 Complete Code

```python
import os
from dotenv import load_dotenv

# Load environment variables dari file .env
load_dotenv()

# --- API KEYS & AUTH ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "admin")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY belum diset! Cek file .env.")

# --- PATHS CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "faq_db")
TAGS_FILE = os.path.join(BASE_DIR, "data", "tags_config.json")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
FAILED_SEARCH_LOG = os.path.join(BASE_DIR, "data", "failed_searches.csv")
COLLECTION_NAME = "faq_universal_v1"

# Setup Folder
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# --- BOT LOGIC CONFIGURATION ---
try:
    BOT_MIN_SCORE = float(os.getenv("BOT_MIN_SCORE", "80.0"))
    BOT_MIN_GAP = float(os.getenv("BOT_MIN_GAP", "10.0"))
except ValueError:
    print("⚠️ Format angka di .env salah, menggunakan default (80.0 & 10.0)")
    BOT_MIN_SCORE = 80.0
    BOT_MIN_GAP = 10.0
```

### 7.3 Exported Constants

| Constant | Type | Description |
|----------|------|-------------|
| `GOOGLE_API_KEY` | str | API key Gemini |
| `ADMIN_PASSWORD_HASH` | str | bcrypt hash password admin |
| `BASE_DIR` | str | Root directory project |
| `DB_PATH` | str | Path ke ChromaDB local |
| `TAGS_FILE` | str | Path ke tags_config.json |
| `IMAGES_DIR` | str | Path ke folder images |
| `FAILED_SEARCH_LOG` | str | Path ke failed_searches.csv |
| `COLLECTION_NAME` | str | Nama collection ChromaDB |
| `BOT_MIN_SCORE` | float | Threshold confidence score |
| `BOT_MIN_GAP` | float | Minimum gap antara hasil |

---

## 8. CORE MODULE: src/utils.py

### 8.1 Purpose
Utility functions untuk tag management, image handling, dan text processing.

### 8.2 Complete Code

```python
import os
import json
import re
import random
import string
import time
import csv
from datetime import datetime
from PIL import Image
from .config import TAGS_FILE, IMAGES_DIR, BASE_DIR

# --- DAFTAR WARNA RESMI STREAMLIT (Restricted Palette) ---
COLOR_PALETTE = {
    "Merah":            {"hex": "#FF4B4B", "name": "red"},
    "Hijau":            {"hex": "#2ECC71", "name": "green"},
    "Biru":             {"hex": "#3498DB", "name": "blue"},
    "Orange":           {"hex": "#FFA500", "name": "orange"},
    "Ungu":             {"hex": "#9B59B6", "name": "violet"},
    "Abu-abu":          {"hex": "#808080", "name": "gray"},
    "Pelangi (Special)":{"hex": "#333333", "name": "rainbow"}
}

# --- 1. JSON TAG CONFIG ---
def load_tags_config():
    """Load tag configuration from JSON file. Creates default if not exists."""
    if not os.path.exists(TAGS_FILE):
        default_tags = {
            "ED": {"color": "#FF4B4B", "desc": "IGD, Emergency, Triage, Ambulans"},
            "OPD": {"color": "#2ECC71", "desc": "Rawat Jalan, Poli, Dokter Spesialis"},
            "IPD": {"color": "#3498DB", "desc": "Rawat Inap, Bangsal, Bed, Visite"},
            "Umum": {"color": "#808080", "desc": "General Info, IT Support"}
        }
        save_tags_config(default_tags)
        return default_tags
    with open(TAGS_FILE, "r") as f:
        return json.load(f)

def save_tags_config(tags_dict):
    """Save tag configuration to JSON file."""
    with open(TAGS_FILE, "w") as f:
        json.dump(tags_dict, f, indent=4)

# --- 2. SAFE ID GENERATOR ---
def get_next_id_safe(collection):
    """Generate next numeric ID for new documents."""
    try:
        data = collection.get(include=[])
        existing_ids = data['ids']
        if not existing_ids: return "1"

        numeric_ids = []
        for x in existing_ids:
            if x.isdigit():
                numeric_ids.append(int(x))

        if not numeric_ids: return "1"
        return str(max(numeric_ids) + 1)
    except Exception:
        return str(int(time.time()))

# --- 3. IMAGE HANDLING ---
def sanitize_filename(text):
    """Remove invalid characters from filename."""
    return re.sub(r'[^\w\-_]', '', text.replace(" ", "_"))[:30]

def save_uploaded_images(uploaded_files, judul, tag):
    """
    Save uploaded images with compression.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects
        judul: FAQ title (used for filename)
        tag: Department tag (used for folder organization)

    Returns:
        Semicolon-delimited string of relative paths, or "none"
    """
    if not uploaded_files: return "none"

    saved_paths = []
    clean_judul = sanitize_filename(judul)
    target_dir = os.path.join(IMAGES_DIR, tag)
    os.makedirs(target_dir, exist_ok=True)

    # Pillow resampling compatibility
    resample_module = getattr(Image, "Resampling", None)
    resample_method = resample_module.LANCZOS if resample_module else getattr(Image, "LANCZOS", Image.BICUBIC)
    max_width = 1024
    quality = 70

    for i, file in enumerate(uploaded_files):
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        filename = f"{clean_judul}_{tag}_{i+1}_{suffix}.jpg"
        full_path = os.path.join(target_dir, filename)

        try:
            if hasattr(file, "seek"):
                file.seek(0)
            image = Image.open(file)

            # Convert RGBA/P to RGB for JPEG
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Resize if too wide
            if image.width > max_width:
                ratio = max_width / float(image.width)
                new_height = int(float(image.height) * ratio)
                image = image.resize((max_width, new_height), resample_method)

            # Save with compression
            image.save(full_path, "JPEG", quality=quality, optimize=True)
        except Exception as e:
            print(f"⚠️ Gagal compress gambar {file.name}: {e}")
            # Fallback: save raw
            if hasattr(file, "seek"):
                file.seek(0)
            with open(full_path, "wb") as f:
                f.write(file.getbuffer())
        finally:
            if hasattr(file, "seek"):
                file.seek(0)

        rel_path = f"./images/{tag}/{filename}"
        saved_paths.append(rel_path)

    return ";".join(saved_paths)

def fix_image_path_for_ui(db_path):
    """Normalize image path from database for UI rendering."""
    clean = str(db_path).strip('"').strip("'")
    if clean.lower() == "none": return None
    clean = clean.replace("\\", "/")
    if clean.startswith("./"):
        return clean
    return clean

# --- 4. TEXT CLEANING FOR AI ---
def clean_text_for_embedding(text):
    """
    Remove [GAMBAR X] tags from text before embedding.
    Preserves markdown formatting like **bold** and lists.
    """
    if not text: return ""
    clean = re.sub(r'\[GAMBAR\s*\d+\]', '', text, flags=re.IGNORECASE)
    return " ".join(clean.split())

def log_failed_search(query):
    """Log failed search query to CSV for analytics."""
    filename = os.path.join(BASE_DIR, "data", "failed_searches.csv")
    file_exists = os.path.exists(filename)

    try:
        with open(filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Query User"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), query])
    except Exception as e:
        print(f"Gagal mencatat log: {e}")
```

### 8.3 Function Reference

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `load_tags_config()` | - | dict | Load tag config dari JSON |
| `save_tags_config(tags_dict)` | dict | - | Simpan tag config ke JSON |
| `get_next_id_safe(collection)` | ChromaDB collection | str | Generate next ID |
| `sanitize_filename(text)` | str | str | Clean filename dari karakter invalid |
| `save_uploaded_images(files, judul, tag)` | list, str, str | str | Upload & compress images |
| `fix_image_path_for_ui(db_path)` | str | str/None | Normalize path untuk UI |
| `clean_text_for_embedding(text)` | str | str | Remove image tags |
| `log_failed_search(query)` | str | - | Log query ke CSV |

---

## 9. CORE MODULE: src/database.py

### 9.1 Purpose
Handle semua operasi vector database (ChromaDB) dan embedding generation.

### 9.2 Key Design Decisions

1. **Dual-mode Database Access:**
   - Raw functions (`_get_db_client_raw()`) untuk Bot/API (no Streamlit dependency)
   - Cached functions (`get_db_client()`) untuk Streamlit apps (performance)

2. **Retry-on-Lock Decorator:**
   - Handle SQLite "database locked" errors
   - Jitter backoff untuk prevent thundering herd

3. **Auto Server/Local Detection:**
   - Jika `CHROMA_HOST` & `CHROMA_PORT` ada → Client-Server mode
   - Jika tidak ada → Local file mode

### 9.3 Complete Code

```python
# --- 1. FORCE USE NEW SQLITE (Wajib Paling Atas untuk Docker/Linux) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# --- 2. IMPORTS ---
import chromadb
import pandas as pd
import streamlit as st
import time
import functools
import random
import os
from google import genai
from google.genai import types
from .config import GOOGLE_API_KEY, DB_PATH, COLLECTION_NAME
from .utils import clean_text_for_embedding, load_tags_config

# --- 3. RETRY DECORATOR ---
def retry_on_lock(max_retries=10, base_delay=0.1):
    """Handle 'Database Locked' errors with jitter backoff."""
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
            raise Exception("Database sedang sibuk (High Traffic), silakan coba lagi sesaat.")
        return wrapper
    return decorator

# --- 4. RAW FUNCTIONS (FOR BOT/API) ---
def _get_ai_client_raw():
    """Create Gemini client (no Streamlit cache)."""
    return genai.Client(api_key=GOOGLE_API_KEY)

def _get_db_client_raw():
    """
    Smart DB client:
    - If CHROMA_HOST/PORT set → Server mode (Docker/Production)
    - Otherwise → Local file mode
    """
    host = os.getenv("CHROMA_HOST")
    port = os.getenv("CHROMA_PORT")

    if host and port:
        return chromadb.HttpClient(host=host, port=int(port))
    else:
        return chromadb.PersistentClient(path=DB_PATH)

def _generate_embedding_raw(text):
    """Generate embedding directly (no Streamlit cache)."""
    client = _get_ai_client_raw()
    try:
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Error Embedding AI: {e}")
        return []

# --- 5. STREAMLIT CACHED FUNCTIONS ---
@st.cache_resource(show_spinner=False)
def get_db_client():
    return _get_db_client_raw()

@st.cache_resource(show_spinner=False)
def get_ai_client():
    return _get_ai_client_raw()

def get_collection():
    client = get_db_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

@st.cache_data(show_spinner=False)
def generate_embedding_cached(text):
    return _generate_embedding_raw(text)

# --- 6. INTERNAL HELPER ---
def _get_next_id_internal(collection):
    data = collection.get(include=[])
    existing_ids = data['ids']

    if not existing_ids: return "1"

    numeric_ids = []
    for x in existing_ids:
        if x.isdigit():
            numeric_ids.append(int(x))

    if not numeric_ids: return "1"
    return str(max(numeric_ids) + 1)

# --- 7. READ OPERATIONS (USER WEB APP) ---
@retry_on_lock()
def search_faq(query_text, filter_tag=None, n_results=50):
    """
    Search FAQ using semantic similarity.
    Used by app.py (Streamlit). Uses cached embedding.
    """
    col = get_collection()
    vec = generate_embedding_cached(query_text)

    if not vec:
        return {"ids": [[]], "metadatas": [[]], "distances": [[]]}

    where_clause = {"tag": filter_tag} if (filter_tag and filter_tag != "Semua Modul") else None

    return col.query(
        query_embeddings=[vec],
        n_results=n_results,
        where=where_clause
    )

@retry_on_lock()
def get_all_faqs_sorted():
    """Get all FAQs sorted by ID descending (newest first)."""
    col = get_collection()
    data = col.get(include=['metadatas'])

    results = []
    if data['ids']:
        for i, doc_id in enumerate(data['ids']):
            meta = data['metadatas'][i]
            try: id_num = int(doc_id)
            except: id_num = 0

            meta['id'] = doc_id
            meta['id_num'] = id_num
            results.append(meta)

    results.sort(key=lambda x: x.get('id_num', 0), reverse=True)
    return results

def get_unique_tags_from_db():
    """Extract unique tags from database for dropdown."""
    col = get_collection()
    data = col.get(include=['metadatas'])
    unique_tags = set()
    if data['metadatas']:
        for meta in data['metadatas']:
            if meta and meta.get('tag'):
                unique_tags.add(meta['tag'])
    return sorted(list(unique_tags))

# --- 8. WRITE OPERATIONS (ADMIN) ---
@st.cache_data(show_spinner=False)
def get_all_data_as_df():
    """Get all data as Pandas DataFrame for admin table."""
    col = get_collection()
    data = col.get(include=['metadatas', 'documents'])

    if not data['ids']: return pd.DataFrame()

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
    return df.sort_values('ID_Num', ascending=False).drop(columns=['ID_Num'])

@retry_on_lock()
def upsert_faq(doc_id, tag, judul, jawaban, keyword, img_paths, src_url):
    """Insert or update FAQ document."""
    col = get_collection()

    final_id = str(doc_id)
    if doc_id == "auto" or doc_id is None:
        final_id = _get_next_id_internal(col)

    clean_jawaban = clean_text_for_embedding(jawaban)

    try:
        tags_config = load_tags_config()
        tag_desc = tags_config.get(tag, {}).get("desc", "")
    except:
        tag_desc = ""

    domain_str = f"{tag} ({tag_desc})" if tag_desc else tag

    # HyDE Embedding Format
    text_embed = f"""DOMAIN: {domain_str}
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keyword}
ISI KONTEN: {clean_jawaban}"""

    vector = generate_embedding_cached(text_embed)

    col.upsert(
        ids=[final_id],
        embeddings=[vector],
        documents=[text_embed],
        metadatas=[{
            "tag": tag,
            "judul": judul,
            "jawaban_tampil": jawaban,
            "keywords_raw": keyword,
            "path_gambar": img_paths,
            "sumber_url": src_url
        }]
    )
    return final_id

@retry_on_lock()
def delete_faq(doc_id):
    """Delete FAQ and its associated images (cascade delete)."""
    col = get_collection()
    try:
        data = col.get(ids=[str(doc_id)], include=['metadatas'])
        if data['metadatas'] and len(data['metadatas']) > 0:
            meta = data['metadatas'][0]
            img_str = meta.get('path_gambar', 'none')
            if img_str and img_str.lower() != 'none':
                paths = img_str.split(';')
                for p in paths:
                    clean_path = p.replace("\\", "/")
                    if os.path.exists(clean_path):
                        try:
                            os.remove(clean_path)
                            print(f"🗑️ Zombie File Deleted: {clean_path}")
                        except Exception as e:
                            print(f"⚠️ Gagal hapus file {clean_path}: {e}")
    except Exception as e:
        print(f"⚠️ Error cleaning images: {e}")

    col.delete(ids=[str(doc_id)])

# --- 9. SPECIAL FUNCTION FOR BOT (NO STREAMLIT) ---
@retry_on_lock()
def search_faq_for_bot(query_text, filter_tag="Semua Modul"):
    """
    Search FAQ for WhatsApp bot.
    INDEPENDENT: Opens own connection, generates own embedding.
    No Streamlit dependency.
    """
    client = _get_db_client_raw()
    col = client.get_or_create_collection(name=COLLECTION_NAME)

    vec = _generate_embedding_raw(query_text)

    if not vec:
        return None

    where_clause = {"tag": filter_tag} if (filter_tag and filter_tag != "Semua Modul") else None

    results = col.query(
        query_embeddings=[vec],
        n_results=5,
        where=where_clause
    )

    return results
```

### 9.4 Function Reference

| Function | Mode | Description |
|----------|------|-------------|
| `_get_ai_client_raw()` | Raw | Get Gemini client (no cache) |
| `_get_db_client_raw()` | Raw | Get ChromaDB client (auto server/local) |
| `_generate_embedding_raw(text)` | Raw | Generate embedding (no cache) |
| `get_db_client()` | Cached | Streamlit-cached DB client |
| `get_ai_client()` | Cached | Streamlit-cached Gemini client |
| `get_collection()` | Cached | Get ChromaDB collection |
| `generate_embedding_cached(text)` | Cached | Cached embedding generation |
| `search_faq(query, filter_tag, n_results)` | Cached | Search for web app |
| `search_faq_for_bot(query, filter_tag)` | Raw | Search for bot |
| `get_all_faqs_sorted()` | Raw | Get all FAQs sorted by ID desc |
| `get_unique_tags_from_db()` | Raw | Get unique tags for dropdown |
| `get_all_data_as_df()` | Cached | Get all data as DataFrame |
| `upsert_faq(...)` | Decorated | Insert/update FAQ |
| `delete_faq(doc_id)` | Decorated | Delete FAQ + images |

---

## 10. USER APPLICATION: app.py

### 10.1 Purpose
Main user-facing web application for searching and browsing FAQs.

### 10.2 Features

1. **Search Mode** - Semantic search dengan Top 3 results (score > 41%)
2. **Browse Mode** - Tampilkan semua FAQ terbaru dengan pagination
3. **Department Filter** - Pre-filter by tag sebelum search
4. **Confidence Badges** - Visual indicator relevansi (green/orange/red)
5. **Inline Images** - Support `[GAMBAR X]` syntax
6. **Failed Search CTA** - WhatsApp link untuk escalation

### 10.3 UI Layout

```
┌────────────────────────────────────────────────────┐
│  ⚡ Fast Cognitive Search System                   │
│  Smart Knowledge Base Retrieval                    │
├────────────────────────────────────────────────────┤
│  [Search Input........................] [Filter ▼] │
├────────────────────────────────────────────────────┤
│  Menampilkan 1-3 dari 3 data                       │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │ [ED] Cara Login EMR ED         (85% Relevansi)  │
│  ├──────────────────────────────────────────────┤  │
│  │ [Expanded Content]                           │  │
│  │ - Text with **markdown**                     │  │
│  │ - [GAMBAR 1] → Inline image                  │  │
│  │ 🔗 Buka Sumber Referensi                     │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  [⬅️ Sebelumnya] [Page 1/3] [Berikutnya ➡️]       │
└────────────────────────────────────────────────────┘
```

### 10.4 Complete Code

```python
import streamlit as st
import os
import math
import re
import warnings
from src import database, utils

# --- 1. CONFIG & SUPPRESS WARNINGS ---
st.set_page_config(page_title="Hospital Knowledge Base", page_icon="🏥", layout="centered")
warnings.filterwarnings("ignore")

# Load Tag Configuration
TAGS_MAP = utils.load_tags_config()

# CSS Styling
st.markdown("""
<style>
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: white;
        margin-bottom: 10px;
    }
    div[data-testid="stExpander"] p {
        font-size: 15px;
        font-family: sans-serif;
    }
    .stApp {
        background-color: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def get_badge_color_name(tag):
    """Convert HEX code to Streamlit color name."""
    tag_data = TAGS_MAP.get(tag, {})
    hex_code = tag_data.get("color", "#808080").upper()

    hex_to_name = {
        "#FF4B4B": "red",
        "#2ECC71": "green",
        "#3498DB": "blue",
        "#FFA500": "orange",
        "#9B59B6": "violet",
        "#808080": "gray",
        "#333333": "gray"
    }

    return hex_to_name.get(hex_code, "gray")

def render_image_safe(image_path):
    if image_path and os.path.exists(image_path):
        st.image(image_path, use_container_width=True)

def render_mixed_content(jawaban_text, images_str):
    """Render text with inline images based on [GAMBAR X] tags."""
    if not images_str or str(images_str).lower() == 'none':
        st.markdown(jawaban_text)
        return

    img_list = images_str.split(';')
    img_list = [x for x in img_list if x.strip()]
    parts = re.split(r'(\[GAMBAR\s*\d+\])', jawaban_text, flags=re.IGNORECASE)

    # Case 1: Fallback (Images at bottom)
    if len(parts) == 1:
        st.markdown(jawaban_text)
        if img_list:
            st.markdown("---")
            cols = st.columns(min(3, len(img_list)))
            for idx, p in enumerate(img_list):
                clean_p = utils.fix_image_path_for_ui(p)
                if clean_p and os.path.exists(clean_p):
                    with cols[idx % 3]:
                        st.image(clean_p, use_container_width=True)
        return

    # Case 2: Inline (Interleaved)
    for part in parts:
        match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
        if match:
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_list):
                    clean_p = utils.fix_image_path_for_ui(img_list[idx])
                    if clean_p and os.path.exists(clean_p):
                        render_image_safe(clean_p)
                    else:
                        st.error(f"🖼️ File gambar tidak ditemukan: {clean_p}")
                else:
                    st.caption(f"*(Gambar #{idx+1} tidak tersedia)*")
            except ValueError: pass
        else:
            if part.strip(): st.markdown(part)

# --- 3. STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = 0
if 'last_query' not in st.session_state: st.session_state.last_query = ""
if 'last_filter' not in st.session_state: st.session_state.last_filter = ""

# --- 4. HEADER UI ---
st.title("⚡Fast Cognitive Search System")
st.caption("Smart Knowledge Base Retrieval")

col_q, col_f = st.columns([3, 1])
with col_q:
    query = st.text_input("Cari isu/kendala:", placeholder="Ketik masalah (cth: Kenapa Gagal Retur Obat, gagal discharge)...")
with col_f:
    try:
        db_tags = database.get_unique_tags_from_db()
    except:
        db_tags = []
    all_tags = ["Semua Modul"] + (db_tags if db_tags else [])
    filter_tag = st.selectbox("Filter:", all_tags)

# --- 5. SEARCH LOGIC ---
if query != st.session_state.last_query or filter_tag != st.session_state.last_filter:
    st.session_state.page = 0
    st.session_state.last_query = query
    st.session_state.last_filter = filter_tag

results = []
is_search_mode = False

if query:
    is_search_mode = True
    raw = database.search_faq(query, filter_tag, n_results=50)

    if raw['ids'][0]:
        for i in range(len(raw['ids'][0])):
            meta = raw['metadatas'][0][i]
            dist = raw['distances'][0][i]
            score = max(0, (1 - dist) * 100)

            # Minimum threshold: 41%
            if score > 41:
                meta['score'] = score
                results.append(meta)

        # Keep Top 3 only
        results = results[:3]
else:
    raw_all = database.get_all_faqs_sorted()
    if filter_tag == "Semua Modul":
        results = raw_all
    else:
        results = [x for x in raw_all if x.get('tag') == filter_tag]

# --- 6. PAGINATION & DISPLAY ---
ITEMS_PER_PAGE = 10
total_docs = len(results)
total_pages = math.ceil(total_docs / ITEMS_PER_PAGE)

if st.session_state.page >= total_pages and total_pages > 0:
    st.session_state.page = 0

start_idx = st.session_state.page * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
page_data = results[start_idx:end_idx]

st.divider()

if not page_data:
    if is_search_mode:
        # Log failed search
        try: utils.log_failed_search(query)
        except: pass

        # WhatsApp CTA
        st.warning(f"❌ Tidak ditemukan hasil yang relevan (Relevansi < 41%).")

        st.markdown("""
        ### 🧐 Belum ada solusinya?
        Sistem telah mencatat pencarianmu untuk perbaikan. Sementara itu, kamu bisa:

        1. Coba gunakan kata kunci yang lebih umum.
        2. Atau langsung request bantuan ke Tim IT Support:
        """)

        wa_number = "6289635225253"  # GANTI DENGAN NOMOR SUPPORT
        wa_text = f"Halo Admin, saya cari solusi tentang '{query}' tapi tidak ketemu di aplikasi FAQ."
        wa_link = f"https://wa.me/{wa_number}?text={wa_text.replace(' ', '%20')}"

        st.markdown(f'''
        <a href="{wa_link}" target="_blank" style="text-decoration: none;">
            <button style="
                background-color: #25D366;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                font-size: 16px;
                display: flex;
                align_items: center;
                gap: 8px;">
                📱 Chat WhatsApp Support
            </button>
        </a>
        ''', unsafe_allow_html=True)

    else:
        st.info("👋 Selamat Datang. Database siap digunakan.")
else:
    st.markdown(f"**Menampilkan {start_idx+1}-{min(end_idx, total_docs)} dari {total_docs} data**")

    for item in page_data:
        tag = item.get('tag', 'Umum')
        badge_color = get_badge_color_name(tag)

        # Score color logic
        score_md = ""
        if item.get('score'):
            sc = item['score']

            if sc > 80:
                score_md = f":green[**({sc:.0f}% Relevansi) 🌟**]"
            elif sc > 50:
                score_md = f":green[({sc:.0f}% Relevansi)]"
            elif sc > 41:
                score_md = f":orange[({sc:.0f}% Relevansi)]"
            else:
                score_md = f":red[({sc:.0f}% Relevansi)]"

        label = f":{badge_color}-background[{tag}] **{item.get('judul')}** {score_md}"

        with st.expander(label):
            render_mixed_content(item.get('jawaban_tampil', '-'), item.get('path_gambar'))

            src_raw = item.get('sumber_url')
            if src_raw and len(str(src_raw)) > 3:
                src = str(src_raw).strip()
                if "http" in src and " " not in src:
                    st.markdown(f"🔗 [Buka Sumber Referensi]({src})")
                else:
                    st.markdown(f"🔗 **Sumber:** {src}")

    # Pagination buttons
    if total_pages > 1:
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.session_state.page > 0:
                if st.button("⬅️ Sebelumnya"):
                    st.session_state.page -= 1
                    st.rerun()
        with c3:
            if st.session_state.page < total_pages - 1:
                if st.button("Berikutnya ➡️"):
                    st.session_state.page += 1
                    st.rerun()
```

### 10.5 Score Color Rules

| Score Range | Color | Display |
|-------------|-------|---------|
| > 80% | Green Bold + 🌟 | `(85% Relevansi) 🌟` |
| 50-80% | Green | `(65% Relevansi)` |
| 41-50% | Orange | `(45% Relevansi)` |
| < 41% | Hidden | Result not shown |

---

## 11. ADMIN APPLICATION: admin.py

### 11.1 Purpose
Content management console untuk CRUD FAQ/SOP.

### 11.2 Features

1. **Password Protected** - bcrypt authentication
2. **5 Tabs:**
   - 📊 Database - View all FAQs
   - ➕ New FAQ - Create with preview
   - ✏️ Edit/Delete - Modify existing
   - ⚙️ Config Tags - Manage departments
   - 📈 Analytics - Failed search logs
3. **Smart Toolbar** - Auto-increment image tags
4. **Draft Preservation** - Anti-amnesia across page reloads
5. **Preview Mode** - Review before publish
6. **Backup/Restore** - ZIP archive of data + images

### 11.3 UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  🛠️ Admin Console (Safe Mode)                          │
├─────────────────────────────────────────────────────────┤
│  [📊 Database] [➕ New] [✏️ Edit] [⚙️ Tags] [📈 Stats] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  (Tab Content)                                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 11.4 Complete Code

```python
import streamlit as st
import pandas as pd
import time
import re
import os
from src import database, utils
from src.config import ADMIN_PASSWORD_HASH, FAILED_SEARCH_LOG, BASE_DIR
import bcrypt
import shutil

# --- AUTH STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False

def login():
    input_bytes = st.session_state.pass_input.encode('utf-8')
    target_hash = ADMIN_PASSWORD_HASH.encode('utf-8')

    if bcrypt.checkpw(input_bytes, target_hash):
        st.session_state.auth = True
    else:
        st.error("Password salah")

# --- LOGIN SCREEN ---
if not st.session_state.auth:
    st.set_page_config(page_title="Admin Login")
    st.markdown("<h1 style='text-align: center;'>🔒 Admin Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.text_input("Password", type="password", key="pass_input", on_change=login)
    st.stop()

# --- MAIN UI SETUP ---
st.set_page_config(page_title="Admin Console", layout="wide")
st.title("🛠️ Admin Console (Safe Mode)")
tags_map = utils.load_tags_config()

# State Management
if 'preview_mode' not in st.session_state: st.session_state.preview_mode = False
if 'draft_data' not in st.session_state: st.session_state.draft_data = {}

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Database", "➕ New FaQ", "✏️ Edit/Delete FaQ", "⚙️ Config Tags", "📈 Analytics"
])

# === TAB 1: LIST DATA ===
with tab1:
    if st.button("🔄 Refresh Data"):
        database.get_all_data_as_df.clear()
        st.rerun()

    df = database.get_all_data_as_df()
    st.dataframe(df, use_container_width=True, hide_index=True)

# === TAB 2: ADD NEW FAQ ===
with tab2:
    def add_text(text):
        if 'in_a' in st.session_state:
            st.session_state.in_a += text

    def add_next_image_tag():
        current_text = st.session_state.get('in_a', "")
        matches = re.findall(r'\[GAMBAR\s*\d+\]', current_text, flags=re.IGNORECASE)
        next_num = len(matches) + 1
        tag_to_insert = f"\n[GAMBAR {next_num}]\n"
        st.session_state.in_a += tag_to_insert

    # PHASE 1: INPUT FORM
    if not st.session_state.preview_mode:
        default_tag = st.session_state.draft_data.get('tag', list(tags_map.keys())[0])
        default_judul = st.session_state.draft_data.get('judul', '')
        default_jawab = st.session_state.draft_data.get('jawab', '')
        default_key = st.session_state.draft_data.get('key', '')
        default_src = st.session_state.draft_data.get('src', '')

        try: idx_tag = list(tags_map.keys()).index(default_tag)
        except: idx_tag = 0

        st.subheader("📝 FaQ/SOP Baru")

        col_m, col_j = st.columns([1, 3])
        with col_m: i_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx_tag, key="in_t")
        with col_j: i_judul = st.text_input("Judul Masalah (Pertanyaan/SOP)", value=default_judul, key="in_j")

        st.markdown("**Jawaban / Solusi:**")

        tb1, tb2, tb3, tb_spacer = st.columns([1, 1, 2, 4])
        tb1.button("𝗕 Bold", on_click=add_text, args=(" **teks tebal** ",),
                   help="Tebalkan teks", use_container_width=True)
        tb2.button("Bars", on_click=add_text, args=("\n- Langkah 1\n- Langkah 2",),
                   help="Buat List", use_container_width=True)
        tb3.button("+ Klik ini untuk add penanda gambar", on_click=add_next_image_tag,
                   type="primary", icon="🖼️", use_container_width=True)

        i_jawab = st.text_area("Editor", value=default_jawab, height=300, key="in_a", label_visibility="collapsed")
        st.caption("💡 *Tips: Klik tombol '📸' untuk memasukkan placeholder gambar secara urut.*")

        c_k, c_s = st.columns(2)
        with c_k:
            st.markdown("Term terkait / Bahasa User (HyDE) 👇")
            i_key = st.text_input("Hidden Label", value=default_key, key="in_k",
                                  placeholder="Contoh: Gabisa login, User not found, Kok gagal discharge?...",
                                  label_visibility="collapsed")
        with c_s:
            st.markdown("Sumber Info/Source URL")
            i_src = st.text_input("Hidden Label 2", value=default_src, key="in_s", label_visibility="collapsed")

        i_imgs = st.file_uploader("Upload Gambar", accept_multiple_files=True, key="in_i")

        st.divider()
        if st.button("🔍 Lanjut ke Preview", type="primary", use_container_width=True):
            if not i_judul or not i_jawab:
                st.error("Judul & Jawaban wajib diisi!")
            else:
                st.session_state.draft_data = {
                    "tag": i_tag, "judul": i_judul, "jawab": i_jawab,
                    "key": i_key, "src": i_src, "imgs": i_imgs
                }
                st.session_state.preview_mode = True
                st.rerun()

    # PHASE 2: PREVIEW & SUBMIT
    else:
        draft = st.session_state.draft_data
        st.info("📱 **Mode Preview:** Periksa tampilan sebelum Publish.")

        with st.container(border=True):
            hex_color = tags_map.get(draft['tag'], {}).get("color", "#808080")
            st.markdown(f"### <span style='color:{hex_color}'>[{draft['tag']}]</span> {draft['judul']}", unsafe_allow_html=True)
            st.caption(f"🔑 Keywords/HyDE: {draft['key']}")
            st.divider()

            parts = re.split(r'(\[GAMBAR\s*\d+\])', draft['jawab'], flags=re.IGNORECASE)
            imgs = draft['imgs'] or []

            for part in parts:
                match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
                if match:
                    try:
                        idx = int(match.group(1)) - 1
                        if 0 <= idx < len(imgs):
                            st.image(imgs[idx], width=400, caption=f"Gambar {idx+1}")
                        else:
                            st.warning(f"⚠️ [GAMBAR {idx+1}] ditulis tapi file belum diupload.")
                    except: pass
                else:
                    if part.strip(): st.markdown(part)

        st.divider()
        c_back, c_save = st.columns([1, 3])

        with c_back:
            if st.button("⬅️ Edit Lagi", use_container_width=True):
                st.session_state.preview_mode = False
                st.rerun()

        with c_save:
            if st.button("💾 PUBLISH KE DATABASE", type="primary", use_container_width=True):
                try:
                    with st.spinner("Menyimpan ke ChromaDB..."):
                        paths = utils.save_uploaded_images(draft['imgs'], draft['judul'], draft['tag'])
                        new_id = database.upsert_faq(
                            doc_id="auto",
                            tag=draft['tag'],
                            judul=draft['judul'],
                            jawaban=draft['jawab'],
                            keyword=draft['key'],
                            img_paths=paths,
                            src_url=draft['src']
                        )

                        st.balloons()
                        st.success(f"✅ Data Tersimpan! ID Dokumen: {new_id}")
                        database.get_all_data_as_df.clear()

                        st.session_state.preview_mode = False
                        st.session_state.draft_data = {}
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error Save: {e}")

# === TAB 3: EDIT/DELETE ===
with tab3:
    st.header("✏️ Edit Data Lama")
    df_e = database.get_all_data_as_df()

    if not df_e.empty:
        opts = [f"{r['ID']} | {r['Judul']}" for _, r in df_e.iterrows()]
        sel = st.selectbox("Pilih Data", opts)

        if sel:
            sel_id = sel.split(" | ")[0]
            row = df_e[df_e['ID'] == sel_id].iloc[0]

            with st.form("edit_form"):
                curr = row['Tag']
                idx = list(tags_map.keys()).index(curr) if curr in tags_map else 0

                c_id, c_t = st.columns([1, 4])
                with c_id: st.text_input("ID", value=sel_id, disabled=True)
                with c_t: e_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx)

                e_jud = st.text_input("Judul SOP", value=row['Judul'])
                e_jaw = st.text_area("Jawaban (Gunakan [GAMBAR X])", value=row['Jawaban'], height=200)
                e_key = st.text_input("Keyword / Bahasa User (HyDE)", value=row['Keyword'])
                e_src = st.text_input("Source URL", value=row['Source'])

                st.markdown(f"**Path Gambar Saat Ini:** `{row['Gambar']}`")
                e_new = st.file_uploader("Timpa Gambar Baru (Opsional)", accept_multiple_files=True)

                st.divider()

                c_up, c_space, c_del = st.columns([4, 0.5, 2])

                with c_up:
                    is_update = st.form_submit_button("💾 UPDATE DATA", type="primary", use_container_width=True)
                with c_del:
                    is_delete = st.form_submit_button("🗑️ Hapus Permanen", type="secondary", use_container_width=True)

                if is_update:
                    p = row['Gambar']
                    if e_new:
                        p = utils.save_uploaded_images(e_new, e_jud, e_tag)

                    database.upsert_faq(sel_id, e_tag, e_jud, e_jaw, e_key, p, e_src)
                    st.toast("Data Berhasil Diupdate!", icon="✅")
                    database.get_all_data_as_df.clear()
                    time.sleep(1)
                    st.rerun()

                if is_delete:
                    database.delete_faq(sel_id)
                    st.toast("Data & Gambar Telah Dihapus.", icon="🗑️")
                    database.get_all_data_as_df.clear()
                    time.sleep(1)
                    st.rerun()

# === TAB 4: CONFIG TAGS ===
with tab4:
    st.subheader("⚙️ Konfigurasi Tag")

    flat = [{"Tag":k, "Warna":v.get("color",""), "Sinonim":v.get("desc","")} for k,v in tags_map.items()]
    st.dataframe(pd.DataFrame(flat), use_container_width=True, hide_index=True)

    st.divider()

    with st.expander("➕ Tambah / Update Tag", expanded=True):
        with st.form("conf_f", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: n_name = st.text_input("Nama Tag (ex: ED)")
            with c2: n_col = st.selectbox("Warna Badge", list(utils.COLOR_PALETTE.keys()))
            n_desc = st.text_input("Sinonim / Kepanjangan", placeholder="ex: Emergency, Poli, Medical Record")

            if st.form_submit_button("Simpan Konfigurasi"):
                if n_name:
                    hex_c = utils.COLOR_PALETTE[n_col]["hex"]
                    tags_map[n_name] = {"color": hex_c, "desc": n_desc}
                    utils.save_tags_config(tags_map)
                    st.toast(f"Tag '{n_name}' berhasil disimpan!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nama Tag wajib diisi.")

    with st.expander("🗑️ Hapus Tag", expanded=False):
        st.markdown("### Hapus Tag dari Sistem")
        del_tag = st.selectbox("Pilih Tag untuk dihapus", list(tags_map.keys()), key="del_tag_sel")

        df_check = database.get_all_data_as_df()
        if not df_check.empty:
            count_usage = len(df_check[df_check['Tag'] == del_tag])
        else:
            count_usage = 0

        if count_usage > 0:
            st.error(f"⚠️ **PERINGATAN:** Tag `{del_tag}` masih digunakan oleh **{count_usage} Dokumen**!")
        else:
            st.success(f"✅ Aman: Tidak ada dokumen yang menggunakan tag `{del_tag}`.")

        c_del_warn, c_del_btn = st.columns([3, 1])
        with c_del_btn:
            if st.button("🔥 Hapus Tag Ini", type="primary", use_container_width=True):
                if del_tag in tags_map:
                    del tags_map[del_tag]
                    utils.save_tags_config(tags_map)
                    st.toast(f"Tag '{del_tag}' telah dihapus.", icon="🗑️")
                    time.sleep(1)
                    st.rerun()

    st.divider()
    st.subheader("💾 Backup & Restore")

    if st.button("📦 Download Full Backup", key="backup_btn"):
        with st.spinner("Mempersiapkan arsip backup..."):
            temp_dir = os.path.join(BASE_DIR, "tmp_backup_bundle")
            archive_base = os.path.join(BASE_DIR, f"backup_faq_{int(time.time())}")
            archive_file = ""
            backup_bytes = None
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                os.makedirs(temp_dir, exist_ok=True)

                copied_any = False
                for folder_name in ["data", "images"]:
                    src_path = os.path.join(BASE_DIR, folder_name)
                    dst_path = os.path.join(temp_dir, folder_name)
                    if os.path.exists(src_path):
                        shutil.copytree(src_path, dst_path)
                        copied_any = True

                if not copied_any:
                    st.warning("Folder data/images tidak ditemukan.")
                else:
                    archive_file = shutil.make_archive(archive_base, 'zip', temp_dir)
                    with open(archive_file, "rb") as f:
                        backup_bytes = f.read()
            except Exception as e:
                st.error(f"Gagal membuat backup: {e}")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                if archive_file and os.path.exists(archive_file):
                    os.remove(archive_file)

        if backup_bytes:
            st.download_button(
                label="⬇️ Klik untuk Simpan ZIP",
                data=backup_bytes,
                file_name=f"backup_faq_{int(time.time())}.zip",
                mime="application/zip"
            )

# === TAB 5: ANALYTICS ===
with tab5:
    st.subheader("📈 Pencarian Gagal (User Feedback)")
    st.caption("Query yang dicari User tapi hasilnya < 41% (Tidak Relevan).")

    if utils.os.path.exists(FAILED_SEARCH_LOG):
        df_log = pd.read_csv(FAILED_SEARCH_LOG)

        col1, col2 = st.columns([4, 1])
        with col1:
            st.metric("Total Miss", len(df_log))
        with col2:
            if st.button("🗑️ Clear Log"):
                utils.os.remove(FAILED_SEARCH_LOG)
                st.rerun()

        if not df_log.empty:
            df_log = df_log.sort_values(by="Timestamp", ascending=False)
            st.dataframe(df_log, use_container_width=True)
    else:
        st.info("Belum ada data pencarian gagal. Sistem bekerja dengan baik!")
```

---

## 12. WHATSAPP BOT: bot_wa.py

### 12.1 Purpose
WhatsApp gateway menggunakan WPPConnect untuk menerima dan membalas pesan.

### 12.2 Features

1. **Webhook Receiver** - `POST /webhook`
2. **Selective Reply Logic:**
   - DM (Private Chat) → Always reply
   - Group → Only if `@faq` or bot mentioned
3. **Multi-bot Identity** - Support multiple phone numbers
4. **Auto Token Refresh** - Regenerate on 401
5. **Image Sending** - Base64 encoded

### 12.3 Complete Code

```python
import os
import requests
import uvicorn
import re
import base64
import mimetypes
import json
import sys
import time
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from src import database, utils

load_dotenv()

app = FastAPI()

# --- CONFIGURATION ---
WA_BASE_URL = os.getenv("WA_BASE_URL", "http://wppconnect:21465")
WA_SECRET_KEY = os.getenv("WA_SESSION_KEY", "THISISMYSECURETOKEN")
WA_SESSION_NAME = "mysession"
WEB_V2_URL = "https://faq-assist.cloud/"  # Your web app URL

# Multiple bot identities
raw_ids = os.getenv("BOT_IDENTITIES", "")
MY_IDENTITIES = [x.strip() for x in raw_ids.split(",") if x.strip()]

CURRENT_TOKEN = None

def log(message):
    print(message, flush=True)

# --- AUTH FUNCTIONS ---
def get_headers():
    global CURRENT_TOKEN
    if not CURRENT_TOKEN:
        log("🔄 Token kosong. Mencoba generate token baru...")
        generate_token()
    return {
        "Authorization": f"Bearer {CURRENT_TOKEN}",
        "Content-Type": "application/json"
    }

def generate_token():
    global CURRENT_TOKEN
    try:
        url = f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/{WA_SECRET_KEY}/generate-token"
        r = requests.post(url)
        if r.status_code in [200, 201]:
            resp = r.json()
            token = resp.get("token") or resp.get("session")
            if not token and "full" in resp: token = resp["full"].split(":")[-1]
            if token:
                CURRENT_TOKEN = token
                log(f"✅ Berhasil Generate Token.")
            else: log(f"❌ Gagal Parse Token.")
        else: log(f"❌ Gagal Generate Token: {r.status_code}")
    except Exception as e: log(f"❌ Error Auth: {e}")

# --- UTILITY FUNCTIONS ---
def get_base64_image(file_path):
    try:
        clean_path = file_path.replace("\\", "/")
        if not os.path.exists(clean_path): return None, None
        mime_type, _ = mimetypes.guess_type(clean_path)
        if not mime_type: mime_type = "image/jpeg"
        with open(clean_path, "rb") as image_file:
            raw_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{raw_base64}", os.path.basename(clean_path)
    except: return None, None

def send_wpp_text(phone, message):
    if not phone or str(phone) == "None": return
    url = f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/send-message"
    is_group_msg = "@g.us" in str(phone)

    payload = {
        "phone": phone,
        "message": message,
        "isGroup": is_group_msg,
        "linkPreview": False,
        "options": {
            "linkPreview": False,
            "createChat": True
        }
    }

    try:
        r = requests.post(url, json=payload, headers=get_headers())
        log(f"📤 Balas ke {phone}: {r.status_code}")
        if r.status_code == 401: generate_token()
    except Exception as e: log(f"❌ Error Kirim Text: {e}")

def send_wpp_image(phone, file_path, caption=""):
    if not phone: return
    url = f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/send-image"
    base64_str, _ = get_base64_image(file_path)
    if not base64_str: return
    is_group_msg = "@g.us" in str(phone)
    payload = {"phone": phone, "base64": base64_str, "caption": caption, "isGroup": is_group_msg}
    try: requests.post(url, json=payload, headers=get_headers())
    except: pass

# --- MAIN LOGIC ---
def process_logic(remote_jid, sender_name, message_body, is_group, mentioned_list):
    log(f"⚙️ Memproses Pesan: '{message_body}' dari {sender_name} (Group: {is_group})")

    should_reply = False

    # DM vs Group logic
    if not is_group:
        should_reply = True
    else:
        if "@faq" in message_body.lower():
            should_reply = True

        if mentioned_list and not should_reply:
            for mentioned_id in mentioned_list:
                for my_id in MY_IDENTITIES:
                    if str(my_id) in str(mentioned_id):
                        should_reply = True
                        log(f"🔔 Bot di-tag di Grup (ID: {my_id})!")
                        break
                if should_reply: break

    if not should_reply: return

    # Clean query
    clean_query = message_body.replace("@faq", "")
    for identity in MY_IDENTITIES:
        clean_query = clean_query.replace(f"@{identity}", "")
    clean_query = re.sub(r'@\d+', '', clean_query).strip()

    if not clean_query:
        send_wpp_text(remote_jid, f"Halo {sender_name}, silakan ketik pertanyaan Anda.")
        return

    log(f"🔍 Mencari: '{clean_query}'")
    try:
        results = database.search_faq_for_bot(clean_query, filter_tag="Semua Modul")
    except:
        send_wpp_text(remote_jid, "Maaf, database sedang gangguan.")
        return

    if not results or not results['ids'][0]:
        fail_msg = f"Maaf, tidak ditemukan hasil untuk: '{clean_query}'\n\n"
        fail_msg += f"Silakan cari manual di: {WEB_V2_URL}"
        send_wpp_text(remote_jid, fail_msg)
        return

    meta = results['metadatas'][0][0]
    score = max(0, (1 - results['distances'][0][0]) * 100)

    if score < 41:
        utils.log_failed_search(clean_query)
        msg = f"Maaf, belum ada data yang cocok.\n\nCoba cek di: {WEB_V2_URL}"
        send_wpp_text(remote_jid, msg)
        return

    # Build response
    if score >= 60:
        header = f"Relevansi: {score:.0f}%\n"
    else:
        header = f"[Relevansi Rendah: {score:.0f}%]\n"

    judul = meta['judul']
    jawaban_raw = meta['jawaban_tampil']

    # Parse images
    raw_paths = meta.get('path_gambar', 'none')
    img_db_list = []
    if raw_paths and str(raw_paths).lower() != 'none':
        img_db_list = [p.strip().replace("\\", "/") for p in raw_paths.split(';')]

    list_gambar_to_send = []
    def replace_tag(match):
        try:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(img_db_list):
                list_gambar_to_send.append(img_db_list[idx])
                return f"*(Lihat Gambar {idx+1})*"
            return ""
        except: return ""

    jawaban_processed = re.sub(r'\[GAMBAR\s*(\d+)\]', replace_tag, jawaban_raw, flags=re.IGNORECASE)
    if not list_gambar_to_send and img_db_list: list_gambar_to_send = img_db_list

    # Build message
    final_text = f"{header}\n"
    final_text += f"*{judul}*\n\n"
    final_text += f"{jawaban_processed}"

    sumber_raw = meta.get('sumber_url')
    sumber = str(sumber_raw).strip() if sumber_raw else ""

    if len(sumber) > 3:
        if "http" in sumber.lower():
            final_text += f"\n\n\nSumber: {sumber}"
        else:
            final_text += f"\n\n\nNote: {sumber}"

    # Send response
    send_wpp_text(remote_jid, final_text)

    for i, img in enumerate(list_gambar_to_send):
        time.sleep(0.5)
        send_wpp_image(remote_jid, img, caption=f"Lampiran {i+1}")

    # Footer
    footer_text = "------------------------------\n"
    footer_text += "Jika bukan ini jawaban yang dimaksud:\n\n"
    footer_text += f"1. Cek Library Lengkap: {WEB_V2_URL}\n"
    footer_text += "2. Gunakan kalimat spesifik beserta nama modul (IPD/ED/Jadwal).\n"

    time.sleep(0.5)
    send_wpp_text(remote_jid, footer_text)

@app.post("/webhook")
async def wpp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        event = body.get("event")

        if event not in ["onMessage", "onAnyMessage", "onmessage"]:
            return {"status": "ignored_event"}

        data = body.get("data") or body

        if data.get("fromMe", False) is True: return {"status": "ignored_self"}

        remote_jid = data.get("from") or data.get("chatId") or data.get("sender", {}).get("id")
        if not remote_jid or "status@broadcast" in str(remote_jid): return {"status": "ignored_status"}

        message_body = data.get("body") or data.get("content") or data.get("caption") or ""
        sender_name = data.get("sender", {}).get("pushname", "User")
        is_group = data.get("isGroupMsg", False) or "@g.us" in str(remote_jid)
        mentioned_list = data.get("mentionedJidList", [])

        background_tasks.add_task(process_logic, remote_jid, sender_name, message_body, is_group, mentioned_list)
        return {"status": "success"}

    except Exception as e:
        log(f"❌ Webhook Error: {e}")
        return {"status": "error"}

@app.on_event("startup")
async def startup_event():
    log(f"🚀 Bot WA Start! Identities: {len(MY_IDENTITIES)}")
    generate_token()
    try:
        requests.post(
            f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/start-session",
            json={"webhook": "http://faq-bot:8000/webhook"},
            headers=get_headers()
        )
    except: pass

if __name__ == "__main__":
    uvicorn.run("bot_wa:app", host="0.0.0.0", port=8000)
```

---

## 13. WEB V2: FASTAPI APPLICATION

### 13.1 Purpose
Alternative web UI menggunakan FastAPI + Jinja2 (lebih ringan dari Streamlit).

### 13.2 File: web_v2/main.py

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys
import markdown
import re
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, utils

app = FastAPI()

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/images", StaticFiles(directory=os.path.join(os.path.dirname(current_dir), "images")), name="images")

templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))
TAGS_MAP = utils.load_tags_config()

def fix_markdown_format(text):
    if not text: return ""
    text = re.sub(r'([^\n])\n(\d+\.\s)', r'\1\n\n\2', text)
    text = re.sub(r'([^\n])\n(-\s)', r'\1\n\n\2', text)
    return text

def process_content_to_html(text_markdown, img_path_str):
    if not text_markdown: return ""

    text_markdown = fix_markdown_format(text_markdown)

    try:
        html_content = markdown.markdown(
            text_markdown,
            extensions=['nl2br', 'extra', 'sane_lists']
        )
    except Exception as e:
        html_content = markdown.markdown(text_markdown)

    img_list = []
    if img_path_str and str(img_path_str).lower() != 'none':
        raw_paths = img_path_str.split(';')
        for p in raw_paths:
            clean = p.replace("\\", "/").strip()
            if clean.startswith("./images"):
                clean = clean[1:]
            img_list.append(clean)

    pattern = re.compile(r'\[GAMBAR\s*(\d+)\]', re.IGNORECASE)

    def replace_match(match):
        try:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(img_list):
                return f'''
                <div class="img-container">
                    <img src="{img_list[idx]}" alt="Gambar {idx+1}" loading="lazy" onclick="window.open(this.src, '_blank');">
                    <span class="img-caption">Gambar {idx+1} (Klik untuk perbesar)</span>
                </div>
                '''
            return ""
        except: return ""

    html_content = pattern.sub(replace_match, html_content)

    if "[GAMBAR" not in text_markdown.upper() and img_list:
        html_content += "<hr class='img-divider'><div class='gallery-grid'>"
        for img in img_list:
             html_content += f'<div class="img-card"><img src="{img}" onclick="window.open(this.src, \'_blank\');"></div>'
        html_content += "</div>"

    return html_content

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: str = "", tag: str = "Semua Modul", page: int = 0):

    ITEMS_PER_PAGE = 10
    results = []
    total_pages = 1
    is_search_mode = False

    try: db_tags = database.get_unique_tags_from_db()
    except: db_tags = []
    all_tags = ["Semua Modul"] + (db_tags if db_tags else [])

    # SEARCH MODE
    if q.strip():
        is_search_mode = True
        raw = database.search_faq(q, filter_tag=tag, n_results=20)

        if raw and raw['ids'][0]:
            temp_results = []
            for i in range(len(raw['ids'][0])):
                meta = raw['metadatas'][0][i]
                dist = raw['distances'][0][i]
                score = max(0, (1 - dist) * 100)

                if score > 41:
                    meta['score'] = int(score)
                    if score > 80: meta['score_class'] = "score-high"
                    elif score > 50: meta['score_class'] = "score-med"
                    else: meta['score_class'] = "score-low"

                    tag_info = TAGS_MAP.get(meta['tag'], {})
                    meta['badge_color'] = tag_info.get('color', '#808080')
                    temp_results.append(meta)

            temp_results.sort(key=lambda x: x['score'], reverse=True)
            results = temp_results[:3]

    # BROWSE MODE
    else:
        raw_all = database.get_all_faqs_sorted()

        if tag != "Semua Modul":
            filtered_data = [x for x in raw_all if x.get('tag') == tag]
        else:
            filtered_data = raw_all

        total_docs = len(filtered_data)
        total_pages = math.ceil(total_docs / ITEMS_PER_PAGE)

        if page >= total_pages: page = 0
        if page < 0: page = 0

        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        sliced_data = filtered_data[start:end]

        for meta in sliced_data:
            meta['score'] = None
            tag_info = TAGS_MAP.get(meta['tag'], {})
            meta['badge_color'] = tag_info.get('color', '#808080')
            results.append(meta)

    # Process content
    for item in results:
        item['html_content'] = process_content_to_html(
            item.get('jawaban_tampil', ''),
            item.get('path_gambar', '')
        )

        src_raw = item.get('sumber_url')
        src = str(src_raw).strip() if src_raw else ""
        item['source_html'] = ""

        if len(src) > 3:
            if "http" in src and " " not in src:
                item['source_html'] = f'<div class="source-box"><a href="{src}" target="_blank">🔗 Buka Sumber Referensi</a></div>'
            else:
                linked_src = re.sub(r'(https?://\S+)', r'<a href="\1" target="_blank">\1</a>', src)
                item['source_html'] = f'<div class="source-box">🔗 {linked_src}</div>'

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
```

### 13.3 File: web_v2/templates/index.html

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hospital Information Hub</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>

    <div class="container">
        <!-- HEADER -->
        <div class="header-box">
            <h1>🏥 Hospital Information Hub: SOPs and FAQs </h1>
            <p class="subtitle">Fast Cognitive Search System</p>
        </div>

        <!-- SEARCH FORM -->
        <form action="/" method="get" class="search-form">
            <input type="hidden" name="page" value="0">

            <input type="text" name="q" class="search-input"
                   placeholder="Cari kendala (cth: gimana sih cara ngedit obat di emr ed pharmacy?)..."
                   value="{{ query }}" autofocus>

            <select name="tag" class="filter-select">
                {% for t in all_tags %}
                    <option value="{{ t }}" {% if t == current_tag %}selected{% endif %}>
                        {{ t }}
                    </option>
                {% endfor %}
            </select>

            <button type="submit" class="search-btn">Cari</button>

            {% if query %}
            <a href="/" class="reset-btn" title="Hapus pencarian">❌</a>
            {% endif %}
        </form>

        <!-- INFO STATUS -->
        {% if is_search_mode %}
            <p class="result-info">🔍 Menampilkan <strong>Top {{ total_items }}</strong> hasil untuk: "<em>{{ query }}</em>"</p>
        {% else %}
            <p class="result-info">📂 Menampilkan SOP dan FAQ Terbaru (Halaman {{ page + 1 }} dari {{ total_pages }})</p>
        {% endif %}

        <!-- RESULTS LIST -->
        <div class="results">
            {% if not results %}
                <div class="empty-state">
                    <h3>❌ Tidak ditemukan data</h3>
                    <p>Coba kalimat lain atau hubungi Tim IT.</p>
                </div>
            {% endif %}

            {% for item in results %}
                <details>
                    <summary>
                        <div class="summary-content">
                            <span class="badge" style="background-color: {{ item.badge_color }}">
                                {{ item.tag }}
                            </span>
                            <span class="title-text">{{ item.judul }}</span>
                        </div>

                        {% if item.score %}
                        <span class="score-badge {{ item.score_class }}">
                            {{ item.score }}% Relevan
                        </span>
                        {% endif %}
                    </summary>

                    <div class="faq-content">
                        {{ item.html_content | safe }}

                        {% if item.source_html %}
                            {{ item.source_html | safe }}
                        {% endif %}
                    </div>
                </details>
            {% endfor %}
        </div>

        <!-- PAGINATION -->
        {% if not is_search_mode and total_pages > 1 %}
        <div class="pagination">
            {% if page > 0 %}
                <a href="/?page={{ page - 1 }}&tag={{ current_tag }}&q=" class="page-btn">⬅️ Sebelumnya</a>
            {% else %}
                <span class="page-btn disabled">⬅️ Sebelumnya</span>
            {% endif %}

            <span class="page-info">{{ page + 1 }} / {{ total_pages }}</span>

            {% if page < total_pages - 1 %}
                <a href="/?page={{ page + 1 }}&tag={{ current_tag }}&q=" class="page-btn">Berikutnya ➡️</a>
            {% else %}
                <span class="page-btn disabled">Berikutnya ➡️</span>
            {% endif %}
        </div>
        {% endif %}

    </div>

</body>
</html>
```

### 13.4 File: web_v2/static/style.css

(Full CSS code provided in exploration - approximately 326 lines covering layout, search form, accordion, badges, images, pagination, and mobile responsive)

---

## 14. DOCKER DEPLOYMENT

### 14.1 Dockerfile

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

EXPOSE 8501 8502 8000

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 14.2 requirements.txt

```
streamlit==1.51.0
chromadb==1.3.4
pandas
google-genai
python-dotenv
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
```

### 14.3 docker-compose.yml

```yaml
version: '3'

services:
  # --- 1. CHROMA DB ---
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

  # --- 2. WPPCONNECT (WhatsApp Gateway) ---
  wppconnect:
    container_name: faq_wppconnect
    build: https://github.com/wppconnect-team/wppconnect-server.git
    restart: always
    ports:
      - "21465:21465"
    environment:
      SECRET_KEY: admin123
      LOG_LEVEL: info
    volumes:
      - ./wpp_tokens:/home/wppconnect/tokens
      - ./wpp_sessions:/home/wppconnect/userData
      - ./wpp_sessions/config.json:/home/wppconnect/config.json

  # --- 3. BOT WA ---
  faq-bot:
    build: .
    container_name: faq_bot_wa
    restart: always
    ports:
      - "8005:8000"
    depends_on:
      chroma-server:
        condition: service_started
      wppconnect:
        condition: service_started
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
      - WA_BASE_URL=http://wppconnect:21465
      - WA_SESSION_KEY=THISISMYSECURETOKEN
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/app/data
      - ./images:/app/images
    command: uvicorn bot_wa:app --host 0.0.0.0 --port 8000

  # --- 4. USER APP ---
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
      - ./.streamlit:/app/.streamlit
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0

  # --- 5. ADMIN APP ---
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
      - ./.streamlit:/app/.streamlit
    env_file: .env
    environment:
      - CHROMA_HOST=chroma-server
      - CHROMA_PORT=8000
    command: streamlit run admin.py --server.port=8502 --server.address=0.0.0.0

  # --- 6. WEB V2 ---
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
    command: uvicorn web_v2.main:app --host 0.0.0.0 --port 8080
```

### 14.4 Port Mapping

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| ChromaDB | 8000 | 8000 |
| WPPConnect | 21465 | 21465 |
| WA Bot | 8000 | 8005 |
| User App | 8501 | 8501 |
| Admin App | 8502 | 8502 |
| Web V2 | 8080 | 8080 |

---

## 15. UI/UX SPECIFICATIONS

### 15.1 Color Palette

| Color Name | HEX Code | Streamlit Name | Usage |
|------------|----------|----------------|-------|
| Merah | #FF4B4B | red | ED (Emergency) |
| Hijau | #2ECC71 | green | OPD (Outpatient) |
| Biru | #3498DB | blue | IPD, MR, Rehab |
| Orange | #FFA500 | orange | Lab, MCU, Internal |
| Ungu | #9B59B6 | violet | Cashier, Warning |
| Abu-abu | #808080 | gray | Default/Umum |

### 15.2 Score Badge Colors

| Score | Background | Text | Class |
|-------|------------|------|-------|
| > 80% | #d4edda (Light Green) | #155724 | score-high |
| 50-80% | #fff3cd (Light Yellow) | #856404 | score-med |
| 41-50% | #f8d7da (Light Red) | #721c24 | score-low |

### 15.3 Responsive Breakpoints

- Mobile: max-width 600px
- Desktop: > 600px

---

## 16. BUSINESS LOGIC RULES

### 16.1 Search Rules

1. **Minimum Score Threshold:** 41%
2. **Maximum Results (Search):** 3
3. **Items Per Page (Browse):** 10
4. **Pre-filtering:** Apply tag filter BEFORE semantic search
5. **Score Calculation:** `score = (1 - distance) × 100`

### 16.2 WhatsApp Bot Rules

1. **DM:** Always reply
2. **Group:** Reply only if:
   - `@faq` keyword in message
   - Bot is mentioned (via `mentionedJidList`)
3. **Query Cleaning:** Remove `@faq`, `@{bot_id}`, and `@digits`
4. **Failed Search:** Log to CSV and suggest web URL

### 16.3 Image Handling Rules

1. **Compression:** Max width 1024px, JPEG quality 70
2. **Storage Format:** `./images/{tag}/{sanitized_title}_{tag}_{index}_{random}.jpg`
3. **Path Delimiter:** Semicolon (`;`)
4. **Cascade Delete:** Deleting FAQ also deletes associated images

### 16.4 HyDE Format Rules

```
DOMAIN: {tag} ({tag_description})
DOKUMEN: {title}
VARIASI PERTANYAAN USER: {keywords}
ISI KONTEN: {cleaned_answer}
```

---

## 17. API ENDPOINTS

### 17.1 WhatsApp Bot (FastAPI)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /webhook` | POST | Receive WhatsApp messages |

**Request Body (from WPPConnect):**
```json
{
  "event": "onMessage",
  "data": {
    "from": "6281234567890@c.us",
    "body": "@faq cara login emr",
    "sender": {"pushname": "John"},
    "isGroupMsg": false,
    "mentionedJidList": []
  }
}
```

### 17.2 Web V2 (FastAPI)

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `GET /` | GET | `q`, `tag`, `page` | Main search page |

---

## 18. TESTING CHECKLIST

### 18.1 Functional Tests

- [ ] Search returns relevant results
- [ ] Filter by tag works correctly
- [ ] Pagination works in browse mode
- [ ] Images display inline with `[GAMBAR X]`
- [ ] Failed search logs to CSV
- [ ] WhatsApp bot responds to DM
- [ ] WhatsApp bot responds to @faq in groups
- [ ] Admin login with bcrypt password
- [ ] Admin CRUD operations work
- [ ] Tag configuration persists
- [ ] Backup/restore creates valid ZIP

### 18.2 Edge Cases

- [ ] Empty search query shows browse mode
- [ ] Score < 41% returns no results
- [ ] Missing image shows error gracefully
- [ ] Long text renders with markdown
- [ ] Special characters in title sanitized
- [ ] Database locked handled with retry

### 18.3 Integration Tests

- [ ] ChromaDB server mode works
- [ ] ChromaDB local mode works
- [ ] Google Gemini API returns embeddings
- [ ] WPPConnect webhook receives messages
- [ ] Docker Compose starts all services

---

## APPENDIX A: QUICK START GUIDE

### Local Development

```bash
# 1. Clone repository
git clone <repo-url>
cd eighthExperiment

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# 5. Run services
streamlit run app.py --server.port 8501  # User app
streamlit run admin.py --server.port 8502  # Admin app
uvicorn bot_wa:app --port 8000  # WhatsApp bot
uvicorn web_v2.main:app --port 8080  # Web V2
```

### Docker Deployment

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your secrets

# 2. Build and run
docker-compose up --build -d

# 3. Access
# User: http://localhost:8501
# Admin: http://localhost:8502
# Web V2: http://localhost:8080
# Bot API: http://localhost:8005
```

---

## APPENDIX B: GENERATE ADMIN PASSWORD HASH

```python
import bcrypt

password = b"your_secure_password"
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
print(hashed.decode())

# Copy output to .env: ADMIN_PASSWORD_HASH=$2b$12$...
```

---

**Dokumen ini mencakup seluruh spesifikasi yang diperlukan untuk merekonstruksi aplikasi dari nol.**

*Generated: February 2026*
