"""Scanner for temporary files in Windows user and system temp folders."""

import os
from pathlib import Path
from typing import Callable, List, Optional

from app.config.constants import CAT_TEMP
from app.models.file_item import FileItem
from app.utils.logging import get_logger
from app.utils.paths import get_system_temp_dir, get_user_temp_dir, is_symlink_or_junction
from app.utils.permissions import is_file_in_use


class TempScanner:
    """Scans Windows temporary directories safely."""

    def __init__(self):
        self.logger = get_logger()

    def scan(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> List[FileItem]:
        """Scan %TEMP% and %WINDIR%\\Temp for temporary files."""
        items: List[FileItem] = []
        dirs_to_scan = []

        user_temp = get_user_temp_dir()
        if user_temp and user_temp.is_dir():
            dirs_to_scan.append(user_temp)

        sys_temp = get_system_temp_dir()
        if sys_temp and sys_temp.is_dir():
            dirs_to_scan.append(sys_temp)

        for temp_dir in dirs_to_scan:
            if cancel_requested and cancel_requested():
                break

            self._scan_directory(temp_dir, items, progress_callback, cancel_requested)

        return items

    def _scan_directory(
        self,
        base_dir: Path,
        results: List[FileItem],
        progress_callback: Optional[Callable[[str, int], None]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Walk directory using os.scandir safely without following symlinks."""
        try:
            with os.scandir(base_dir) as it:
                for entry in it:
                    if cancel_requested and cancel_requested():
                        return

                    try:
                        p = Path(entry.path)
                        # Skip symlinks/junctions
                        if entry.is_symlink() or is_symlink_or_junction(p):
                            continue

                        if entry.is_file(follow_symlinks=False):
                            stat_res = entry.stat(follow_symlinks=False)
                            size = stat_res.st_size
                            mtime = stat_res.st_mtime
                            in_use = is_file_in_use(p)

                            item = FileItem(
                                path=p,
                                size=size,
                                category=CAT_TEMP,
                                modified_time=mtime,
                                reason="Temporary file",
                                is_selected=not in_use,
                                is_locked=in_use,
                            )
                            results.append(item)

                            if progress_callback:
                                progress_callback(str(p), len(results))

                        elif entry.is_dir(follow_symlinks=False):
                            # Recurse into subdirectories
                            self._scan_directory(p, results, progress_callback, cancel_requested)

                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
