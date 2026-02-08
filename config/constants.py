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

# === EMBEDDING & LLM ===
EMBEDDING_MODEL = "models/gemini-embedding-001"  # Model embedding Google
EMBEDDING_DIMENSION = 3072                       # Dimension for gemini-embedding-001
LLM_MODEL = "gemini-3-flash-preview"             # Model LLM untuk agent mode (default)
LLM_MODEL_PRO = "gemini-3-pro-preview"           # Model LLM untuk high-precision mode

# === AGENT MODE ===
AGENT_CANDIDATE_LIMIT = 20                       # Top N candidates for LLM grading
AGENT_MIN_SCORE = 20.0                           # Minimum relevancy % for agent candidates
AGENT_CONFIDENCE_THRESHOLD = 0.3                 # Minimum confidence to accept grader result

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
