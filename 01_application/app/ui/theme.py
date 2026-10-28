"""Thème de l'application : style Fusion, palette claire, feuille de style unique.

Repris de `00_ancien/wikidocs_qt/theme.py` (feuille de style, mot pour mot)
et `00_ancien/qt_main.py` (palette, police).
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


# Feuille de style propre à l'écran d'accueil (`00_ancien/wikidocs_qt/home_window.py`).
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
