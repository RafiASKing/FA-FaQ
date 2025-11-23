# --- 1. FORCE USE NEW SQLITE (Wajib di Paling Atas untuk Docker/Linux) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass # Fallback jika pysqlite3 belum terinstall (misal di Windows local)

# --- 2. IMPORT LIBRARY ---
import chromadb
import pandas as pd
import streamlit as st # Untuk Caching
from google import genai
from google.genai import types
from .config import GOOGLE_API_KEY, DB_PATH, COLLECTION_NAME
from .utils import load_tags_config, clean_text_for_embedding

# --- SETUP CLIENTS ---
# Inisialisasi Client sekali saja
client_ai = genai.Client(api_key=GOOGLE_API_KEY)
client_db = chromadb.PersistentClient(path=DB_PATH)

def get_collection():
    return client_db.get_or_create_collection(name=COLLECTION_NAME)

# --- 3. OPTIMIZED EMBEDDING (CACHING) ---
# Menyimpan hasil embedding query di RAM.
# Jika user ganti filter (tapi query sama), API Gemini TIDAK dipanggil lagi.
@st.cache_data(show_spinner=False)
def generate_embedding_cached(text):
    response = client_ai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return response.embeddings[0].values

def generate_embedding(text):
    # Wrapper untuk penggunaan di fungsi upsert
    return generate_embedding_cached(text)

def build_context_text(judul, jawaban, keyword, tag):
    tags_cfg = load_tags_config()
    
    # Ambil context deskripsi dari config
    tag_data = tags_cfg.get(tag, {})
    if isinstance(tag_data, dict):
        extra_context = tag_data.get("desc", "")
    else:
        extra_context = "" 

    # Bersihkan jawaban dari tag [GAMBAR X] agar AI fokus ke teks
    jawaban_clean = clean_text_for_embedding(jawaban)

    return f"""Modul Sistem: {tag}
Konsep Terkait: {extra_context}

Masalah/Pertanyaan:
{judul}

Solusi/Langkah-langkah:
{jawaban_clean}

Keyword Tambahan (Slang/Error Code):
{keyword}"""

# --- CORE FEATURES FOR USER APP ---

def search_faq(query_text, filter_tag=None, n_results=50):
    """
    Search dengan Pre-Filtering & Caching.
    Mengambil 50 data agar pagination mulus.
    """
    collection = get_collection()
    
    # Step 1: Embed Query (Instant jika sudah di-cache)
    q_vec = generate_embedding_cached(query_text)
    
    # Step 2: Pre-Filtering (Hanya cari di dalam tag yg dipilih)
    where_clause = {"tag": filter_tag} if (filter_tag and filter_tag != "Semua Modul") else None
    
    # Step 3: Retrieval
    results = collection.query(
        query_embeddings=[q_vec],
        n_results=n_results,
        where=where_clause
    )
    return results

def get_all_faqs_sorted():
    """
    Mengambil SEMUA metadata untuk mode Browse.
    Diurutkan berdasarkan ID Numeric (Terbesar/Terbaru di atas).
    """
    collection = get_collection()
    data = collection.get(include=['metadatas'])
    
    results = []
    if data['ids']:
        for i, doc_id in enumerate(data['ids']):
            meta = data['metadatas'][i]
            
            # Safe conversion ID to int
            try: id_num = int(doc_id)
            except: id_num = 0
                
            results.append({
                "id": doc_id,
                "id_num": id_num, 
                "tag": meta.get('tag', 'Umum'),
                "judul": meta.get('judul', '-'),
                "jawaban_tampil": meta.get('jawaban_tampil', ''),
                "path_gambar": meta.get('path_gambar', 'none'),
                "sumber_url": meta.get('sumber_url', '')
            })
    
    # Sort descending
    results.sort(key=lambda x: x['id_num'], reverse=True)
    return results

def get_unique_tags_from_db():
    """Mengambil list Tag yang BENAR-BENAR ADA di database (untuk Filter UI)"""
    collection = get_collection()
    data = collection.get(include=['metadatas'])
    unique_tags = set()
    if data['metadatas']:
        for meta in data['metadatas']:
            if meta.get('tag'): unique_tags.add(meta['tag'])
    return sorted(list(unique_tags))

# --- CORE FEATURES FOR ADMIN PANEL ---

def get_all_data_as_df():
    """Mengambil data lengkap untuk tabel Admin"""
    collection = get_collection()
    data = collection.get(include=['metadatas', 'documents', 'embeddings'])
    
    if not data['ids']: return pd.DataFrame()
    
    rows = []
    all_embeddings = data.get('embeddings') 
    
    for i, doc_id in enumerate(data['ids']):
        meta = data['metadatas'][i]
        context_full = data['documents'][i] if data['documents'] else ""
        
        # Preview Vector
        embed_vec = []
        if all_embeddings is not None and len(all_embeddings) > 0:
            embed_vec = all_embeddings[i]
        embed_preview = str(embed_vec[:5]) + "..." if len(embed_vec) > 0 else "[]"

        rows.append({
            "ID": doc_id,
            "Tag": meta.get('tag', '-'),
            "Judul": meta.get('judul', '-'),
            "Jawaban": meta.get('jawaban_tampil', ''),
            "Keyword": meta.get('keywords_raw', ''),
            "Gambar": meta.get('path_gambar', 'none'),
            "Source": meta.get('sumber_url', ''),
            "AI Context": context_full,
            "Embed Vector": embed_preview
        })
    
    df = pd.DataFrame(rows)
    df['ID_Num'] = pd.to_numeric(df['ID'], errors='coerce')
    df = df.sort_values('ID_Num', ascending=False).drop(columns=['ID_Num'])
    return df

def upsert_faq(doc_id, tag, judul, jawaban, keyword, img_paths, src_url):
    """Insert atau Update Data"""
    collection = get_collection()
    
    # Build Context (Text Cleaner dipanggil di dalam fungsi ini)
    text_embed = build_context_text(judul, jawaban, keyword, tag)
    vector = generate_embedding_cached(text_embed)
    
    collection.upsert(
        ids=[str(doc_id)],
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

def delete_faq(doc_id):
    collection = get_collection()
    collection.delete(ids=[str(doc_id)])