"""
Embedding Service - Mengelola generasi embedding vector.
HyDE formatting (business logic) lives here. Raw text-to-vector conversion
is delegated to the EmbeddingPort via container.
"""

from typing import List

from config import container
from core.content_parser import ContentParser
from core.tag_manager import TagManager


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
            List of float (embedding vector)
        """
        return container.get_embedding().embed(text)

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
            List of float (embedding vector)
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

        return container.get_embedding().embed(text_embed)

    @staticmethod
    def generate_query_embedding(query: str) -> List[float]:
        """
        Generate embedding untuk query pencarian.

        Args:
            query: Query pencarian user

        Returns:
            List of float (embedding vector)
        """
        return container.get_embedding().embed(query)


# Singleton instance untuk kemudahan import
embedding_service = EmbeddingService()
