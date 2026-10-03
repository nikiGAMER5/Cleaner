"""Scanner for finding large files on the system."""

import os
from pathlib import Path
from typing import Callable, List, Optional

from app.config.constants import CAT_LARGE_FILES, CRITICAL_SYSTEM_DIRS
from app.models.file_item import FileItem
from app.utils.logging import get_logger
from app.utils.paths import get_user_profile_dir, is_symlink_or_junction
from app.utils.permissions import is_file_in_use


class LargeFileScanner:
    """Scans user directories or entire drives for files above a size threshold."""

    def __init__(self, min_size_bytes: int = 100 * 1024 * 1024):
        self.min_size_bytes = min_size_bytes
        self.logger = get_logger()

    def scan(
        self,
        target_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> List[FileItem]:
        """Scan target directory (default: User Profile) for large files."""
        if target_dir is None:
            target_dir = get_user_profile_dir()

        if not target_dir or not target_dir.exists():
            return []

        results: List[FileItem] = []
        self._scan_dir(target_dir, results, progress_callback, cancel_requested)

        # Sort largest first
        results.sort(key=lambda item: item.size, reverse=True)
        return results

    def _scan_dir(
        self,
        current_dir: Path,
        results: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Scan directory recursively for large files while skipping system directories."""
        if cancel_requested and cancel_requested():
            return

        # Skip critical system directories
        dir_str_lower = str(current_dir).lower()
        for sys_dir in CRITICAL_SYSTEM_DIRS:
            if dir_str_lower.startswith(sys_dir.lower()):
                return

        # Skip AppData subfolder when scanning user profile
        if current_dir.name.lower() == "appdata":
            return

        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    if cancel_requested and cancel_requested():
                        return

                    p = Path(entry.path)
                    if entry.is_symlink() or is_symlink_or_junction(p):
                        continue

                    try:
                        if entry.is_file(follow_symlinks=False):
                            st = entry.stat(follow_symlinks=False)
                            if st.st_size >= self.min_size_bytes:
                                in_use = is_file_in_use(p)
                                results.append(
                                    FileItem(
                                        path=p,
                                        size=st.st_size,
                                        category=CAT_LARGE_FILES,
                                        modified_time=st.st_mtime,
                                        reason="Large File",
                                        is_selected=False,  # MUST NEVER be auto-selected
                                        is_locked=in_use,
                                    )
                                )
                                if progress_callback:
                                    progress_callback(str(p), len(results))

                        elif entry.is_dir(follow_symlinks=False):
                            self._scan_dir(p, results, progress_callback, cancel_requested)

                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
