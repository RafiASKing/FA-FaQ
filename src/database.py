import chromadb
import pandas as pd
from google import genai
from google.genai import types
from .config import GOOGLE_API_KEY, DB_PATH, COLLECTION_NAME

# --- SETUP CLIENTS ---
# Pakai check_api_heartbeat() nanti kalau mau production
client_ai = genai.Client(api_key=GOOGLE_API_KEY)
client_db = chromadb.PersistentClient(path=DB_PATH)

def get_collection():
    return client_db.get_or_create_collection(name=COLLECTION_NAME)

def generate_embedding(text):
    response = client_ai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return response.embeddings[0].values

def build_context_text(judul, jawaban, keyword, tag):
    # 1. Definisikan "Kamus Pintar" Konteks Tambahan
    # Tujuannya: Menangkap sinonim yang sering dipakai orang RS tapi beda istilah sistem
    context_map = {
        "IPD": "Rawat Inap, In-Patient Department, Bangsal, Opname, Ranap, Kamar Perawatan",
        "OPD": "Rawat Jalan, Poliklinik, Out-Patient, Rajal, Konsultasi Dokter, Kontrol",
        "ED": "Emergency, IGD, UGD, Gawat Darurat, Accident & Emergency, Triage, Resusitasi",
        "MR": "Medical Record, Rekam Medis, Filling, Coding, Casemix, Resume Medis",
        "Rehab": "Fisioterapi, Terapi, Rehabilitasi Medik, Rehab Medik"
    }
    
    extra_context = context_map.get(tag, "")
    
    return f"""Modul Sistem: {tag}
Sinonim/Konteks tambahan: {extra_context}

Masalah/Pertanyaan:
{judul}

Solusi/Langkah-langkah:
{jawaban}

Keyword Tambahan (Slang/Error Code):
{keyword}"""


# --- CORE FEATURES ---

def search_faq(query_text, filter_tag=None, n_results=3):
    collection = get_collection()
    
    # 1. Embed Query
    resp = client_ai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query_text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    q_vec = resp.embeddings[0].values
    
    # 2. Define Filter (Pre-Filtering)
    where_clause = {"tag": filter_tag} if (filter_tag and filter_tag != "Semua Modul") else None
    
    # 3. Query Chroma
    results = collection.query(
        query_embeddings=[q_vec],
        n_results=n_results,
        where=where_clause
    )
    return results

def get_all_data_as_df():
    collection = get_collection()
    data = collection.get(include=['metadatas', 'documents'])
    if not data['ids']: return pd.DataFrame()
    
    rows = []
    for i, doc_id in enumerate(data['ids']):
        meta = data['metadatas'][i]
        rows.append({
            "ID": doc_id,
            "Tag": meta.get('tag', '-'),
            "Judul": meta.get('judul', '-'),
            "Jawaban": meta.get('jawaban_tampil', ''),
            "Keyword": meta.get('keywords_raw', ''),
            "Gambar": meta.get('path_gambar', 'none'),
            "Source": meta.get('sumber_url', '')
        })
    
    df = pd.DataFrame(rows)
    # Sort numeric ID
    df['ID_Num'] = pd.to_numeric(df['ID'], errors='coerce')
    df = df.sort_values('ID_Num', ascending=False).drop(columns=['ID_Num'])
    return df

def upsert_faq(doc_id, tag, judul, jawaban, keyword, img_paths, src_url):
    collection = get_collection()
    text_embed = build_context_text(judul, jawaban, keyword, tag)
    vector = generate_embedding(text_embed)
    
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