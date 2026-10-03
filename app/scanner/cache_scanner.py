"""Scanner for system caches, browser caches, thumbnails, application caches, and logs."""

import glob
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from app.config.constants import (
    CAT_APP_CACHE,
    CAT_BROWSER_CACHE,
    CAT_CACHE,
    CAT_LOGS,
    CAT_THUMBNAILS,
)
from app.models.file_item import FileItem
from app.utils.logging import get_logger
from app.utils.paths import (
    get_appdata_dir,
    get_local_appdata_dir,
    get_programdata_dir,
    is_symlink_or_junction,
)
from app.utils.permissions import is_file_in_use


class CacheScanner:
    """Scans well-defined safe cache and log directories."""

    def __init__(self):
        self.logger = get_logger()

    def scan(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> List[FileItem]:
        """Runs scan across all cache categories."""
        items: List[FileItem] = []

        # 1. Thumbnails
        self._scan_thumbnails(items, progress_callback, cancel_requested)

        # 2. System and Crash Dumps Cache
        self._scan_system_cache(items, progress_callback, cancel_requested)

        # 3. Browser Cache
        self._scan_browser_cache(items, progress_callback, cancel_requested)

        # 4. Application Cache
        self._scan_app_cache(items, progress_callback, cancel_requested)

        # 5. Windows Error Reporting / Safe Logs
        self._scan_logs(items, progress_callback, cancel_requested)

        return items

    def _scan_thumbnails(
        self,
        items: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Scan Windows Explorer thumbnail and icon cache."""
        local = get_local_appdata_dir()
        if not local:
            return

        explorer_dir = local / "Microsoft" / "Windows" / "Explorer"
        if explorer_dir.exists() and explorer_dir.is_dir():
            try:
                for entry in os.scandir(explorer_dir):
                    if cancel_requested and cancel_requested():
                        return
                    name = entry.name.lower()
                    if (name.startswith("thumbcache_") or name.startswith("iconcache_")) and name.endswith(".db"):
                        p = Path(entry.path)
                        try:
                            st = entry.stat(follow_symlinks=False)
                            in_use = is_file_in_use(p)
                            items.append(
                                FileItem(
                                    path=p,
                                    size=st.st_size,
                                    category=CAT_THUMBNAILS,
                                    modified_time=st.st_mtime,
                                    reason="Windows Thumbnail/Icon Cache",
                                    is_selected=False,  # default unchecked for thumbnails
                                    is_locked=in_use,
                                )
                            )
                            if progress_callback:
                                progress_callback(str(p), len(items))
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                pass

    def _scan_system_cache(
        self,
        items: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Scan safe Windows crash dumps and DirectX shader caches."""
        local = get_local_appdata_dir()
        if not local:
            return

        target_dirs = [
            (local / "CrashDumps", "Windows Crash Dump"),
            (local / "D3DSCache", "DirectX Shader Cache"),
        ]

        for target_dir, desc in target_dirs:
            if target_dir.exists() and target_dir.is_dir():
                self._collect_files_in_dir(
                    target_dir,
                    CAT_CACHE,
                    desc,
                    items,
                    progress_callback,
                    cancel_requested,
                    default_selected=True,
                )

    def _scan_browser_cache(
        self,
        items: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Scan safe browser cache subfolders only (no cookies, passwords or logins!)."""
        local = get_local_appdata_dir()
        if not local:
            return

        browser_targets: List[Tuple[Path, str]] = [
            # Chrome
            (local / "Google" / "Chrome" / "User Data" / "Default" / "Cache", "Chrome Web Cache"),
            (local / "Google" / "Chrome" / "User Data" / "Default" / "Code Cache", "Chrome Code Cache"),
            (local / "Google" / "Chrome" / "User Data" / "Default" / "GPUCache", "Chrome GPU Cache"),
            # Edge
            (local / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache", "Edge Web Cache"),
            (local / "Microsoft" / "Edge" / "User Data" / "Default" / "Code Cache", "Edge Code Cache"),
            (local / "Microsoft" / "Edge" / "User Data" / "Default" / "GPUCache", "Edge GPU Cache"),
            # Brave
            (local / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Cache", "Brave Web Cache"),
            # Opera
            (local / "Opera Software" / "Opera Stable" / "Cache", "Opera Web Cache"),
        ]

        for target_dir, desc in browser_targets:
            if target_dir.exists() and target_dir.is_dir():
                self._collect_files_in_dir(
                    target_dir,
                    CAT_BROWSER_CACHE,
                    desc,
                    items,
                    progress_callback,
                    cancel_requested,
                    default_selected=False,  # Unchecked by default
                )

        # Firefox cache2
        ff_profiles = local / "Mozilla" / "Firefox" / "Profiles"
        if ff_profiles.exists():
            try:
                for prof in ff_profiles.iterdir():
                    if cancel_requested and cancel_requested():
                        return
                    cache2 = prof / "cache2"
                    if cache2.exists() and cache2.is_dir():
                        self._collect_files_in_dir(
                            cache2,
                            CAT_BROWSER_CACHE,
                            "Firefox Web Cache",
                            items,
                            progress_callback,
                            cancel_requested,
                            default_selected=False,
                        )
            except (OSError, PermissionError):
                pass

    def _scan_app_cache(
        self,
        items: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Scan safe application caches like Discord, Spotify, Steam."""
        appdata = get_appdata_dir()
        local = get_local_appdata_dir()

        targets: List[Tuple[Path, str]] = []
        if appdata:
            targets.extend([
                (appdata / "discord" / "Cache", "Discord Cache"),
                (appdata / "discord" / "Code Cache", "Discord Code Cache"),
                (appdata / "discord" / "GPUCache", "Discord GPU Cache"),
            ])
        if local:
            targets.extend([
                (local / "Spotify" / "Data", "Spotify Cache"),
                (local / "Spotify" / "Storage", "Spotify Cache"),
                (local / "Steam" / "htmlcache", "Steam Web Cache"),
            ])

        for target_dir, desc in targets:
            if target_dir.exists() and target_dir.is_dir():
                self._collect_files_in_dir(
                    target_dir,
                    CAT_APP_CACHE,
                    desc,
                    items,
                    progress_callback,
                    cancel_requested,
                    default_selected=False,
                )

    def _scan_logs(
        self,
        items: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Scan Windows Error Reporting and application log archives."""
        progdata = get_programdata_dir()
        if not progdata:
            return

        wer_targets = [
            progdata / "Microsoft" / "Windows" / "WER" / "ReportArchive",
            progdata / "Microsoft" / "Windows" / "WER" / "ReportQueue",
        ]

        for wer_dir in wer_targets:
            if wer_dir.exists() and wer_dir.is_dir():
                self._collect_files_in_dir(
                    wer_dir,
                    CAT_LOGS,
                    "Windows Error Report",
                    items,
                    progress_callback,
                    cancel_requested,
                    default_selected=True,
                )

    def _collect_files_in_dir(
        self,
        dir_path: Path,
        category: str,
        reason: str,
        items: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
        default_selected: bool,
    ) -> None:
        """Recursively collect files within an authorized directory."""
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    if cancel_requested and cancel_requested():
                        return

                    p = Path(entry.path)
                    if entry.is_symlink() or is_symlink_or_junction(p):
                        continue

                    try:
                        if entry.is_file(follow_symlinks=False):
                            st = entry.stat(follow_symlinks=False)
                            in_use = is_file_in_use(p)
                            items.append(
                                FileItem(
                                    path=p,
                                    size=st.st_size,
                                    category=category,
                                    modified_time=st.st_mtime,
                                    reason=reason,
                                    is_selected=default_selected and not in_use,
                                    is_locked=in_use,
                                )
                            )
                            if progress_callback:
                                progress_callback(str(p), len(items))
                        elif entry.is_dir(follow_symlinks=False):
                            self._collect_files_in_dir(
                                p,
                                category,
                                reason,
                                items,
                                progress_callback,
                                cancel_requested,
                                default_selected,
                            )
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
