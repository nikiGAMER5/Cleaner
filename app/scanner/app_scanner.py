"""Windows Installed Application Analyzer using winreg."""

from dataclasses import dataclass
import os
import subprocess
from typing import List, Optional
import winreg

from app.utils.logging import get_logger


@dataclass
class InstalledApp:
    name: str
    publisher: str
    version: str
    size_bytes: int
    install_date: str
    uninstall_string: str
    quiet_uninstall_string: str
    install_location: str


class AppScanner:
    """Reads installed applications from the Windows Registry."""

    REGISTRY_KEYS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    def __init__(self):
        self.logger = get_logger()

    def get_installed_apps(self) -> List[InstalledApp]:
        """Query registry uninstall keys and return a deduplicated list of installed applications."""
        apps_dict = {}

        for hkey, subkey_path in self.REGISTRY_KEYS:
            try:
                with winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            app_sub_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_sub_name) as app_key:
                                app = self._parse_app_key(app_key)
                                if app and app.name:
                                    # Deduplicate by app name
                                    if app.name not in apps_dict:
                                        apps_dict[app.name] = app
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        apps_list = list(apps_dict.values())
        apps_list.sort(key=lambda a: a.name.lower())
        return apps_list

    def _parse_app_key(self, app_key) -> Optional[InstalledApp]:
        """Extract properties from an uninstall registry key."""
        try:
            # Check SystemComponent (skip internal windows updates/components)
            try:
                system_component, _ = winreg.QueryValueEx(app_key, "SystemComponent")
                if system_component == 1:
                    return None
            except OSError:
                pass

            # Name
            name = ""
            for val_name in ["DisplayName", "QuietDisplayName"]:
                try:
                    name, _ = winreg.QueryValueEx(app_key, val_name)
                    if name:
                        break
                except OSError:
                    pass

            if not name or not str(name).strip():
                return None

            name = str(name).strip()

            # Skip Windows updates (KB...)
            if name.startswith("KB") and len(name.split()[0]) > 6:
                return None

            # Publisher
            publisher = ""
            try:
                publisher, _ = winreg.QueryValueEx(app_key, "Publisher")
                publisher = str(publisher).strip()
            except OSError:
                pass

            # Version
            version = ""
            try:
                version, _ = winreg.QueryValueEx(app_key, "DisplayVersion")
                version = str(version).strip()
            except OSError:
                pass

            # Estimated Size (stored in KB in Windows Registry)
            size_bytes = 0
            try:
                size_kb, _ = winreg.QueryValueEx(app_key, "EstimatedSize")
                if isinstance(size_kb, int):
                    size_bytes = size_kb * 1024
            except OSError:
                pass

            # Install Date
            install_date = ""
            try:
                install_date, _ = winreg.QueryValueEx(app_key, "InstallDate")
                install_date = str(install_date).strip()
            except OSError:
                pass

            # Uninstall string
            uninstall_str = ""
            try:
                uninstall_str, _ = winreg.QueryValueEx(app_key, "UninstallString")
                uninstall_str = str(uninstall_str).strip()
            except OSError:
                pass

            quiet_uninstall_str = ""
            try:
                quiet_uninstall_str, _ = winreg.QueryValueEx(app_key, "QuietUninstallString")
                quiet_uninstall_str = str(quiet_uninstall_str).strip()
            except OSError:
                pass

            install_loc = ""
            try:
                install_loc, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                install_loc = str(install_loc).strip()
            except OSError:
                pass

            return InstalledApp(
                name=name,
                publisher=publisher,
                version=version,
                size_bytes=size_bytes,
                install_date=install_date,
                uninstall_string=uninstall_str,
                quiet_uninstall_string=quiet_uninstall_str,
                install_location=install_loc,
            )
        except Exception:
            return None

    def launch_uninstaller(self, app: InstalledApp) -> bool:
        """
        Executes the official uninstaller provided by the application vendor.
        Never deletes program files directly!
        """
        cmd = app.uninstall_string
        if not cmd:
            return False

        try:
            self.logger.info(f"Launching official uninstaller for {app.name}: {cmd}")
            # Launch uninstaller process independently
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch uninstaller for {app.name}: {e}")
            return False
