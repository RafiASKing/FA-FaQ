"""
Search Service - Mengelola logika pencarian semantic.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from config.database import DatabaseFactory
from config.constants import (
    RELEVANCE_THRESHOLD,
    HIGH_RELEVANCE_THRESHOLD,
    MEDIUM_RELEVANCE_THRESHOLD,
    SEARCH_CANDIDATE_LIMIT,
    WEB_TOP_RESULTS,
    BOT_TOP_RESULTS
)
from core.tag_manager import TagManager
from .embedding_service import EmbeddingService, retry_on_lock


@dataclass
class SearchResult:
    """Representasi hasil pencarian."""
    id: str
    tag: str
    judul: str
    jawaban_tampil: str
    keywords_raw: str
    path_gambar: str
    sumber_url: str
    score: float
    score_class: str  # high, med, low
    badge_color: str
    
    @property
    def is_relevant(self) -> bool:
        """Apakah hasil ini dianggap relevan."""
        return self.score > RELEVANCE_THRESHOLD


class SearchService:
    """
    Service untuk pencarian semantic.
    Menangani:
    - Query ke ChromaDB
    - Kalkulasi relevance score
    - Filtering berdasarkan threshold
    - Pre-filtering berdasarkan tag
    """
    
    @staticmethod
    def calculate_relevance(distance: float) -> float:
        """
        Hitung score relevance dari Euclidean distance.
        
        ChromaDB mengembalikan L2 distance (semakin kecil = semakin mirip).
        Kita konversi ke persentase (semakin besar = semakin relevan).
        
        Args:
            distance: L2 Euclidean distance dari ChromaDB
            
        Returns:
            Score 0-100 (persentase relevance)
        """
        return max(0, (1 - distance) * 100)
    
    @staticmethod
    def get_score_class(score: float) -> str:
        """
        Tentukan class CSS berdasarkan score.
        
        Args:
            score: Relevance score (0-100)
            
        Returns:
            String class (score-high, score-med, score-low)
        """
        if score > HIGH_RELEVANCE_THRESHOLD:
            return "score-high"
        elif score > MEDIUM_RELEVANCE_THRESHOLD:
            return "score-med"
        else:
            return "score-low"
    
    @classmethod
    @retry_on_lock()
    def search(
        cls,
        query: str,
        filter_tag: Optional[str] = None,
        n_results: int = SEARCH_CANDIDATE_LIMIT,
        min_score: float = RELEVANCE_THRESHOLD
    ) -> List[SearchResult]:
        """
        Pencarian semantic di database.
        
        Args:
            query: Query pencarian
            filter_tag: Filter berdasarkan tag (None = semua)
            n_results: Jumlah kandidat hasil dari DB
            min_score: Minimum score untuk dianggap relevan
            
        Returns:
            List of SearchResult yang sudah difilter dan diurutkan
        """
        # Generate embedding untuk query
        query_vector = EmbeddingService.generate_query_embedding(query)
        
        if not query_vector:
            return []
        
        # Build where clause untuk pre-filtering
        where_clause = None
        if filter_tag and filter_tag != "Semua Modul":
            where_clause = {"tag": filter_tag}
        
        # Query ke ChromaDB
        collection = DatabaseFactory.get_collection()
        raw_results = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where_clause
        )
        
        # Parse dan filter hasil
        results = []
        
        if raw_results['ids'][0]:
            for i in range(len(raw_results['ids'][0])):
                doc_id = raw_results['ids'][0][i]
                meta = raw_results['metadatas'][0][i]
                distance = raw_results['distances'][0][i]
                
                score = cls.calculate_relevance(distance)
                
                # Filter berdasarkan threshold
                if score > min_score:
                    tag = meta.get('tag', 'Umum')
                    results.append(SearchResult(
                        id=doc_id,
                        tag=tag,
                        judul=meta.get('judul', ''),
                        jawaban_tampil=meta.get('jawaban_tampil', ''),
                        keywords_raw=meta.get('keywords_raw', ''),
                        path_gambar=meta.get('path_gambar', 'none'),
                        sumber_url=meta.get('sumber_url', ''),
                        score=score,
                        score_class=cls.get_score_class(score),
                        badge_color=TagManager.get_tag_color(tag)
                    ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    @classmethod
    def search_for_web(
        cls,
        query: str,
        filter_tag: Optional[str] = None,
        top_n: int = WEB_TOP_RESULTS
    ) -> List[SearchResult]:
        """
        Pencarian untuk Web UI (Top N hasil).
        
        Args:
            query: Query pencarian
            filter_tag: Filter tag
            top_n: Jumlah hasil maksimal
            
        Returns:
            Top N SearchResult
        """
        results = cls.search(query, filter_tag)
        return results[:top_n]
    
    @classmethod
    def search_for_bot(
        cls,
        query: str,
        filter_tag: Optional[str] = None,
        top_n: int = BOT_TOP_RESULTS
    ) -> List[SearchResult]:
        """
        Pencarian untuk WhatsApp Bot.
        
        Args:
            query: Query pencarian
            filter_tag: Filter tag
            top_n: Jumlah hasil maksimal
            
        Returns:
            Top N SearchResult
        """
        results = cls.search(query, filter_tag, n_results=top_n)
        return results[:1]  # Bot hanya return 1 hasil terbaik
    
    @classmethod
    @retry_on_lock()
    def get_all_faqs(cls, filter_tag: Optional[str] = None) -> List[Dict]:
        """
        Ambil semua FAQ (untuk browse mode).
        
        Args:
            filter_tag: Filter berdasarkan tag (None = semua)
            
        Returns:
            List of FAQ metadata, sorted by ID descending
        """
        collection = DatabaseFactory.get_collection()
        data = collection.get(include=['metadatas'])
        
        results = []
        if data['ids']:
            for i, doc_id in enumerate(data['ids']):
                meta = data['metadatas'][i]
                
                # Filter by tag jika ada
                if filter_tag and filter_tag != "Semua Modul":
                    if meta.get('tag') != filter_tag:
                        continue
                
                try:
                    id_num = int(doc_id)
                except:
                    id_num = 0
                
                tag = meta.get('tag', 'Umum')
                meta['id'] = doc_id
                meta['id_num'] = id_num
                meta['badge_color'] = TagManager.get_tag_color(tag)
                results.append(meta)
        
        # Sort by ID descending (terbaru di atas)
        results.sort(key=lambda x: x.get('id_num', 0), reverse=True)
        
        return results
    
    @classmethod
    @retry_on_lock()
    def get_unique_tags(cls) -> List[str]:
        """
        Ambil daftar tag unik dari database.
        
        Returns:
            List of unique tag names, sorted alphabetically
        """
        collection = DatabaseFactory.get_collection()
        data = collection.get(include=['metadatas'])
        
        unique_tags = set()
        if data['metadatas']:
            for meta in data['metadatas']:
                if meta and meta.get('tag'):
                    unique_tags.add(meta['tag'])
        
        return sorted(list(unique_tags))


# Singleton instance
search_service = SearchService()
