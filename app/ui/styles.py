"""Modern, refined Dark and Light Theme stylesheets for PySide6 with high-visibility buttons and cards."""

DARK_THEME = """
/* Global Settings - No background on generic QWidget to prevent nested black box bugs */
QWidget {
    color: #e2e8f0;
    font-family: "Segoe UI", "Segoe UI Variable Display", -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

/* Background applied strictly to container windows and main views */
QMainWindow, QDialog, #contentArea {
    background-color: #0b0e14;
}

/* Scoped scroll area styles - never cascade plain background/border onto children */
QScrollArea {
    background-color: transparent;
    border: none;
}

#scrollWidget {
    background-color: transparent;
}

/* All labels are transparent by default */
QLabel {
    background: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}

/* Generic frames default to transparent */
QFrame {
    background: transparent;
    border: none;
}

/* Sidebar Navigation */
#sidebar {
    background-color: #121620;
    border-right: 1px solid #1f2637;
    min-width: 220px;
    max-width: 220px;
}

#logoLabel {
    color: #ffffff;
    font-size: 18px;
    font-weight: 800;
    padding: 18px 14px 2px 14px;
    background: transparent;
}

#logoSubtitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 16px;
    padding-left: 14px;
    background: transparent;
}

/* Navigation Buttons - distinct button shape & outline */
QPushButton[class="nav-btn"],
QPushButton.nav-btn,
QPushButton#navBtn {
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1.5px solid #1f283a;
    background-color: #151a26;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
    margin: 3px 8px;
}

QPushButton[class="nav-btn"]:hover,
QPushButton.nav-btn:hover,
QPushButton#navBtn:hover {
    background-color: #1e2638;
    border: 1.5px solid #3b82f6;
    color: #ffffff;
}

QPushButton[class="nav-btn"]:checked,
QPushButton.nav-btn:checked,
QPushButton#navBtn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    border: 1.5px solid #60a5fa;
    color: #ffffff;
    font-weight: 700;
}

/* ========================================================
   MODERN CARD CONTAINERS: Elevated, crisp borders & dark fill
   ======================================================== */
QFrame[class="card"],
QFrame.card,
QFrame#card,
StatCard,
#statCard {
    background-color: #141824;
    border: 1.5px solid #222a3d;
    border-radius: 12px;
}

QFrame[class="card"]:hover,
QFrame.card:hover,
QFrame#card:hover,
StatCard:hover {
    border: 1.5px solid #33405c;
}

/* ========================================================
   BUTTONS: Clear, High-Contrast & Instantly Recognizable
   ======================================================== */

/* Generic QPushButton fallback */
QPushButton {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    background-color: #1e2638;
    color: #f1f5f9;
    border: 2px solid #3b82f6;
}

QPushButton:hover {
    background-color: #2a364f;
    border-color: #60a5fa;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #151b27;
    border-color: #2563eb;
}

QPushButton:disabled {
    background-color: #151a24;
    border: 1.5px solid #222b3b;
    color: #475569;
}

/* Primary Action Buttons (Scan, Analyze, Save) */
QPushButton[class="primary-btn"],
QPushButton.primary-btn,
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #1d4ed8);
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 10px 22px;
    border: 2px solid #60a5fa;
}

QPushButton[class="primary-btn"]:hover,
QPushButton.primary-btn:hover,
QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60a5fa, stop:1 #2563eb);
    border: 2px solid #bfdbfe;
    color: #ffffff;
}

QPushButton[class="primary-btn"]:pressed,
QPushButton.primary-btn:pressed,
QPushButton#primaryBtn:pressed {
    background: #1e40af;
    border: 2px solid #3b82f6;
}

QPushButton[class="primary-btn"]:disabled,
QPushButton.primary-btn:disabled,
QPushButton#primaryBtn:disabled {
    background-color: #1c2436;
    border: 1.5px solid #2b364d;
    color: #586782;
}

/* Secondary Buttons (Review, Select All, Open in Explorer) */
QPushButton[class="secondary-btn"],
QPushButton.secondary-btn,
QPushButton#secondaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #232c40, stop:1 #182030);
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 18px;
    border: 2px solid #3b82f6;
}

QPushButton[class="secondary-btn"]:hover,
QPushButton.secondary-btn:hover,
QPushButton#secondaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2c3850, stop:1 #202b3f);
    border: 2px solid #60a5fa;
    color: #ffffff;
}

QPushButton[class="secondary-btn"]:pressed,
QPushButton.secondary-btn:pressed,
QPushButton#secondaryBtn:pressed {
    background: #141a26;
    border: 2px solid #2563eb;
}

QPushButton[class="secondary-btn"]:disabled,
QPushButton.secondary-btn:disabled,
QPushButton#secondaryBtn:disabled {
    background-color: #141824;
    border: 1.5px solid #232b3c;
    color: #4b5563;
}

/* Danger / Clean Buttons (Clean Selected, Empty Bin, Delete) */
QPushButton[class="danger-btn"],
QPushButton.danger-btn,
QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #b91c1c);
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 20px;
    border: 2px solid #f87171;
}

QPushButton[class="danger-btn"]:hover,
QPushButton.danger-btn:hover,
QPushButton#dangerBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f87171, stop:1 #dc2626);
    border: 2px solid #fca5a5;
    color: #ffffff;
}

QPushButton[class="danger-btn"]:pressed,
QPushButton.danger-btn:pressed,
QPushButton#dangerBtn:pressed {
    background: #991b1b;
    border: 2px solid #dc2626;
}

QPushButton[class="danger-btn"]:disabled,
QPushButton.danger-btn:disabled,
QPushButton#dangerBtn:disabled {
    background-color: #25181b;
    border: 1.5px solid #3d2329;
    color: #6e444b;
}

/* Success Buttons */
QPushButton[class="success-btn"],
QPushButton.success-btn,
QPushButton#successBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669);
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 20px;
    border: 2px solid #34d399;
}

QPushButton[class="success-btn"]:hover,
QPushButton.success-btn:hover,
QPushButton#successBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34d399, stop:1 #10b981);
    border: 2px solid #6ee7b7;
}

/* Tables and Tree Views */
QTableWidget, QTreeWidget {
    background-color: #10141e;
    border: 1.5px solid #1f2738;
    border-radius: 8px;
    gridline-color: #171d2b;
    color: #cbd5e1;
    outline: none;
}

QHeaderView::section {
    background-color: #141926;
    color: #94a3b8;
    padding: 9px 12px;
    border: none;
    border-bottom: 1.5px solid #20283a;
    font-weight: 700;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #151a27;
}

QTableWidget::item:selected, QTreeWidget::item:selected {
    background-color: #1a2a47;
    color: #93c5fd;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
    font-size: 13px;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid #475569;
    background-color: #131824;
}

QCheckBox::indicator:hover {
    border-color: #3b82f6;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #60a5fa;
}

/* Progress Bar */
QProgressBar {
    border: none;
    border-radius: 5px;
    background-color: #181e2b;
    text-align: center;
    color: #f1f5f9;
    font-size: 10px;
    font-weight: 700;
    height: 10px;
}

QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0b0e14;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #242c3f;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #37435f;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Text Inputs & Comboboxes */
QLineEdit, QComboBox {
    background-color: #131824;
    border: 1.5px solid #28334a;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f1f5f9;
}

QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #131824;
    border: 1.5px solid #28334a;
    color: #e2e8f0;
    selection-background-color: #2563eb;
}
"""

LIGHT_THEME = """
QWidget {
    color: #1e293b;
    font-family: "Segoe UI", -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QMainWindow, QDialog, #contentArea {
    background-color: #f8fafc;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

#scrollWidget {
    background-color: transparent;
}

QLabel {
    background: transparent;
    border: none;
}

QFrame {
    background: transparent;
    border: none;
}

#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
    min-width: 220px;
    max-width: 220px;
}

#logoLabel {
    color: #0f172a;
    font-size: 18px;
    font-weight: 800;
    padding: 18px 14px 2px 14px;
}

#logoSubtitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 16px;
    padding-left: 14px;
}

QPushButton[class="nav-btn"],
QPushButton.nav-btn,
QPushButton#navBtn {
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1.5px solid #e2e8f0;
    background-color: #f8fafc;
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
    margin: 3px 8px;
}

QPushButton[class="nav-btn"]:hover,
QPushButton.nav-btn:hover,
QPushButton#navBtn:hover {
    background-color: #f1f5f9;
    border: 1.5px solid #cbd5e1;
    color: #0f172a;
}

QPushButton[class="nav-btn"]:checked,
QPushButton.nav-btn:checked,
QPushButton#navBtn:checked {
    background: #2563eb;
    border: 1.5px solid #1d4ed8;
    color: #ffffff;
    font-weight: 700;
}

QFrame[class="card"],
QFrame.card,
QFrame#card,
StatCard,
#statCard {
    background-color: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
}

QFrame[class="card"]:hover,
QFrame.card:hover,
QFrame#card:hover,
StatCard:hover {
    border: 1.5px solid #cbd5e1;
}

QPushButton {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    background-color: #ffffff;
    color: #1e293b;
    border: 2px solid #cbd5e1;
}

QPushButton[class="primary-btn"],
QPushButton.primary-btn,
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 10px 22px;
    border: 2px solid #2563eb;
}

QPushButton[class="primary-btn"]:hover,
QPushButton.primary-btn:hover,
QPushButton#primaryBtn:hover {
    background: #1d4ed8;
    border-color: #1e40af;
}

QPushButton[class="secondary-btn"],
QPushButton.secondary-btn,
QPushButton#secondaryBtn {
    background: #ffffff;
    color: #1e293b;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 18px;
    border: 2px solid #3b82f6;
}

QPushButton[class="secondary-btn"]:hover,
QPushButton.secondary-btn:hover,
QPushButton#secondaryBtn:hover {
    background: #eff6ff;
    border-color: #2563eb;
}

QPushButton[class="danger-btn"],
QPushButton.danger-btn,
QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #dc2626);
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 20px;
    border: 2px solid #dc2626;
}

QPushButton[class="danger-btn"]:hover,
QPushButton.danger-btn:hover,
QPushButton#dangerBtn:hover {
    background: #b91c1c;
}

QTableWidget, QTreeWidget {
    background-color: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    color: #1e293b;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 9px 12px;
    border: none;
    border-bottom: 1.5px solid #e2e8f0;
    font-weight: 700;
    font-size: 12px;
}

QCheckBox {
    spacing: 8px;
    color: #1e293b;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid #cbd5e1;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QProgressBar {
    border: none;
    border-radius: 5px;
    background-color: #e2e8f0;
    text-align: center;
    color: #0f172a;
    font-size: 10px;
    font-weight: 700;
    height: 10px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}

QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 12px;
    color: #0f172a;
}
"""
