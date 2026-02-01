"""
Database Connection Factory - ChromaDB Client Management.
Mengelola koneksi ke ChromaDB dengan support server mode dan local mode.
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


def get_db_client_raw():
    """
    Fungsi standalone untuk mendapatkan DB client.
    Berguna untuk penggunaan di luar class (compatibility dengan kode lama).
    """
    return DatabaseFactory.get_db_client()


def get_ai_client_raw():
    """
    Fungsi standalone untuk mendapatkan AI client.
    Berguna untuk penggunaan di luar class (compatibility dengan kode lama).
    """
    return DatabaseFactory.get_ai_client()


def get_collection_raw():
    """
    Fungsi standalone untuk mendapatkan collection.
    Berguna untuk penggunaan di luar class (compatibility dengan kode lama).
    """
    return DatabaseFactory.get_collection()


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
