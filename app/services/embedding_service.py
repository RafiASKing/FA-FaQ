"""
Embedding Service - Mengelola generasi embedding vector.
"""

import functools
import time
import random
from typing import List, Optional

from config.database import DatabaseFactory, generate_embedding
from config.constants import MAX_RETRIES, RETRY_BASE_DELAY
from core.content_parser import ContentParser
from core.tag_manager import TagManager


def retry_on_lock(max_retries: int = MAX_RETRIES, base_delay: float = RETRY_BASE_DELAY):
    """
    Decorator untuk menangani error 'Database Locked' pada SQLite.
    Menggunakan Jitter Backoff untuk menghindari thundering herd.
    """
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


class EmbeddingService:
    """
    Service untuk mengelola embedding generation.
    Menggunakan HyDE (Hypothetical Document Embeddings) format.
    """
    
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """
        Generate embedding vector untuk teks.
        
        Args:
            text: Teks yang akan di-embed
            
        Returns:
            List of float (768 dimensions)
        """
        return generate_embedding(text)
    
    @classmethod
    def generate_faq_embedding(
        cls,
        tag: str,
        judul: str,
        jawaban: str,
        keywords: str
    ) -> List[float]:
        """
        Generate embedding untuk dokumen FAQ menggunakan format HyDE.
        
        Format HyDE membantu menjembatani semantic gap antara:
        - Bahasa formal dokumentasi
        - Bahasa user yang panik/informal
        
        Args:
            tag: Tag/modul (ED, OPD, IPD, dll)
            judul: Judul FAQ
            jawaban: Isi jawaban
            keywords: Variasi pertanyaan user
            
        Returns:
            List of float (768 dimensions)
        """
        # Bersihkan jawaban dari tag [GAMBAR X]
        clean_jawaban = ContentParser.clean_for_embedding(jawaban)
        
        # Dapatkan deskripsi tag
        try:
            tag_desc = TagManager.get_tag_description(tag)
        except:
            tag_desc = ""
        
        # Buat domain string
        domain_str = f"{tag} ({tag_desc})" if tag_desc else tag
        
        # Format HyDE
        text_embed = f"""DOMAIN: {domain_str}
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keywords}
ISI KONTEN: {clean_jawaban}"""
        
        return cls.generate_embedding(text_embed)
    
    @staticmethod
    def generate_query_embedding(query: str) -> List[float]:
        """
        Generate embedding untuk query pencarian.
        
        Args:
            query: Query pencarian user
            
        Returns:
            List of float (768 dimensions)
        """
        return generate_embedding(query)


# Singleton instance untuk kemudahan import
embedding_service = EmbeddingService()
