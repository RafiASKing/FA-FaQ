"""
Bot Configuration Service - Manages global bot settings.

Settings stored in data/bot_config.json for easy admin management.
"""

import json
from pathlib import Path
from typing import Any, Dict, Literal


class BotConfig:
    """
    Service for managing global bot configuration.
    
    Storage: data/bot_config.json
    """
    
    CONFIG_PATH = Path(__file__).parent.parent / "data" / "bot_config.json"
    
    # Default config
    DEFAULTS = {
        "search_mode": "immediate",
        "agent_confidence_threshold": 0.3,
    }
    
    @classmethod
    def _load(cls) -> Dict[str, Any]:
        """Load config from JSON file."""
        if not cls.CONFIG_PATH.exists():
            return cls.DEFAULTS.copy()
        
        try:
            with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                return {**cls.DEFAULTS, **config}
        except (json.JSONDecodeError, IOError):
            return cls.DEFAULTS.copy()
    
    @classmethod
    def _save(cls, config: Dict[str, Any]) -> None:
        """Save config to JSON file."""
        cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_search_mode(cls) -> Literal["immediate", "agent"]:
        """
        Get current search mode.
        
        Returns:
            "immediate" - Direct top-1 retrieval with 41% threshold
            "agent" - LLM-powered grading of top 20 candidates
        """
        config = cls._load()
        mode = config.get("search_mode", "immediate")
        return mode if mode in ("immediate", "agent") else "immediate"
    
    @classmethod
    def set_search_mode(cls, mode: Literal["immediate", "agent"]) -> None:
        """Set search mode."""
        if mode not in ("immediate", "agent"):
            raise ValueError(f"Invalid mode: {mode}")
        
        config = cls._load()
        config["search_mode"] = mode
        cls._save(config)
    
    @classmethod
    def get_confidence_threshold(cls) -> float:
        """Get agent confidence threshold."""
        config = cls._load()
        return float(config.get("agent_confidence_threshold", 0.3))
    
    @classmethod
    def set_confidence_threshold(cls, threshold: float) -> None:
        """Set agent confidence threshold."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be 0-1, got: {threshold}")
        
        config = cls._load()
        config["agent_confidence_threshold"] = threshold
        cls._save(config)
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all config values."""
        return cls._load()
