"""FileItem and CleanResult data models."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FileItem:
    """Represents a single file or directory identified during scanning."""
    path: Path
    size: int
    category: str
    modified_time: float
    reason: str = ""
    is_selected: bool = True
    is_locked: bool = False
    file_hash: Optional[str] = None

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @property
    def path_str(self) -> str:
        return str(self.path)


@dataclass
class CleanResult:
    """Represents the outcome of a cleanup operation on a single file or folder."""
    path: Path
    category: str
    success: bool
    freed_bytes: int
    error_reason: Optional[str] = None
