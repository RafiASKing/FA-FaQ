"""
Image Handler - Mengelola upload, kompresi, dan path gambar.
"""

import os
import re
import random
import string
import base64
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image

from config.settings import paths
from config.constants import IMAGE_MAX_WIDTH, IMAGE_QUALITY
from core.logger import log


class ImageHandler:
    """
    Handler untuk operasi gambar:
    - Upload dan kompresi
    - Path normalization
    - Base64 conversion (untuk WhatsApp)
    - Cleanup/delete
    """
    
    @staticmethod
    def sanitize_filename(text: str) -> str:
        """
        Membersihkan nama file dari karakter tidak valid.
        
        Args:
            text: Nama file original
            
        Returns:
            Nama file yang sudah dibersihkan
        """
        return re.sub(r'[^\w\-_]', '', text.replace(" ", "_"))[:30]
    
    @classmethod
    def save_uploaded_images(
        cls, 
        uploaded_files: List, 
        judul: str, 
        tag: str,
        images_dir: Path = None
    ) -> str:
        """
        Simpan dan kompres gambar yang diupload.
        
        Args:
            uploaded_files: List of uploaded file objects
            judul: Judul FAQ (untuk nama file)
            tag: Tag/modul (untuk subfolder)
            images_dir: Directory untuk menyimpan gambar
            
        Returns:
            String path yang dipisahkan semicolon, atau "none"
        """
        if not uploaded_files:
            return "none"
        
        if images_dir is None:
            images_dir = paths.IMAGES_DIR
        
        saved_paths = []
        clean_judul = cls.sanitize_filename(judul)
        target_dir = Path(images_dir) / tag
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Get resampling method (compatible dengan berbagai versi Pillow)
        resample_module = getattr(Image, "Resampling", None)
        resample_method = resample_module.LANCZOS if resample_module else getattr(Image, "LANCZOS", Image.BICUBIC)
        
        for i, file in enumerate(uploaded_files):
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            filename = f"{clean_judul}_{tag}_{i+1}_{suffix}.jpg"
            full_path = target_dir / filename
            
            try:
                if hasattr(file, "seek"):
                    file.seek(0)
                
                image = Image.open(file)
                
                # Convert RGBA/P to RGB
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                
                # Resize jika terlalu besar
                if image.width > IMAGE_MAX_WIDTH:
                    ratio = IMAGE_MAX_WIDTH / float(image.width)
                    new_height = int(float(image.height) * ratio)
                    image = image.resize((IMAGE_MAX_WIDTH, new_height), resample_method)
                
                # Simpan dengan kompresi
                image.save(str(full_path), "JPEG", quality=IMAGE_QUALITY, optimize=True)
                
            except Exception as e:
                log(f"Gagal compress gambar {getattr(file, 'name', 'unknown')}: {e}")
                # Fallback: simpan raw
                if hasattr(file, "seek"):
                    file.seek(0)
                with open(full_path, "wb") as f:
                    f.write(file.getbuffer() if hasattr(file, 'getbuffer') else file.read())
            finally:
                if hasattr(file, "seek"):
                    file.seek(0)
            
            # Simpan relative path
            rel_path = f"./images/{tag}/{filename}"
            saved_paths.append(rel_path)
        
        return ";".join(saved_paths)
    
    @staticmethod
    def fix_path_for_ui(db_path: str) -> Optional[str]:
        """
        Normalisasi path gambar dari database untuk UI.
        
        Args:
            db_path: Path dari database
            
        Returns:
            Path yang sudah dinormalisasi atau None
        """
        if not db_path:
            return None
            
        clean = str(db_path).strip('"').strip("'")
        if clean.lower() == "none":
            return None
            
        clean = clean.replace("\\", "/")
        if clean.startswith("./"):
            return clean
        return clean
    
    @staticmethod
    def get_base64_image(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert gambar ke base64 string (untuk WhatsApp API).
        
        Args:
            file_path: Path ke file gambar
            
        Returns:
            Tuple of (base64_data_uri, filename) atau (None, None) jika error
        """
        try:
            clean_path = file_path.replace("\\", "/")
            if not os.path.exists(clean_path):
                return None, None
            
            mime_type, _ = mimetypes.guess_type(clean_path)
            if not mime_type:
                mime_type = "image/jpeg"
            
            with open(clean_path, "rb") as image_file:
                raw_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            return f"data:{mime_type};base64,{raw_base64}", os.path.basename(clean_path)
        except Exception:
            return None, None
    
    @classmethod
    def delete_images(cls, path_string: str) -> List[str]:
        """
        Hapus file gambar dari disk.
        
        Args:
            path_string: String path dari database (semicolon-separated)
            
        Returns:
            List of deleted file paths
        """
        deleted = []
        
        if not path_string or path_string.lower() == 'none':
            return deleted
        
        paths_list = path_string.split(';')
        for p in paths_list:
            clean_path = p.strip().replace("\\", "/")
            if os.path.exists(clean_path):
                try:
                    os.remove(clean_path)
                    deleted.append(clean_path)
                    log(f"File Deleted: {clean_path}")
                except Exception as e:
                    log(f"Gagal hapus file {clean_path}: {e}")
        
        return deleted
    
    @staticmethod
    def check_image_exists(path: str) -> bool:
        """Check apakah file gambar ada."""
        if not path:
            return False
        clean = path.replace("\\", "/")
        return os.path.exists(clean)
