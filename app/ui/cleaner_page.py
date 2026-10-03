"""Cleaner page with category selectors, detailed file review, and cleanup controls."""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import (
    CAT_APP_CACHE,
    CAT_BROWSER_CACHE,
    CAT_CACHE,
    CAT_LOGS,
    CAT_TEMP,
    CAT_THUMBNAILS,
    TRANSLATIONS,
)
from app.models.file_item import FileItem
from app.models.scan_result import ScanResultSet
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
from app.utils.formatting import format_bytes, format_number


class CleanerPage(QWidget):
    """Review and selective cleanup page."""

    clean_requested = Signal(list)  # emits list of selected FileItem to clean

    def __init__(self, language: str = "de", parent=None):
        super().__init__(parent)
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        self.current_scan: Optional[ScanResultSet] = None
        self.filtered_items: List[FileItem] = []

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # 1. Page Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["cleaner"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["cleaner_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Select all / Deselect all
        self.btn_select_all = QPushButton(f"✓ {self.t['select_all']}")
        self.btn_select_all.setObjectName("secondaryBtn")
        self.btn_select_all.setProperty("class", "secondary-btn")
        self.btn_select_all.setCursor(Qt.PointingHandCursor)
        self.btn_select_all.clicked.connect(lambda: self._set_all_selection(True))
        header_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton(f"✗ {self.t['deselect_all']}")
        self.btn_deselect_all.setObjectName("secondaryBtn")
        self.btn_deselect_all.setProperty("class", "secondary-btn")
        self.btn_deselect_all.setCursor(Qt.PointingHandCursor)
        self.btn_deselect_all.clicked.connect(lambda: self._set_all_selection(False))
        header_layout.addWidget(self.btn_deselect_all)

        main_layout.addLayout(header_layout)

        # 2. Category Cards Grid (2 rows x 3 columns for spacious layout without text clipping)
        self.cat_cards_layout = QGridLayout()
        self.cat_cards_layout.setSpacing(12)
        self.category_checkboxes: Dict[str, QCheckBox] = {}
        self.category_labels: Dict[str, QLabel] = {}

        categories = [
            (CAT_TEMP, self.t["category_temp"]),
            (CAT_CACHE, self.t["category_cache"]),
            (CAT_LOGS, self.t["category_logs"]),
            (CAT_BROWSER_CACHE, self.t["category_browser_cache"]),
            (CAT_THUMBNAILS, self.t["category_thumbnails"]),
            (CAT_APP_CACHE, self.t["category_app_cache"]),
        ]

        for i, (cat_id, cat_name) in enumerate(categories):
            row = i // 3
            col = i % 3

            card = QFrame()
            card.setObjectName("card")
            card.setProperty("class", "card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(6)

            cb = QCheckBox(cat_name)
            cb.setChecked(cat_id in [CAT_TEMP, CAT_CACHE, CAT_LOGS])
            cb.stateChanged.connect(self._on_category_toggled)
            self.category_checkboxes[cat_id] = cb
            card_layout.addWidget(cb)

            lbl = QLabel(f"0 {self.t['files_count'].format(count=0)} (0 B)")
            lbl.setStyleSheet("background: transparent; color: #64748b; font-size: 11px; margin-left: 24px;")
            self.category_labels[cat_id] = lbl
            card_layout.addWidget(lbl)

            self.cat_cards_layout.addWidget(card, row, col)

        main_layout.addLayout(self.cat_cards_layout)

        # 3. Filter Bar
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"{self.t['search_placeholder']}")
        self.search_input.textChanged.connect(self._filter_items)
        filter_layout.addWidget(self.search_input)
        main_layout.addLayout(filter_layout)

        # 4. Detailed File List Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self._on_table_item_changed)
        main_layout.addWidget(self.table)

        # 5. Cleaning In-Progress Banner (hidden by default)
        self.clean_progress_box = QFrame()
        self.clean_progress_box.setObjectName("card")
        self.clean_progress_box.setProperty("class", "card")
        self.clean_progress_box.setVisible(False)
        cp_layout = QVBoxLayout(self.clean_progress_box)
        cp_layout.setContentsMargins(14, 12, 14, 12)
        cp_layout.setSpacing(6)

        self.clean_status_label = QLabel(self.t["cleaning"])
        self.clean_status_label.setStyleSheet("background: transparent; color: #3b82f6; font-size: 13px; font-weight: 700;")
        cp_layout.addWidget(self.clean_status_label)

        self.clean_bar = QProgressBar()
        self.clean_bar.setFixedHeight(8)
        cp_layout.addWidget(self.clean_bar)
        main_layout.addWidget(self.clean_progress_box)

        # 6. Bottom Action Bar
        action_bar = QFrame()
        action_bar.setObjectName("card")
        action_bar.setProperty("class", "card")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(18, 14, 18, 14)

        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(2)
        self.lbl_selected_count = QLabel(f"{self.t['files_selected']}: 0")
        self.lbl_selected_count.setStyleSheet("background: transparent; color: #e2e8f0; font-size: 14px; font-weight: 700;")
        metrics_layout.addWidget(self.lbl_selected_count)

        self.lbl_selected_size = QLabel(f"{self.t['space_to_free']}: 0 B")
        self.lbl_selected_size.setStyleSheet("background: transparent; color: #10b981; font-size: 13px; font-weight: 700;")
        metrics_layout.addWidget(self.lbl_selected_size)
        action_layout.addLayout(metrics_layout)

        action_layout.addStretch()

        self.clean_btn = QPushButton(f"🧹 {self.t['clean_selected']}")
        self.clean_btn.setObjectName("dangerBtn")
        self.clean_btn.setProperty("class", "danger-btn")
        self.clean_btn.setCursor(Qt.PointingHandCursor)
        self.clean_btn.clicked.connect(self._on_clean_clicked)
        self.clean_btn.setEnabled(False)
        action_layout.addWidget(self.clean_btn)

        main_layout.addWidget(action_bar)

    def _update_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            "✓",
            self.t["name_header"],
            "Category",
            self.t["size_header"],
            self.t["path_header"],
        ])

    def retranslate_ui(self, language: str):
        """Update strings when language changes."""
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["cleaner"])
        self.subtitle_label.setText(self.t["cleaner_subtitle"])
        self.btn_select_all.setText(f"✓ {self.t['select_all']}")
        self.btn_deselect_all.setText(f"✗ {self.t['deselect_all']}")
        self.search_input.setPlaceholderText(self.t["search_placeholder"])
        self.clean_btn.setText(f"🧹 {self.t['clean_selected']}")
        self._update_table_headers()

        # Update category checkboxes text
        cat_labels = {
            CAT_TEMP: self.t["category_temp"],
            CAT_CACHE: self.t["category_cache"],
            CAT_LOGS: self.t["category_logs"],
            CAT_BROWSER_CACHE: self.t["category_browser_cache"],
            CAT_THUMBNAILS: self.t["category_thumbnails"],
            CAT_APP_CACHE: self.t["category_app_cache"],
        }
        for cat_id, cb in self.category_checkboxes.items():
            if cat_id in cat_labels:
                cb.setText(cat_labels[cat_id])

        self._update_selection_metrics()

    def set_scan_result(self, result: ScanResultSet):
        """Populate table and category metrics from scan result."""
        self.current_scan = result

        # Update category summaries
        summaries = result.get_summaries()
        for cat_id, lbl in self.category_labels.items():
            if cat_id in summaries:
                summary = summaries[cat_id]
                lbl.setText(f"{format_number(summary.file_count)} {self.t['files_count'].format(count='')} ({format_bytes(summary.total_size)})")
            else:
                lbl.setText("0 (0 B)")

        # Sync item is_selected with category checkbox initial state
        for item in result.items:
            cb = self.category_checkboxes.get(item.category)
            if cb:
                item.is_selected = cb.isChecked() and not item.is_locked

        self._filter_items()

    def _filter_items(self):
        """Filter table items by search text."""
        if not self.current_scan:
            return

        query = self.search_input.text().strip().lower()
        if not query:
            self.filtered_items = self.current_scan.items[:]
        else:
            self.filtered_items = [
                item for item in self.current_scan.items
                if query in item.filename.lower() or query in str(item.path).lower()
            ]

        self._populate_table()
        self._update_selection_metrics()

    def _populate_table(self):
        """Render items in QTableWidget."""
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.filtered_items))

        for row, item in enumerate(self.filtered_items):
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Checked if item.is_selected else Qt.Unchecked)
            self.table.setItem(row, 0, chk_item)

            name_item = QTableWidgetItem(item.filename)
            name_item.setToolTip(str(item.path))
            if item.is_locked:
                name_item.setForeground(Qt.darkGray)
            self.table.setItem(row, 1, name_item)

            cat_item = QTableWidgetItem(item.category)
            self.table.setItem(row, 2, cat_item)

            size_item = QTableWidgetItem(format_bytes(item.size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, size_item)

            path_item = QTableWidgetItem(str(item.path.parent))
            path_item.setToolTip(str(item.path))
            self.table.setItem(row, 4, path_item)

        self.table.blockSignals(False)

    def _on_table_item_changed(self, item: QTableWidgetItem):
        """Handle individual file checkbox changes."""
        if item.column() == 0 and item.row() < len(self.filtered_items):
            is_checked = (item.checkState() == Qt.Checked)
            self.filtered_items[item.row()].is_selected = is_checked
            self._update_selection_metrics()

    def _on_category_toggled(self):
        """Synchronize category toggle with items."""
        if not self.current_scan:
            return

        for item in self.current_scan.items:
            cb = self.category_checkboxes.get(item.category)
            if cb and not item.is_locked:
                item.is_selected = cb.isChecked()

        self._populate_table()
        self._update_selection_metrics()

    def _set_all_selection(self, selected: bool):
        """Select or deselect all unlocked items."""
        if not self.current_scan:
            return

        for item in self.current_scan.items:
            if not item.is_locked:
                item.is_selected = selected

        for cb in self.category_checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(selected)
            cb.blockSignals(False)

        self._populate_table()
        self._update_selection_metrics()

    def _update_selection_metrics(self):
        """Refresh selected file count and size counters."""
        if not self.current_scan:
            self.lbl_selected_count.setText(f"{self.t['files_selected']}: 0")
            self.lbl_selected_size.setText(f"{self.t['space_to_free']}: 0 B")
            self.clean_btn.setEnabled(False)
            return

        count = self.current_scan.selected_count
        size = self.current_scan.selected_size

        self.lbl_selected_count.setText(f"{self.t['files_selected']}: {format_number(count)}")
        self.lbl_selected_size.setText(f"{self.t['space_to_free']}: {format_bytes(size)}")
        self.clean_btn.setEnabled(count > 0)

    def _on_clean_clicked(self):
        """Trigger cleanup after modal confirmation."""
        if not self.current_scan:
            return

        selected_items = [i for i in self.current_scan.items if i.is_selected]
        if not selected_items:
            return

        dlg = ConfirmationDialog(
            file_count=len(selected_items),
            total_bytes=sum(i.size for i in selected_items),
            title=self.t["confirm_clean_title"],
            message=self.t["confirm_clean_msg"].format(
                count=format_number(len(selected_items)),
                size=format_bytes(sum(i.size for i in selected_items)),
            ),
            parent=self,
        )
        if dlg.exec():
            self.clean_requested.emit(selected_items)

    def set_cleaning_in_progress(self, is_cleaning: bool, total: int = 1):
        """Show/hide cleanup progress bar."""
        self.clean_progress_box.setVisible(is_cleaning)
        self.clean_btn.setEnabled(not is_cleaning)
        if is_cleaning:
            self.clean_bar.setRange(0, max(1, total))
            self.clean_bar.setValue(0)

    def update_clean_progress(self, current: int, total: int, freed_bytes: int, filename: str):
        """Update cleanup progress indicators."""
        self.clean_bar.setValue(current)
        self.clean_status_label.setText(
            f"{self.t['cleaning']} {current} / {total} — Freed: {format_bytes(freed_bytes)} ({filename})"
        )
