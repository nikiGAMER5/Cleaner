"""StatCard widget for displaying summary metrics without visual artifacts."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class StatCard(QFrame):
    """Modern card displaying a single key metric."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        accent_color: str = "#3b82f6",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setProperty("class", "card")
        self.accent_color = accent_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        # Header row: Title + colored dot
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.dot_label = QLabel("●")
        self.dot_label.setStyleSheet(
            f"background: transparent; color: {accent_color}; font-size: 10px;"
        )
        header_layout.addWidget(self.dot_label)
        layout.addLayout(header_layout)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            "background: transparent; color: #ffffff; font-size: 22px; font-weight: 800; margin-top: 2px;"
        )
        layout.addWidget(self.value_label)

        # Subtitle
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(
            "background: transparent; color: #64748b; font-size: 12px; font-weight: 500;"
        )
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str, subtitle: Optional[str] = None):
        """Update value and optionally subtitle."""
        self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)

    def retranslate(self, title: str, subtitle: Optional[str] = None):
        """Update translated title and subtitle labels."""
        self.title_label.setText(title.upper())
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)
