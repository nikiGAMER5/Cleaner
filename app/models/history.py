"""Scan and clean history database using SQLite."""

import os
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime


class HistoryManager:
    """Manages scan and cleaning history records stored in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            app_data = os.environ.get("LOCALAPPDATA")
            if app_data:
                db_dir = Path(app_data) / "PCCleaner"
            else:
                db_dir = Path.home() / ".pccleaner"
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = db_dir / "history.db"
            except Exception:
                self.db_path = Path("history.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _init_db(self) -> None:
        """Create tables if not already existing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    duration REAL NOT NULL,
                    files_found INTEGER NOT NULL,
                    bytes_found INTEGER NOT NULL,
                    files_cleaned INTEGER NOT NULL DEFAULT 0,
                    bytes_cleaned INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def add_record(
        self,
        duration: float,
        files_found: int,
        bytes_found: int,
        files_cleaned: int = 0,
        bytes_cleaned: int = 0,
    ) -> int:
        """Insert a new history entry."""
        now_str = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scan_history (timestamp, duration, files_found, bytes_found, files_cleaned, bytes_cleaned)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now_str, duration, files_found, bytes_found, files_cleaned, bytes_cleaned),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def update_cleaned(self, record_id: int, files_cleaned: int, bytes_cleaned: int) -> None:
        """Update a scan record with cleanup statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE scan_history
                SET files_cleaned = ?, bytes_cleaned = ?
                WHERE id = ?
                """,
                (files_cleaned, bytes_cleaned, record_id),
            )
            conn.commit()

    def get_all_records(self) -> List[Dict]:
        """Fetch all history records sorted by timestamp descending."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scan_history ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_history(self) -> None:
        """Remove all history entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scan_history")
            conn.commit()

    def get_last_scan_record(self) -> Optional[Dict]:
        """Get the most recent scan record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scan_history ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None
