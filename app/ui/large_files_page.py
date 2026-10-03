"""Large files analyzer page."""

import os
from pathlib import Path
import subprocess
from typing import List, Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.cleaner.cleaner import SystemCleaner
from app.cleaner.safety import SafetyValidator
from app.config.constants import LARGE_FILE_THRESHOLDS, TRANSLATIONS
from app.models.file_item import FileItem
from app.scanner.large_file_scanner import LargeFileScanner
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
from app.utils.formatting import format_bytes, format_datetime, format_number
from app.utils.paths import get_user_profile_dir


class LargeFileScanWorker(QThread):
    """Worker thread for large file scanning."""

    progress = Signal(str, int)
    finished_scan = Signal(list)

    def __init__(self, threshold_bytes: int):
        super().__init__()
        self.threshold_bytes = threshold_bytes
        self.scanner = LargeFileScanner(min_size_bytes=threshold_bytes)
        self.is_cancelled = False

    def run(self):
        items = self.scanner.scan(
            progress_callback=lambda p, count: self.progress.emit(p, count),
            cancel_requested=lambda: self.is_cancelled,
        )
        self.finished_scan.emit(items)

    def cancel(self):
        self.is_cancelled = True


class LargeFilesPage(QWidget):
    """Page for discovering and optionally removing large files."""

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.items: List[FileItem] = []
        self.worker: Optional[LargeFileScanWorker] = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["large_files"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["large_files_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Threshold Filter Combobox
        filter_box = QHBoxLayout()
        self.lbl_filter = QLabel(self.t["filter_min_size"])
        self.lbl_filter.setStyleSheet("background: transparent; color: #94a3b8; font-weight: 600;")
        filter_box.addWidget(self.lbl_filter)

        self.threshold_combo = QComboBox()
        for label in LARGE_FILE_THRESHOLDS.keys():
            self.threshold_combo.addItem(label)
        self.threshold_combo.setCurrentText("100 MB")
        filter_box.addWidget(self.threshold_combo)

        # Scan Button
        self.scan_btn = QPushButton(f"🔍 {self.t['scan_large_files']}")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.setProperty("class", "primary-btn")
        self.scan_btn.setCursor(Qt.PointingHandCursor)
        self.scan_btn.clicked.connect(self._start_scan)
        filter_box.addWidget(self.scan_btn)

        header_layout.addLayout(filter_box)
        layout.addLayout(header_layout)

        # 2. Progress Banner (hidden by default)
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("card")
        self.progress_frame.setProperty("class", "card")
        self.progress_frame.setVisible(False)
        p_layout = QVBoxLayout(self.progress_frame)
        p_layout.setContentsMargins(14, 12, 14, 12)
        p_layout.setSpacing(6)

        self.lbl_scan_status = QLabel(self.t["scanning"])
        self.lbl_scan_status.setStyleSheet("background: transparent; color: #3b82f6; font-weight: 700;")
        p_layout.addWidget(self.lbl_scan_status)
        self.scan_bar = QProgressBar()
        self.scan_bar.setRange(0, 0)
        self.scan_bar.setFixedHeight(8)
        p_layout.addWidget(self.scan_bar)
        layout.addWidget(self.progress_frame)

        # 3. Large Files Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table)

        # 4. Bottom Action Bar
        action_bar = QFrame()
        action_bar.setObjectName("card")
        action_bar.setProperty("class", "card")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(18, 14, 18, 14)

        self.lbl_selected = QLabel(f"{self.t['files_selected']}: 0 (0 B)")
        self.lbl_selected.setStyleSheet("background: transparent; color: #e2e8f0; font-size: 13px; font-weight: 700;")
        action_layout.addWidget(self.lbl_selected)
        action_layout.addStretch()

        self.btn_open_folder = QPushButton(f"📂 {self.t['open_in_explorer']}")
        self.btn_open_folder.setObjectName("secondaryBtn")
        self.btn_open_folder.setProperty("class", "secondary-btn")
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self._open_selected_in_explorer)
        action_layout.addWidget(self.btn_open_folder)

        self.btn_delete_selected = QPushButton(f"🗑️ {self.t['delete_selected']}")
        self.btn_delete_selected.setObjectName("dangerBtn")
        self.btn_delete_selected.setProperty("class", "danger-btn")
        self.btn_delete_selected.setCursor(Qt.PointingHandCursor)
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.clicked.connect(self._delete_selected)
        action_layout.addWidget(self.btn_delete_selected)

        layout.addWidget(action_bar)

    def _update_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            "✓",
            self.t["name_header"],
            self.t["size_header"],
            self.t["date_header"],
            self.t["path_header"],
        ])

    def retranslate_ui(self, language: str):
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["large_files"])
        self.subtitle_label.setText(self.t["large_files_subtitle"])
        self.lbl_filter.setText(self.t["filter_min_size"])
        self.scan_btn.setText(f"🔍 {self.t['scan_large_files']}")
        self.btn_open_folder.setText(f"📂 {self.t['open_in_explorer']}")
        self.btn_delete_selected.setText(f"🗑️ {self.t['delete_selected']}")
        self._update_table_headers()
        self._update_selection()

    def _start_scan(self):
        """Initiate background scan for large files."""
        threshold_label = self.threshold_combo.currentText()
        threshold_bytes = LARGE_FILE_THRESHOLDS.get(threshold_label, 100 * 1024 * 1024)

        self.scan_btn.setEnabled(False)
        self.progress_frame.setVisible(True)

        self.worker = LargeFileScanWorker(threshold_bytes)
        self.worker.progress.connect(self._on_scan_progress)
        self.worker.finished_scan.connect(self._on_scan_finished)
        self.worker.start()

    def _on_scan_progress(self, path: str, count: int):
        self.lbl_scan_status.setText(f"{self.t['scanning']} ({format_number(count)} {self.t['files_found'].lower()})")

    def _on_scan_finished(self, items: List[FileItem]):
        self.items = items
        self.progress_frame.setVisible(False)
        self.scan_btn.setEnabled(True)
        self._populate_table()
        self._update_selection()

    def _populate_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.items))

        for row, item in enumerate(self.items):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)  # Never checked by default!
            self.table.setItem(row, 0, chk)

            name_item = QTableWidgetItem(item.filename)
            self.table.setItem(row, 1, name_item)

            size_item = QTableWidgetItem(format_bytes(item.size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, size_item)

            date_item = QTableWidgetItem(format_datetime(item.modified_time))
            self.table.setItem(row, 3, date_item)

            path_item = QTableWidgetItem(str(item.path.parent))
            path_item.setToolTip(str(item.path))
            self.table.setItem(row, 4, path_item)

        self.table.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0 and item.row() < len(self.items):
            self.items[item.row()].is_selected = (item.checkState() == Qt.Checked)
            self._update_selection()

    def _update_selection(self):
        selected = [i for i in self.items if i.is_selected]
        count = len(selected)
        size = sum(i.size for i in selected)
        self.lbl_selected.setText(f"{self.t['files_selected']}: {format_number(count)} ({format_bytes(size)})")
        self.btn_delete_selected.setEnabled(count > 0)

    def _open_selected_in_explorer(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.items):
            p = self.items[row].path
            if p.exists():
                subprocess.Popen(f'explorer /select,"{p}"', shell=True)

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if 0 <= row < len(self.items):
            menu = QMenu(self)
            open_action = menu.addAction(self.t["open_in_explorer"])
            action = menu.exec(self.table.viewport().mapToGlobal(pos))
            if action == open_action:
                p = self.items[row].path
                if p.exists():
                    subprocess.Popen(f'explorer /select,"{p}"', shell=True)

    def _delete_selected(self):
        selected = [i for i in self.items if i.is_selected]
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
            self.items = [i for i in self.items if i.path not in deleted_paths]
            self._populate_table()
            self._update_selection()
