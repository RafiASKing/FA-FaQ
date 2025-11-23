import os

# --- API KEYS ---
# Pastikan file .env sudah ada dan berisi GOOGLE_API_KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

if not GOOGLE_API_KEY:
    # Warning log di console server
    raise ValueError("❌ GOOGLE_API_KEY belum diset! Cek file .env atau environment server.")

# --- PATHS CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folder Database ChromaDB
DB_PATH = os.path.join(BASE_DIR, "data", "faq_db")

# File Konfigurasi Tag (JSON)
TAGS_FILE = os.path.join(BASE_DIR, "data", "tags_config.json")

# Folder Gambar
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# Nama Collection di ChromaDB
COLLECTION_NAME = "faq_universal_v1"

# Setup Folder jika belum ada
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)