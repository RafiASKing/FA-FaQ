"""
Logger - Centralized logging utilities.

Uses Python's logging module with:
- Console output (StreamHandler) for stdout
- Rotating file output (RotatingFileHandler) for persistent logs
- CSV writers for structured analytics (search_log, failed_searches)
"""

import csv
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config.settings import paths


# === Setup Python logging ===
LOG_DIR = paths.DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("fafaq")
_logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers on re-import
if not _logger.handlers:
    # Console handler (stdout)
    _console = logging.StreamHandler()
    _console.setLevel(logging.INFO)
    _console.setFormatter(logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _logger.addHandler(_console)

    # Rotating file handler (5 MB per file, keep 3 backups)
    _file = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    _file.setLevel(logging.DEBUG)
    _file.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _logger.addHandler(_file)


# === Log file paths (analytics CSVs) ===
SEARCH_LOG_FILE = paths.DATA_DIR / "search_log.csv"
SEARCH_LOG_HEADERS = [
    "timestamp", "query", "score", "faq_id", "faq_title",
    "mode", "response_ms", "source"
]


def log(message: str, flush: bool = True):
    """
    Application logging function.
    Outputs to both console and rotating log file.

    Args:
        message: Pesan yang akan di-log
        flush: Unused, kept for backward compatibility
    """
    _logger.info(message)


def log_search(
    query: str,
    score: float,
    faq_id: str = "",
    faq_title: str = "",
    mode: str = "immediate",
    response_ms: int = 0,
    source: str = "whatsapp",
) -> bool:
    """
    Log every search query with full context for analytics.

    Args:
        query: User's search query
        score: Relevance score (0-100), 0 if no match
        faq_id: ID of the retrieved FAQ document
        faq_title: Title of the retrieved FAQ
        mode: "immediate" or "agent"
        response_ms: Response time in milliseconds
        source: "whatsapp", "web", "api", "streamlit"
    """
    log_file = SEARCH_LOG_FILE
    file_exists = log_file.exists()

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(SEARCH_LOG_HEADERS)

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                query,
                f"{score:.1f}",
                faq_id,
                faq_title,
                mode,
                response_ms,
                source,
            ])
        return True
    except Exception as e:
        _logger.error(f"Gagal mencatat search log: {e}")
        return False


def get_search_log_path() -> Path:
    """Get the search log file path."""
    return SEARCH_LOG_FILE


def clear_search_log() -> bool:
    """Clear the search log file."""
    try:
        if SEARCH_LOG_FILE.exists():
            os.remove(SEARCH_LOG_FILE)
        return True
    except Exception as e:
        _logger.error(f"Gagal menghapus search log: {e}")
        return False


FAILED_SEARCH_HEADERS = [
    "timestamp", "query", "reason", "mode", "top_score",
    "top_faq_id", "top_faq_title", "response_ms", "source", "detail"
]


def log_failed_search(
    query: str,
    reason: str = "no_results",
    mode: str = "immediate",
    top_score: float = 0,
    top_faq_id: str = "",
    top_faq_title: str = "",
    response_ms: int = 0,
    source: str = "whatsapp",
    detail: str = "",
    log_file: Path = None,
) -> bool:
    """
    Log failed search with full diagnostic context.

    Args:
        query: User's search query
        reason: Why it failed — "no_results", "below_threshold", "low_confidence", "no_relevant"
        mode: Search mode used (immediate/agent/agent_pro)
        top_score: Score of the top candidate (if any)
        top_faq_id: ID of the top candidate
        top_faq_title: Title of the top candidate
        response_ms: Response time in milliseconds
        source: Origin (whatsapp/web/api)
        detail: Extra info (e.g. agent reasoning snippet)
    """
    if log_file is None:
        log_file = paths.FAILED_SEARCH_LOG

    log_file = Path(log_file)
    file_exists = log_file.exists()

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(FAILED_SEARCH_HEADERS)

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                query,
                reason,
                mode,
                f"{top_score:.1f}" if top_score else "0",
                top_faq_id,
                top_faq_title,
                response_ms,
                source,
                detail[:200] if detail else "",
            ])
        return True
    except Exception as e:
        _logger.error(f"Gagal mencatat log: {e}")
        return False


def clear_failed_search_log(log_file: Path = None) -> bool:
    """
    Hapus file log pencarian gagal.

    Args:
        log_file: Path ke file log (optional)

    Returns:
        True jika berhasil menghapus
    """
    if log_file is None:
        log_file = paths.FAILED_SEARCH_LOG

    try:
        if os.path.exists(log_file):
            os.remove(log_file)
        return True
    except Exception as e:
        _logger.error(f"Gagal menghapus log: {e}")
        return False


class LoggerMixin:
    """
    Mixin class untuk menambahkan logging ke class lain.
    """

    def _log(self, message: str, level: str = "INFO"):
        """Log dengan prefix class name."""
        class_name = self.__class__.__name__
        msg = f"{class_name}: {message}"
        if level == "WARN":
            _logger.warning(msg)
        elif level == "ERROR":
            _logger.error(msg)
        else:
            _logger.info(msg)

    def _log_info(self, message: str):
        self._log(message, "INFO")

    def _log_warning(self, message: str):
        self._log(message, "WARN")

    def _log_error(self, message: str):
        self._log(message, "ERROR")
