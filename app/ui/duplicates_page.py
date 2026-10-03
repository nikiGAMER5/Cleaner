"""Duplicate file finder page."""

import os
from pathlib import Path
import subprocess
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.cleaner.cleaner import SystemCleaner
from app.cleaner.safety import SafetyValidator
from app.config.constants import TRANSLATIONS
from app.models.file_item import FileItem
from app.scanner.duplicate_scanner import DuplicateScanner
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
from app.utils.formatting import format_bytes, format_number
from app.utils.paths import get_user_profile_dir


class DuplicateScanWorker(QThread):
    progress = Signal(str, int)
    finished_scan = Signal(dict)

    def __init__(self):
        super().__init__()
        self.is_cancelled = False
        self.scanner = DuplicateScanner(min_size_bytes=1024 * 1024)

    def run(self):
        results = self.scanner.scan(
            progress_callback=lambda p, count: self.progress.emit(p, count),
            cancel_requested=lambda: self.is_cancelled,
        )
        self.finished_scan.emit(results)

    def cancel(self):
        self.is_cancelled = True


class DuplicatesPage(QWidget):
    """Page for discovering identical duplicate files."""

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.duplicates_map: Dict[str, List[FileItem]] = {}
        self.flat_items: List[FileItem] = []
        self.worker: Optional[DuplicateScanWorker] = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["duplicates"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["duplicates_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_scan = QPushButton(f"🔍 {self.t['find_duplicates']}")
        self.btn_scan.setObjectName("primaryBtn")
        self.btn_scan.setProperty("class", "primary-btn")
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        self.btn_scan.clicked.connect(self._start_scan)
        header_layout.addWidget(self.btn_scan)
        layout.addLayout(header_layout)

        # 2. Progress Banner
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("card")
        self.progress_frame.setProperty("class", "card")
        self.progress_frame.setVisible(False)
        p_layout = QVBoxLayout(self.progress_frame)
        p_layout.setContentsMargins(14, 12, 14, 12)
        p_layout.setSpacing(6)

        self.lbl_progress = QLabel(self.t["scanning"])
        self.lbl_progress.setStyleSheet("background: transparent; color: #3b82f6; font-weight: 700;")
        p_layout.addWidget(self.lbl_progress)
        self.p_bar = QProgressBar()
        self.p_bar.setRange(0, 0)
        self.p_bar.setFixedHeight(8)
        p_layout.addWidget(self.p_bar)
        layout.addWidget(self.progress_frame)

        # 3. Duplicates Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table)

        # 4. Action bar
        action_bar = QFrame()
        action_bar.setObjectName("card")
        action_bar.setProperty("class", "card")
        act_layout = QHBoxLayout(action_bar)
        act_layout.setContentsMargins(18, 14, 18, 14)

        self.lbl_status = QLabel(self.t["ready_to_analyze"])
        self.lbl_status.setStyleSheet("background: transparent; color: #94a3b8; font-size: 13px;")
        act_layout.addWidget(self.lbl_status)
        act_layout.addStretch()

        self.btn_open = QPushButton(f"📂 {self.t['open_in_explorer']}")
        self.btn_open.setObjectName("secondaryBtn")
        self.btn_open.setProperty("class", "secondary-btn")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self._open_in_explorer)
        act_layout.addWidget(self.btn_open)

        self.btn_delete = QPushButton(f"🗑️ {self.t['delete_selected']}")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setProperty("class", "danger-btn")
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_selected)
        act_layout.addWidget(self.btn_delete)

        layout.addWidget(action_bar)

    def _update_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            "✓",
            self.t["name_header"],
            self.t["size_header"],
            "SHA-256",
            self.t["path_header"],
        ])

    def retranslate_ui(self, language: str):
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["duplicates"])
        self.subtitle_label.setText(self.t["duplicates_subtitle"])
        self.btn_scan.setText(f"🔍 {self.t['find_duplicates']}")
        self.btn_open.setText(f"📂 {self.t['open_in_explorer']}")
        self.btn_delete.setText(f"🗑️ {self.t['delete_selected']}")
        self._update_table_headers()

    def _start_scan(self):
        self.btn_scan.setEnabled(False)
        self.progress_frame.setVisible(True)

        self.worker = DuplicateScanWorker()
        self.worker.progress.connect(
            lambda p, count: self.lbl_progress.setText(f"{self.t['scanning']} ({count} {self.t['files_found'].lower()})")
        )
        self.worker.finished_scan.connect(self._on_scan_finished)
        self.worker.start()

    def _on_scan_finished(self, results: Dict[str, List[FileItem]]):
        self.duplicates_map = results
        self.progress_frame.setVisible(False)
        self.btn_scan.setEnabled(True)

        self.flat_items = []
        for group in results.values():
            self.flat_items.extend(group)

        self.lbl_status.setText(
            f"{len(results)} groups ({len(self.flat_items)} {self.t['files_found'].lower()})"
        )
        self._populate_table()

    def _populate_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.flat_items))

        for row, item in enumerate(self.flat_items):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)  # Never auto-selected!
            self.table.setItem(row, 0, chk)

            name_item = QTableWidgetItem(item.filename)
            self.table.setItem(row, 1, name_item)

            size_item = QTableWidgetItem(format_bytes(item.size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, size_item)

            short_hash = (item.file_hash[:16] + "...") if item.file_hash else "-"
            hash_item = QTableWidgetItem(short_hash)
            hash_item.setToolTip(item.file_hash or "")
            self.table.setItem(row, 3, hash_item)

            path_item = QTableWidgetItem(str(item.path.parent))
            path_item.setToolTip(str(item.path))
            self.table.setItem(row, 4, path_item)

        self.table.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0 and item.row() < len(self.flat_items):
            self.flat_items[item.row()].is_selected = (item.checkState() == Qt.Checked)
            selected = [i for i in self.flat_items if i.is_selected]
            self.btn_delete.setEnabled(len(selected) > 0)

    def _open_in_explorer(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.flat_items):
            p = self.flat_items[row].path
            if p.exists():
                subprocess.Popen(f'explorer /select,"{p}"', shell=True)

    def _delete_selected(self):
        selected = [i for i in self.flat_items if i.is_selected]
        if not selected:
            return

        total_bytes = sum(i.size for i in selected)
        dlg = ConfirmationDialog(
            file_count=len(selected),
            total_bytes=total_bytes,
            title=self.t["confirm_clean_title"],
            message=self.t["confirm_clean_msg"].format(
                count=format_number(len(selected)),
                size=format_bytes(total_bytes),
            ),
            parent=self,
        )
        if dlg.exec():
            user_prof = get_user_profile_dir()
            allowed = [user_prof] if user_prof else []
            validator = SafetyValidator(allowed_roots=allowed)
            cleaner = SystemCleaner(validator)
            results = cleaner.clean_items(selected)

            deleted_paths = {r.path for r in results if r.success}
            self.flat_items = [i for i in self.flat_items if i.path not in deleted_paths]
            self._populate_table()
            self.btn_delete.setEnabled(False)
