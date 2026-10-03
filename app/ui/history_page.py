"""Scan and clean history page."""

from typing import List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import TRANSLATIONS
from app.models.history import HistoryManager
from app.utils.formatting import format_bytes, format_duration, format_number


class HistoryPage(QWidget):
    """Page displaying historical scans and cleanup operations."""

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.history_mgr = HistoryManager()

        self._init_ui()
        self.load_history()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["history"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["history_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_clear = QPushButton(f"🗑️ {self.t['clear_history']}")
        self.btn_clear.setObjectName("dangerBtn")
        self.btn_clear.setProperty("class", "danger-btn")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_history)
        header_layout.addWidget(self.btn_clear)

        layout.addLayout(header_layout)

        # 2. History Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _update_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            self.t["history_date"],
            self.t["history_duration"],
            self.t["files_found"],
            self.t["history_found"],
            self.t["history_cleaned"],
        ])

    def retranslate_ui(self, language: str):
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["history"])
        self.subtitle_label.setText(self.t["history_subtitle"])
        self.btn_clear.setText(f"🗑️ {self.t['clear_history']}")
        self._update_table_headers()
        self.load_history()

    def load_history(self):
        records = self.history_mgr.get_all_records()
        self.table.setRowCount(len(records))

        for row, r in enumerate(records):
            # Date
            date_item = QTableWidgetItem(r["timestamp"][:19].replace("T", " "))
            self.table.setItem(row, 0, date_item)

            # Duration
            dur_item = QTableWidgetItem(format_duration(r["duration"]))
            dur_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, dur_item)

            # Files found
            files_item = QTableWidgetItem(format_number(r["files_found"]))
            files_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, files_item)

            # Space found
            found_item = QTableWidgetItem(format_bytes(r["bytes_found"]))
            found_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, found_item)

            # Space cleaned
            cleaned_str = f"{format_bytes(r['bytes_cleaned'])} ({format_number(r['files_cleaned'])})"
            cleaned_item = QTableWidgetItem(cleaned_str)
            if r["bytes_cleaned"] > 0:
                cleaned_item.setForeground(Qt.green)
            self.table.setItem(row, 4, cleaned_item)

        self.btn_clear.setEnabled(len(records) > 0)

    def _clear_history(self):
        ret = QMessageBox.question(
            self,
            self.t["clear_history"],
            "Clear all history?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            self.history_mgr.clear_history()
            self.load_history()
