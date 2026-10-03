"""Main entry point for PC Cleaner Windows application."""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.constants import APP_NAME, APP_ORGANIZATION
from app.models.settings import AppSettings
from app.ui.main_window import MainWindow
from app.utils.logging import get_logger, setup_logger


def main():
    """Application initialization and main loop execution."""
    # Initialize logger
    logger = setup_logger()
    logger.info(f"Starting {APP_NAME}...")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)

    # Set Application Icon
    icon_path = PROJECT_ROOT / "assets" / "icons" / "app_icon.ico"
    if not icon_path.exists():
        icon_path = PROJECT_ROOT / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Load persistent settings
    settings = AppSettings.load()

    # Create and display Main Window
    window = MainWindow(settings=settings)

    if settings.start_minimized:
        window.showMinimized()
    else:
        window.show()

    logger.info("Application main window displayed.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
