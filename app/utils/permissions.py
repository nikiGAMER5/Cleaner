"""Permission and in-use file detection utilities."""

import os
from pathlib import Path
from typing import Tuple


def is_file_in_use(path: Path) -> bool:
    """
    Check if a file is currently open and locked by another process on Windows.
    Tries non-destructive access check.
    """
    if not path.is_file():
        return False

    try:
        # On Windows, opening with 'r+b' fails with WinError 32 if another process has exclusive lock
        with open(path, "r+b"):
            pass
        return False
    except (PermissionError, OSError) as e:
        # Error 32: ERROR_SHARING_VIOLATION, Error 33: ERROR_LOCK_VIOLATION
        winerror = getattr(e, "winerror", None)
        if winerror in (32, 33):
            return True
        # If access is denied (error 5), it might be protected or in use
        if winerror == 5:
            return True
        return True


def can_delete_file(path: Path) -> Tuple[bool, str]:
    """
    Evaluate if a file can be safely deleted without raising unhandled errors.
    Returns (can_delete, reason).
    """
    if not path.exists():
        return False, "File does not exist"

    if path.is_dir():
        # Directory check
        if not os.access(path, os.W_OK | os.X_OK):
            return False, "Directory access denied"
        return True, "OK"

    # File checks
    if is_file_in_use(path):
        return False, "File currently in use"

    if not os.access(path, os.W_OK):
        # On Windows, read-only files can have their readonly attribute cleared if safe,
        # but let's check basic permission
        try:
            # Check if read-only attribute is set
            import stat
            mode = path.stat().st_mode
            if not (mode & stat.S_IWRITE):
                # We can remove read-only attribute if needed, but report permission status
                return True, "Read-only attribute present (clearing allowed)"
        except Exception:
            return False, "Access denied / insufficient permissions"

    return True, "OK"
