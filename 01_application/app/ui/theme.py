"""Thème de l'application : style Fusion, palette claire, feuille de style unique.

Repris de `v1-avant-refonte:wikidocs_qt/theme.py` (feuille de style, mot pour mot)
et `v1-avant-refonte:qt_main.py` (palette, police).
"""

from __future__ import annotations

import sys

from PySide6 import QtGui, QtWidgets

# Couleurs de la palette (rôle Qt → couleur).
_PALETTE = {
    QtGui.QPalette.ColorRole.Window: "#f5f6f8",
    QtGui.QPalette.ColorRole.WindowText: "#111827",
    QtGui.QPalette.ColorRole.Base: "#ffffff",
    QtGui.QPalette.ColorRole.AlternateBase: "#f9fafb",
    QtGui.QPalette.ColorRole.Text: "#111827",
    QtGui.QPalette.ColorRole.Button: "#ffffff",
    QtGui.QPalette.ColorRole.ButtonText: "#111827",
    QtGui.QPalette.ColorRole.Highlight: "#2563eb",
    QtGui.QPalette.ColorRole.HighlightedText: "#ffffff",
}

FEUILLE_DE_STYLE = """
    QWidget {
        background: #F6F8FB;
        color: #1F2937;
        font-family: "Segoe UI";
        font-size: 10pt;
    }

    QMainWindow, QDialog {
        background: #F6F8FB;
    }

    QFrame#card {
        background: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 14px;
    }

    QFrame#heroCard {
        background: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 18px;
    }

    QLabel#heroTitle {
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        background: transparent;
    }

    QLabel#heroSubtitle {
        font-size: 12px;
        color: #6B7280;
        background: transparent;
    }

    QLabel#sectionTitle {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
        background: transparent;
    }

    QLabel#mutedLabel {
        color: #6B7280;
        background: transparent;
    }

    QPushButton {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 8px 14px;
        min-height: 36px;
        font-weight: 600;
    }

    
    QPushButton:hover {
        background: #F8FAFC;
        border: 1px solid #94A3B8;
    }

    QPushButton:pressed {
        background: #E2E8F0;
    }

    QPushButton#primaryButton {
        background: #2563EB;
        color: white;
        border: 1px solid #2563EB;
    }

    QPushButton#primaryButton:hover {
        background: #1D4ED8;
        border: 1px solid #1D4ED8;
    }

    QPushButton#successButton {
        background: #16A34A;
        color: white;
        border: 1px solid #16A34A;
    }

    QPushButton#successButton:hover {
        background: #15803D;
        border: 1px solid #15803D;
    }

    QPushButton[filterActive="true"] {
    background: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #93C5FD;
    font-weight: 700;
    }

    QLabel#metricChip {
    background: #F8FAFC;
    border: 1px solid #D9E2EC;
    border-radius: 8px;
    padding: 4px 8px;
    color: #475569;
    font-weight: 600;
}

    QPushButton[filterActive="true"]:hover {
        background: #DBEAFE;
        border: 1px solid #60A5FA;
    }

    QSplitter::handle {
        background: #D9E2EC;
        border-radius: 4px;
    }

    QSplitter::handle:horizontal {
        width: 10px;
        margin: 8px 0;
    }

    QSplitter::handle:hover {
        background: #94A3B8;
    }
    
    QLineEdit, QComboBox, QPlainTextEdit, QTextEdit, QListWidget, QTreeWidget {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 6px 8px;
        selection-background-color: #DBEAFE;
        selection-color: #111827;
    }

    QTreeWidget, QListWidget {
        alternate-background-color: #F8FAFC;
    }

    QHeaderView::section {
        background: #EFF4FA;
        color: #334155;
        border: none;
        border-bottom: 1px solid #D9E2EC;
        padding: 8px;
        font-weight: 700;
    }

    QGroupBox {
        background: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 12px;
        margin-top: 14px;
        font-weight: 700;
        padding-top: 10px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
        color: #374151;
        background: #FFFFFF;
    }

    QSplitter::handle {
        background: #E5E7EB;
        width: 2px;
        height: 2px;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 2px;
    }

    QScrollBar::handle:vertical {
        background: #C7D2DE;
        border-radius: 5px;
        min-height: 24px;
    }

    QScrollBar:horizontal {
        background: transparent;
        height: 10px;
        margin: 2px;
    }

    QScrollBar::handle:horizontal {
        background: #C7D2DE;
        border-radius: 5px;
        min-width: 24px;
    }
    """


def palette_claire() -> QtGui.QPalette:
    palette = QtGui.QPalette()
    for role, couleur in _PALETTE.items():
        palette.setColor(role, QtGui.QColor(couleur))
    return palette


def appliquer_theme(app: QtWidgets.QApplication) -> None:
    """Style Fusion, palette claire, feuille de style et police Segoe UI 10 sous Windows."""
    app.setStyle("Fusion")
    app.setPalette(palette_claire())
    app.setStyleSheet(FEUILLE_DE_STYLE)
    if sys.platform.startswith("win"):
        QtWidgets.QApplication.setFont(QtGui.QFont("Segoe UI", 10))


# Feuille de style propre à l'écran d'accueil (`v1-avant-refonte:wikidocs_qt/home_window.py`).
STYLE_ACCUEIL = """
/* ── Global ── */
QMainWindow, QWidget#centralWidget {
    background-color: #f0f2f5;
}
QWidget {
    font-family: "Segoe UI", "IBM Plex Sans", Arial, sans-serif;
    font-size: 13px;
    color: #1a1d23;
}

/* ── Hero header ── */
QFrame#heroFrame {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 0px;
}
QLabel#heroTitle {
    font-size: 22px;
    font-weight: 700;
    color: #1a1d23;
    letter-spacing: -0.5px;
}
QLabel#heroSubtitle {
    font-size: 12px;
    color: #6b7280;
}
QLabel#versionLabel {
    font-size: 12px;
    color: #6b7280;
}
QPushButton#userButton {
    font-size: 13px;
    color: #374151;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 5px 14px 5px 8px;
    text-align: left;
}
QPushButton#userButton:hover {
    background: #e9ebee;
}

/* ── Action buttons ── */
QPushButton#primaryButton {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 0 20px;
    min-height: 42px;
}
QPushButton#primaryButton:hover  { background: #1d4ed8; }
QPushButton#primaryButton:pressed { background: #1e40af; }

QPushButton#outlineButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 20px;
    min-height: 42px;
}
QPushButton#outlineButton:hover  { background: #f9fafb; border-color: #9ca3af; }
QPushButton#outlineButton:pressed { background: #f3f4f6; }

QPushButton#ghostButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 16px;
    min-height: 36px;
}
QPushButton#ghostButton:hover  { background: #f9fafb; }

QPushButton#dangerButton {
    background: #ffffff;
    color: #dc2626;
    border: 1.5px solid #fecaca;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 16px;
    min-height: 36px;
}
QPushButton#dangerButton:hover  { background: #fff5f5; }

QPushButton#openFooterButton {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 0 16px;
    min-height: 36px;
}
QPushButton#openFooterButton:hover  { background: #1d4ed8; }

/* ── Panels ── */
QFrame#panelLeft, QFrame#panelRight {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 12px;
}
QLabel#panelTitle {
    font-size: 14px;
    font-weight: 600;
    color: #1a1d23;
}

/* ── Search box ── */
QLineEdit#searchBox {
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 8px;
    padding: 4px 10px 4px 32px;
    font-size: 13px;
    color: #374151;
    min-width: 220px;
    min-height: 32px;
}
QLineEdit#searchBox:focus {
    border-color: #2563eb;
    background: #ffffff;
}

/* ── Tree widget (project table) ── */
QTreeWidget#projectTree {
    background: #ffffff;
    border: none;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    outline: none;
    alternate-background-color: #f9fafb;
}
QTreeWidget#projectTree::item {
    padding: 10px 4px;
    border-bottom: 1px solid #f3f4f6;
}
QTreeWidget#projectTree::item:selected {
    background: #eff6ff;
    color: #1a1d23;
}
QTreeWidget#projectTree::item:hover:!selected {
    background: #f0f6ff;
}
QHeaderView::section {
    background: #f9fafb;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
}
QHeaderView::section:first { border-radius: 0; }

/* ── Hint label ── */
QLabel#hintLabel {
    font-size: 12px;
    color: #9ca3af;
    padding: 8px 16px;
}

/* ── Footer status ── */
QLabel#footerStatus {
    font-size: 12px;
    color: #9ca3af;
    font-style: italic;
}

/* ── Separator ── */
QFrame#hLine {
    background: #e5e7eb;
    max-height: 1px;
    border: none;
}

/* ── Info panel right ── */
QLabel#infoPanelTitle {
    font-size: 14px;
    font-weight: 600;
    color: #1a1d23;
    padding: 16px 20px 14px;
    border-bottom: 1px solid #e5e7eb;
}
QLabel#infoPlaceholderTitle {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
}
QLabel#infoPlaceholderSub {
    font-size: 12px;
    color: #9ca3af;
}
QLabel#infoKey {
    font-size: 13px;
    color: #6b7280;
    font-weight: 500;
}
QLabel#infoValue {
    font-size: 13px;
    color: #1a1d23;
}

/* ── Status bar ── */
QLabel#statusBar {
    font-size: 12px;
    color: #6b7280;
    padding: 8px 0px;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #d1d5db;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""


# Feuille de style reprise de `v1-avant-refonte:wikidocs_qt/new_project_dialog.py`.
STYLE_DIALOGUE_PROJET = """
QDialog {
    background: #f5f6f8;
    font-family: "Segoe UI", "IBM Plex Sans", Arial, sans-serif;
    font-size: 13px;
    color: #1a1d23;
}
QWidget {
    font-family: "Segoe UI", "IBM Plex Sans", Arial, sans-serif;
    font-size: 13px;
    color: #1a1d23;
}

/* ── Section cards ── */
QFrame#sectionCard {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 10px;
}

/* ── Labels ── */
QLabel#dialogTitle {
    font-size: 20px;
    font-weight: 700;
    color: #1a1d23;
}
QLabel#dialogSubtitle {
    font-size: 12px;
    color: #6b7280;
}
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: #1a1d23;
}
QLabel#fieldLabel {
    font-size: 12px;
    color: #374151;
    font-weight: 500;
}
QLabel#required {
    font-size: 12px;
    color: #dc2626;
    font-weight: 500;
}
QLabel#rowCounter {
    font-size: 12px;
    color: #2563eb;
    font-style: italic;
}

/* ── Line edits ── */
QLineEdit {
    background: #ffffff;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    padding: 7px 10px;

    font-size: 13px;
    font-weight: 500;          /* ← texte un peu plus marqué */
    color: #111827;            /* ← texte saisi plus sombre */

    min-height: 34px;
}

QLineEdit:focus {
    border-color: #2563eb;
    background: #ffffff;
}

QLineEdit:disabled {
    background: #f9fafb;
    color: #6b7280;            /* ← moins fade */
}

/* Placeholder plus lisible */
QLineEdit::placeholder {
    color: #6b7280;            /* ← gris plus foncé */
    font-weight: 400;
}

/* ── ComboBox ── */
QComboBox {
    background: #ffffff;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 13px;
    color: #1a1d23;
    min-height: 34px;
}
QComboBox:focus { border-color: #2563eb; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    selection-background-color: #eff6ff;
    selection-color: #1a1d23;
    outline: none;
}

/* ── Checkboxes ── */
QCheckBox {
    font-size: 13px;
    color: #374151;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
    image: none;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

/* ── Table header ── */
QFrame#tableHeaderFrame {
    background: #f9fafb;
    border: none;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
}
QLabel#tableHeaderLabel {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Table rows ── */
QFrame#tableRow {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #f3f4f6;
}
QFrame#tableRowAlt {
    background: #fafafa;
    border: none;
    border-bottom: 1px solid #f3f4f6;
}
QLabel#rowIndex {
    font-size: 13px;
    color: #9ca3af;
    font-weight: 500;
}

/* ── Buttons ── */
QPushButton#primaryButton {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 0 24px;
    min-height: 40px;
}
QPushButton#primaryButton:hover  { background: #1d4ed8; }
QPushButton#primaryButton:pressed { background: #1e40af; }

QPushButton#outlineButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 20px;
    min-height: 40px;
}
QPushButton#outlineButton:hover { background: #f9fafb; border-color: #9ca3af; }

QPushButton#browseButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 14px;
    min-height: 36px;
}
QPushButton#browseButton:hover { background: #f9fafb; }

QPushButton#addRowsButton {
    background: #ffffff;
    color: #2563eb;
    border: 1.5px solid #bfdbfe;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 600;
    padding: 0 14px;
    min-height: 32px;
}
QPushButton#addRowsButton:hover { background: #eff6ff; }

QPushButton#clearButton {
    background: #ffffff;
    color: #6b7280;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 500;
    padding: 0 12px;
    min-height: 32px;
}
QPushButton#clearButton:hover { background: #f9fafb; color: #dc2626; border-color: #fecaca; }

QPushButton#deleteRowButton {
    background: transparent;
    border: none;
    color: #fca5a5;
    font-size: 16px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
}
QPushButton#deleteRowButton:hover { color: #dc2626; }

/* ── Scroll area ── */
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical {
    background: transparent; width: 8px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #d1d5db; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


# Feuille de style reprise de `v1-avant-refonte:wikidocs_qt/upload_document_dialog.py`.
STYLE_DEPOT = """
QDialog {
    background: #f5f6f8;
    font-family: "Segoe UI", "IBM Plex Sans", Arial, sans-serif;
    font-size: 13px;
    color: #1a1d23;
}
QWidget {
    font-family: "Segoe UI", "IBM Plex Sans", Arial, sans-serif;
    font-size: 13px;
    color: #1a1d23;
}

/* ── Cards ── */
QFrame#sectionCard {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 10px;
}

/* ── Labels ── */
QLabel#dialogTitle {
    font-size: 17px;
    font-weight: 700;
    color: #1a1d23;
}
QLabel#dialogSubtitle {
    font-size: 12px;
    color: #6b7280;
}
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #1a1d23;
}
QLabel#fieldLabel {
    font-size: 12px;
    color: #374151;
    font-weight: 500;
}
QLabel#fieldLabelOpt {
    font-size: 12px;
    color: #374151;
    font-weight: 400;
}
QLabel#required {
    font-size: 12px;
    color: #dc2626;
}
QLabel#hintLabel {
    font-size: 11px;
    color: #6b7280;
}
QLabel#formatHint {
    font-size: 11px;
    color: #2563eb;
}
QLabel#infoIcon {
    font-size: 13px;
    color: #9ca3af;
}
QLabel#previewLabel {
    font-size: 12px;
    color: #374151;
    padding: 4px 0;
}
QLabel#reqCountLabel {
    font-size: 12px;
    color: #374151;
    padding: 6px 0;
}

/* ── Line edits / ComboBox ── */
QLineEdit {
    background: #ffffff;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 13px;
    color: #1a1d23;
    min-height: 34px;
}
QLineEdit:focus { border-color: #2563eb; }
QLineEdit:disabled { background: #f9fafb; color: #9ca3af; }
QLineEdit[readOnly="true"] { background: #f9fafb; }

QComboBox {
    background: #ffffff;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 13px;
    color: #1a1d23;
    min-height: 34px;
}
QComboBox:focus { border-color: #2563eb; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { width: 12px; height: 12px; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    selection-background-color: #eff6ff;
    selection-color: #1a1d23;
    outline: none;
    padding: 4px;
}

/* ── Drop zone ── */
QFrame#dropZone {
    background: #f8faff;
    border: 2px dashed #bfdbfe;
    border-radius: 10px;
}
QFrame#dropZone:hover { background: #eff6ff; border-color: #2563eb; }

/* ── Search box ── */
QLineEdit#searchBox {
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    padding: 6px 10px 6px 32px;
    min-height: 32px;
}
QLineEdit#searchBox:focus { border-color: #2563eb; background: #ffffff; }

/* ── Requirements table ── */
QFrame#reqTableHeader {
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    border-left: none;
    border-right: none;
}
QLabel#reqHeaderLabel {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
}
QFrame#reqRow {
    background: #ffffff;
    border-bottom: 1px solid #f3f4f6;
    border-left: none;
    border-right: none;
    border-top: none;
}
QLabel#reqName {
    font-size: 13px;
    font-weight: 500;
    color: #1a1d23;
}
QLabel#reqDesc {
    font-size: 12px;
    color: #9ca3af;
}

/* ── Toggle switch ── */
QCheckBox#toggleSwitch {
    spacing: 0px;
}
QCheckBox#toggleSwitch::indicator {
    width: 42px;
    height: 24px;
    border-radius: 12px;
    background: #d1d5db;
    border: none;
}
QCheckBox#toggleSwitch::indicator:checked {
    background: #2563eb;
}

/* ── Row checkbox ── */
QCheckBox#rowCheck::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox#rowCheck::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
}

/* ── Buttons ── */
QPushButton#primaryButton {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 0 24px;
    min-height: 40px;
}
QPushButton#primaryButton:hover  { background: #1d4ed8; }
QPushButton#primaryButton:pressed { background: #1e40af; }

QPushButton#outlineButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 20px;
    min-height: 40px;
}
QPushButton#outlineButton:hover { background: #f9fafb; }

QPushButton#browseButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 14px;
    min-height: 36px;
}
QPushButton#browseButton:hover { background: #f9fafb; }

QPushButton#ghostSmallButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 500;
    padding: 0 14px;
    min-height: 34px;
}
QPushButton#ghostSmallButton:hover { background: #f9fafb; }

QPushButton#infoButton {
    background: transparent;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    color: #9ca3af;
    font-size: 14px;
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0;
}
QPushButton#infoButton:hover { background: #f3f4f6; }

/* ── Scroll ── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent; width: 8px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #d1d5db; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
