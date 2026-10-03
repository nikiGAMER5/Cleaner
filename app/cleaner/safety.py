"""Security and Safety Engine for validating file deletion requests."""

import os
from pathlib import Path
from typing import List, Optional, Set, Tuple

from app.config.constants import (
    CRITICAL_SYSTEM_DIRS,
    PROTECTED_FILENAMES,
    PROTECTED_SYSTEM_FILES,
    PROTECTED_USER_FOLDERS,
)
from app.utils.paths import (
    get_user_profile_dir,
    is_safe_subpath,
    is_symlink_or_junction,
)
from app.utils.permissions import is_file_in_use, can_delete_file


class SafetyValidator:
    """Strict security validator ensuring no critical or personal files are deleted."""

    def __init__(self, allowed_roots: Optional[List[Path]] = None):
        self.allowed_roots: List[Path] = allowed_roots or []
        self._user_profile = get_user_profile_dir()

    def add_allowed_root(self, root: Path) -> None:
        """Register an authorized root directory where deletions may occur."""
        resolved = Path(os.path.realpath(str(root))).resolve()
        if resolved not in self.allowed_roots:
            self.allowed_roots.append(resolved)

    def is_protected_system_path(self, path: Path) -> bool:
        """Verify if a path targets or is inside a protected Windows directory."""
        path_str_lower = str(path).lower()

        # Check critical system dirs
        for sys_dir in CRITICAL_SYSTEM_DIRS:
            sys_dir_lower = sys_dir.lower()
            if path_str_lower == sys_dir_lower or path_str_lower.startswith(sys_dir_lower + "\\"):
                # Exception: Only Windows\Temp sub-items are permissible if Temp itself is an allowed root,
                # but C:\Windows or C:\Windows\System32 are never allowed!
                win_temp = os.environ.get("WINDIR", r"C:\Windows") + r"\Temp"
                win_temp_lower = win_temp.lower()
                if path_str_lower.startswith(win_temp_lower) and path_str_lower != win_temp_lower:
                    continue  # Inside Temp is acceptable
                return True

        # Check protected filenames
        filename_lower = path.name.lower()
        if filename_lower in {f.lower() for f in PROTECTED_SYSTEM_FILES}:
            return True

        return False

    def is_protected_user_path(self, path: Path) -> bool:
        """Verify if path is located in personal user folders (Documents, Desktop, etc.)."""
        if not self._user_profile:
            return False

        user_prof_lower = str(self._user_profile).lower()
        path_lower = str(path).lower()

        for folder in PROTECTED_USER_FOLDERS:
            protected_dir = f"{user_prof_lower}\\{folder.lower()}"
            if path_lower == protected_dir or path_lower.startswith(protected_dir + "\\"):
                return True

        return False

    def is_sensitive_credential_file(self, path: Path) -> bool:
        """Verify if file contains browser logins, keys, or authentication tokens."""
        filename_lower = path.name.lower()
        for protected in PROTECTED_FILENAMES:
            if filename_lower == protected.lower() or filename_lower.startswith(protected.lower()):
                return True

        # Sensitive credential extensions
        sensitive_exts = {".key", ".pem", ".pfx", ".p12", ".kdbx"}
        if path.suffix.lower() in sensitive_exts:
            return True

        return False

    def validate_delete(
        self,
        candidate_path: Path,
        scan_set_paths: Optional[Set[Path]] = None,
    ) -> Tuple[bool, str]:
        """
        Executes strict multi-layer verification before any delete operation.
        Returns (is_safe, reason_if_not_safe).
        """
        try:
            # 1. Existence check
            if not candidate_path.exists():
                return False, "File does not exist"

            # 2. Canonical resolution (resolves symlinks and traversal elements)
            try:
                resolved = Path(os.path.realpath(str(candidate_path))).resolve()
            except Exception as e:
                return False, f"Failed to resolve path: {e}"

            # 3. Prevent root directory deletions (e.g. C:\ or C:\Windows or C:\Temp itself)
            if resolved == resolved.parent:
                return False, "Cannot delete drive root"

            for root in self.allowed_roots:
                if resolved == root:
                    return False, "Cannot delete category root directory itself"

            # 4. Critical system check
            if self.is_protected_system_path(resolved):
                return False, "Protected Windows system path"

            # 5. Protected user personal directory check
            if self.is_protected_user_path(resolved):
                return False, "Protected user personal folder"

            # 6. Sensitive credentials / session check
            if self.is_sensitive_credential_file(resolved):
                return False, "Protected credential or session file"

            # 7. Allowed target directory containment
            is_contained = False
            for allowed_root in self.allowed_roots:
                if is_safe_subpath(candidate_path, allowed_root) and is_safe_subpath(resolved, allowed_root):
                    is_contained = True
                    break

            if not is_contained:
                return False, "Path is not inside an authorized whitelist directory"

            # 8. Check for symlink / junction breakout
            if is_symlink_or_junction(candidate_path):
                # We do not delete junctions or symlinks pointing outside
                return False, "Skipped symbolic link or directory junction"

            # 9. Verify membership in current scan result (if set is provided)
            if scan_set_paths is not None:
                if resolved not in scan_set_paths and candidate_path not in scan_set_paths:
                    return False, "File is not part of the active scan result"

            # 10. Check if file is currently open / locked
            if resolved.is_file() and is_file_in_use(resolved):
                return False, "File currently in use"

            # 11. Check delete permissions
            can_del, perm_reason = can_delete_file(resolved)
            if not can_del:
                return False, perm_reason

            return True, "Safe to delete"

        except Exception as err:
            return False, f"Safety validation exception: {str(err)}"
