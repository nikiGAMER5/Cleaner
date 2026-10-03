"""Main application window with modern sidebar navigation, dynamic language switching, and worker threads."""

from typing import List, Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.cleaner.cleaner import SystemCleaner
from app.cleaner.safety import SafetyValidator
from app.config.constants import APP_NAME, APP_VERSION, TRANSLATIONS
from app.models.file_item import CleanResult, FileItem
from app.models.history import HistoryManager
from app.models.scan_result import ScanResultSet
from app.models.settings import AppSettings
from app.scanner.scanner import SystemScanner
from app.ui.apps_page import AppsPage
from app.ui.cleaner_page import CleanerPage
from app.ui.dashboard import DashboardPage
from app.ui.duplicates_page import DuplicatesPage
from app.ui.history_page import HistoryPage
from app.ui.large_files_page import LargeFilesPage
from app.ui.settings_page import SettingsPage
from app.ui.storage_page import StoragePage
from app.ui.styles import DARK_THEME, LIGHT_THEME
from app.utils.formatting import format_bytes, format_number
from app.utils.logging import get_logger
from app.utils.paths import get_safe_whitelist_roots


class MasterScanWorker(QThread):
    """Worker thread executing system scan without freezing GUI."""

    progress = Signal(str, int, int)
    finished_scan = Signal(object)

    def __init__(self, categories: List[str]):
        super().__init__()
        self.categories = categories
        self.scanner = SystemScanner(enabled_categories=categories)
        self.is_cancelled = False

    def run(self):
        result = self.scanner.run_scan(
            progress_callback=lambda p, count, b: self.progress.emit(p, count, b),
            cancel_requested=lambda: self.is_cancelled,
        )
        self.finished_scan.emit(result)

    def cancel(self):
        self.is_cancelled = True


class MasterCleanWorker(QThread):
    """Worker thread safely deleting files without freezing GUI."""

    progress = Signal(int, int, int, str)
    finished_clean = Signal(list)

    def __init__(self, items: List[FileItem]):
        super().__init__()
        self.items = items
        self.is_cancelled = False

    def run(self):
        allowed_roots = get_safe_whitelist_roots()
        validator = SafetyValidator(allowed_roots=allowed_roots)
        cleaner = SystemCleaner(validator)

        results = cleaner.clean_items(
            items=self.items,
            progress_callback=lambda cur, tot, freed, fn: self.progress.emit(cur, tot, freed, fn),
            cancel_requested=lambda: self.is_cancelled,
        )
        self.finished_clean.emit(results)

    def cancel(self):
        self.is_cancelled = True


class MainWindow(QMainWindow):
    """Top-level application window with modern dark UI and navigation."""

    def __init__(self, settings: Optional[AppSettings] = None):
        super().__init__()
        self.settings = settings or AppSettings.load()
        self.language = self.settings.language
        self.t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        self.logger = get_logger()
        self.history_mgr = HistoryManager()

        self.last_scan_record_id: Optional[int] = None
        self.scan_worker: Optional[MasterScanWorker] = None
        self.clean_worker: Optional[MasterCleanWorker] = None

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1140, 780)
        self.setMinimumSize(980, 660)

        self._apply_theme()
        self._init_ui()

        # Startup auto scan if enabled in settings
        if self.settings.run_on_startup:
            self._start_scan()

    def _apply_theme(self):
        if self.settings.theme == "light":
            self.setStyleSheet(LIGHT_THEME)
        else:
            self.setStyleSheet(DARK_THEME)

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 18, 12, 18)
        sb_layout.setSpacing(4)

        # App Logo & Version
        self.lbl_logo = QLabel(APP_NAME)
        self.lbl_logo.setObjectName("logoLabel")
        sb_layout.addWidget(self.lbl_logo)

        self.lbl_version = QLabel(f"{self.t['professional_edition']} • v{APP_VERSION}")
        self.lbl_version.setObjectName("logoSubtitle")
        sb_layout.addWidget(self.lbl_version)

        # Navigation buttons group
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_keys = [
            ("dashboard", 0, "🏠"),
            ("cleaner", 1, "🧹"),
            ("large_files", 2, "📦"),
            ("apps", 3, "📱"),
            ("storage", 4, "📊"),
            ("duplicates", 5, "🗂️"),
            ("history", 6, "📜"),
            ("settings", 7, "⚙️"),
        ]

        self.nav_buttons: List[QPushButton] = []
        for key, page_idx, icon in self.nav_keys:
            text = f"{icon} {self.t[key]}"
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setProperty("class", "nav-btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            if page_idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, idx=page_idx: self._switch_page(idx))
            self.nav_group.addButton(btn, page_idx)
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Status badge
        self.lbl_system_status = QLabel(self.t["status_protected"])
        self.lbl_system_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 700; padding: 10px;")
        sb_layout.addWidget(self.lbl_system_status)

        root_layout.addWidget(sidebar)

        # 2. Main Content Stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")

        # Instantiate pages
        self.dashboard_page = DashboardPage(language=self.language, parent=self)
        self.dashboard_page.scan_requested.connect(self._start_scan)
        self.dashboard_page.review_requested.connect(lambda: self._switch_page(1))
        self.stack.addWidget(self.dashboard_page)  # 0

        self.cleaner_page = CleanerPage(language=self.language, parent=self)
        self.cleaner_page.clean_requested.connect(self._start_clean)
        self.stack.addWidget(self.cleaner_page)  # 1

        self.large_files_page = LargeFilesPage(language=self.language, parent=self)
        self.stack.addWidget(self.large_files_page)  # 2

        self.apps_page = AppsPage(language=self.language, parent=self)
        self.stack.addWidget(self.apps_page)  # 3

        self.storage_page = StoragePage(language=self.language, parent=self)
        self.stack.addWidget(self.storage_page)  # 4

        self.duplicates_page = DuplicatesPage(language=self.language, parent=self)
        self.stack.addWidget(self.duplicates_page)  # 5

        self.history_page = HistoryPage(language=self.language, parent=self)
        self.stack.addWidget(self.history_page)  # 6

        self.settings_page = SettingsPage(settings=self.settings, parent=self)
        self.settings_page.settings_changed.connect(self._on_settings_updated)
        self.settings_page.language_changed.connect(self._on_language_changed)
        self.stack.addWidget(self.settings_page)  # 7

        root_layout.addWidget(self.stack)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        btn = self.nav_group.button(index)
        if btn:
            btn.setChecked(True)

    def _on_language_changed(self, new_lang: str):
        """Immediately update all UI texts across the entire application."""
        self.language = new_lang
        self.t = TRANSLATIONS.get(new_lang, TRANSLATIONS["en"])

        # Update sidebar
        self.lbl_version.setText(f"{self.t['professional_edition']} • v{APP_VERSION}")
        self.lbl_system_status.setText(self.t["status_protected"])

        for btn, (key, _, icon) in zip(self.nav_buttons, self.nav_keys):
            btn.setText(f"{icon} {self.t[key]}")

        # Update all pages
        self.dashboard_page.retranslate_ui(new_lang)
        self.cleaner_page.retranslate_ui(new_lang)
        self.large_files_page.retranslate_ui(new_lang)
        self.apps_page.retranslate_ui(new_lang)
        self.storage_page.retranslate_ui(new_lang)
        self.duplicates_page.retranslate_ui(new_lang)
        self.history_page.retranslate_ui(new_lang)
        self.settings_page.retranslate_ui(new_lang)

    def _start_scan(self):
        """Initiate background system scan."""
        self.logger.info("Main window requested system scan.")
        self.lbl_system_status.setText(self.t["status_scanning"])
        self.lbl_system_status.setStyleSheet("color: #3b82f6; font-size: 11px; font-weight: 700; padding: 10px;")
        self.dashboard_page.set_scan_in_progress(True)

        self.scan_worker = MasterScanWorker(categories=self.settings.enabled_categories)
        self.scan_worker.progress.connect(self.dashboard_page.update_scan_progress)
        self.scan_worker.finished_scan.connect(self._on_scan_completed)
        self.scan_worker.start()

    def _on_scan_completed(self, result: ScanResultSet):
        """Handle completed scan results."""
        self.lbl_system_status.setText(self.t["status_protected"])
        self.lbl_system_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 700; padding: 10px;")
        self.dashboard_page.set_scan_in_progress(False)
        self.dashboard_page.apply_scan_result(result)
        self.cleaner_page.set_scan_result(result)

        # Store in SQLite history
        self.last_scan_record_id = self.history_mgr.add_record(
            duration=result.duration,
            files_found=result.total_count,
            bytes_found=result.total_size,
        )
        self.history_page.load_history()

    def _start_clean(self, items: List[FileItem]):
        """Initiate background cleaning of selected items."""
        self.logger.info(f"Starting cleanup of {len(items)} items.")
        self.cleaner_page.set_cleaning_in_progress(True, total=len(items))

        self.clean_worker = MasterCleanWorker(items=items)
        self.clean_worker.progress.connect(self.cleaner_page.update_clean_progress)
        self.clean_worker.finished_clean.connect(self._on_clean_completed)
        self.clean_worker.start()

    def _on_clean_completed(self, results: List[CleanResult]):
        """Handle cleanup completion and metrics update."""
        self.cleaner_page.set_cleaning_in_progress(False)

        freed_bytes = sum(r.freed_bytes for r in results if r.success)
        freed_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)

        # Update SQLite record
        if self.last_scan_record_id:
            self.history_mgr.update_cleaned(
                record_id=self.last_scan_record_id,
                files_cleaned=freed_count,
                bytes_cleaned=freed_bytes,
            )
            self.history_page.load_history()

        # Feedback dialog
        msg = self.t["clean_completed_msg"].format(
            freed_size=format_bytes(freed_bytes),
            failed_count=format_number(failed_count),
        )
        QMessageBox.information(self, self.t["clean_completed"], msg)

        # Refresh dashboard and storage metrics
        self.dashboard_page.refresh_storage()
        self.dashboard_page.update_recycle_bin()

        # Re-scan to provide fresh state
        self._start_scan()

    def _on_settings_updated(self, new_settings: AppSettings):
        """Apply theme and configuration changes."""
        self.settings = new_settings
        self._apply_theme()
        if new_settings.language != self.language:
            self._on_language_changed(new_settings.language)
