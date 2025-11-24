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
import random  # Penting untuk jitter (jeda acak)
from google import genai
from google.genai import types
from .config import GOOGLE_API_KEY, DB_PATH, COLLECTION_NAME
from .utils import load_tags_config, clean_text_for_embedding

# --- 3. RETRY DECORATOR (SAFE CONCURRENCY) ---
def retry_on_lock(max_retries=10, base_delay=0.1):
    """
    Decorator untuk menangani Database Locked (SQLite).
    Menggunakan 'Random Jitter' agar jika 5 user akses bareng,
    mereka tidak mencoba ulang di detik yang sama persis.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Cek error spesifik SQLite Locked/Busy
                    err_msg = str(e).lower()
                    if "locked" in err_msg or "busy" in err_msg:
                        retries += 1
                        # Sleep acak antara 0.1s s/d 0.2s (Jitter)
                        sleep_time = base_delay * (1 + random.random())
                        time.sleep(sleep_time)
                        # print(f"⚠️ DB Locked, retrying {retries}/{max_retries}...")
                    else:
                        raise e  # Error lain (coding error) tetap dilempar
            raise Exception("Database sedang sibuk (High Traffic), silakan coba lagi sesaat.")
        return wrapper
    return decorator

# --- 4. CLIENT INITIALIZATION (CACHED) ---
@st.cache_resource(show_spinner=False)
def get_db_client():
    return chromadb.PersistentClient(path=DB_PATH)

@st.cache_resource(show_spinner=False)
def get_ai_client():
    return genai.Client(api_key=GOOGLE_API_KEY)

def get_collection():
    client = get_db_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

# --- 5. EMBEDDING (CACHED) ---
@st.cache_data(show_spinner=False)
def generate_embedding_cached(text):
    client = get_ai_client()
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

# --- 6. INTERNAL HELPER (ID GENERATOR) ---
def _get_next_id_internal(collection):
    """
    Hitung ID max + 1. 
    Fungsi ini dipanggil DALAM lock upsert agar thread-safe.
    """
    data = collection.get(include=[])
    existing_ids = data['ids']
    
    if not existing_ids: 
        return "1"
    
    numeric_ids = []
    for x in existing_ids:
        # Filter hanya ID angka agar sorting benar (1, 2, 10, bukan 1, 10, 2)
        if x.isdigit(): 
            numeric_ids.append(int(x))
    
    if not numeric_ids: 
        return "1"
        
    return str(max(numeric_ids) + 1)

# --- 7. CORE LOGIC (READ - USER) ---

@retry_on_lock()
def search_faq(query_text, filter_tag=None, n_results=50):
    col = get_collection()
    vec = generate_embedding_cached(query_text)
    
    if not vec: 
        return {"ids": [[]], "metadatas": [[]], "distances": [[]]}

    # Pre-Filtering logic
    where_clause = {"tag": filter_tag} if (filter_tag and filter_tag != "Semua Modul") else None
    
    return col.query(
        query_embeddings=[vec],
        n_results=n_results,
        where=where_clause
    )

@retry_on_lock()
def get_all_faqs_sorted():
    col = get_collection()
    data = col.get(include=['metadatas'])
    
    results = []
    if data['ids']:
        for i, doc_id in enumerate(data['ids']):
            meta = data['metadatas'][i]
            
            # Defense: Handle jika ID bukan angka
            try: id_num = int(doc_id)
            except: id_num = 0
            
            meta['id'] = doc_id
            meta['id_num'] = id_num
            results.append(meta)
            
    # Sort descending (Terbaru diatas)
    results.sort(key=lambda x: x.get('id_num', 0), reverse=True)
    return results

def get_unique_tags_from_db():
    col = get_collection()
    data = col.get(include=['metadatas'])
    unique_tags = set()
    if data['metadatas']:
        for meta in data['metadatas']:
            if meta and meta.get('tag'):
                unique_tags.add(meta['tag'])
    return sorted(list(unique_tags))

# --- 8. CORE LOGIC (WRITE - ADMIN) ---

def get_all_data_as_df():
    """Mengambil data lengkap untuk Tabel Admin"""
    col = get_collection()
    data = col.get(include=['metadatas', 'documents', 'embeddings'])
    
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
    # Sorting numeric untuk tabel
    df['ID_Num'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0)
    return df.sort_values('ID_Num', ascending=False).drop(columns=['ID_Num'])

@retry_on_lock()
def upsert_faq(doc_id, tag, judul, jawaban, keyword, img_paths, src_url):
    col = get_collection()
    
    # KUNCI LOGIKA: 
    # Jika doc_id diisi (saat Edit), gunakan itu.
    # Jika doc_id="auto" (saat New), generate baru.
    final_id = str(doc_id)
    if doc_id == "auto" or doc_id is None:
        final_id = _get_next_id_internal(col)
    
    # 1. Text Cleaning (Hapus [GAMBAR X] agar AI tidak bingung)
    clean_jawaban = clean_text_for_embedding(jawaban)
    
    # 2. Build Context Prompt
    text_embed = f"""MODUL: {tag}
PERTANYAAN: {judul}
SOLUSI TEKNIS: {clean_jawaban}
KEYWORD: {keyword}"""
    
    # 3. Generate Vector
    vector = generate_embedding_cached(text_embed)
    
    # 4. Upsert ke ChromaDB
    col.upsert(
        ids=[final_id],
        embeddings=[vector],
        documents=[text_embed],
        metadatas=[{
            "tag": tag, 
            "judul": judul, 
            "jawaban_tampil": jawaban, # Simpan yg asli (ada marker [GAMBAR]) untuk user UI
            "keywords_raw": keyword,
            "path_gambar": img_paths,
            "sumber_url": src_url
        }]
    )
    return final_id  # Return ID agar Admin Console bisa menampilkan pesan sukses

@retry_on_lock()
def delete_faq(doc_id):
    col = get_collection()
    col.delete(ids=[str(doc_id)])