"""
Tag Manager - Mengelola konfigurasi tag/modul.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List

from config.settings import paths
from config.constants import DEFAULT_TAGS, HEX_TO_STREAMLIT_COLOR, COLOR_PALETTE
from core.logger import log


class TagManager:
    """
    Manager untuk tag/modul configuration.
    Menangani:
    - Load/save tags dari JSON
    - Mapping warna
    - Validasi tag
    """
    
    _cache: Dict = None
    _cache_file_mtime: float = 0
    
    @classmethod
    def load_tags(cls, force_reload: bool = False) -> Dict:
        """
        Load konfigurasi tag dari JSON file.
        Menggunakan cache untuk performa.
        
        Args:
            force_reload: Force reload dari disk
            
        Returns:
            Dict of tags configuration
        """
        tags_file = paths.TAGS_FILE
        
        # Check if cache is valid
        if not force_reload and cls._cache is not None:
            try:
                current_mtime = tags_file.stat().st_mtime
                if current_mtime == cls._cache_file_mtime:
                    return cls._cache
            except FileNotFoundError:
                pass
        
        # Load from file or create default
        if not tags_file.exists():
            cls.save_tags(DEFAULT_TAGS)
            cls._cache = DEFAULT_TAGS.copy()
            cls._cache_file_mtime = tags_file.stat().st_mtime
            return cls._cache
        
        try:
            with open(tags_file, "r", encoding="utf-8") as f:
                cls._cache = json.load(f)
                cls._cache_file_mtime = tags_file.stat().st_mtime
                return cls._cache
        except (json.JSONDecodeError, IOError) as e:
            log(f"Error loading tags config: {e}")
            return DEFAULT_TAGS.copy()
    
    @classmethod
    def save_tags(cls, tags_dict: Dict) -> bool:
        """
        Simpan konfigurasi tag ke JSON file.
        
        Args:
            tags_dict: Dict of tags configuration
            
        Returns:
            True jika sukses
        """
        tags_file = paths.TAGS_FILE
        
        try:
            # Ensure directory exists
            tags_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(tags_file, "w", encoding="utf-8") as f:
                json.dump(tags_dict, f, indent=4, ensure_ascii=False)
            
            # Update cache
            cls._cache = tags_dict.copy()
            cls._cache_file_mtime = tags_file.stat().st_mtime
            return True
        except IOError as e:
            log(f"Error saving tags config: {e}")
            return False
    
    @classmethod
    def get_tag_info(cls, tag_name: str) -> Dict:
        """
        Dapatkan info untuk tag tertentu.
        
        Args:
            tag_name: Nama tag
            
        Returns:
            Dict dengan color dan desc, atau default values
        """
        tags = cls.load_tags()
        return tags.get(tag_name, {"color": "#808080", "desc": ""})
    
    @classmethod
    def get_tag_color(cls, tag_name: str) -> str:
        """Dapatkan warna HEX untuk tag."""
        return cls.get_tag_info(tag_name).get("color", "#808080")
    
    @classmethod
    def get_tag_description(cls, tag_name: str) -> str:
        """Dapatkan deskripsi untuk tag."""
        return cls.get_tag_info(tag_name).get("desc", "")
    
    @classmethod
    def get_streamlit_color_name(cls, tag_name: str) -> str:
        """
        Convert tag color ke nama warna Streamlit.
        Streamlit badge hanya support nama warna tertentu.
        
        Args:
            tag_name: Nama tag
            
        Returns:
            Nama warna Streamlit (red, green, blue, orange, violet, gray)
        """
        hex_code = cls.get_tag_color(tag_name).upper()
        return HEX_TO_STREAMLIT_COLOR.get(hex_code, "gray")
    
    @classmethod
    def hex_to_streamlit_color(cls, hex_code: str) -> str:
        """
        Convert HEX color ke nama warna Streamlit.
        
        Args:
            hex_code: Kode warna HEX (e.g. "#FF0000")
            
        Returns:
            Nama warna Streamlit (red, green, blue, orange, violet, gray)
        """
        return HEX_TO_STREAMLIT_COLOR.get(hex_code.upper(), "gray")
    
    @classmethod
    def add_tag(cls, name: str, color: str, description: str = "") -> bool:
        """
        Tambah atau update tag.
        
        Args:
            name: Nama tag
            color: Warna HEX
            description: Deskripsi/sinonim
            
        Returns:
            True jika sukses
        """
        tags = cls.load_tags()
        tags[name] = {"color": color, "desc": description}
        return cls.save_tags(tags)
    
    @classmethod
    def delete_tag(cls, name: str) -> bool:
        """
        Hapus tag.
        
        Args:
            name: Nama tag
            
        Returns:
            True jika sukses
        """
        tags = cls.load_tags()
        if name in tags:
            del tags[name]
            return cls.save_tags(tags)
        return False
    
    @classmethod
    def get_all_tag_names(cls) -> List[str]:
        """Dapatkan list semua nama tag."""
        return list(cls.load_tags().keys())
    
    @classmethod
    def get_color_palette(cls) -> Dict:
        """Dapatkan color palette untuk admin UI."""
        return COLOR_PALETTE.copy()
    
    @classmethod
    def invalidate_cache(cls):
        """Invalidate cache (untuk testing atau force refresh)."""
        cls._cache = None
        cls._cache_file_mtime = 0


# Backward compatibility functions
def load_tags_config() -> Dict:
    """Legacy function untuk kompatibilitas."""
    return TagManager.load_tags()

def save_tags_config(tags_dict: Dict) -> bool:
    """Legacy function untuk kompatibilitas."""
    return TagManager.save_tags(tags_dict)
