"""
WhatsApp Service - Mengelola integrasi dengan WPPConnect API.
"""

import requests
import time
from typing import Optional, List, Dict, Any

from config.settings import settings
from core.logger import log
from core.image_handler import ImageHandler


class WhatsAppService:
    """
    Service untuk integrasi WhatsApp via WPPConnect.
    Menangani:
    - Token management
    - Send text message
    - Send image message
    - Session management
    """
    
    _current_token: Optional[str] = None
    
    @classmethod
    def _get_base_url(cls) -> str:
        """Get WPPConnect base URL."""
        return settings.wa_base_url
    
    @classmethod
    def _get_session_name(cls) -> str:
        """Get session name."""
        return settings.wa_session_name
    
    @classmethod
    def _get_secret_key(cls) -> str:
        """Get secret key."""
        return settings.wa_secret_key
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """
        Get HTTP headers dengan auth token.
        Auto-generate token jika belum ada.
        """
        if not cls._current_token:
            log("🔄 Token kosong. Mencoba generate token baru...")
            cls.generate_token()
        
        return {
            "Authorization": f"Bearer {cls._current_token}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def generate_token(cls) -> bool:
        """
        Generate authentication token dari WPPConnect.
        
        Returns:
            True jika berhasil
        """
        try:
            url = f"{cls._get_base_url()}/api/{cls._get_session_name()}/{cls._get_secret_key()}/generate-token"
            r = requests.post(url, timeout=10)
            
            if r.status_code in [200, 201]:
                resp = r.json()
                token = resp.get("token") or resp.get("session")
                
                if not token and "full" in resp:
                    token = resp["full"].split(":")[-1]
                
                if token:
                    cls._current_token = token
                    log("✅ Berhasil Generate Token.")
                    return True
                else:
                    log("❌ Gagal Parse Token.")
            else:
                log(f"❌ Gagal Generate Token: {r.status_code}")
        except Exception as e:
            log(f"❌ Error Auth: {e}")
        
        return False
    
    @classmethod
    def send_text(cls, phone: str, message: str) -> bool:
        """
        Kirim pesan teks ke WhatsApp.
        
        Args:
            phone: Nomor telepon atau group ID
            message: Pesan yang akan dikirim
            
        Returns:
            True jika berhasil
        """
        if not phone or str(phone) == "None":
            return False
        
        url = f"{cls._get_base_url()}/api/{cls._get_session_name()}/send-message"
        is_group = "@g.us" in str(phone)
        
        payload = {
            "phone": phone,
            "message": message,
            "isGroup": is_group,
            "linkPreview": False,
            "options": {
                "linkPreview": False,
                "createChat": True
            }
        }
        
        try:
            r = requests.post(url, json=payload, headers=cls.get_headers(), timeout=30)
            log(f"📤 Balas ke {phone}: {r.status_code}")
            
            if r.status_code == 401:
                cls.generate_token()
                # Retry sekali
                r = requests.post(url, json=payload, headers=cls.get_headers(), timeout=30)
            
            return r.status_code in [200, 201]
        except Exception as e:
            log(f"❌ Error Kirim Text: {e}")
            return False
    
    @classmethod
    def send_image(cls, phone: str, file_path: str, caption: str = "") -> bool:
        """
        Kirim gambar ke WhatsApp.
        
        Args:
            phone: Nomor telepon atau group ID
            file_path: Path ke file gambar
            caption: Caption untuk gambar
            
        Returns:
            True jika berhasil
        """
        if not phone:
            return False
        
        base64_str, filename = ImageHandler.get_base64_image(file_path)
        if not base64_str:
            log(f"⚠️ Gambar tidak ditemukan: {file_path}")
            return False
        
        url = f"{cls._get_base_url()}/api/{cls._get_session_name()}/send-image"
        is_group = "@g.us" in str(phone)
        
        payload = {
            "phone": phone,
            "base64": base64_str,
            "caption": caption,
            "isGroup": is_group
        }
        
        try:
            r = requests.post(url, json=payload, headers=cls.get_headers(), timeout=60)
            return r.status_code in [200, 201]
        except Exception as e:
            log(f"❌ Error Kirim Image: {e}")
            return False
    
    @classmethod
    def send_images(cls, phone: str, file_paths: List[str], delay: float = 0.5) -> int:
        """
        Kirim multiple gambar dengan delay.
        
        Args:
            phone: Nomor telepon
            file_paths: List of image paths
            delay: Delay antar pengiriman (seconds)
            
        Returns:
            Jumlah gambar yang berhasil dikirim
        """
        success_count = 0
        for i, path in enumerate(file_paths):
            if cls.send_image(phone, path, caption=f"Lampiran {i+1}"):
                success_count += 1
            time.sleep(delay)
        return success_count
    
    @classmethod
    def start_session(cls, webhook_url: str) -> bool:
        """
        Start WhatsApp session dan register webhook.
        
        Args:
            webhook_url: URL webhook untuk menerima pesan masuk
            
        Returns:
            True jika berhasil
        """
        try:
            url = f"{cls._get_base_url()}/api/{cls._get_session_name()}/start-session"
            r = requests.post(
                url,
                json={"webhook": webhook_url},
                headers=cls.get_headers(),
                timeout=30
            )
            return r.status_code in [200, 201]
        except Exception as e:
            log(f"⚠️ Gagal start session: {e}")
            return False
    
    @classmethod
    def should_reply_to_message(
        cls,
        is_group: bool,
        message_body: str,
        mentioned_list: List[str]
    ) -> bool:
        """
        Tentukan apakah bot harus membalas pesan.
        
        Rules:
        - Private chat: Selalu balas
        - Group: Hanya jika di-mention atau ada keyword @faq
        
        Args:
            is_group: Apakah pesan dari grup
            message_body: Isi pesan
            mentioned_list: List of mentioned JIDs
            
        Returns:
            True jika harus membalas
        """
        if not is_group:
            # DM: Selalu balas
            return True
        
        # Group: Cek @faq keyword
        if "@faq" in message_body.lower():
            return True
        
        # Group: Cek mention bot
        my_identities = settings.bot_identity_list
        
        if mentioned_list:
            for mentioned_id in mentioned_list:
                for my_id in my_identities:
                    if str(my_id) in str(mentioned_id):
                        log(f"🔔 Bot di-tag di Grup (via ID: {my_id})!")
                        return True
        
        return False
    
    @classmethod
    def clean_query(cls, message_body: str) -> str:
        """
        Bersihkan query dari mention dan keyword.
        
        Args:
            message_body: Pesan original
            
        Returns:
            Query yang sudah dibersihkan
        """
        import re
        
        clean = message_body.replace("@faq", "")
        
        # Hapus mention bot identities
        for identity in settings.bot_identity_list:
            clean = clean.replace(f"@{identity}", "")
        
        # Hapus mention format @628xxx
        clean = re.sub(r'@\d+', '', clean)
        
        return clean.strip()


# Singleton instance
whatsapp_service = WhatsAppService()
