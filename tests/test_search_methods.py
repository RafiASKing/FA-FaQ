import streamlit as st
import os
import chromadb
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- IMPORT MODUL PROJECT ---
from src import utils, config

load_dotenv()

# --- CONFIG HALAMAN (WIDE MODE BIAR MUAT 4 KOLOM) ---
st.set_page_config(page_title="⚔️ Battle Arena: Search Methods", layout="wide")

# --- JUDUL ---
st.title("⚔️ Search Method Battle Arena")
st.markdown("""
Dashboard ini membandingkan 4 strategi **Query Embedding** secara side-by-side.
Database diasumsikan statis (menggunakan `RETRIEVAL_DOCUMENT`). Kita memanipulasi cara AI melihat **Pertanyaan User**.
""")

# --- FUNGSI EMBEDDING DINAMIS ---
def get_experimental_embedding(text, task_type):
    if not text: return []
    try:
        client = genai.Client(api_key=config.GOOGLE_API_KEY)
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                # Kita pakai default 3072 dimensi (Full Precision)
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        return []

def get_chroma_collection():
    host = os.getenv("CHROMA_HOST")
    port = os.getenv("CHROMA_PORT")
    if host and port:
        client = chromadb.HttpClient(host=host, port=int(port))
    else:
        client = chromadb.PersistentClient(path=config.DB_PATH)
    return client.get_or_create_collection(name=config.COLLECTION_NAME)

# --- DEFINISI METODE ---
METHODS = {
    "RETRIEVAL_QUERY": {
        "label": "Asymmetric (Recommended)",
        "desc": "Fokus pada Intent, abaikan basa-basi.",
        "icon": "🛡️"
    },
    "RETRIEVAL_DOCUMENT": {
        "label": "Symmetric (Document)",
        "desc": "Mencocokkan pola kalimat & kata.",
        "icon": "📄"
    },
    "SEMANTIC_SIMILARITY": {
        "label": "Semantic Similarity",
        "desc": "Kemiripan makna murni.",
        "icon": "⚖️"
    },
    "QUESTION_ANSWERING": {
        "label": "Question Answering",
        "desc": "Ekspektasi kalimat tanya baku.",
        "icon": "🎓"
    }
}

# --- INPUT QUERY ---
with st.container():
    c1, c2 = st.columns([3, 1])
    with c1:
        query = st.text_input("💬 Masukkan Pertanyaan User:", placeholder="Contoh: gagal discharge, form aps, selamat pagi error...", value="gagal discharge")
    with c2:
        st.write("") # Spacer
        st.write("")
        run_btn = st.button("🔥 MULAI PERTARUNGAN", type="primary", use_container_width=True)

st.divider()

# --- MAIN LOGIC ---
if run_btn and query:
    # Siapkan 4 Kolom
    cols = st.columns(4)
    col_idx = 0
    
    # Koneksi DB
    chroma_col = get_chroma_collection()

    # Loop setiap metode
    for task_name, meta in METHODS.items():
        with cols[col_idx]:
            # Header Kolom
            st.subheader(f"{meta['icon']} {meta['label']}")
            st.caption(f"Task: `{task_name}`")
            st.caption(meta['desc'])
            
            # 1. Embed
            with st.spinner("Embedding..."):
                vec = get_experimental_embedding(query, task_name)
            
            if vec:
                # 2. Search (Top 5)
                results = chroma_col.query(query_embeddings=[vec], n_results=5)
                
                if results['ids'][0]:
                    ids = results['ids'][0]
                    metas = results['metadatas'][0]
                    dists = results['distances'][0]
                    
                    # --- ANALISIS GAP (JUARA 1 vs JUARA 2) ---
                    score_1 = max(0, (1 - dists[0]) * 100)
                    score_2 = max(0, (1 - dists[1]) * 100) if len(dists) > 1 else 0
                    gap = score_1 - score_2
                    
                    # Tampilkan Metric GAP
                    # Gap besar = Bagus (Sangat yakin bedanya benar dan salah)
                    # Gap kecil = Bahaya (Bingung mana yang benar)
                    gap_color = "normal"
                    if gap > 15: gap_color = "normal" # Hijau di metric
                    elif gap < 5: gap_color = "inverse" # Merah/Warning
                    
                    st.metric(
                        label="Top Score / Safety Gap", 
                        value=f"{score_1:.1f}%", 
                        delta=f"Gap: {gap:.1f}%",
                        delta_color=gap_color
                    )
                    
                    st.markdown("---")
                    
                    # 3. Render List
                    for i in range(len(ids)):
                        curr_score = max(0, (1 - dists[i]) * 100)
                        curr_meta = metas[i]
                        
                        # Style Card
                        tag = curr_meta.get('tag', 'Umum')
                        judul = curr_meta.get('judul', 'No Title')
                        
                        # Highlight Juara 1
                        bg_style = ""
                        if i == 0:
                            bg_style = "border: 2px solid #4CAF50; background-color: #f0fff0; padding: 10px; border-radius: 5px;"
                            emoji = "🥇"
                        elif i == 1:
                            bg_style = "border: 1px solid #ff9800; padding: 5px; border-radius: 5px; opacity: 0.8;"
                            emoji = "🥈"
                        else:
                            bg_style = "border: 1px solid #ddd; padding: 5px; border-radius: 5px; opacity: 0.6;"
                            emoji = f"#{i+1}"

                        # HTML Card Sederhana
                        st.markdown(f"""
                        <div style="{bg_style} margin-bottom: 10px; color: black;">
                            <small><b>{emoji} Score: {curr_score:.2f}%</b></small><br>
                            <span style="background-color: #eee; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">{tag}</span>
                            <span style="font-size: 0.9em; font-weight: bold;">{judul}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Expander untuk intip isi (buat debug)
                        with st.expander("🔍 Intip Konten"):
                            st.caption(f"Hidden Keyword: {curr_meta.get('keywords_raw')}")
                            st.text(curr_meta.get('jawaban_tampil')[:100] + "...")
                            
                else:
                    st.warning("Tidak ada hasil.")
            else:
                st.error("Gagal Embedding.")
        
        col_idx += 1

else:
    # State Awal (Belum Run)
    st.info("👋 Ketik pertanyaan dan tekan tombol oranye untuk melihat pertarungan algoritma.")