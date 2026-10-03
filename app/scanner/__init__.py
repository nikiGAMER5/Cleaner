"""Scanner modules for PC Cleaner."""

from app.scanner.scanner import SystemScanner
from app.scanner.temp_scanner import TempScanner
from app.scanner.cache_scanner import CacheScanner
from app.scanner.large_file_scanner import LargeFileScanner
from app.scanner.storage_scanner import StorageScanner, DiskStorageInfo
from app.scanner.app_scanner import AppScanner, InstalledApp
from app.scanner.duplicate_scanner import DuplicateScanner

__all__ = [
    "SystemScanner",
    "TempScanner",
    "CacheScanner",
    "LargeFileScanner",
    "StorageScanner",
    "DiskStorageInfo",
    "AppScanner",
    "InstalledApp",
    "DuplicateScanner",
]
