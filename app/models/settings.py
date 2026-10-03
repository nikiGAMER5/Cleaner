"""Application settings and configuration manager."""

import json
import os
from pathlib import Path
from dataclasses import asdict, dataclass, field
from typing import List
from app.config.constants import (
    CAT_CACHE,
    CAT_LOGS,
    CAT_TEMP,
    CAT_THUMBNAILS,
)


@dataclass
class AppSettings:
    """Settings data structure with default values."""
    # General
    confirm_before_clean: bool = True
    start_minimized: bool = False
    run_on_startup: bool = False

    # Default cleaning categories selected
    enabled_categories: List[str] = field(
        default_factory=lambda: [CAT_TEMP, CAT_CACHE, CAT_LOGS]
    )

    # Appearance
    theme: str = "dark"  # "dark", "light", "system"

    # Language
    language: str = "de"  # "de" or "en"

    # Large Files threshold
    large_file_threshold_mb: int = 100

    @classmethod
    def get_settings_file(cls) -> Path:
        """Locate user settings file in AppData or local folder."""
        app_data = os.environ.get("LOCALAPPDATA")
        if app_data:
            settings_dir = Path(app_data) / "PCCleaner"
        else:
            settings_dir = Path.home() / ".pccleaner"
        try:
            settings_dir.mkdir(parents=True, exist_ok=True)
            return settings_dir / "settings.json"
        except Exception:
            return Path("settings.json")

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from disk or return defaults if missing/corrupt."""
        file_path = cls.get_settings_file()
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self) -> bool:
        """Persist current settings to disk."""
        file_path = self.get_settings_file()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
