"""
Messaging Port - Abstract interface for sending messages via a messaging provider.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class MessagingPort(ABC):
    """
    Port for messaging provider integration (WhatsApp, Telegram, etc).

    Note: Bot decision logic (should_reply_to_message, clean_query) is NOT
    part of this port. That is business logic handled by BotLogicService.

    Implementations:
    - WPPConnectMessagingAdapter (WPPConnect)
    - Future: WAHA, Meta Cloud API (official), Baileys, etc.
    """

    @abstractmethod
    def initialize(self, webhook_url: Optional[str] = None) -> bool:
        """
        Initialize the messaging session.
        Handles authentication, token generation, session start, etc.

        Args:
            webhook_url: URL to receive incoming message webhooks.

        Returns:
            True if initialization succeeded.
        """
        ...

    @abstractmethod
    def send_text(self, recipient: str, message: str) -> bool:
        """
        Send a text message.

        Args:
            recipient: Phone number or group ID.
            message: Text content.

        Returns:
            True if sent successfully.
        """
        ...

    @abstractmethod
    def send_image(self, recipient: str, file_path: str, caption: str = "") -> bool:
        """
        Send a single image.

        Args:
            recipient: Phone number or group ID.
            file_path: Path to image file on disk.
            caption: Optional caption text.

        Returns:
            True if sent successfully.
        """
        ...

    @abstractmethod
    def send_images(self, recipient: str, file_paths: List[str], delay: float = 0.5) -> int:
        """
        Send multiple images sequentially.

        Args:
            recipient: Phone number or group ID.
            file_paths: List of image file paths.
            delay: Delay between sends in seconds.

        Returns:
            Number of images successfully sent.
        """
        ...
