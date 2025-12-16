import streamlit as st
import os
import re
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- IMPORT DARI MODULE PROJECT KAMU ---
# Pastikan script ini ada di root folder (sejajar dengan folder src)
from src import utils, config

# Load Environment Variables
load_dotenv()

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="🔬 Search Method Lab", layout="centered")
st.title("🔬 Search Method Experiment")
st.caption("Bandingkan 4 strategi Task Type embedding secara realtime.")

# Load Config Tag untuk Warna
TAGS_MAP = utils.load_tags_config()

# --- FUNGSI KHUSUS UNTUK TESTING INI (BYPASS CACHE) ---
# Kita buat fungsi embedding lokal di sini supaya bisa gonta-ganti Task Type
# tanpa mengganggu kode produksi di src/database.py

def get_experimental_embedding(text, task_type):
    """
    Generate embedding dengan Task Type yang dinamis sesuai pilihan Dropdown.
    """
    if not text: return []
    
    try:
        client = genai.Client(api_key=config.GOOGLE_API_KEY)
        
        # Panggil Model Gemini-Embedding-001
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                # Kita pakai default 3072 dimensi (Full Precision)
                # output_dimensionality=None 
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        st.error(f"⚠️ Error API Google: {e}")
        return []

def get_chroma_collection():
    """Koneksi ke ChromaDB yang sudah ada"""
    # Cek apakah pakai server atau file lokal
    host = os.getenv("CHROMA_HOST")
    port = os.getenv("CHROMA_PORT")

    if host and port:
        client = chromadb.HttpClient(host=host, port=int(port))
    else:
        client = chromadb.PersistentClient(path=config.DB_PATH)
        
    return client.get_or_create_collection(name=config.COLLECTION_NAME)

# --- HELPER UI ---
def get_badge_color_name(tag):
    tag_data = TAGS_MAP.get(tag, {})
    hex_code = tag_data.get("color", "#808080").upper() 
    hex_to_name = {
        "#FF4B4B": "red", "#2ECC71": "green", "#3498DB": "blue",
        "#FFA500": "orange", "#9B59B6": "violet", "#808080": "gray"
    }
    return hex_to_name.get(hex_code, "gray")

def render_mixed_content(jawaban_text, images_str):
    # Render sederhana untuk preview
    if not images_str or str(images_str).lower() == 'none':
        st.markdown(jawaban_text)
        return

    img_list = images_str.split(';')
    parts = re.split(r'(\[GAMBAR\s*\d+\])', jawaban_text, flags=re.IGNORECASE)
    
    for part in parts:
        match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
        if match:
            try:
                idx = int(match.group(1)) - 1 
                if 0 <= idx < len(img_list):
                    clean_p = utils.fix_image_path_for_ui(img_list[idx])
                    if clean_p and os.path.exists(clean_p):
                        st.image(clean_p, use_container_width=True)
            except: pass
        else:
            if part.strip(): st.markdown(part)

# --- UI UTAMA ---

# 1. SETUP STRATEGI
st.sidebar.header("⚙️ Konfigurasi Eksperimen")
st.sidebar.markdown("Pilih bagaimana sistem melihat **Pertanyaan User**:")

method_option = st.sidebar.radio(
    "Task Type (User Query):",
    [
        "RETRIEVAL_QUERY (Asymmetric - Recommended)",
        "RETRIEVAL_DOCUMENT (Symmetric)",
        "SEMANTIC_SIMILARITY (Symmetric)",
        "QUESTION_ANSWERING (Strict QA)"
    ],
    index=0
)

# Mapping pilihan ke string API Google
TASK_TYPE_MAP = {
    "RETRIEVAL_QUERY (Asymmetric - Recommended)": "RETRIEVAL_QUERY",
    "RETRIEVAL_DOCUMENT (Symmetric)": "RETRIEVAL_DOCUMENT",
    "SEMANTIC_SIMILARITY (Symmetric)": "SEMANTIC_SIMILARITY",
    "QUESTION_ANSWERING (Strict QA)": "QUESTION_ANSWERING"
}
selected_task_type = TASK_TYPE_MAP[method_option]

st.sidebar.info(f"""
**Strategi saat ini:**
User Query di-embed sebagai `{selected_task_type}`.

*Database diasumsikan sudah di-embed menggunakan `RETRIEVAL_DOCUMENT` (Default).*
""")

# 2. INPUT QUERY
query = st.text_input("Tes Pertanyaan User:", placeholder="Contoh: gagal discharge, resep error...", key="q_test")

# 3. PROSES PENCARIAN
if query:
    st.divider()
    
    with st.spinner(f"Mencari menggunakan metode {selected_task_type}..."):
        # A. Embed Query User (Pakai Task Type Pilihan)
        query_vec = get_experimental_embedding(query, selected_task_type)
        
        if query_vec:
            # B. Query ke Chroma
            col = get_chroma_collection()
            results = col.query(
                query_embeddings=[query_vec],
                n_results=10 
            )
            
            # C. Tampilkan Hasil
            if results['ids'][0]:
                st.markdown(f"### Hasil Pencarian ({len(results['ids'][0])} Teratas)")
                
                for i in range(len(results['ids'][0])):
                    meta = results['metadatas'][0][i]
                    dist = results['distances'][0][i]
                    score = max(0, (1 - dist) * 100)
                    
                    # Logic Warna Score
                    if score > 80: score_color = "green"
                    elif score > 50: score_color = "orange"
                    else: score_color = "red"
                    
                    # Badge Tag
                    tag = meta.get('tag', 'Umum')
                    badge_col = get_badge_color_name(tag)
                    
                    # Judul Expander
                    label = f"**{score:.2f}%** - :{badge_col}-background[{tag}] {meta.get('judul')}"
                    
                    with st.expander(label, expanded=(i==0)): # Yg pertama auto open
                        st.caption(f"ID Dokumen: {results['ids'][0][i]}")
                        st.markdown(f"**Score Relevansi:** :{score_color}[{score:.4f}%]")
                        st.markdown("---")
                        render_mixed_content(meta.get('jawaban_tampil', ''), meta.get('path_gambar'))
                        
                        st.markdown("---")
                        st.caption(f"**Keywords (Hidden):** {meta.get('keywords_raw')}")
                        st.caption(f"**Source URL:** {meta.get('sumber_url')}")
            else:
                st.warning("Tidak ditemukan hasil.")
        else:
            st.error("Gagal melakukan embedding. Cek koneksi internet/API Key.")

else:
    st.info("👋 Masukkan pertanyaan di atas untuk mulai membandingkan hasil.")
    st.markdown("""
    ### Panduan Eksperimen Task Type:
    
    1. **RETRIEVAL_QUERY**: 
       - Menganggap input user adalah *pencarian* (informal, keyword acak).
       - Biasanya terbaik untuk search bar.
       
    2. **RETRIEVAL_DOCUMENT**: 
       - Menganggap input user adalah *fakta/dokumen*.
       - Coba gunakan kalimat pernyataan lengkap, misal: *"Cara melakukan discharge pasien adalah..."*
       
    3. **SEMANTIC_SIMILARITY**:
       - Mengukur kemiripan makna murni.
       - Coba gunakan kalimat yang mirip persis dengan judul FAQ.
       
    4. **QUESTION_ANSWERING**:
       - Menganggap input user adalah *pertanyaan ujian*.
       - Coba gunakan format tanya baku: *"Bagaimana cara discharge?"*
    """)