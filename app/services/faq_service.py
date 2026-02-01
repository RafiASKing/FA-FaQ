"""
FAQ Service - Mengelola CRUD operasi untuk FAQ.
"""

import os
import pandas as pd
from typing import Dict, Optional, List, Any

from config.database import DatabaseFactory
from config.constants import COLLECTION_NAME
from core.image_handler import ImageHandler
from .embedding_service import EmbeddingService, retry_on_lock


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
    def _get_next_id(cls, collection) -> str:
        """
        Generate ID baru untuk FAQ.
        ID adalah auto-increment numeric string.
        """
        data = collection.get(include=[])
        existing_ids = data['ids']
        
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
    @retry_on_lock()
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
        collection = DatabaseFactory.get_collection()
        
        # Determine ID
        final_id = str(doc_id) if doc_id and doc_id != "auto" else cls._get_next_id(collection)
        
        # Generate embedding dengan format HyDE
        vector = EmbeddingService.generate_faq_embedding(
            tag=tag,
            judul=judul,
            jawaban=jawaban,
            keywords=keywords
        )
        
        # Build document text (untuk retrieval)
        from core.content_parser import ContentParser
        from core.tag_manager import TagManager
        
        clean_jawaban = ContentParser.clean_for_embedding(jawaban)
        tag_desc = TagManager.get_tag_description(tag)
        domain_str = f"{tag} ({tag_desc})" if tag_desc else tag
        
        text_embed = f"""DOMAIN: {domain_str}
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keywords}
ISI KONTEN: {clean_jawaban}"""
        
        # Upsert ke ChromaDB
        collection.upsert(
            ids=[final_id],
            embeddings=[vector],
            documents=[text_embed],
            metadatas=[{
                "tag": tag,
                "judul": judul,
                "jawaban_tampil": jawaban,
                "keywords_raw": keywords,
                "path_gambar": img_paths,
                "sumber_url": source_url
            }]
        )
        
        return final_id
    
    @classmethod
    @retry_on_lock()
    def delete(cls, doc_id: str) -> bool:
        """
        Hapus FAQ beserta gambar terkait (cascade delete).
        
        Args:
            doc_id: ID dokumen
            
        Returns:
            True jika berhasil
        """
        collection = DatabaseFactory.get_collection()
        
        try:
            # Ambil data dulu untuk hapus gambar
            data = collection.get(ids=[str(doc_id)], include=['metadatas'])
            
            if data['metadatas'] and len(data['metadatas']) > 0:
                meta = data['metadatas'][0]
                img_str = meta.get('path_gambar', 'none')
                
                # Hapus file gambar
                if img_str and img_str.lower() != 'none':
                    ImageHandler.delete_images(img_str)
            
            # Hapus dari database
            collection.delete(ids=[str(doc_id)])
            return True
            
        except Exception as e:
            print(f"⚠️ Error deleting FAQ {doc_id}: {e}")
            return False
    
    @classmethod
    @retry_on_lock()
    def get_by_id(cls, doc_id: str) -> Optional[Dict]:
        """
        Ambil FAQ berdasarkan ID.
        
        Args:
            doc_id: ID dokumen
            
        Returns:
            Dict metadata atau None jika tidak ditemukan
        """
        collection = DatabaseFactory.get_collection()
        
        try:
            data = collection.get(ids=[str(doc_id)], include=['metadatas', 'documents'])
            
            if data['ids'] and len(data['ids']) > 0:
                meta = data['metadatas'][0]
                meta['id'] = data['ids'][0]
                meta['document'] = data['documents'][0] if data['documents'] else ""
                return meta
            
            return None
        except Exception:
            return None
    
    @classmethod
    @retry_on_lock()
    def get_all_as_dataframe(cls) -> pd.DataFrame:
        """
        Ambil semua FAQ sebagai DataFrame.
        Berguna untuk tampilan admin.
        
        Returns:
            DataFrame dengan semua FAQ
        """
        collection = DatabaseFactory.get_collection()
        data = collection.get(include=['metadatas', 'documents'])
        
        if not data['ids']:
            return pd.DataFrame()
        
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
