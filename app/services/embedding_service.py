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
    def _build_document_text(
        cls,
        tag: str,
        judul: str,
        jawaban: str,
        keywords: str
    ) -> str:
        """
        Build document text for embedding (single source of truth).
        
        Template:
            MODUL: {tag} ({tag_description})
            TOPIK: {judul}
            TERKAIT: {keywords}
            ISI KONTEN: {clean_jawaban}
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

        # Format HyDE (single source of truth!)
        return f"""MODUL: {domain_str}
TOPIK: {judul}
TERKAIT: {keywords}
ISI KONTEN: {clean_jawaban}"""

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

        Args:
            tag: Tag/modul (ED, OPD, IPD, dll)
            judul: Judul FAQ
            jawaban: Isi jawaban
            keywords: Keywords/terms terkait

        Returns:
            List of float (embedding vector)
        """
        text_embed = cls._build_document_text(tag, judul, jawaban, keywords)
        return container.get_embedding().embed(text_embed)

    @classmethod
    def build_faq_document(
        cls,
        tag: str,
        judul: str,
        jawaban: str,
        keywords: str
    ) -> tuple[List[float], str]:
        """
        Build FAQ document: generate embedding AND document text.
        Use this when you need both (e.g., upsert to vector store).

        Returns:
            Tuple of (embedding_vector, document_text)
        """
        text_embed = cls._build_document_text(tag, judul, jawaban, keywords)
        embedding = container.get_embedding().embed(text_embed)
        return embedding, text_embed

    @staticmethod
    def generate_query_embedding(query: str) -> List[float]:
        """
        Generate embedding untuk query pencarian.
        Uses RETRIEVAL_QUERY task type for optimal query-document matching.

        Args:
            query: Query pencarian user

        Returns:
            List of float (embedding vector)
        """
        return container.get_embedding().embed(query, task_type="RETRIEVAL_QUERY")


# Singleton instance untuk kemudahan import
embedding_service = EmbeddingService()
