"""Settings configuration page with dynamic language and theme switching."""

from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
from app.models.settings import AppSettings


class SettingsPage(QWidget):
    """User preferences and configuration view."""

    settings_changed = Signal(AppSettings)
    language_changed = Signal(str)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.language = settings.language
        self.t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        self.title_label = QLabel(self.t["settings"])
        self.title_label.setStyleSheet("background: transparent; color: #ffffff; font-size: 26px; font-weight: 800;")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.t["settings_subtitle"])
        self.subtitle_label.setStyleSheet("background: transparent; color: #64748b; font-size: 13px; font-weight: 500;")
        title_box.addWidget(self.subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_save = QPushButton(f"💾 {self.t['save_settings']}")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setProperty("class", "primary-btn")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_settings)
        header_layout.addWidget(self.btn_save)

        layout.addLayout(header_layout)

        # 2. General Settings Card
        gen_card = QFrame()
        gen_card.setObjectName("card")
        gen_card.setProperty("class", "card")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(18, 16, 18, 16)
        gen_layout.setSpacing(12)

        self.lbl_gen_title = QLabel(self.t["settings_general"])
        self.lbl_gen_title.setStyleSheet("background: transparent; color: #f1f5f9; font-size: 15px; font-weight: 700;")
        gen_layout.addWidget(self.lbl_gen_title)

        self.cb_confirm = QCheckBox(self.t["confirm_before_clean"])
        self.cb_confirm.setChecked(self.settings.confirm_before_clean)
        gen_layout.addWidget(self.cb_confirm)

        self.cb_startup_scan = QCheckBox(self.t["run_on_startup"])
        self.cb_startup_scan.setChecked(self.settings.run_on_startup)
        gen_layout.addWidget(self.cb_startup_scan)

        self.cb_minimized = QCheckBox(self.t["start_minimized"])
        self.cb_minimized.setChecked(self.settings.start_minimized)
        gen_layout.addWidget(self.cb_minimized)

        layout.addWidget(gen_card)

        # 3. Cleaning Defaults Card
        clean_card = QFrame()
        clean_card.setObjectName("card")
        clean_card.setProperty("class", "card")
        clean_layout = QVBoxLayout(clean_card)
        clean_layout.setContentsMargins(18, 16, 18, 16)
        clean_layout.setSpacing(12)

        self.lbl_clean_title = QLabel(self.t["settings_cleaning"])
        self.lbl_clean_title.setStyleSheet("background: transparent; color: #f1f5f9; font-size: 15px; font-weight: 700;")
        clean_layout.addWidget(self.lbl_clean_title)

        self.category_checkboxes: Dict[str, QCheckBox] = {}
        categories = [
            (CAT_TEMP, self.t["category_temp"]),
            (CAT_CACHE, self.t["category_cache"]),
            (CAT_LOGS, self.t["category_logs"]),
            (CAT_THUMBNAILS, self.t["category_thumbnails"]),
            (CAT_BROWSER_CACHE, self.t["category_browser_cache"]),
            (CAT_APP_CACHE, self.t["category_app_cache"]),
        ]

        for cat_id, cat_name in categories:
            cb = QCheckBox(cat_name)
            cb.setChecked(cat_id in self.settings.enabled_categories)
            self.category_checkboxes[cat_id] = cb
            clean_layout.addWidget(cb)

        layout.addWidget(clean_card)

        # 4. Appearance & Language Card
        ui_card = QFrame()
        ui_card.setObjectName("card")
        ui_card.setProperty("class", "card")
        ui_layout = QVBoxLayout(ui_card)
        ui_layout.setContentsMargins(18, 16, 18, 16)
        ui_layout.setSpacing(14)

        self.lbl_app_title = QLabel(f"{self.t['settings_appearance']} & {self.t['settings_language']}")
        self.lbl_app_title.setStyleSheet("background: transparent; color: #f1f5f9; font-size: 15px; font-weight: 700;")
        ui_layout.addWidget(self.lbl_app_title)

        theme_row = QHBoxLayout()
        self.lbl_theme = QLabel(self.t["theme_label"])
        self.lbl_theme.setStyleSheet("background: transparent; color: #94a3b8; font-weight: 600; min-width: 90px;")
        theme_row.addWidget(self.lbl_theme)

        self.combo_theme = QComboBox()
        self.combo_theme.addItem(self.t["theme_dark"], "dark")
        self.combo_theme.addItem(self.t["theme_light"], "light")
        if self.settings.theme == "light":
            self.combo_theme.setCurrentIndex(1)
        else:
            self.combo_theme.setCurrentIndex(0)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.combo_theme)
        theme_row.addStretch()
        ui_layout.addLayout(theme_row)

        lang_row = QHBoxLayout()
        self.lbl_lang = QLabel(self.t["language_label"])
        self.lbl_lang.setStyleSheet("background: transparent; color: #94a3b8; font-weight: 600; min-width: 90px;")
        lang_row.addWidget(self.lbl_lang)

        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Deutsch", "de")
        self.combo_lang.addItem("English", "en")
        if self.settings.language == "en":
            self.combo_lang.setCurrentIndex(1)
        else:
            self.combo_lang.setCurrentIndex(0)
        self.combo_lang.currentIndexChanged.connect(self._on_language_selection_changed)
        lang_row.addWidget(self.combo_lang)
        lang_row.addStretch()
        ui_layout.addLayout(lang_row)

        layout.addWidget(ui_card)

        # Status feedback label
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setStyleSheet("background: transparent; color: #10b981; font-weight: 600; font-size: 13px;")
        layout.addWidget(self.lbl_feedback)

        layout.addStretch()

    def _on_language_selection_changed(self):
        new_lang = self.combo_lang.currentData()
        if new_lang != self.settings.language:
            self.settings.language = new_lang
            self.language = new_lang
            self.t = TRANSLATIONS.get(new_lang, TRANSLATIONS["en"])
            self.retranslate_ui(new_lang)
            self.language_changed.emit(new_lang)

    def _on_theme_changed(self):
        new_theme = self.combo_theme.currentData()
        if new_theme != self.settings.theme:
            self.settings.theme = new_theme
            self.settings_changed.emit(self.settings)

    def retranslate_ui(self, language: str):
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["en"])

        self.title_label.setText(self.t["settings"])
        self.subtitle_label.setText(self.t["settings_subtitle"])
        self.btn_save.setText(f"💾 {self.t['save_settings']}")
        self.lbl_gen_title.setText(self.t["settings_general"])
        self.cb_confirm.setText(self.t["confirm_before_clean"])
        self.cb_startup_scan.setText(self.t["run_on_startup"])
        self.cb_minimized.setText(self.t["start_minimized"])
        self.lbl_clean_title.setText(self.t["settings_cleaning"])
        self.lbl_app_title.setText(f"{self.t['settings_appearance']} & {self.t['settings_language']}")
        self.lbl_theme.setText(self.t["theme_label"])
        self.lbl_lang.setText(self.t["language_label"])

        # Update combobox labels
        self.combo_theme.blockSignals(True)
        cur_theme = self.combo_theme.currentData()
        self.combo_theme.clear()
        self.combo_theme.addItem(self.t["theme_dark"], "dark")
        self.combo_theme.addItem(self.t["theme_light"], "light")
        idx = 1 if cur_theme == "light" else 0
        self.combo_theme.setCurrentIndex(idx)
        self.combo_theme.blockSignals(False)

        # Update category checkboxes
        cat_labels = {
            CAT_TEMP: self.t["category_temp"],
            CAT_CACHE: self.t["category_cache"],
            CAT_LOGS: self.t["category_logs"],
            CAT_THUMBNAILS: self.t["category_thumbnails"],
            CAT_BROWSER_CACHE: self.t["category_browser_cache"],
            CAT_APP_CACHE: self.t["category_app_cache"],
        }
        for cat_id, cb in self.category_checkboxes.items():
            if cat_id in cat_labels:
                cb.setText(cat_labels[cat_id])

    def _save_settings(self):
        self.settings.confirm_before_clean = self.cb_confirm.isChecked()
        self.settings.run_on_startup = self.cb_startup_scan.isChecked()
        self.settings.start_minimized = self.cb_minimized.isChecked()

        self.settings.enabled_categories = [
            cat_id for cat_id, cb in self.category_checkboxes.items() if cb.isChecked()
        ]

        self.settings.theme = self.combo_theme.currentData()
        self.settings.language = self.combo_lang.currentData()

        if self.settings.save():
            self.lbl_feedback.setText(f"✓ {self.t['settings_saved']}")
            self.settings_changed.emit(self.settings)
        else:
            self.lbl_feedback.setText("Error writing settings.")
