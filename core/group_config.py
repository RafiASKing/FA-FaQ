"""
Group Configuration Service - Manages per-group module whitelist.

Each WA group can be configured to only receive search results from specific modules.
Groups are auto-registered on first @faq mention with default "all" modules.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class GroupConfig:
    """
    Service for managing group module whitelist configuration.
    
    Storage: data/group_config.json
    """
    
    CONFIG_PATH = Path(__file__).parent.parent / "data" / "group_config.json"
    
    @classmethod
    def _load(cls) -> Dict[str, Any]:
        """Load config from JSON file."""
        if not cls.CONFIG_PATH.exists():
            return {"groups": {}}
        
        try:
            with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"groups": {}}
    
    @classmethod
    def _save(cls, config: Dict[str, Any]) -> None:
        """Save config to JSON file."""
        cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_config(cls, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific group.
        
        Returns:
            Dict with name, allowed_modules, first_seen or None if not found
        """
        config = cls._load()
        return config["groups"].get(group_id)
    
    @classmethod
    def get_allowed_modules(cls, group_id: str) -> List[str]:
        """
        Get allowed modules for a group.
        
        Returns:
            List of module names, or ["all"] if not configured
        """
        group = cls.get_config(group_id)
        if not group:
            return ["all"]
        return group.get("allowed_modules", ["all"])
    
    @classmethod
    def is_module_allowed(cls, group_id: str, module: str) -> bool:
        """
        Check if a specific module is allowed for a group.
        
        Args:
            group_id: WhatsApp group JID
            module: Module/tag name
            
        Returns:
            True if allowed, False otherwise
        """
        allowed = cls.get_allowed_modules(group_id)
        if "all" in allowed:
            return True
        return module in allowed
    
    @classmethod
    def register_group(cls, group_id: str, name: str) -> None:
        """
        Register a new group with default "all" modules.
        Called automatically on first @faq mention.
        
        Args:
            group_id: WhatsApp group JID
            name: Group display name
        """
        config = cls._load()
        
        if group_id not in config["groups"]:
            config["groups"][group_id] = {
                "name": name,
                "allowed_modules": ["all"],
                "first_seen": datetime.now().isoformat()
            }
            cls._save(config)
    
    @classmethod
    def set_allowed_modules(cls, group_id: str, modules: List[str]) -> bool:
        """
        Set allowed modules for a group.
        
        Args:
            group_id: WhatsApp group JID
            modules: List of allowed module names (or ["all"])
            
        Returns:
            True if successful, False if group not found
        """
        config = cls._load()
        
        if group_id not in config["groups"]:
            return False
        
        config["groups"][group_id]["allowed_modules"] = modules
        cls._save(config)
        return True
    
    @classmethod
    def update_group_name(cls, group_id: str, name: str) -> bool:
        """
        Update group display name.
        
        Args:
            group_id: WhatsApp group JID
            name: New display name
            
        Returns:
            True if successful, False if group not found
        """
        config = cls._load()
        
        if group_id not in config["groups"]:
            return False
        
        config["groups"][group_id]["name"] = name
        cls._save(config)
        return True
    
    @classmethod
    def get_all_groups(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered groups.
        
        Returns:
            Dict of group_id -> config
        """
        config = cls._load()
        return config.get("groups", {})
    
    @classmethod
    def delete_group(cls, group_id: str) -> bool:
        """
        Delete a group from config.
        
        Returns:
            True if deleted, False if not found
        """
        config = cls._load()
        
        if group_id not in config["groups"]:
            return False
        
        del config["groups"][group_id]
        cls._save(config)
        return True


# Convenience functions
def is_group_message(remote_jid: str) -> bool:
    """Check if JID is a group (ends with @g.us)."""
    return remote_jid.endswith("@g.us")


def is_dm_message(remote_jid: str) -> bool:
    """Check if JID is a direct message (ends with @s.whatsapp.net)."""
    return remote_jid.endswith("@s.whatsapp.net")
