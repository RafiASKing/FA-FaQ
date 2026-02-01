"""
Logger - Centralized logging utilities.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import paths


def log(message: str, flush: bool = True):
    """
    Simple logging function.
    Menggantikan print() biasa dengan format timestamp.
    
    Args:
        message: Pesan yang akan di-log
        flush: Force flush output
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=flush)


def log_failed_search(query: str, log_file: Path = None) -> bool:
    """
    Mencatat pencarian yang gagal (score < threshold) ke CSV.
    
    Args:
        query: Query yang dicari user
        log_file: Path ke file log (optional)
        
    Returns:
        True jika berhasil mencatat
    """
    if log_file is None:
        log_file = paths.FAILED_SEARCH_LOG
    
    log_file = Path(log_file)
    file_exists = log_file.exists()
    
    try:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header jika file baru
            if not file_exists:
                writer.writerow(["Timestamp", "Query User"])
            
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                query
            ])
        return True
    except Exception as e:
        print(f"⚠️ Gagal mencatat log: {e}")
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
        print(f"⚠️ Gagal menghapus log: {e}")
        return False


class LoggerMixin:
    """
    Mixin class untuk menambahkan logging ke class lain.
    """
    
    def _log(self, message: str, level: str = "INFO"):
        """Log dengan prefix class name."""
        class_name = self.__class__.__name__
        log(f"[{level}] {class_name}: {message}")
    
    def _log_info(self, message: str):
        self._log(message, "INFO")
    
    def _log_warning(self, message: str):
        self._log(message, "WARN")
    
    def _log_error(self, message: str):
        self._log(message, "ERROR")
