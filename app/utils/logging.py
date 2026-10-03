"""Application logging system with rotation and privacy safeguards."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Optional


_logger: Optional[logging.Logger] = None


def get_log_dir() -> Path:
    """Get the directory where application logs are stored."""
    # Use workspace or local appdata
    base_dir = Path.cwd() / "logs"
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Fallback to user temp if current working directory is not writable
        base_dir = Path(os.environ.get("TEMP", ".")) / "pc_cleaner_logs"
        base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def sanitize_message(msg: str) -> str:
    """Remove potential sensitive tokens/passwords from log messages."""
    sensitive_words = ["password", "token", "auth", "secret", "bearer", "cookie"]
    lower = msg.lower()
    for word in sensitive_words:
        if word in lower:
            # Mask anything that might look like sensitive parameters
            return f"[REDACTED CONTENT - sensitive keyword detected: {word}]"
    return msg


class SafeFormatter(logging.Formatter):
    """Formatter that ensures messages don't leak passwords or sensitive tokens."""
    def format(self, record: logging.LogRecord) -> str:
        record.msg = sanitize_message(str(record.msg))
        return super().format(record)


def setup_logger() -> logging.Logger:
    """Set up and return the application logger."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("pc_cleaner")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Avoid duplicate handlers
    if not logger.handlers:
        log_dir = get_log_dir()
        log_file = log_dir / "app.log"

        # Rotating file handler: 5 MB max per file, keep 3 backups
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        formatter = SafeFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler for console (development)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Retrieve the application logger."""
    if _logger is None:
        return setup_logger()
    return _logger
