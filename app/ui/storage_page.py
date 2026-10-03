"""Storage Analyzer page with visual distribution chart and folder hierarchy."""

from typing import List, Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
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

from app.config.constants import TRANSLATIONS
from app.scanner.storage_scanner import DiskStorageInfo, StorageScanner
from app.ui.widgets.storage_chart import StorageChartWidget
from app.utils.formatting import format_bytes


class StorageScanWorker(QThread):
    progress = Signal(str)
    finished_scan = Signal(object)

    def __init__(self, drive: str):
        super().__init__()
        self.drive = drive
        self.is_cancelled = False
        self.scanner = StorageScanner()

    def run(self):
        info = self.scanner.analyze_drive(
            drive=self.drive,
            progress_callback=lambda msg: self.progress.emit(msg),
            cancel_requested=lambda: self.is_cancelled,
        )
        self.finished_scan.emit(info)

    def cancel(self):
        self.is_cancelled = True


class StoragePage(QWidget):
    """Visual storage breakdown page."""

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.worker: Optional[StorageScanWorker] = None
        self.last_info: Optional[DiskStorageInfo] = None

        self._init_ui()
        self._load_drives()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["storage_analyzer_title"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["storage_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Drive selector
        self.lbl_drive = QLabel(self.t["select_drive"])
        self.lbl_drive.setStyleSheet("background: transparent; color: #94a3b8; font-weight: 600;")
        header_layout.addWidget(self.lbl_drive)

        self.drive_combo = QComboBox()
        self.drive_combo.currentIndexChanged.connect(self._on_drive_changed)
        header_layout.addWidget(self.drive_combo)

        self.btn_analyze = QPushButton(f"⚡ {self.t['analyze_drive']}")
        self.btn_analyze.setObjectName("primaryBtn")
        self.btn_analyze.setProperty("class", "primary-btn")
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.clicked.connect(self._start_analysis)
        header_layout.addWidget(self.btn_analyze)

        layout.addLayout(header_layout)

        # 2. Visual Storage Chart Card
        self.chart_card = QFrame()
        self.chart_card.setObjectName("card")
        self.chart_card.setProperty("class", "card")
        chart_layout = QVBoxLayout(self.chart_card)
        chart_layout.setContentsMargins(18, 16, 18, 16)
        chart_layout.setSpacing(12)

        self.chart_title = QLabel(self.t["storage_distribution"])
        self.chart_title.setStyleSheet("background: transparent; color: #f1f5f9; font-size: 14px; font-weight: 700;")
        chart_layout.addWidget(self.chart_title)

        self.chart_widget = StorageChartWidget()
        chart_layout.addWidget(self.chart_widget)
        layout.addWidget(self.chart_card)

        # 3. Progress indicator
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("card")
        self.progress_frame.setProperty("class", "card")
        self.progress_frame.setVisible(False)
        p_layout = QVBoxLayout(self.progress_frame)
        p_layout.setContentsMargins(14, 12, 14, 12)
        self.lbl_progress = QLabel(self.t["scanning"])
        self.lbl_progress.setStyleSheet("background: transparent; color: #3b82f6; font-size: 13px; font-weight: 700;")
        p_layout.addWidget(self.lbl_progress)
        self.p_bar = QProgressBar()
        self.p_bar.setRange(0, 0)
        self.p_bar.setFixedHeight(8)
        p_layout.addWidget(self.p_bar)
        layout.addWidget(self.progress_frame)

        # 4. Folder Breakdown Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _update_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            "Item",
            self.t["size_header"],
            "% Ratio",
            self.t["path_header"],
        ])

    def retranslate_ui(self, language: str):
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["storage_analyzer_title"])
        self.subtitle_label.setText(self.t["storage_subtitle"])
        self.lbl_drive.setText(self.t["select_drive"])
        self.btn_analyze.setText(f"⚡ {self.t['analyze_drive']}")
        self.chart_title.setText(self.t["storage_distribution"])
        self._update_table_headers()

        if self.last_info:
            self._on_analysis_finished(self.last_info)

    def _load_drives(self):
        drives = StorageScanner.get_available_drives()
        self.drive_combo.clear()
        for d in drives:
            self.drive_combo.addItem(d)
        if drives:
            self._start_analysis()

    def _on_drive_changed(self):
        pass

    def _start_analysis(self):
        selected_drive = self.drive_combo.currentText()
        if not selected_drive:
            return

        self.btn_analyze.setEnabled(False)
        self.progress_frame.setVisible(True)

        self.worker = StorageScanWorker(selected_drive)
        self.worker.progress.connect(lambda msg: self.lbl_progress.setText(msg))
        self.worker.finished_scan.connect(self._on_analysis_finished)
        self.worker.start()

    def _on_analysis_finished(self, info: DiskStorageInfo):
        self.last_info = info
        self.progress_frame.setVisible(False)
        self.btn_analyze.setEnabled(True)

        # Prepare chart segments
        segments = []
        for folder in info.folders[:5]:
            segments.append((folder.name, folder.size_bytes))
        segments.append((self.t["free"], info.free_bytes))

        self.chart_title.setText(
            f"{self.t['storage_distribution']} ({info.drive}) — "
            f"{self.t['total']}: {format_bytes(info.total_bytes)} ({self.t['free']}: {format_bytes(info.free_bytes)})"
        )
        self.chart_widget.update_data(segments, info.total_bytes)

        # Populate table
        self.table.setRowCount(len(info.folders))
        for row, f in enumerate(info.folders):
            # Name
            icon = "📁 " if f.is_dir else "📄 "
            name_item = QTableWidgetItem(f"{icon}{f.name}")
            self.table.setItem(row, 0, name_item)

            # Size
            size_item = QTableWidgetItem(format_bytes(f.size_bytes))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, size_item)

            # % of used space
            pct = (f.size_bytes / max(1, info.used_bytes)) * 100
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, pct_item)

            # Path
            path_item = QTableWidgetItem(str(f.path))
            self.table.setItem(row, 3, path_item)
