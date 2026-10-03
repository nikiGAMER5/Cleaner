"""Custom storage distribution bar chart widget using QPainter."""

from typing import List, Tuple
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from app.utils.formatting import format_bytes


SEGMENT_COLORS = [
    QColor("#3b82f6"),  # Blue
    QColor("#10b981"),  # Emerald
    QColor("#f59e0b"),  # Amber
    QColor("#ec4899"),  # Pink
    QColor("#8b5cf6"),  # Purple
    QColor("#06b6d4"),  # Cyan
    QColor("#64748b"),  # Slate / Other
]


class StorageBarCanvas(QWidget):
    """Custom painting widget for drawing horizontal segmented storage bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments: List[Tuple[str, int, QColor]] = []
        self.total_bytes: int = 1
        self.setFixedHeight(24)

    def set_data(self, segments: List[Tuple[str, int]], total_bytes: int):
        self.total_bytes = max(1, total_bytes)
        colored_segments = []
        for i, (name, size) in enumerate(segments):
            color = SEGMENT_COLORS[i % len(SEGMENT_COLORS)]
            colored_segments.append((name, size, color))
        self.segments = colored_segments
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Background (empty bar)
        bg_brush = QBrush(QColor("#1e2433"))
        painter.setBrush(bg_brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 6, 6)

        if self.total_bytes <= 0 or not self.segments:
            return

        current_x = 0.0
        for name, size, color in self.segments:
            seg_width = (size / self.total_bytes) * width
            if seg_width < 1.0:
                continue

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            # Clip or draw rect
            painter.drawRoundedRect(QRectF(current_x, 0, seg_width, height), 4, 4)
            current_x += seg_width


class StorageChartWidget(QWidget):
    """Container holding the StorageBarCanvas and a modern legend."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(12)

        self.bar = StorageBarCanvas(self)
        self.main_layout.addWidget(self.bar)

        self.legend_layout = QHBoxLayout()
        self.legend_layout.setSpacing(16)
        self.main_layout.addLayout(self.legend_layout)

    def update_data(self, segments: List[Tuple[str, int]], total_bytes: int):
        """Update chart and legend items."""
        self.bar.set_data(segments, total_bytes)

        # Clear old legend
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build legend items
        for i, (name, size) in enumerate(segments[:6]):
            color_hex = SEGMENT_COLORS[i % len(SEGMENT_COLORS)].name()
            pct = (size / max(1, total_bytes)) * 100

            lbl = QLabel(f"<span style='color:{color_hex}; font-size:14px;'>■</span> "
                         f"<b style='color:#e2e8f0;'>{name}</b> "
                         f"<span style='color:#94a3b8;'>({format_bytes(size)}, {pct:.1f}%)</span>")
            lbl.setStyleSheet("font-size: 11px;")
            self.legend_layout.addWidget(lbl)

        self.legend_layout.addStretch()
