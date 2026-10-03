"""Dashboard page displaying system storage overview, quick scan, and cleanup potential."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.cleaner.recycle_bin import RecycleBinManager
from app.config.constants import (
    CAT_CACHE,
    CAT_LARGE_FILES,
    CAT_TEMP,
    TRANSLATIONS,
)
from app.models.scan_result import ScanResultSet
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
from app.ui.widgets.stat_card import StatCard
from app.utils.formatting import format_bytes, format_datetime, format_number
from app.scanner.storage_scanner import StorageScanner


class DashboardPage(QWidget):
    """Main dashboard displaying system health, storage, and scan controls."""

    scan_requested = Signal()
    review_requested = Signal()

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.last_scan_result: Optional[ScanResultSet] = None

        self._init_ui()
        self.refresh_storage()
        self.update_recycle_bin()

    def _init_ui(self):
        # Top-level layout with a smooth scroll area to prevent clipping on small displays
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.viewport().setAutoFillBackground(False)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollArea > QWidget > QWidget { background: transparent; }")

        content_widget = QWidget()
        content_widget.setObjectName("scrollWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(18)

        # 1. Page Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["dashboard"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["tagline"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.refresh_btn = QPushButton(f"🔄 {self.t['refresh_storage']}")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.setProperty("class", "secondary-btn")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_storage)
        header_layout.addWidget(self.refresh_btn)
        content_layout.addLayout(header_layout)

        # 2. Storage Overview Card
        storage_card = QFrame()
        storage_card.setObjectName("card")
        storage_card.setProperty("class", "card")
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(18, 16, 18, 16)
        storage_layout.setSpacing(12)

        storage_header = QHBoxLayout()
        self.lbl_storage_title = QLabel(f"• {self.t['storage_title']} (C:\\)")
        self.lbl_storage_title.setStyleSheet("background: transparent; color: #f1f5f9; font-size: 15px; font-weight: 700;")
        storage_header.addWidget(self.lbl_storage_title)
        storage_header.addStretch()

        self.storage_free_badge = QLabel(f"-- GB {self.t['free_suffix']}")
        self.storage_free_badge.setStyleSheet(
            "background-color: #1e293b; color: #10b981; font-weight: 700; "
            "padding: 4px 12px; border-radius: 6px; font-size: 12px;"
        )
        storage_header.addWidget(self.storage_free_badge)
        storage_layout.addLayout(storage_header)

        # Progress bar
        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setValue(0)
        self.storage_bar.setFixedHeight(10)
        storage_layout.addWidget(self.storage_bar)

        # Storage Numbers row
        numbers_layout = QHBoxLayout()
        self.lbl_storage_used = QLabel(f"{self.t['used']}: -- GB")
        self.lbl_storage_used.setStyleSheet("background: transparent; color: #94a3b8; font-size: 13px; font-weight: 500;")
        numbers_layout.addWidget(self.lbl_storage_used)

        self.lbl_storage_total = QLabel(f"{self.t['total']}: -- GB")
        self.lbl_storage_total.setStyleSheet("background: transparent; color: #94a3b8; font-size: 13px; font-weight: 500;")
        numbers_layout.addWidget(self.lbl_storage_total)
        numbers_layout.addStretch()

        storage_layout.addLayout(numbers_layout)
        content_layout.addWidget(storage_card)

        # 3. Middle Section: Scan Action Hero Card & Recycle Bin Card
        hero_row = QHBoxLayout()
        hero_row.setSpacing(16)

        # Scan Hero Card
        self.hero_card = QFrame()
        self.hero_card.setObjectName("card")
        self.hero_card.setProperty("class", "card")
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(10)

        self.lbl_hero_title = QLabel(self.t["potential_cleanup"].upper())
        self.lbl_hero_title.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;"
        )
        hero_layout.addWidget(self.lbl_hero_title)

        self.cleanup_size_label = QLabel("0.00 B")
        self.cleanup_size_label.setStyleSheet(
            "background: transparent; color: #3b82f6; font-size: 38px; font-weight: 800;"
        )
        hero_layout.addWidget(self.cleanup_size_label)

        self.cleanup_files_label = QLabel(self.t["ready_to_analyze"])
        self.cleanup_files_label.setStyleSheet(
            "background: transparent; color: #64748b; font-size: 13px; font-weight: 500;"
        )
        hero_layout.addWidget(self.cleanup_files_label)

        hero_actions = QHBoxLayout()
        hero_actions.setSpacing(12)
        self.scan_btn = QPushButton(f"⚡ {self.t['scan_pc']}")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.setProperty("class", "primary-btn")
        self.scan_btn.setCursor(Qt.PointingHandCursor)
        self.scan_btn.clicked.connect(self.scan_requested.emit)
        hero_actions.addWidget(self.scan_btn)

        self.review_btn = QPushButton(f"🔍 {self.t['review_files']}")
        self.review_btn.setObjectName("secondaryBtn")
        self.review_btn.setProperty("class", "secondary-btn")
        self.review_btn.setCursor(Qt.PointingHandCursor)
        self.review_btn.setEnabled(False)
        self.review_btn.clicked.connect(self.review_requested.emit)
        hero_actions.addWidget(self.review_btn)
        hero_actions.addStretch()
        hero_layout.addLayout(hero_actions)

        hero_row.addWidget(self.hero_card, stretch=2)

        # Recycle Bin Quick Card
        rb_card = QFrame()
        rb_card.setObjectName("card")
        rb_card.setProperty("class", "card")
        rb_layout = QVBoxLayout(rb_card)
        rb_layout.setContentsMargins(18, 18, 18, 18)
        rb_layout.setSpacing(8)

        self.lbl_rb_title = QLabel(self.t["recycle_bin_title"].upper())
        self.lbl_rb_title.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;"
        )
        rb_layout.addWidget(self.lbl_rb_title)

        self.rb_size_label = QLabel("0 B")
        self.rb_size_label.setStyleSheet(
            "background: transparent; color: #f1f5f9; font-size: 24px; font-weight: 800;"
        )
        rb_layout.addWidget(self.rb_size_label)

        self.rb_items_label = QLabel(self.t["items_count"].format(count=0))
        self.rb_items_label.setStyleSheet(
            "background: transparent; color: #64748b; font-size: 12px; font-weight: 500;"
        )
        rb_layout.addWidget(self.rb_items_label)

        self.empty_rb_btn = QPushButton(f"🗑️ {self.t['empty_bin_btn']}")
        self.empty_rb_btn.setObjectName("dangerBtn")
        self.empty_rb_btn.setProperty("class", "danger-btn")
        self.empty_rb_btn.setCursor(Qt.PointingHandCursor)
        self.empty_rb_btn.clicked.connect(self._handle_empty_recycle_bin)
        rb_layout.addWidget(self.empty_rb_btn)
        rb_layout.addStretch()

        hero_row.addWidget(rb_card, stretch=1)
        content_layout.addLayout(hero_row)

        # 4. Live Scan Progress Box (hidden by default)
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("card")
        self.progress_frame.setProperty("class", "card")
        self.progress_frame.setVisible(False)
        prog_layout = QVBoxLayout(self.progress_frame)
        prog_layout.setContentsMargins(16, 14, 16, 14)
        prog_layout.setSpacing(8)

        self.prog_status_lbl = QLabel(self.t["scanning"])
        self.prog_status_lbl.setStyleSheet(
            "background: transparent; color: #3b82f6; font-size: 14px; font-weight: 700;"
        )
        prog_layout.addWidget(self.prog_status_lbl)

        self.prog_path_lbl = QLabel("...")
        self.prog_path_lbl.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 12px;"
        )
        prog_layout.addWidget(self.prog_path_lbl)

        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 0)
        self.prog_bar.setFixedHeight(8)
        prog_layout.addWidget(self.prog_bar)

        content_layout.addWidget(self.progress_frame)

        # 5. Key Metrics Grid
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)

        self.card_last_scan = StatCard(
            self.t["last_scan"], self.t["never"], self.t["status_label"], "#3b82f6"
        )
        metrics_layout.addWidget(self.card_last_scan)

        self.card_files_found = StatCard(
            self.t["files_found"], "0", self.t["cleanable_items"], "#10b981"
        )
        metrics_layout.addWidget(self.card_files_found)

        self.card_temp = StatCard(
            self.t["temp_files_count"], "0 B", self.t["files_count"].format(count=0), "#f59e0b"
        )
        metrics_layout.addWidget(self.card_temp)

        self.card_cache = StatCard(
            self.t["cache_files_count"], "0 B", self.t["files_count"].format(count=0), "#8b5cf6"
        )
        metrics_layout.addWidget(self.card_cache)

        content_layout.addLayout(metrics_layout)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

    def retranslate_ui(self, language: str):
        """Dynamically retranslate all labels on this page."""
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["dashboard"])
        self.subtitle_label.setText(self.t["tagline"])
        self.refresh_btn.setText(f"🔄 {self.t['refresh_storage']}")
        self.lbl_storage_title.setText(f"• {self.t['storage_title']} (C:\\)")
        self.lbl_hero_title.setText(self.t["potential_cleanup"].upper())
        self.scan_btn.setText(f"⚡ {self.t['scan_pc']}")
        self.review_btn.setText(f"🔍 {self.t['review_files']}")
        self.lbl_rb_title.setText(self.t["recycle_bin_title"].upper())
        self.empty_rb_btn.setText(f"🗑️ {self.t['empty_bin_btn']}")

        if not self.last_scan_result:
            self.cleanup_files_label.setText(self.t["ready_to_analyze"])
            self.card_last_scan.retranslate(self.t["last_scan"], self.t["status_label"])
            self.card_last_scan.set_value(self.t["never"])
            self.card_files_found.retranslate(self.t["files_found"], self.t["cleanable_items"])
            self.card_temp.retranslate(self.t["temp_files_count"], self.t["files_count"].format(count=0))
            self.card_cache.retranslate(self.t["cache_files_count"], self.t["files_count"].format(count=0))
        else:
            self.apply_scan_result(self.last_scan_result)

        self.refresh_storage()
        self.update_recycle_bin()

    def refresh_storage(self):
        """Fetch real Windows drive usage."""
        try:
            usage = StorageScanner.get_drive_usage("C:\\")
            used_str = format_bytes(usage.used)
            total_str = format_bytes(usage.total)
            free_str = format_bytes(usage.free)

            self.lbl_storage_used.setText(f"{self.t['used']}: {used_str}")
            self.lbl_storage_total.setText(f"{self.t['total']}: {total_str}")
            self.storage_free_badge.setText(f"{free_str} {self.t['free_suffix']}")
            self.storage_bar.setValue(int(usage.percent))
        except Exception:
            pass

    def update_recycle_bin(self):
        """Query and display recycle bin metrics."""
        size, count = RecycleBinManager.get_recycle_bin_info()
        self.rb_size_label.setText(format_bytes(size))
        self.rb_items_label.setText(self.t["items_count"].format(count=format_number(count)))
        self.empty_rb_btn.setEnabled(count > 0 or size > 0)

    def _handle_empty_recycle_bin(self):
        """Confirmation and emptying of Windows recycle bin."""
        size, count = RecycleBinManager.get_recycle_bin_info()
        dlg = ConfirmationDialog(
            file_count=count,
            total_bytes=size,
            title=self.t["empty_recycle_bin"],
            message=self.t["recycle_bin_warning"],
            parent=self,
        )
        if dlg.exec():
            RecycleBinManager.empty_recycle_bin(confirm=False)
            self.update_recycle_bin()
            self.refresh_storage()

    def set_scan_in_progress(self, is_running: bool):
        """Toggle UI between idle and scanning states."""
        self.scan_btn.setEnabled(not is_running)
        self.review_btn.setEnabled(not is_running)
        self.progress_frame.setVisible(is_running)
        if is_running:
            self.scan_btn.setText(f"⏳ {self.t['scanning']}")
        else:
            self.scan_btn.setText(f"⚡ {self.t['scan_pc']}")

    def update_scan_progress(self, path: str, count: int, bytes_found: int):
        """Update live scan readout."""
        self.prog_path_lbl.setText(path)
        self.prog_status_lbl.setText(
            f"{self.t['scanning']} ({format_number(count)} {self.t['files_found'].lower()}, {format_bytes(bytes_found)})"
        )

    def apply_scan_result(self, result: ScanResultSet):
        """Update all dashboard widgets with fresh scan results."""
        self.last_scan_result = result
        self.cleanup_size_label.setText(format_bytes(result.total_size))
        self.cleanup_files_label.setText(
            f"{format_number(result.total_count)} {self.t['cleanable_items'].lower()} ({result.duration:.1f}s)"
        )
        self.review_btn.setEnabled(result.total_count > 0)

        # Update metrics
        self.card_last_scan.retranslate(self.t["last_scan"], f"{result.duration:.1f}s")
        self.card_last_scan.set_value(format_datetime(result.end_time))

        self.card_files_found.retranslate(self.t["files_found"], format_bytes(result.total_size))
        self.card_files_found.set_value(format_number(result.total_count))

        temp_summary = result.get_category_summary(CAT_TEMP)
        self.card_temp.retranslate(
            self.t["temp_files_count"],
            self.t["files_count"].format(count=format_number(temp_summary.file_count)),
        )
        self.card_temp.set_value(format_bytes(temp_summary.total_size))

        cache_summary = result.get_category_summary(CAT_CACHE)
        self.card_cache.retranslate(
            self.t["cache_files_count"],
            self.t["files_count"].format(count=format_number(cache_summary.file_count)),
        )
        self.card_cache.set_value(format_bytes(cache_summary.total_size))

        self.update_recycle_bin()
        self.refresh_storage()
