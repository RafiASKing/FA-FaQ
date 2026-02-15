"""
Unified Content Parser - Menangani parsing [GAMBAR X] dan format konten.
Menggantikan 4 implementasi terpisah di app.py, admin.py, bot_wa.py, dan web_v2/main.py
"""

import re
import os
import markdown
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class ParsedImage:
    """Representasi gambar yang sudah diparsing."""
    index: int          # 1-based index (sesuai [GAMBAR 1])
    path: str           # Path file gambar
    exists: bool        # Apakah file ada


class ContentParser:
    """
    Parser terpusat untuk konten FAQ.
    Menangani:
    - Parsing tag [GAMBAR X] 
    - Konversi ke berbagai format output (Streamlit, HTML, WhatsApp)
    - Pembersihan teks untuk embedding
    """
    
    # Regex pattern untuk [GAMBAR X]
    IMAGE_TAG_PATTERN = re.compile(r'\[GAMBAR\s*(\d+)\]', re.IGNORECASE)
    
    @classmethod
    def parse_image_paths(cls, path_string: str) -> List[str]:
        """
        Parse string path gambar dari database.
        
        Args:
            path_string: String path dari DB (semicolon-separated)
            
        Returns:
            List of cleaned image paths
        """
        if not path_string or str(path_string).lower() == 'none':
            return []
        
        paths = []
        for p in path_string.split(';'):
            clean = p.strip().replace("\\", "/")
            if clean:
                paths.append(clean)
        return paths
    
    @classmethod
    def split_by_image_tags(cls, text: str) -> List[str]:
        """
        Split teks berdasarkan tag [GAMBAR X].
        
        Args:
            text: Teks dengan tag gambar
            
        Returns:
            List of parts (teks dan tag gambar bergantian)
        """
        return cls.IMAGE_TAG_PATTERN.split(text)
    
    @classmethod
    def extract_image_index(cls, tag_text: str) -> Optional[int]:
        """
        Ekstrak nomor dari tag gambar.
        
        Args:
            tag_text: String seperti "[GAMBAR 1]"
            
        Returns:
            Integer index (0-based) atau None
        """
        match = cls.IMAGE_TAG_PATTERN.search(tag_text)
        if match:
            return int(match.group(1)) - 1  # Convert ke 0-based
        return None
    
    @classmethod
    def clean_for_embedding(cls, text: str) -> str:
        """
        Membersihkan teks untuk embedding AI.
        Menghapus tag [GAMBAR X] tapi mempertahankan markdown.
        
        Args:
            text: Teks raw dengan tag gambar
            
        Returns:
            Teks bersih tanpa tag gambar
        """
        if not text:
            return ""
        clean = cls.IMAGE_TAG_PATTERN.sub('', text)
        return " ".join(clean.split())
    
    @classmethod
    def count_image_tags(cls, text: str) -> int:
        """
        Hitung jumlah tag [GAMBAR X] dalam teks.
        Berguna untuk auto-increment di admin panel.
        """
        return len(cls.IMAGE_TAG_PATTERN.findall(text))
    
    @classmethod
    def to_html(cls, text: str, image_paths: str, base_image_url: str = "/images") -> str:
        """
        Convert konten ke HTML untuk web_v2.
        
        Args:
            text: Teks markdown dengan tag gambar
            image_paths: String path gambar dari DB
            base_image_url: Base URL untuk gambar
            
        Returns:
            HTML string
        """
        if not text:
            return ""
        
        # Fix markdown format
        text = cls._fix_markdown_format(text)
        
        # Convert markdown to HTML
        try:
            html_content = markdown.markdown(
                text, 
                extensions=['nl2br', 'extra', 'sane_lists']
            )
        except Exception:
            html_content = markdown.markdown(text)
        
        # Parse image paths
        img_list = cls.parse_image_paths(image_paths)
        
        # Fix paths untuk web (hapus ./ prefix)
        web_img_list = []
        for p in img_list:
            if p.startswith("./images"):
                p = p[1:]  # Hapus titik, jadi /images/...
            web_img_list.append(p)
        
        # Replace [GAMBAR X] dengan HTML img
        def replace_match(match):
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(web_img_list):
                    return f'''
                    <div class="img-container">
                        <img src="{web_img_list[idx]}" alt="Gambar {idx+1}" loading="lazy" onclick="window.open(this.src, '_blank');">
                        <span class="img-caption">Gambar {idx+1} (Klik untuk perbesar)</span>
                    </div>
                    '''
                return ""
            except Exception:
                return ""
        
        html_content = cls.IMAGE_TAG_PATTERN.sub(replace_match, html_content)
        
        # Fallback gallery jika tidak ada tag [GAMBAR] tapi ada gambar
        if "[GAMBAR" not in text.upper() and web_img_list:
            html_content += "<hr class='img-divider'><div class='gallery-grid'>"
            for img in web_img_list:
                html_content += f'<div class="img-card"><img src="{img}" onclick="window.open(this.src, \'_blank\');"></div>'
            html_content += "</div>"
        
        return html_content
    
    @classmethod
    def to_whatsapp(cls, text: str, image_paths: str) -> Tuple[str, List[str]]:
        """
        Convert konten untuk WhatsApp.
        
        Args:
            text: Teks dengan tag gambar
            image_paths: String path gambar dari DB
            
        Returns:
            Tuple of (processed_text, list_of_image_paths_to_send)
        """
        img_list = cls.parse_image_paths(image_paths)
        images_to_send = []
        
        def replace_tag(match):
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_list):
                    images_to_send.append(img_list[idx])
                    return f"*(Lihat Gambar {idx+1})*"
                return ""
            except Exception:
                return ""
        
        processed_text = cls.IMAGE_TAG_PATTERN.sub(replace_tag, text)
        
        # Jika tidak ada tag tapi ada gambar, kirim semua
        if not images_to_send and img_list:
            images_to_send = img_list
        
        return processed_text, images_to_send
    
    @classmethod 
    def get_streamlit_parts(cls, text: str, image_paths: str) -> List[dict]:
        """
        Parse konten untuk rendering Streamlit.
        
        Args:
            text: Teks dengan tag gambar
            image_paths: String path gambar dari DB
            
        Returns:
            List of dicts dengan type='text' atau type='image'
        """
        img_list = cls.parse_image_paths(image_paths)
        parts = re.split(r'(\[GAMBAR\s*\d+\])', text, flags=re.IGNORECASE)
        
        result = []
        for part in parts:
            match = cls.IMAGE_TAG_PATTERN.search(part)
            if match:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_list):
                    path = cls._fix_path_for_ui(img_list[idx])
                    result.append({
                        'type': 'image',
                        'index': idx + 1,
                        'path': path,
                        'exists': path and os.path.exists(path)
                    })
                else:
                    result.append({
                        'type': 'missing_image',
                        'index': idx + 1
                    })
            else:
                if part.strip():
                    result.append({
                        'type': 'text',
                        'content': part
                    })
        
        # Fallback: jika tidak ada tag tapi ada gambar
        if len(result) == 1 and result[0].get('type') == 'text' and img_list:
            result.append({'type': 'divider'})
            for idx, p in enumerate(img_list):
                path = cls._fix_path_for_ui(p)
                result.append({
                    'type': 'gallery_image',
                    'index': idx,
                    'path': path,
                    'exists': path and os.path.exists(path)
                })
        
        return result
    
    @staticmethod
    def _fix_markdown_format(text: str) -> str:
        """Memperbaiki format markdown agar list terbaca dengan benar."""
        if not text:
            return ""
        # Paksa list angka punya enter ganda sebelumnya
        text = re.sub(r'([^\n])\n(\d+\.\s)', r'\1\n\n\2', text)
        # Paksa list bullet punya enter ganda sebelumnya
        text = re.sub(r'([^\n])\n(-\s)', r'\1\n\n\2', text)
        return text
    
    @staticmethod
    def _fix_path_for_ui(db_path: str) -> Optional[str]:
        """Normalisasi path gambar untuk UI."""
        clean = str(db_path).strip('"').strip("'")
        if clean.lower() == "none":
            return None
        clean = clean.replace("\\", "/")
        if clean.startswith("./"):
            return clean
        return clean
