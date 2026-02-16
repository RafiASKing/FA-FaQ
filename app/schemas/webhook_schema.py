"""
Webhook Schemas - Pydantic models untuk WhatsApp webhook.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SenderInfo(BaseModel):
    """Info pengirim pesan."""
    id: Optional[str] = None
    pushname: Optional[str] = None


class WhatsAppWebhookPayload(BaseModel):
    """Schema untuk WhatsApp webhook payload dari WPPConnect."""
    event: Optional[str] = None
    
    # Message data (bisa di root atau di nested 'data')
    data: Optional[Dict[str, Any]] = None
    
    # Direct fields (kadang WPPConnect tidak wrap dalam 'data')
    fromMe: Optional[bool] = Field(default=False, alias="fromMe")
    from_: Optional[str] = Field(default=None, alias="from")
    chatId: Optional[str] = None
    body: Optional[str] = None
    content: Optional[str] = None
    caption: Optional[str] = None
    sender: Optional[SenderInfo] = None
    isGroupMsg: Optional[bool] = False
    mentionedJidList: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
        extra = "allow"  # Allow extra fields
    
    def get_message_body(self) -> str:
        """Get message body dari berbagai possible fields."""
        if self.data:
            return (
                self.data.get("caption") or 
                self.data.get("body") or 
                self.data.get("content") or 
                ""
            )
        return self.caption or self.body or self.content or ""

    def has_image_payload(self) -> bool:
        """Check apakah payload mengandung media gambar."""
        source = self.data if self.data else self.__dict__

        msg_type = str(source.get("type") or "").lower()
        mime_type = str(
            source.get("mimetype") or
            source.get("mimeType") or
            ""
        ).lower()

        if msg_type == "image":
            return True

        if mime_type.startswith("image/"):
            return True

        body_text = str(
            source.get("body") or
            source.get("content") or
            self.body or
            self.content or
            ""
        ).strip()

        if body_text.lower().startswith("data:image/"):
            return True

        if body_text.startswith("/9j/") and len(body_text) >= 120:
            return True

        return False
    
    def get_remote_jid(self) -> Optional[str]:
        """Get remote JID (pengirim)."""
        if self.data:
            return (
                self.data.get("from") or 
                self.data.get("chatId") or
                self.data.get("sender", {}).get("id")
            )
        return self.from_ or self.chatId
    
    def get_sender_name(self) -> str:
        """Get nama pengirim."""
        if self.data:
            return self.data.get("sender", {}).get("pushname", "User")
        return self.sender.pushname if self.sender else "User"
    
    def is_group_message(self) -> bool:
        """Check apakah pesan dari grup."""
        remote_jid = self.get_remote_jid()
        
        if self.data:
            is_group = self.data.get("isGroupMsg", False)
        else:
            is_group = self.isGroupMsg or False
        
        return is_group or (remote_jid and "@g.us" in str(remote_jid))
    
    def get_mentioned_list(self) -> List[str]:
        """Get list of mentioned JIDs."""
        if self.data:
            return self.data.get("mentionedJidList", [])
        return self.mentionedJidList or []
    
    def get_group_name(self) -> str:
        """Get group name (if group message)."""
        if self.data:
            # Try various field names used by WPPConnect
            return (
                self.data.get("chat", {}).get("name") or
                self.data.get("groupName") or
                self.data.get("notifyName") or
                ""
            )
        return ""
    
    def is_from_me(self) -> bool:
        """Check apakah pesan dari bot sendiri."""
        if self.data:
            return self.data.get("fromMe", False) is True
        return self.fromMe is True
    
    def should_process(self) -> bool:
        """Check apakah pesan harus diproses."""
        # Ignore pesan dari diri sendiri
        if self.is_from_me():
            return False
        
        # Ignore status broadcast
        remote_jid = self.get_remote_jid()
        if not remote_jid or "status@broadcast" in str(remote_jid):
            return False
        
        # Check valid events
        valid_events = ["onMessage", "onAnyMessage", "onmessage"]
        if self.event and self.event not in valid_events:
            return False
        
        return True


class WebhookResponse(BaseModel):
    """Schema untuk webhook response."""
    status: str = Field(..., description="Status response (success, ignored, error)")
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Message processed"
            }
        }
