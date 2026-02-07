"""
Application Constants - Magic Numbers Terpusat.
Semua nilai konstan yang sebelumnya hardcoded tersebar di berbagai file.
"""

# === SEARCH & RELEVANCE ===
RELEVANCE_THRESHOLD = 41          # Minimum score untuk hasil dianggap relevan (%)
HIGH_RELEVANCE_THRESHOLD = 80     # Score >= ini dianggap sangat relevan (hijau tua)
MEDIUM_RELEVANCE_THRESHOLD = 50   # Score >= ini dianggap cukup relevan (hijau muda)

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
COLLECTION_NAME = "faq_universal_v1"  # Nama collection ChromaDB
EMBEDDING_MODEL = "models/gemini-embedding-001"  # Model embedding Google
LLM_MODEL = "gemini-2.5-flash"                    # Model LLM untuk agent mode (reranking)

# === RETRY LOGIC ===
MAX_RETRIES = 10                  # Max retry untuk database lock
RETRY_BASE_DELAY = 0.1            # Base delay untuk retry (seconds)

# === STREAMLIT COLOR MAPPING ===
# Mapping HEX code ke nama warna Streamlit
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
