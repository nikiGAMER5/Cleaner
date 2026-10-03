"""Formatting utilities for sizes, numbers, and dates."""

from datetime import datetime
from typing import Union


def format_bytes(size_bytes: Union[int, float]) -> str:
    """Format bytes into human-readable string (B, KB, MB, GB, TB)."""
    if size_bytes is None or size_bytes < 0:
        return "0 B"
    
    bytes_float = float(size_bytes)
    if bytes_float == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    while bytes_float >= 1024.0 and unit_index < len(units) - 1:
        bytes_float /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(bytes_float)} B"
    elif unit_index == 1:
        return f"{bytes_float:.1f} KB"
    else:
        return f"{bytes_float:.2f} {units[unit_index]}"


def format_number(number: int) -> str:
    """Format an integer with thousand separators."""
    if number is None:
        return "0"
    return f"{number:,}".replace(",", ".")


def format_duration(seconds: float) -> str:
    """Format duration in seconds into a friendly string."""
    if seconds < 1.0:
        return f"{seconds * 1000:.0f} ms"
    elif seconds < 60.0:
        return f"{seconds:.1f} s"
    else:
        minutes = int(seconds // 60)
        remaining_sec = int(seconds % 60)
        return f"{minutes}m {remaining_sec}s"


def format_datetime(dt: Union[datetime, float, int]) -> str:
    """Format a datetime or timestamp into readable format."""
    if isinstance(dt, (int, float)):
        try:
            dt = datetime.fromtimestamp(dt)
        except (ValueError, OSError):
            return "N/A"
    if isinstance(dt, datetime):
        return dt.strftime("%d.%m.%Y %H:%M")
    return "N/A"
