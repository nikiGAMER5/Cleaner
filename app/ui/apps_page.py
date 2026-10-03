"""Installed applications analyzer and uninstaller page."""

from typing import List, Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import TRANSLATIONS
from app.scanner.app_scanner import AppScanner, InstalledApp
from app.utils.formatting import format_bytes


class AppScanWorker(QThread):
    finished_scan = Signal(list)

    def run(self):
        scanner = AppScanner()
        apps = scanner.get_installed_apps()
        self.finished_scan.emit(apps)


class AppsPage(QWidget):
    """Page showing installed programs and allowing official uninstallation."""

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.scanner = AppScanner()
        self.apps: List[InstalledApp] = []
        self.filtered_apps: List[InstalledApp] = []
        self.worker: Optional[AppScanWorker] = None

        self._init_ui()
        self.load_apps()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["apps"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["apps_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = QPushButton(f"🔄 {self.t['refresh_apps']}")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.setProperty("class", "secondary-btn")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_apps)
        header_layout.addWidget(self.btn_refresh)
        layout.addLayout(header_layout)

        # 2. Filter Bar
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.t["search_placeholder"])
        self.search_input.textChanged.connect(self._filter_apps)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)

        # 3. Loading bar
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFixedHeight(6)
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)

        # 4. Applications Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # 5. Safety notice
        notice_card = QFrame()
        notice_card.setObjectName("card")
        notice_card.setProperty("class", "card")
        nc_layout = QHBoxLayout(notice_card)
        nc_layout.setContentsMargins(14, 12, 14, 12)
        self.lbl_notice = QLabel(self.t["apps_safety_notice"])
        self.lbl_notice.setStyleSheet("background: transparent; color: #94a3b8; font-size: 12px;")
        nc_layout.addWidget(self.lbl_notice)
        layout.addWidget(notice_card)

    def _update_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            self.t["name_header"],
            self.t["publisher_header"],
            self.t["version_header"],
            self.t["size_header"],
            self.t["action_header"],
        ])

    def retranslate_ui(self, language: str):
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["apps"])
        self.subtitle_label.setText(self.t["apps_subtitle"])
        self.btn_refresh.setText(f"🔄 {self.t['refresh_apps']}")
        self.search_input.setPlaceholderText(self.t["search_placeholder"])
        self.lbl_notice.setText(self.t["apps_safety_notice"])
        self._update_table_headers()
        self._populate_table()

    def load_apps(self):
        """Asynchronously scan registry for apps."""
        self.loading_bar.setVisible(True)
        self.btn_refresh.setEnabled(False)

        self.worker = AppScanWorker()
        self.worker.finished_scan.connect(self._on_apps_loaded)
        self.worker.start()

    def _on_apps_loaded(self, apps: List[InstalledApp]):
        self.apps = apps
        self.loading_bar.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self._filter_apps()

    def _filter_apps(self):
        query = self.search_input.text().strip().lower()
        if not query:
            self.filtered_apps = self.apps[:]
        else:
            self.filtered_apps = [
                a for a in self.apps
                if query in a.name.lower() or query in a.publisher.lower()
            ]
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self.filtered_apps))

        for row, app in enumerate(self.filtered_apps):
            # Name
            name_item = QTableWidgetItem(app.name)
            name_item.setToolTip(f"Installed: {app.install_date or 'Unknown'}")
            self.table.setItem(row, 0, name_item)

            # Publisher
            pub_item = QTableWidgetItem(app.publisher or "-")
            self.table.setItem(row, 1, pub_item)

            # Version
            ver_item = QTableWidgetItem(app.version or "-")
            self.table.setItem(row, 2, ver_item)

            # Size
            size_str = format_bytes(app.size_bytes) if app.size_bytes > 0 else "-"
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, size_item)

            # Uninstall button
            uninstall_btn = QPushButton(f"🗑️ {self.t['uninstall_btn']}")
            uninstall_btn.setObjectName("secondaryBtn")
            uninstall_btn.setProperty("class", "secondary-btn")
            uninstall_btn.setCursor(Qt.PointingHandCursor)
            uninstall_btn.setEnabled(bool(app.uninstall_string))
            uninstall_btn.clicked.connect(lambda _, a=app: self._uninstall_app(a))
            self.table.setCellWidget(row, 4, uninstall_btn)

    def _uninstall_app(self, app: InstalledApp):
        ret = QMessageBox.question(
            self,
            f"{self.t['uninstall_btn']} {app.name}",
            f"{self.t['uninstall_btn']} '{app.name}'?\n\nCommand:\n{app.uninstall_string}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            success = self.scanner.launch_uninstaller(app)
            if not success:
                QMessageBox.warning(
                    self,
                    "Failed",
                    f"Could not launch uninstaller for {app.name}.",
                )
