"""Storage and disk space analyzer."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional
import psutil

from app.utils.logging import get_logger
from app.utils.paths import is_symlink_or_junction


@dataclass
class FolderSizeInfo:
    name: str
    path: Path
    size_bytes: int
    is_dir: bool


@dataclass
class DiskStorageInfo:
    drive: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float
    folders: List[FolderSizeInfo]


class StorageScanner:
    """Analyzes disk partitions and directory sizes."""

    def __init__(self):
        self.logger = get_logger()

    @staticmethod
    def get_available_drives() -> List[str]:
        """List all valid mount points / drives on Windows (e.g. ['C:\\', 'D:\\'])."""
        drives = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                drives.append(part.mountpoint)
        except Exception:
            drives = ["C:\\"]
        return drives

    @staticmethod
    def get_drive_usage(drive: str):
        """Fetch total, used, free for given drive."""
        return psutil.disk_usage(drive)

    def analyze_drive(
        self,
        drive: str = "C:\\",
        progress_callback: Optional[Callable[[str], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> DiskStorageInfo:
        """Calculates disk usage and sizes of top-level folders on drive."""
        usage = self.get_drive_usage(drive)
        drive_path = Path(drive)
        folder_infos: List[FolderSizeInfo] = []

        total_analyzed = 0
        try:
            entries = list(os.scandir(drive_path))
        except (PermissionError, OSError):
            entries = []

        for entry in entries:
            if cancel_requested and cancel_requested():
                break

            p = Path(entry.path)
            # Skip hidden system volume info, pagefile, recycle bin
            name = entry.name
            if name.startswith("$") or name in ("System Volume Information", "Recovery"):
                continue

            if progress_callback:
                progress_callback(f"Analyzing {entry.name}...")

            if entry.is_dir(follow_symlinks=False):
                if is_symlink_or_junction(p):
                    continue
                size = self._calc_dir_size(p, depth_limit=3, cancel_requested=cancel_requested)
                folder_infos.append(
                    FolderSizeInfo(name=name, path=p, size_bytes=size, is_dir=True)
                )
                total_analyzed += size
            elif entry.is_file(follow_symlinks=False):
                try:
                    size = entry.stat(follow_symlinks=False).st_size
                    folder_infos.append(
                        FolderSizeInfo(name=name, path=p, size_bytes=size, is_dir=False)
                    )
                    total_analyzed += size
                except (OSError, PermissionError):
                    pass

        # Sort largest folders first
        folder_infos.sort(key=lambda f: f.size_bytes, reverse=True)

        # Calculate 'Other' (system metadata, inaccessible files, etc.)
        other_bytes = max(0, usage.used - total_analyzed)
        if other_bytes > 0:
            folder_infos.append(
                FolderSizeInfo(
                    name="Other / System Protected",
                    path=drive_path,
                    size_bytes=other_bytes,
                    is_dir=True,
                )
            )

        return DiskStorageInfo(
            drive=drive,
            mountpoint=drive,
            fstype="",
            total_bytes=usage.total,
            used_bytes=usage.used,
            free_bytes=usage.free,
            percent=usage.percent,
            folders=folder_infos,
        )

    def _calc_dir_size(
        self,
        directory: Path,
        depth_limit: int,
        cancel_requested: Optional[Callable[[], bool]],
        current_depth: int = 0,
    ) -> int:
        """Fast directory size aggregator with depth limit to prevent infinite hangs."""
        if current_depth > depth_limit or (cancel_requested and cancel_requested()):
            return 0

        total = 0
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    if cancel_requested and cancel_requested():
                        break
                    p = Path(entry.path)
                    if entry.is_symlink() or is_symlink_or_junction(p):
                        continue
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += self._calc_dir_size(
                                p, depth_limit, cancel_requested, current_depth + 1
                            )
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass

        return total
