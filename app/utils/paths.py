"""Windows path resolution, environment expansion, and containment checking."""

import os
from pathlib import Path
from typing import List, Optional, Set
import stat


def get_env_dir(env_var: str, default: Optional[str] = None) -> Optional[Path]:
    """Retrieve and resolve a directory from a Windows environment variable."""
    val = os.environ.get(env_var, default)
    if not val:
        return None
    try:
        p = Path(os.path.expandvars(val)).resolve()
        return p if p.exists() else None
    except Exception:
        return None


def get_user_temp_dir() -> Optional[Path]:
    """Get user %TEMP% directory."""
    return get_env_dir("TEMP") or get_env_dir("TMP")


def get_system_temp_dir() -> Optional[Path]:
    """Get Windows %WINDIR%\\Temp directory."""
    windir = get_env_dir("WINDIR", r"C:\Windows")
    if windir:
        p = windir / "Temp"
        return p if p.exists() else None
    return None


def get_local_appdata_dir() -> Optional[Path]:
    """Get %LOCALAPPDATA% directory."""
    return get_env_dir("LOCALAPPDATA")


def get_appdata_dir() -> Optional[Path]:
    """Get %APPDATA% (Roaming) directory."""
    return get_env_dir("APPDATA")


def get_programdata_dir() -> Optional[Path]:
    """Get %PROGRAMDATA% directory."""
    return get_env_dir("PROGRAMDATA", r"C:\ProgramData")


def get_user_profile_dir() -> Optional[Path]:
    """Get %USERPROFILE% directory."""
    return get_env_dir("USERPROFILE")


def is_symlink_or_junction(path: Path) -> bool:
    """Check if a path is a symbolic link or a Windows directory junction."""
    try:
        if path.is_symlink():
            return True
        # Check reparse point attribute on Windows
        st = path.lstat()
        if hasattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT"):
            if bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                return True
        return False
    except (OSError, ValueError):
        return True  # If unreadable, treat with caution


def is_safe_subpath(candidate: Path, base_dir: Path) -> bool:
    """
    Check strictly if candidate is inside base_dir without symlink breakout.
    Uses canonical realpath to prevent path traversal (../) and junction hopping.
    """
    try:
        real_base = Path(os.path.realpath(str(base_dir))).resolve()
        real_candidate = Path(os.path.realpath(str(candidate))).resolve()

        # real_candidate must start with real_base and not be identical to real_base
        try:
            rel = real_candidate.relative_to(real_base)
            # Must not be the base directory itself!
            if str(rel) == ".":
                return False
        except ValueError:
            return False

        # Verify that candidate does not traverse through an untrusted symlink or junction
        curr = candidate
        while curr != curr.parent:
            if is_symlink_or_junction(curr):
                # If any path component is a symlink/junction, ensure its target remains in real_base
                real_curr = Path(os.path.realpath(str(curr))).resolve()
                try:
                    real_curr.relative_to(real_base)
                except ValueError:
                    return False  # Symlink/junction points outside allowed base!
            if curr == base_dir:
                break
            curr = curr.parent

        return True
    except Exception:
        return False


def get_safe_whitelist_roots() -> List[Path]:
    """
    Returns explicitly allowed root paths where cleaners are permitted to operate.
    Every cleanable file MUST reside within one of these safe roots.
    """
    allowed: List[Path] = []
    user_temp = get_user_temp_dir()
    if user_temp and user_temp.is_dir():
        allowed.append(user_temp.resolve())

    sys_temp = get_system_temp_dir()
    if sys_temp and sys_temp.is_dir():
        allowed.append(sys_temp.resolve())

    local_appdata = get_local_appdata_dir()
    if local_appdata and local_appdata.is_dir():
        # Specific subfolders under LocalAppData that are safe
        crash_dumps = local_appdata / "CrashDumps"
        if crash_dumps.exists():
            allowed.append(crash_dumps.resolve())
        d3d_cache = local_appdata / "D3DSCache"
        if d3d_cache.exists():
            allowed.append(d3d_cache.resolve())
        # Temp under localappdata
        local_temp = local_appdata / "Temp"
        if local_temp.exists() and local_temp not in allowed:
            allowed.append(local_temp.resolve())

    return allowed
