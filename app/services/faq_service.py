"""
FAQ Service - Mengelola CRUD operasi untuk FAQ.
Uses VectorStorePort via container (no direct ChromaDB dependency).
"""

import pandas as pd
from typing import Dict, Optional, List, Any

from config import container
from core.image_handler import ImageHandler
from .embedding_service import EmbeddingService


class FaqService:
    """
    Service untuk operasi CRUD pada FAQ.
    Menangani:
    - Create/Update FAQ
    - Delete FAQ (dengan cascade delete gambar)
    - Get FAQ by ID
    - Export ke DataFrame (untuk admin)
    """

    @classmethod
    def _get_next_id(cls) -> str:
        """
        Generate ID baru untuk FAQ.
        ID adalah auto-increment numeric string.
        """
        store = container.get_vector_store()
        existing_ids = store.get_all_ids()

        if not existing_ids:
            return "1"

        numeric_ids = []
        for x in existing_ids:
            if x.isdigit():
                numeric_ids.append(int(x))

        if not numeric_ids:
            return "1"

        return str(max(numeric_ids) + 1)

    @classmethod
    def upsert(
        cls,
        tag: str,
        judul: str,
        jawaban: str,
        keywords: str,
        img_paths: str = "none",
        source_url: str = "",
        doc_id: Optional[str] = None
    ) -> str:
        """
        Create atau Update FAQ.

        Args:
            tag: Tag/modul
            judul: Judul FAQ
            jawaban: Isi jawaban (dengan markdown dan [GAMBAR X])
            keywords: Variasi pertanyaan user (HyDE)
            img_paths: Path gambar (semicolon-separated)
            source_url: URL sumber referensi
            doc_id: ID dokumen (None atau "auto" untuk create baru)

        Returns:
            ID dokumen yang disimpan
        """
        store = container.get_vector_store()

        # Determine ID
        final_id = str(doc_id) if doc_id and doc_id != "auto" else cls._get_next_id()

        # Generate embedding AND document text (single source of truth)
        vector, text_embed = EmbeddingService.build_faq_document(
            tag=tag,
            judul=judul,
            jawaban=jawaban,
            keywords=keywords
        )

        # Upsert ke vector store
        store.upsert(
            doc_id=final_id,
            embedding=vector,
            document=text_embed,
            metadata={
                "tag": tag,
                "judul": judul,
                "jawaban_tampil": jawaban,
                "keywords_raw": keywords,
                "path_gambar": img_paths,
                "sumber_url": source_url
            }
        )

        return final_id

    @classmethod
    def delete(cls, doc_id: str) -> bool:
        """
        Hapus FAQ beserta gambar terkait (cascade delete).

        Args:
            doc_id: ID dokumen

        Returns:
            True jika berhasil
        """
        store = container.get_vector_store()

        try:
            # Ambil data dulu untuk hapus gambar
            doc = store.get_by_id(str(doc_id), include_documents=False)

            if doc:
                img_str = doc.metadata.get('path_gambar', 'none')

                # Hapus file gambar
                if img_str and img_str.lower() != 'none':
                    ImageHandler.delete_images(img_str)

            # Hapus dari database
            return store.delete(str(doc_id))

        except Exception as e:
            print(f"Error deleting FAQ {doc_id}: {e}")
            return False

    @classmethod
    def get_by_id(cls, doc_id: str) -> Optional[Dict]:
        """
        Ambil FAQ berdasarkan ID.

        Args:
            doc_id: ID dokumen

        Returns:
            Dict metadata atau None jika tidak ditemukan
        """
        store = container.get_vector_store()
        doc = store.get_by_id(str(doc_id), include_documents=True)

        if doc:
            result = dict(doc.metadata)
            result['id'] = doc.id
            result['document'] = doc.document
            return result

        return None

    @classmethod
    def get_all_as_dataframe(cls) -> pd.DataFrame:
        """
        Ambil semua FAQ sebagai DataFrame.
        Berguna untuk tampilan admin.

        Returns:
            DataFrame dengan semua FAQ
        """
        store = container.get_vector_store()
        docs = store.get_all(include_documents=True)

        if not docs:
            return pd.DataFrame()

        rows = []
        for doc in docs:
            meta = doc.metadata
            rows.append({
                "ID": doc.id,
                "Tag": meta.get('tag'),
                "Judul": meta.get('judul'),
                "Jawaban": meta.get('jawaban_tampil'),
                "Keyword": meta.get('keywords_raw'),
                "Gambar": meta.get('path_gambar'),
                "Source": meta.get('sumber_url'),
                "AI Context": doc.document
            })

        df = pd.DataFrame(rows)

        # Sort by ID descending
        df['ID_Num'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0)
        df = df.sort_values('ID_Num', ascending=False).drop(columns=['ID_Num'])

        return df

    @classmethod
    def count_by_tag(cls, tag: str) -> int:
        """
        Hitung jumlah FAQ dengan tag tertentu.
        Berguna untuk validasi sebelum hapus tag.

        Args:
            tag: Nama tag

        Returns:
            Jumlah FAQ dengan tag tersebut
        """
        df = cls.get_all_as_dataframe()
        if df.empty:
            return 0
        return len(df[df['Tag'] == tag])


# Singleton instance
faq_service = FaqService()
