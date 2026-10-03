# PC Cleaner

[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20%28Qt6%29-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6.svg)](https://microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**PC Cleaner** ist eine moderne, professionelle Windows-Desktop-Anwendung zur sicheren Speicherplatzanalyse und Systemoptimierung. Entwickelt mit **Python 3.12+** und **PySide6 (Qt6)**, bietet das Tool eine elegante Benutzeroberfläche im modernen Dark Mode, reaktionsschnelle Hintergrund-Threads und ein mehrstufiges Sicherheitskonzept.


---

## 📸 Screenshots & UI Preview

```text
----------------------------------------------------------------------------------------------------
  🛡️ PC Cleaner                                                          ⚙️ Settings   v1.0.0
----------------------------------------------------------------------------------------------------
  [🏠 Dashboard]     💾 Storage Overview (C:\)
  [🧹 Cleaner]        ████████████████████████░░░░░░░░░░░░░░  412.5 GB / 512.0 GB   (99.5 GB Free)
  [📦 Large Files]   -------------------------------------------------------------------------------
  [📱 Apps]           POTENTIAL CLEANUP
  [📊 Storage]             2.84 GB               [ ⚡ Scan PC ]       [ 👁 Review Files ]
  [🗂️ Duplicates]    -------------------------------------------------------------------------------
  [📜 History]        Key Metrics
  [⚙️ Settings]       ● Last Scan: 03.10.2026 17:45  ● Files: 1,842   ● Temp: 1.42 GB  ● Cache: 820 MB
----------------------------------------------------------------------------------------------------
```

---

## ✨ Features

- **🏠 Modernes Dashboard**:
  - Live-Anzeige des Speicherplatzes (Gesamt, Belegt, Frei) mit visueller Fortschrittsanzeige.
  - 1-Klick-System-Scan mit sofortiger Berechnung des freizugebenden Speichers.
  - Direkte Anzeige und sicheres Leeren des Windows-Papierkorbs über die native Windows Shell API.
- **🧹 Intelligenter System-Cleaner**:
  - Kategorisierte Erkennung:
    - **Temporäre Dateien**: `%TEMP%`, `%WINDIR%\Temp`
    - **System- und App-Caches**: `%LOCALAPPDATA%\CrashDumps`, DirectX Shader Cache (`D3DSCache`), Discord, Spotify, Steam
    - **Log-Dateien**: Windows Error Reporting (`WER`), temporäre Log-Dateien
    - **Thumbnails**: Explorer Thumbnail- & Icon-Caches (`thumbcache_*.db`)
    - **Browser-Caches**: Chrome, Edge, Firefox, Brave, Opera (isoliert auf Web-Cache – keine Passwörter, Cookies oder Login-Daten!)
  - Vollständige Dateivorschau mit Filterung und Checkboxen vor dem Löschen.
- **📦 Große Dateien (Large Files)**:
  - Findet speicherintensive Dateien filterbar nach Schwellenwerten (`> 100 MB`, `> 500 MB`, `> 1 GB`, `> 5 GB`).
  - Sortierung nach Größe (größte zuerst).
  - Kontextmenü mit „Im Explorer anzeigen“.
  - **Sicherheitsgarantie**: Große Dateien werden **niemals automatisch ausgewählt oder gelöscht**.
- **📱 App- & Programm-Analyzer**:
  - Liest installierte Windows-Anwendungen aus der Registry aus (`HKLM` und `HKCU`).
  - Zeigt Name, Herausgeber, Version und geschätzte Größe.
  - Startet den offiziellen Windows-Deinstaller der Anwendung – keine willkürliche manuelle Ordnerlöschung!
- **📊 Storage Analyzer (Speicherverteilung)**:
  - Interaktives Segment-Diagramm zur Verteilung des belegten Speichers.
  - Detaillierte Ordneranalyse der obersten Verzeichnisse auf jedem angeschlossenen Laufwerk (C:\, D:\ usw.).
- **🗂️ Duplikat-Finder (Duplicate Files)**:
  - Findet inhaltsgleiche Dateien mittels zweistufigem Verfahren (Dateigrößen-Vorfilterung + SHA-256 Hash).
  - Keine automatische Löschung – der Benutzer behält volle Kontrolle.
- **📜 Scan-Historie**:
  - Lokale SQLite-Datenbank (`history.db`) mit Audit-Trail (Datum, Scan-Dauer, gefundene Dateien, bereinigter Speicher).
  - Speichert garantiert keine Dateiinhalte oder persönlichen Daten.
- **⚙️ Benutzerdefinierte Einstellungen & Themes**:
  - Dunkles Design (Dark Mode) und helles Design (Light Mode).
  - Mehrsprachig: **Deutsch** und **Englisch**.
  - Anpassbare Standardkategorien und Bestätigungsdialoge.

---

## 🛡️ Sicherheit & Schutzmechanismen (Safety First)

PC Cleaner ist ein **präzises Werkzeug** und kein destruktives Löschprogramm. Jede Datei durchläuft vor der Löschung die `SafetyValidator`-Engine:

1. **Pfadexistenzprüfung**: Prüft, ob die Datei tatsächlich existiert.
2. **Kanonische Pfadauflösung**: Verhindert Path Traversal (`../`, relative Pfadmanipulationen).
3. **Strikte Whitelist-Prüfung**: Dateien dürfen ausschließlich innerhalb explizit autorisierter temporärer Verzeichnisse liegen.
4. **Symlink- & Directory Junction-Schutz**: Verhindert das Ausbrechen aus sicheren Pfaden über symbolische Verknüpfungen oder Windows Reparse Points.
5. **Systempfad-Sperre**: Verhindert strikt den Zugriff auf:
   - `C:\Windows`, `C:\Windows\System32`, `SysWOW64`, `WinSxS`, `Boot`
   - `pagefile.sys`, `hiberfil.sys`, `swapfile.sys`, `bootmgr`
6. **Schutz persönlicher Dateien**: Persönliche Verzeichnisse (`Desktop`, `Dokumente`, `Bilder`, `Videos`, `Downloads`, `OneDrive`) sind im automatischen Cleaner gesperrt.
7. **Schutz sensibler Daten**: Browser-Profile, Cookies, Passwörter, Authentifizierungs-Tokens und Zertifikate (`.key`, `.pem`, `tokens.json`) werden niemals angetastet.
8. **Erkennung geöffneter Dateien**: Gerade verwendete Dateien (`WinError 32: Sharing Violation`) werden sicher übersprungen.
9. **Fehlertoleranz**: Berechtigungsfehler (`Access Denied`) führen niemals zum Absturz der Anwendung.

---

## 🏗️ Architektur

Das Projekt folgt einer modularen, wartbaren Architektur mit Trennung von UI, Business-Logik und Datenmodellen:

```text
pc-cleaner/
│
├── app/
│   ├── config/
│   │   └── constants.py          # Konstanten, Schwellenwerte, Systempfade, Übersetzungen
│   │
│   ├── models/
│   │   ├── file_item.py          # Datenmodelle FileItem & CleanResult
│   │   ├── scan_result.py        # ScanResultSet & CategorySummary
│   │   ├── settings.py           # AppSettings mit JSON-Persistenz
│   │   └── history.py            # SQLite HistoryManager
│   │
│   ├── utils/
│   │   ├── paths.py              # Pfadauflösung, Subpfadprüfung & Symlink-Erkennung
│   │   ├── permissions.py        # Dateisperr- und Berechtigungsprüfungen
│   │   ├── formatting.py         # Formatierung (Bytes, Zahlen, Datumsangaben)
│   │   └── logging.py            # Rotierendes lokales Application-Log
│   │
│   ├── cleaner/
│   │   ├── safety.py             # Mehrstufige Sicherheitsprüfung (SafetyValidator)
│   │   ├── cleaner.py            # SystemCleaner Engine mit Abbruch- & Fortschrittslogik
│   │   └── recycle_bin.py        # Native Windows Shell32 API Integration
│   │
│   ├── scanner/
│   │   ├── scanner.py            # Orchestrator (SystemScanner)
│   │   ├── temp_scanner.py       # Schneller os.scandir Scanner für %TEMP%
│   │   ├── cache_scanner.py      # Scanner für System-, App- & Browser-Caches
│   │   ├── large_file_scanner.py # Filter-Scanner für große Dateien
│   │   ├── storage_scanner.py    # psutil Speicher- und Verzeichnisanalyse
│   │   ├── app_scanner.py        # Windows Registry Scanner für installierte Apps
│   │   └── duplicate_scanner.py  # SHA-256 Hash-Scanner für Duplikate
│   │
│   └── ui/
│       ├── styles.py             # Moderne Dark- & Light-QSS-Stylesheets
│       ├── widgets/
│       │   ├── stat_card.py      # KPI-Metrikkarten
│       │   ├── storage_chart.py  # Segmentierter Speicherbalken & Legende
│       │   └── confirmation_dialog.py # Lösch-Bestätigungsdialog
│       ├── main_window.py        # Hauptfenster mit Sidebar & Worker-Threads (QThread)
│       ├── dashboard.py          # Dashboard-Ansicht
│       ├── cleaner_page.py       # Detaillierte Bereinigungsansicht
│       ├── large_files_page.py   # Große-Dateien-Verwaltung
│       ├── apps_page.py          # Deinstallationsmanager
│       ├── storage_page.py       # Speicherplatz-Visualisierung
│       ├── duplicates_page.py    # Duplikate-Manager
│       ├── history_page.py       # SQLite Scan-Historie
│       └── settings_page.py      # Konfiguration & Design
│
├── tests/                        # 21 automatisierte Pytest-Unittests
├── assets/icons/                 # 256x256 ICO & PNG Icons
├── main.py                       # Anwendungsstart mit High-DPI Support
├── requirements.txt              # Python-Abhängigkeiten
├── build.bat / build.ps1         # Standalone Windows PyInstaller Build-Skripte
├── LICENSE                       # MIT Lizenz
├── CONTRIBUTING.md               # Mitwirkungsrichtlinien
└── CHANGELOG.md                  # Versionsverlauf
```

---

## 🚀 Installation & Start (Development)

### Voraussetzungen

- Windows 10 oder Windows 11
- Python 3.12 oder neuer

### 1. Repository klonen & Abhängigkeiten installieren

```powershell
cd "c:\Users`\Documents\ai\windows cleaner"
python -m pip install -r requirements.txt
```

### 2. Anwendung starten

```powershell
python main.py
```

---

## 🧪 Tests ausführen

Das Testpaket deckt Pfadsicherheit, Path Traversal, Berechtigungen, Formatierung, Scanner, Cleaner-Regeln und SQLite-Persistenz ab:

```powershell
pytest -v
```

Beispielausgabe:
```text
============================= test session starts =============================
collected 21 items

tests/test_cleaner.py::test_cleaner_deletes_valid_file PASSED            [  4%]
tests/test_cleaner.py::test_cleaner_refuses_system_file PASSED           [  9%]
tests/test_formatting.py::test_format_bytes PASSED                       [ 14%]
tests/test_formatting.py::test_format_number PASSED                      [ 19%]
tests/test_formatting.py::test_format_duration PASSED                    [ 23%]
tests/test_permissions.py::test_is_symlink_or_junction_regular_file PASSED [ 28%]
tests/test_permissions.py::test_can_delete_file_non_existent PASSED      [ 33%]
tests/test_permissions.py::test_can_delete_file_valid PASSED             [ 38%]
tests/test_safety.py::test_is_safe_subpath_valid PASSED                  [ 42%]
tests/test_safety.py::test_is_safe_subpath_traversal PASSED              [ 47%]
tests/test_safety.py::test_safety_validator_rejects_system_path PASSED   [ 52%]
tests/test_safety.py::test_safety_validator_rejects_personal_files PASSED [ 57%]
tests/test_safety.py::test_safety_validator_rejects_credentials PASSED   [ 61%]
tests/test_safety.py::test_safety_validator_allows_valid_temp_file PASSED [ 66%]
tests/test_safety.py::test_safety_validator_rejects_unwhitelisted_file PASSED [ 71%]
tests/test_scanner.py::test_temp_scanner_with_tmp_dir PASSED             [ 76%]
tests/test_scanner.py::test_large_file_scanner PASSED                    [ 80%]
tests/test_scanner.py::test_duplicate_scanner PASSED                     [ 85%]
tests/test_settings.py::test_settings_defaults PASSED                    [ 90%]
tests/test_settings.py::test_settings_save_and_load PASSED               [ 95%]
tests/test_settings.py::test_history_manager PASSED                      [100%]

============================= 21 passed in 0.19s ==============================
```

---

## 📦 Build: Windows EXE erstellen

Zur Erstellung einer eigenständigen Windows `.exe`-Datei (ohne dass der Endbenutzer Python installieren muss):

### Mit PowerShell:
```powershell
.\build.ps1
```

### Oder per Batch:
```cmd
build.bat
```

Die fertige ausführbare Datei befindet sich anschließend in:
`dist\PC Cleaner\PC Cleaner.exe`

---

## ⚠️ Disclaimer (Wichtiger Hinweis)

> [!WARNING]
> **PC Cleaner** dient dem Bereinigen temporärer Dateien, Caches und der Systemoptimierung. Obwohl die integrierte `SafetyValidator`-Engine rigoros verhindert, dass wichtige System-, Betriebssystem- oder persönliche Benutzerdateien angetastet werden, sollten Sie vor jedem Bereinigungsvorgang prüfen, welche Kategorien ausgewählt sind. Dateien, die im Bereich *Große Dateien* oder *Duplikate* gelöscht werden, können nicht wiederhergestellt werden.

---

## 📄 Lizenz

Dieses Projekt ist unter der **MIT-Lizenz** lizenziert. Weitere Details finden Sie in der [LICENSE](LICENSE)-Datei.
