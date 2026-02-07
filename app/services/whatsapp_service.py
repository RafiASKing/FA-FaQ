"""
WhatsApp Service - Bot logic + messaging facade.

BotLogicService: Provider-agnostic bot decision logic (should_reply, clean_query).
WhatsAppService: Thin facade that delegates messaging to the active MessagingPort adapter.
"""

import re
from typing import Optional, List, Dict, Any

from config import container
from config.settings import settings
from core.logger import log


class BotLogicService:
    """
    Bot decision logic - provider-agnostic.
    Handles:
    - Whether the bot should reply to a message
    - Cleaning user queries from mentions and keywords
    """

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
                        log(f"Bot di-tag di Grup (via ID: {my_id})!")
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
        clean = message_body.replace("@faq", "")

        # Hapus mention bot identities
        for identity in settings.bot_identity_list:
            clean = clean.replace(f"@{identity}", "")

        # Hapus mention format @628xxx
        clean = re.sub(r'@\d+', '', clean)

        return clean.strip()


class WhatsAppService:
    """
    Backward-compatible facade for messaging operations.
    Delegates to the active MessagingPort adapter via container,
    and to BotLogicService for bot decision logic.

    This facade exists so that webhook_controller.py and other consumers
    don't need any import changes.
    """

    # === Messaging delegation (via port) ===

    @classmethod
    def generate_token(cls) -> bool:
        """Initialize messaging adapter (generate token, etc)."""
        return container.get_messaging().initialize()

    @classmethod
    def start_session(cls, webhook_url: str) -> bool:
        """Start messaging session with webhook URL."""
        return container.get_messaging().initialize(webhook_url=webhook_url)

    @classmethod
    def send_text(cls, phone: str, message: str) -> bool:
        """Kirim pesan teks."""
        return container.get_messaging().send_text(phone, message)

    @classmethod
    def send_image(cls, phone: str, file_path: str, caption: str = "") -> bool:
        """Kirim gambar."""
        return container.get_messaging().send_image(phone, file_path, caption)

    @classmethod
    def send_images(cls, phone: str, file_paths: List[str], delay: float = 0.5) -> int:
        """Kirim multiple gambar."""
        return container.get_messaging().send_images(phone, file_paths, delay)

    # === Bot logic delegation ===

    @classmethod
    def should_reply_to_message(
        cls,
        is_group: bool,
        message_body: str,
        mentioned_list: List[str]
    ) -> bool:
        """Delegate to BotLogicService."""
        return BotLogicService.should_reply_to_message(is_group, message_body, mentioned_list)

    @classmethod
    def clean_query(cls, message_body: str) -> str:
        """Delegate to BotLogicService."""
        return BotLogicService.clean_query(message_body)


# Singleton instances
bot_logic_service = BotLogicService()
whatsapp_service = WhatsAppService()
