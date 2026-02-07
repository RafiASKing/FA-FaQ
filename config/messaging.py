"""
WPPConnect Messaging Adapter - WPPConnect implementation of MessagingPort.
Following Siloam convention: config/messaging.py (external service connections in config/).
"""

import time
import requests
from typing import Optional, List

from app.ports.messaging_port import MessagingPort
from core.logger import log
from core.image_handler import ImageHandler


class WPPConnectMessagingAdapter(MessagingPort):
    """
    WhatsApp messaging adapter using WPPConnect server.

    Args:
        base_url: WPPConnect server base URL (e.g. "http://wppconnect:21465").
        session_name: Session identifier.
        secret_key: Authentication secret key.
    """

    def __init__(self, base_url: str, session_name: str, secret_key: str):
        self._base_url = base_url
        self._session_name = session_name
        self._secret_key = secret_key
        self._token: Optional[str] = None

    def _get_headers(self) -> dict:
        """Get HTTP headers with auth token. Auto-generates token if missing."""
        if not self._token:
            self._generate_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _generate_token(self) -> bool:
        """Generate authentication token from WPPConnect."""
        try:
            url = f"{self._base_url}/api/{self._session_name}/{self._secret_key}/generate-token"
            r = requests.post(url, timeout=10)

            if r.status_code in [200, 201]:
                resp = r.json()
                token = resp.get("token") or resp.get("session")

                if not token and "full" in resp:
                    token = resp["full"].split(":")[-1]

                if token:
                    self._token = token
                    log("Berhasil Generate Token.")
                    return True
                else:
                    log("Gagal Parse Token.")
            else:
                log(f"Gagal Generate Token: {r.status_code}")
        except Exception as e:
            log(f"Error Auth: {e}")

        return False

    def initialize(self, webhook_url: Optional[str] = None) -> bool:
        """Initialize WPPConnect session: generate token and optionally start session with webhook."""
        success = self._generate_token()

        if success and webhook_url:
            try:
                url = f"{self._base_url}/api/{self._session_name}/start-session"
                r = requests.post(
                    url,
                    json={"webhook": webhook_url},
                    headers=self._get_headers(),
                    timeout=30,
                )
                return r.status_code in [200, 201]
            except Exception as e:
                log(f"Gagal start session: {e}")
                return False

        return success

    def send_text(self, recipient: str, message: str) -> bool:
        """Send text message via WPPConnect."""
        if not recipient or str(recipient) == "None":
            return False

        url = f"{self._base_url}/api/{self._session_name}/send-message"
        is_group = "@g.us" in str(recipient)

        payload = {
            "phone": recipient,
            "message": message,
            "isGroup": is_group,
            "linkPreview": False,
            "options": {"linkPreview": False, "createChat": True},
        }

        try:
            r = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            log(f"Balas ke {recipient}: {r.status_code}")

            if r.status_code == 401:
                self._generate_token()
                r = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)

            return r.status_code in [200, 201]
        except Exception as e:
            log(f"Error Kirim Text: {e}")
            return False

    def send_image(self, recipient: str, file_path: str, caption: str = "") -> bool:
        """Send image via WPPConnect (base64 encoded)."""
        if not recipient:
            return False

        base64_str, filename = ImageHandler.get_base64_image(file_path)
        if not base64_str:
            log(f"Gambar tidak ditemukan: {file_path}")
            return False

        url = f"{self._base_url}/api/{self._session_name}/send-image"
        is_group = "@g.us" in str(recipient)

        payload = {
            "phone": recipient,
            "base64": base64_str,
            "caption": caption,
            "isGroup": is_group,
        }

        try:
            r = requests.post(url, json=payload, headers=self._get_headers(), timeout=60)
            return r.status_code in [200, 201]
        except Exception as e:
            log(f"Error Kirim Image: {e}")
            return False

    def send_images(self, recipient: str, file_paths: List[str], delay: float = 0.5) -> int:
        """Send multiple images with delay between each."""
        count = 0
        for i, path in enumerate(file_paths):
            if self.send_image(recipient, path, caption=f"Lampiran {i + 1}"):
                count += 1
            time.sleep(delay)
        return count
