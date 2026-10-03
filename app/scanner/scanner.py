"""SystemScanner orchestrating temp, cache, log and recycle bin scanning."""

import time
from typing import Callable, List, Optional, Set

from app.cleaner.recycle_bin import RecycleBinManager
from app.config.constants import (
    CAT_CACHE,
    CAT_LOGS,
    CAT_RECYCLE_BIN,
    CAT_TEMP,
    CLEANABLE_CATEGORIES,
)
from app.models.file_item import FileItem
from app.models.scan_result import ScanResultSet
from app.scanner.cache_scanner import CacheScanner
from app.scanner.temp_scanner import TempScanner
from app.utils.logging import get_logger


class SystemScanner:
    """Coordinates category scanners and constructs the full scan result."""

    def __init__(self, enabled_categories: Optional[List[str]] = None):
        self.enabled_categories: Set[str] = set(enabled_categories or CLEANABLE_CATEGORIES)
        self.temp_scanner = TempScanner()
        self.cache_scanner = CacheScanner()
        self.logger = get_logger()

    def run_scan(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> ScanResultSet:
        """
        Executes scan across all configured categories.
        progress_callback signature: (current_path, files_scanned_count, total_bytes_accumulated)
        """
        self.logger.info("Starting system scan.")
        start_time = time.time()
        all_items: List[FileItem] = []
        total_bytes = 0

        def sub_progress(p_str: str, count: int):
            nonlocal total_bytes
            if progress_callback:
                progress_callback(p_str, len(all_items) + count, total_bytes)

        # 1. Temp files scan
        if CAT_TEMP in self.enabled_categories and not (cancel_requested and cancel_requested()):
            temp_items = self.temp_scanner.scan(
                progress_callback=sub_progress,
                cancel_requested=cancel_requested,
            )
            for item in temp_items:
                total_bytes += item.size
            all_items.extend(temp_items)

        # 2. Cache, Logs, Thumbnails scan
        if not (cancel_requested and cancel_requested()):
            cache_items = self.cache_scanner.scan(
                progress_callback=sub_progress,
                cancel_requested=cancel_requested,
            )
            # Filter according to enabled categories
            for item in cache_items:
                if item.category in self.enabled_categories:
                    total_bytes += item.size
                    all_items.append(item)

        # 3. Recycle Bin Query
        rb_size, rb_count = RecycleBinManager.get_recycle_bin_info()

        end_time = time.time()
        self.logger.info(
            f"Scan completed in {end_time - start_time:.2f}s. "
            f"Found {len(all_items)} files ({total_bytes} bytes). "
            f"Recycle bin: {rb_count} items ({rb_size} bytes)."
        )

        return ScanResultSet(
            items=all_items,
            start_time=start_time,
            end_time=end_time,
            recycle_bin_size=rb_size,
            recycle_bin_count=rb_count,
        )
