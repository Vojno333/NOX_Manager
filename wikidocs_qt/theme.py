from __future__ import annotations

def get_app_stylesheet() -> str:
    return """
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