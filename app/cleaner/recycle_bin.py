"""Windows Recycle Bin interaction using ctypes and Shell32 API."""

import ctypes
from ctypes import wintypes
import os
from typing import Tuple


class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]


SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004


class RecycleBinManager:
    """Provides methods to inspect and empty the Windows Recycle Bin."""

    @staticmethod
    def get_recycle_bin_info(drive_path: str = "C:\\") -> Tuple[int, int]:
        """
        Returns (total_size_bytes, num_items) in the Recycle Bin for the given drive or all drives.
        """
        if os.name != "nt":
            return 0, 0

        try:
            shell32 = ctypes.windll.shell32
            rb_info = SHQUERYRBINFO()
            rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)

            # Query recycle bin (drive_path can be None for entire recycle bin)
            res = shell32.SHQueryRecycleBinW(drive_path, ctypes.byref(rb_info))
            if res == 0:
                return int(rb_info.i64Size), int(rb_info.i64NumItems)
            return 0, 0
        except Exception:
            return 0, 0

    @staticmethod
    def empty_recycle_bin(confirm: bool = False, sound: bool = True) -> bool:
        """
        Empties the Windows Recycle Bin.
        If confirm is False, SHERB_NOCONFIRMATION is sent to the Windows API
        (since the UI dialog already confirms with the user).
        """
        if os.name != "nt":
            return False

        try:
            shell32 = ctypes.windll.shell32
            flags = 0
            if not confirm:
                flags |= SHERB_NOCONFIRMATION
            if not sound:
                flags |= SHERB_NOSOUND

            res = shell32.SHEmptyRecycleBinW(None, None, flags)
            # S_OK is 0
            return res == 0
        except Exception:
            return False
