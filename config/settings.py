"""
Centralized Settings menggunakan Pydantic BaseSettings.
Semua environment variables dikelola di sini.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application Settings - Single Source of Truth untuk semua konfigurasi.
    Nilai diambil dari environment variables atau menggunakan default.
    """
    
    # === API KEYS & AUTH ===
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    admin_password_hash: str = Field(default="admin", alias="ADMIN_PASSWORD_HASH")
    
    # === CHROMA DB ===
    chroma_host: str | None = Field(default=None, alias="CHROMA_HOST")
    chroma_port: int | None = Field(default=None, alias="CHROMA_PORT")
    
    # === WHATSAPP BOT ===
    wa_base_url: str = Field(default="http://wppconnect:21465", alias="WA_BASE_URL")
    wa_secret_key: str = Field(default="THISISMYSECURETOKEN", alias="WA_SESSION_KEY")
    wa_session_name: str = Field(default="mysession", alias="WA_SESSION_NAME")
    bot_identities: str = Field(default="", alias="BOT_IDENTITIES")
    
    # === BOT LOGIC THRESHOLDS ===
    bot_min_score: float = Field(default=80.0, alias="BOT_MIN_SCORE")
    bot_min_gap: float = Field(default=10.0, alias="BOT_MIN_GAP")
    
    # === WEB CONFIG ===
    web_v2_url: str = Field(default="https://faq-assist.cloud/", alias="WEB_V2_URL")
    wa_support_number: str = Field(default="6289635225253", alias="WA_SUPPORT_NUMBER")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars
    
    @property
    def bot_identity_list(self) -> List[str]:
        """Parse BOT_IDENTITIES string menjadi list."""
        if not self.bot_identities:
            return []
        return [x.strip() for x in self.bot_identities.split(",") if x.strip()]
    
    @property
    def is_chroma_server_mode(self) -> bool:
        """Cek apakah menggunakan ChromaDB server mode."""
        return bool(self.chroma_host and self.chroma_port)


class PathSettings:
    """
    Path Configuration - Semua path dikelola di sini.
    Tidak menggunakan Pydantic karena path perlu dihitung dari BASE_DIR.
    """
    
    def __init__(self):
        # Base directory (root project)
        self.BASE_DIR = Path(__file__).parent.parent.resolve()
        
        # Data paths
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DB_PATH = self.DATA_DIR / "chroma_data"
        self.TAGS_FILE = self.DATA_DIR / "tags_config.json"
        self.FAILED_SEARCH_LOG = self.DATA_DIR / "failed_searches.csv"
        
        # Assets paths
        self.IMAGES_DIR = self.BASE_DIR / "images"
        
        # Web V2 paths
        self.WEB_V2_DIR = self.BASE_DIR / "web_v2"
        self.TEMPLATES_DIR = self.WEB_V2_DIR / "templates"
        self.STATIC_DIR = self.WEB_V2_DIR / "static"
        
        # Ensure directories exist
        self._setup_directories()
    
    def _setup_directories(self):
        """Membuat folder yang diperlukan jika belum ada."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.IMAGES_DIR.mkdir(exist_ok=True)
        self.DB_PATH.mkdir(exist_ok=True)


# Singleton instances
settings = Settings()
paths = PathSettings()
