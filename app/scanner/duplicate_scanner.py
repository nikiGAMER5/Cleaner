"""Duplicate file finder using size grouping and SHA-256 hashing."""

from collections import defaultdict
import hashlib
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

from app.models.file_item import FileItem
from app.utils.logging import get_logger
from app.utils.paths import get_user_profile_dir, is_symlink_or_junction
from app.utils.permissions import is_file_in_use


def compute_file_hash(path: Path, max_bytes: Optional[int] = None) -> str:
    """Computes SHA-256 hash of a file or its first max_bytes."""
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            if max_bytes:
                chunk = f.read(max_bytes)
                hasher.update(chunk)
            else:
                while chunk := f.read(65536):
                    hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


class DuplicateScanner:
    """Finds duplicate files based on content hash."""

    def __init__(self, min_size_bytes: int = 1024 * 1024):  # Default 1 MB minimum
        self.min_size_bytes = min_size_bytes
        self.logger = get_logger()

    def scan(
        self,
        target_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, List[FileItem]]:
        """
        Scans target directory and returns a dictionary of:
        { sha256_hash: [FileItem, FileItem, ...] }
        Only entries with 2 or more files are returned.
        """
        if target_dir is None:
            target_dir = get_user_profile_dir()

        if not target_dir or not target_dir.exists():
            return {}

        # 1. Collect candidate files grouped by size
        size_groups: Dict[int, List[Path]] = defaultdict(list)
        self._collect_by_size(target_dir, size_groups, cancel_requested)

        # 2. Filter sizes with at least 2 files
        candidates_by_size = {size: paths for size, paths in size_groups.items() if len(paths) >= 2}

        # 3. Hash verification
        duplicates_map: Dict[str, List[FileItem]] = defaultdict(list)
        processed = 0

        for size, paths in candidates_by_size.items():
            if cancel_requested and cancel_requested():
                break

            # Fast partial check (first 4KB)
            partial_groups: Dict[str, List[Path]] = defaultdict(list)
            for p in paths:
                if cancel_requested and cancel_requested():
                    break
                part_hash = compute_file_hash(p, max_bytes=4096)
                if part_hash:
                    partial_groups[part_hash].append(p)

            # Full hash check for candidates matching partial hash
            for p_hash, candidate_paths in partial_groups.items():
                if len(candidate_paths) >= 2:
                    for p in candidate_paths:
                        if cancel_requested and cancel_requested():
                            break
                        full_hash = compute_file_hash(p)
                        if full_hash:
                            try:
                                st = p.stat()
                                in_use = is_file_in_use(p)
                                item = FileItem(
                                    path=p,
                                    size=st.st_size,
                                    category="duplicates",
                                    modified_time=st.st_mtime,
                                    reason="Duplicate content",
                                    is_selected=False,  # NEVER auto-select duplicates!
                                    is_locked=in_use,
                                    file_hash=full_hash,
                                )
                                duplicates_map[full_hash].append(item)
                                processed += 1
                                if progress_callback:
                                    progress_callback(str(p), processed)
                            except (OSError, PermissionError):
                                continue

        # Keep only groups with actual duplicates
        return {h: items for h, items in duplicates_map.items() if len(items) >= 2}

    def _collect_by_size(
        self,
        directory: Path,
        size_groups: Dict[int, List[Path]],
        cancel_requested: Optional[Callable[[], bool]],
    ) -> None:
        """Collect all files above min_size_bytes grouped by file size."""
        if cancel_requested and cancel_requested():
            return

        try:
            with os.scandir(directory) as it:
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
                                size_groups[st.st_size].append(p)
                        elif entry.is_dir(follow_symlinks=False):
                            # Skip AppData and hidden directories
                            if not entry.name.startswith(".") and entry.name.lower() != "appdata":
                                self._collect_by_size(p, size_groups, cancel_requested)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
