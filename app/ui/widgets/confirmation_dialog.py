"""Confirmation dialog before executing deletions."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.utils.formatting import format_bytes, format_number


class ConfirmationDialog(QDialog):
    """Custom styled confirmation dialog with deletion metrics."""

    def __init__(
        self,
        file_count: int,
        total_bytes: int,
        title: str = "Are you sure?",
        message: str = "Do you want to permanently remove selected files?",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(440, 240)
        self.setWindowModality(Qt.ApplicationModal)
        self.setStyleSheet("""
            QDialog {
                background-color: #151922;
                border: 1px solid #283042;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        # Header with warning badge
        header_layout = QHBoxLayout()
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 26px;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 700;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        layout.addWidget(msg_label)

        # Metrics banner
        metrics_box = QHBoxLayout()
        metrics_box.setContentsMargins(12, 10, 12, 10)

        count_badge = QLabel(f"<b>Files:</b> {format_number(file_count)}")
        count_badge.setStyleSheet(
            "background-color: #1e2536; color: #f1f5f9; padding: 6px 12px; "
            "border-radius: 6px; font-size: 13px;"
        )
        metrics_box.addWidget(count_badge)

        size_badge = QLabel(f"<b>Space:</b> {format_bytes(total_bytes)}")
        size_badge.setStyleSheet(
            "background-color: #1e2536; color: #ef4444; padding: 6px 12px; "
            "border-radius: 6px; font-size: 13px;"
        )
        metrics_box.addWidget(size_badge)
        metrics_box.addStretch()
        layout.addLayout(metrics_box)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary-btn")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Clean Files")
        confirm_btn.setProperty("class", "danger-btn")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)
