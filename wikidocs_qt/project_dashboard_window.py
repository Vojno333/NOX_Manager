from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette

from .filter_popup import FilterPopup
from .metadata_db import init_metadata_db, get_uploaded_documents
from .upload_document_dialog import UploadDocumentDialog
from .export_templates import export_project_templates
from .document_rules import CE_REQUIREMENTS, DPE_REQUIREMENTS, JUSTIFICATION_TYPES
from .project_manager import ProjectManager
from .project_structure import create_folders_and_subfolders
from .new_project_dialog import NewProjectDialog

# ── Palette ───────────────────────────────────────────────────────────────────
TOPBAR_BG   = "#111827"
TOPBAR_FG   = "#CBD5E1"
WHITE       = "#FFFFFF"
BG          = "#F6F8FB"
BLUE        = "#2563EB"
BLUE_LIGHT  = "#EFF6FF"
BLUE_DARK   = "#1D4ED8"
GREEN_OK    = "#059669"
GREEN_BG    = "#D1FAE5"
ORANGE_WARN = "#D97706"
ORANGE_BG   = "#FEF3C7"
RED_KO      = "#DC2626"
RED_BG      = "#FEE2E2"
PURPLE      = "#7C3AED"
PURPLE_BG   = "#EDE9FE"
GRAY_BORDER = "#E5E7EB"
GRAY_CARD   = "#D9E2EC"
GRAY_TEXT   = "#6B7280"
GRAY_LIGHT  = "#F8FAFC"
DARK        = "#111827"
ALT_ROW     = "#F8FAFC"
SEL_BG      = "#EFF6FF"
SEL_FG      = BLUE

# Type badge colours  (bg, fg)
TYPE_COLORS: dict[str, tuple[str, str]] = {
    "CE":   (ORANGE_BG,  "#92400E"),
    "CECC": (PURPLE_BG,  "#5B21B6"),
    "DPE":  (GREEN_BG,   "#065F46"),
}

# KPI bar colours
KPI_BAR_COLORS: dict[str, str] = {
    "CE":   ORANGE_WARN,
    "CECC": PURPLE,
    "DPE":  GREEN_OK,
}

# ── Fonts ─────────────────────────────────────────────────────────────────────
F_BODY   = QFont("Segoe UI", 9)
F_BOLD   = QFont("Segoe UI", 9, QFont.Bold)
F_SMALL  = QFont("Segoe UI", 8)
F_TINY   = QFont("Segoe UI", 7)
F_H1     = QFont("Segoe UI", 13, QFont.Bold)
F_TOPBAR = QFont("Segoe UI", 9)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _hline() -> QtWidgets.QFrame:
    f = QtWidgets.QFrame()
    f.setFrameShape(QtWidgets.QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{GRAY_BORDER}; border:none;")
    return f

def _make_label(text: str, font: QFont = F_BODY, color: str = DARK) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color:{color}; background:transparent;")
    return lbl

# ── KPI card ──────────────────────────────────────────────────────────────────
class KpiCard(QtWidgets.QFrame):
    """White card with icon, value, subtitle and optional progress bar."""

    def __init__(self, icon: str, title: str, value: str = "—",
                 subtitle: str = "", bar_color: str = "", icon_bg: str = "#F0F4FF",
                 parent=None):
        super().__init__(parent)
        self._bar_color = bar_color
        self._bar_fill: QtWidgets.QFrame | None = None
        self._bar_bg:   QtWidgets.QFrame | None = None
        self._value_lbl: QtWidgets.QLabel | None = None
        self._pct_value = 0

        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            KpiCard {{
                background:{WHITE};
                border:1px solid {GRAY_CARD};
                border-radius:12px;
            }}
        """)

        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(14, 10, 14, 10)
        h.setSpacing(12)

        icon_frame = QtWidgets.QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"background:{icon_bg}; border-radius:8px;")
        icon_lbl = QtWidgets.QLabel(icon, icon_frame)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size:16px; background:transparent;")
        il = QtWidgets.QVBoxLayout(icon_frame)
        il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(icon_lbl)
        h.addWidget(icon_frame)

        col = QtWidgets.QVBoxLayout()
        col.setSpacing(1)
        col.setContentsMargins(0, 0, 0, 0)

        title_lbl = _make_label(title, F_SMALL, GRAY_TEXT)
        col.addWidget(title_lbl)

        self._value_lbl = _make_label(value, F_H1, DARK)
        col.addWidget(self._value_lbl)

        if subtitle:
            sub_lbl = _make_label(subtitle, F_TINY, GRAY_TEXT)
            col.addWidget(sub_lbl)

        if bar_color:
            bar_bg = QtWidgets.QFrame()
            bar_bg.setFixedHeight(3)
            bar_bg.setStyleSheet("background:#E5E7EB; border-radius:2px;")
            self._bar_bg = bar_bg
            bar_fill = QtWidgets.QFrame(bar_bg)
            bar_fill.setFixedHeight(3)
            bar_fill.setStyleSheet(f"background:{bar_color}; border-radius:2px;")
            bar_fill.setFixedWidth(0)
            self._bar_fill = bar_fill
            col.addWidget(bar_bg)

        h.addLayout(col)

    def set_value(self, text: str, pct: int = -1):
        if self._value_lbl:
            self._value_lbl.setText(text)
        if pct >= 0:
            self._pct_value = pct
            self._refresh_bar()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_bar()

    def _refresh_bar(self):
        if self._bar_fill and self._bar_bg:
            w = self._bar_bg.width()
            fill = 0 if self._pct_value <= 0 else max(4, int(w * self._pct_value / 100))
            self._bar_fill.setFixedWidth(fill)

# ── Filter chip ───────────────────────────────────────────────────────────────
class FilterChip(QtWidgets.QPushButton):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.base_label = label
        self.setText(f"{label}  ▾")
        self.setFont(F_SMALL)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self._set_style(False)

    def set_active(self, active: bool):
        self.setText(f"{self.base_label}  {'●' if active else '▾'}")
        self._set_style(active)

    def _set_style(self, active: bool):
        bg     = BLUE_LIGHT if active else WHITE
        border = BLUE       if active else GRAY_BORDER
        color  = BLUE       if active else DARK
        fw     = "700"      if active else "400"
        self.setStyleSheet(f"""
            QPushButton {{
                background:{bg}; border:1px solid {border};
                border-radius:15px; padding:2px 14px; color:{color};
                font-weight:{fw}; font-size:8pt;
            }}
            QPushButton:hover   {{ background:{BLUE_LIGHT}; border-color:{BLUE}; color:{BLUE}; }}
            QPushButton:pressed {{ background:#DBEAFE; }}
        """)

# ── Type badge label ───────────────────────────────────────────────────────────
class TypeBadge(QtWidgets.QLabel):
    def __init__(self, type_: str, parent=None):
        super().__init__(type_, parent)
        bg, fg = TYPE_COLORS.get(type_, ("#F1F5F9", "#374151"))
        self.setStyleSheet(f"""
            background:{bg}; color:{fg};
            border-radius:10px; padding:2px 10px;
            font-size:9pt; font-weight:700;
        """)
        self.setFixedHeight(22)

# ── Completion badge ──────────────────────────────────────────────────────────
def _completion_badge(pct_str: str) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(pct_str)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFont(F_BOLD)
    try:
        val = int(str(pct_str).replace("%", "").replace(" ", ""))
    except ValueError:
        val = -1
    if val == 100:
        bg, fg = GREEN_BG,  "#065F46"
    elif val == 0:
        bg, fg = RED_BG,    "#991B1B"
    else:
        bg, fg = ORANGE_BG, "#92400E"
    lbl.setStyleSheet(f"""
        background:{bg}; color:{fg};
        border-radius:10px; padding:1px 10px;
        font-size:9pt; font-weight:700;
    """)
    return lbl

# ── Detail panel ──────────────────────────────────────────────────────────────
class DetailPanel(QtWidgets.QFrame):
    requestModify  = QtCore.Signal(dict)   # emits row_data
    requestDelete  = QtCore.Signal(dict)   # emits row_data
    requestOpenDoc = QtCore.Signal(str)    # emits file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(340)
        self.setStyleSheet(f"""
            DetailPanel {{
                background:{WHITE};
                border:1px solid {GRAY_CARD};
                border-radius:12px;
            }}
        """)
        self._row_data: dict | None = None
        self._nb_docs = 0
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._hdr = QtWidgets.QWidget()
        self._hdr.setStyleSheet(f"background:{WHITE}; border-radius:12px 12px 0 0;")
        hdr_lay = QtWidgets.QVBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(16, 14, 16, 12)
        hdr_lay.setSpacing(4)

        title_row = QtWidgets.QHBoxLayout()
        title_row.setSpacing(8)
        self._lbl_title = _make_label("—", F_H1, DARK)
        self._lbl_title.setWordWrap(True)
        title_row.addWidget(self._lbl_title, 1)
        self._badge = TypeBadge("CE")
        self._badge.hide()
        title_row.addWidget(self._badge)
        hdr_lay.addLayout(title_row)

        self._lbl_sub = _make_label("", F_SMALL, GRAY_TEXT)
        hdr_lay.addWidget(self._lbl_sub)
        root.addWidget(self._hdr)
        root.addWidget(_hline())

        # Scroll body
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent;")
        body_w = QtWidgets.QWidget()
        body_w.setStyleSheet("background:transparent;")
        self._body = QtWidgets.QVBoxLayout(body_w)
        self._body.setContentsMargins(16, 12, 16, 12)
        self._body.setSpacing(12)
        scroll.setWidget(body_w)
        root.addWidget(scroll, 1)

        # Sections (created once, shown/hidden per selection)
        self._lbl_docs_title = _make_label("Documents liés", F_BOLD, DARK)
        self._body.addWidget(self._lbl_docs_title)

        self._tbl_docs = self._make_doc_table()
        self._body.addWidget(self._tbl_docs)

        self._body.addWidget(_hline())

        self._lbl_info_title = _make_label("Informations", F_BOLD, DARK)
        self._body.addWidget(self._lbl_info_title)

        self._info_widget = QtWidgets.QWidget()
        self._info_widget.setStyleSheet("background:transparent;")
        self._info_lay = QtWidgets.QVBoxLayout(self._info_widget)
        self._info_lay.setContentsMargins(0, 0, 0, 0)
        self._info_lay.setSpacing(4)
        self._body.addWidget(self._info_widget)
        self._body.addStretch(1)

        # Footer buttons
        root.addWidget(_hline())
        footer = QtWidgets.QWidget()
        footer.setStyleSheet(f"background:{WHITE}; border-radius:0 0 12px 12px;")
        footer_lay = QtWidgets.QVBoxLayout(footer)
        footer_lay.setContentsMargins(14, 10, 14, 12)
        footer_lay.setSpacing(6)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_modify = QtWidgets.QPushButton("✏   Modifier la référence")
        self._btn_modify.setFont(F_BOLD)
        self._btn_modify.setCursor(Qt.PointingHandCursor)
        self._btn_modify.setFixedHeight(34)
        self._btn_modify.setStyleSheet(f"""
            QPushButton {{
                background:{BLUE}; color:{WHITE};
                border:none; border-radius:8px; padding:0 12px; font-size:8pt;
            }}
            QPushButton:hover {{ background:{BLUE_DARK}; }}
        """)
        self._btn_modify.clicked.connect(self._on_modify)

        self._btn_view = QtWidgets.QPushButton("📄  Voir les documents (0)")
        self._btn_view.setFont(F_BODY)
        self._btn_view.setCursor(Qt.PointingHandCursor)
        self._btn_view.setFixedHeight(34)
        self._btn_view.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE}; color:{DARK};
                border:1px solid {GRAY_BORDER}; border-radius:8px; padding:0 10px; font-size:8pt;
            }}
            QPushButton:hover {{ background:{GRAY_LIGHT}; }}
        """)
        btn_row.addWidget(self._btn_modify, 1)
        btn_row.addWidget(self._btn_view, 1)
        footer_lay.addLayout(btn_row)

        self._btn_delete = QtWidgets.QPushButton("🗑   Supprimer la référence")
        self._btn_delete.setFont(F_BODY)
        self._btn_delete.setCursor(Qt.PointingHandCursor)
        self._btn_delete.setFixedHeight(34)
        self._btn_delete.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE}; color:{RED_KO};
                border:1px solid #FCA5A5; border-radius:8px; padding:0 12px; font-size:8pt;
            }}
            QPushButton:hover {{ background:{RED_BG}; }}
        """)
        self._btn_delete.clicked.connect(self._on_delete)
        footer_lay.addWidget(self._btn_delete)
        root.addWidget(footer)

    def _make_doc_table(self) -> QtWidgets.QTableWidget:
        t = QtWidgets.QTableWidget(0, 3)
        t.setHorizontalHeaderLabels(["Exigence", "Applicabilité", "Nom du document"])
        t.horizontalHeader().setFont(F_BOLD)
        t.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        t.setSelectionMode(QtWidgets.QTableWidget.NoSelection)
        t.setMaximumHeight(240)
        t.setStyleSheet(f"""
            QTableWidget {{
                border:1px solid {GRAY_BORDER}; border-radius:8px;
                font-size:8pt; background:{WHITE};
                alternate-background-color:{ALT_ROW};
            }}
            QHeaderView::section {{
                background:{GRAY_LIGHT}; color:{GRAY_TEXT};
                border:none; border-bottom:1px solid {GRAY_BORDER};
                padding:5px 6px; font-weight:700; font-size:8pt;
            }}
            QTableWidget::item {{ padding:4px 6px; color:{DARK}; }}
        """)
        t.cellClicked.connect(self._on_doc_clicked)
        return t

    # ── Public API ────────────────────────────────────────────────────────────
    def clear(self):
        self._row_data = None
        self._lbl_title.setText("Sélectionne une ligne")
        self._lbl_sub.setText("")
        self._badge.hide()
        self._tbl_docs.setRowCount(0)
        self._clear_info()
        self._btn_modify.setEnabled(False)
        self._btn_view.setEnabled(False)
        self._btn_delete.setEnabled(False)

    def populate(self, row_data: dict, detail_rows: list[dict]):
        self._row_data = row_data
        supplier  = row_data["supplier"]
        reference = row_data["reference"]
        jtype     = row_data["type"]
        docs      = row_data.get("docs", [])
        self._nb_docs = len(docs)

        # Header
        self._lbl_title.setText(f"{supplier}  –  {reference}")
        self._badge.setText(jtype)
        bg, fg = TYPE_COLORS.get(jtype, ("#F1F5F9", "#374151"))
        self._badge.setStyleSheet(f"""
            background:{bg}; color:{fg};
            border-radius:10px; padding:2px 10px;
            font-size:9pt; font-weight:700;
        """)
        self._badge.show()
        self._lbl_sub.setText(
            f"Type : {jtype}    ·    {self._nb_docs} document(s) enregistré(s)"
        )

        # Documents liés table
        is_cecc = (jtype == "CECC")
        if is_cecc:
            self._tbl_docs.setColumnCount(2)
            self._tbl_docs.setHorizontalHeaderLabels(["Champ", "Valeur"])
            self._tbl_docs.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        else:
            self._tbl_docs.setColumnCount(3)
            self._tbl_docs.setHorizontalHeaderLabels(["Exigence", "Applicabilité", "Nom du document"])
            self._tbl_docs.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self._tbl_docs.setRowCount(len(detail_rows))
        for i, detail in enumerate(detail_rows):
            applicability = str(detail.get("applicability", "Applicable"))
            req_item = QtWidgets.QTableWidgetItem(str(detail.get("requirement", "")))
            req_item.setData(Qt.UserRole, detail.get("path", ""))
            self._tbl_docs.setItem(i, 0, req_item)

            if not is_cecc:
                app_item = QtWidgets.QTableWidgetItem(applicability)
                app_item.setTextAlignment(Qt.AlignCenter)
                if applicability == "Non applicable":
                    app_item.setForeground(QColor(ORANGE_WARN))
                else:
                    app_item.setForeground(QColor(GREEN_OK))
                self._tbl_docs.setItem(i, 1, app_item)
                doc_col = 2
            else:
                doc_col = 1

            filename = str(detail.get("filename", "—"))
            file_item = QtWidgets.QTableWidgetItem(filename)
            if filename not in ("—", "N/A", ""):
                file_item.setForeground(QColor(BLUE))
                font = file_item.font()
                font.setUnderline(True)
                file_item.setFont(font)
                file_item.setToolTip("Cliquer pour ouvrir")
            file_item.setData(Qt.UserRole, detail.get("path", ""))
            self._tbl_docs.setItem(i, doc_col, file_item)

        self._tbl_docs.resizeRowsToContents()

        # Informations section
        self._clear_info()
        pct_str  = row_data.get("completion", "—")
        try:
            pct_val = int(str(pct_str).replace("%", "").replace(" ", ""))
        except ValueError:
            pct_val = -1

        info_items = [
            ("👤", "Fournisseur",       supplier),
            ("📋", "Référence",         reference),
            ("📦", "Type",              jtype),
            ("📄", "Nb de documents",   str(self._nb_docs)),
            ("✅", "Complétude",        pct_str),
        ]
        for icon, label, value in info_items:
            row_w = QtWidgets.QWidget()
            row_w.setStyleSheet("background:transparent;")
            row_h = QtWidgets.QHBoxLayout(row_w)
            row_h.setContentsMargins(0, 0, 0, 0)
            row_h.setSpacing(6)

            icon_lbl = _make_label(icon, F_BODY, GRAY_TEXT)
            icon_lbl.setFixedWidth(16)
            label_lbl = _make_label(label, F_SMALL, GRAY_TEXT)
            label_lbl.setFixedWidth(110)

            if label == "Complétude" and pct_val >= 0:
                val_w = _completion_badge(pct_str)
            else:
                val_w = _make_label(value, F_SMALL, DARK)

            row_h.addWidget(icon_lbl)
            row_h.addWidget(label_lbl)
            row_h.addWidget(val_w)
            row_h.addStretch(1)
            self._info_lay.addWidget(row_w)

        # Buttons
        self._btn_view.setText(f"📄  Voir les documents ({self._nb_docs})")
        self._btn_modify.setEnabled(True)
        self._btn_view.setEnabled(True)
        self._btn_delete.setEnabled(True)

    def _clear_info(self):
        while self._info_lay.count():
            item = self._info_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_doc_clicked(self, row: int, col: int):
        doc_col = 1 if self._tbl_docs.columnCount() == 2 else 2
        if col != doc_col:
            return
        item = self._tbl_docs.item(row, doc_col)
        if item:
            path = item.data(Qt.UserRole)
            if path:
                self.requestOpenDoc.emit(str(path))

    def _on_modify(self):
        if self._row_data:
            self.requestModify.emit(self._row_data)

    def _on_delete(self):
        if self._row_data:
            self.requestDelete.emit(self._row_data)

# ── Table tab (one per BDD type + "Tous") ────────────────────────────────────
class MainTab(QtWidgets.QWidget):
    COLUMNS = [
        "Fournisseur", "Référence", "Libellé équipement",
        "MNP", "N° de commande", "Type",
        "Nb docs", "Complétude",
    ]

    rowSelected = QtCore.Signal(dict)  # emits row_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.table = QtWidgets.QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        hh = self.table.horizontalHeader()
        hh.setFont(F_BOLD)
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border:none; font-size:9pt;
                background:{WHITE}; alternate-background-color:{ALT_ROW};
            }}
            QHeaderView::section {{
                background:{GRAY_LIGHT}; color:{GRAY_TEXT};
                border:none; border-bottom:2px solid {GRAY_BORDER};
                padding:7px 8px; font-weight:700; font-size:8pt;
            }}
            QTableWidget::item {{ padding:6px 8px; color:{DARK}; }}
            QTableWidget::item:selected {{ background:{SEL_BG}; color:{BLUE}; }}
        """)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        h.addWidget(self.table, 1)

    def _on_selection_changed(self):
        idxs = self.table.selectedIndexes()
        if not idxs:
            return
        row = idxs[0].row()
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            if data:
                self.rowSelected.emit(data)

    def load_rows(self, rows: list[dict]):
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(rows))
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        for ri, row in enumerate(rows):
            pct = row.get("completion_value", 0.0)
            if pct >= 1.0:
                c_color = GREEN_OK
            elif pct > 0:
                c_color = ORANGE_WARN
            else:
                c_color = RED_KO

            values = [
                (row.get("supplier", ""),       Qt.AlignLeft  | Qt.AlignVCenter),
                (row.get("reference", ""),       Qt.AlignLeft  | Qt.AlignVCenter),
                (row.get("label", ""),           Qt.AlignLeft  | Qt.AlignVCenter),
                (str(row.get("documents_db", row.get("documents", 0))),
                                                 Qt.AlignCenter),
                (row.get("order_number", ""),    Qt.AlignCenter),
                (row.get("type", ""),            Qt.AlignCenter),
                (str(row.get("documents", 0)),   Qt.AlignCenter),
                (row.get("completion", "—"),     Qt.AlignCenter),
            ]

            for ci, (val, align) in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(val))
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, row)
                if ci == 7:  # Complétude column
                    item.setForeground(QtGui.QBrush(QColor(c_color)))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(ri, ci, item)

        self.table.resizeRowsToContents()
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.AscendingOrder)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def selected_rows_data(self) -> list[dict]:
        rows = []
        seen = set()
        for idx in self.table.selectedIndexes():
            r = idx.row()
            if r in seen:
                continue
            seen.add(r)
            item = self.table.item(r, 0)
            if item:
                data = item.data(Qt.UserRole)
                if data:
                    rows.append(data)
        return rows

# ── Main window ───────────────────────────────────────────────────────────────
class ProjectDashboardWindow(QtWidgets.QMainWindow):

    def __init__(self, project_data: dict, parent=None):
        super().__init__(parent)
        self.project_data   = project_data
        self.project_dir    = Path(project_data["project_path"])
        self.project_manager = ProjectManager()
        self.enabled_bdds   = list(project_data.get("enabled_bdds", JUSTIFICATION_TYPES))

        self.column_filters: dict[str, set[str] | None] = {
            "supplier": None, "reference": None,
            "type": None,     "completion": None,
        }
        self.tab_widgets_by_name: dict[str, MainTab] = {}
        self._all_rows_cache:      list[dict] = []
        self._filtered_rows_cache: list[dict] = []
        self.current_rows_by_tab:  dict[str, list[dict]] = {}

        init_metadata_db(self.project_dir)
        self.setWindowTitle(
            f"NOX_Manager — {project_data.get('project_name', self.project_dir.name)}"
        )
        self.resize(1400, 860)
        self.setMinimumSize(1100, 700)

        self._build_ui()
        self._load_table()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        central = QtWidgets.QWidget()
        central.setStyleSheet(f"background:{BG};")
        self.setCentralWidget(central)

        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        # Body: sidebar + content
        body = QtWidgets.QWidget()
        body_h = QtWidgets.QHBoxLayout(body)
        body_h.setContentsMargins(0, 0, 0, 0)
        body_h.setSpacing(0)
        body_h.addWidget(self._build_sidebar())
        body_h.addWidget(self._build_content(), 1)
        root.addWidget(body, 1)

    # ── Top bar (dark) ────────────────────────────────────────────────────────
    def _build_topbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"background:{TOPBAR_BG};")

        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(2)

        brand = QtWidgets.QLabel("NOX Manager")
        brand.setFont(QFont("Segoe UI", 10, QFont.Bold))
        brand.setStyleSheet(f"color:{WHITE}; background:transparent;")
        h.addWidget(brand)
        h.addSpacing(12)

        actions = [
            ("⚙  Paramétrage", self._open_project_settings),
            ("📥  Importer",    self._open_upload_from_selection),
            ("↺  Actualiser",  self._load_table),
            ("📊  Exporter BDD", self._export_templates),
        ]

        for label, slot in actions:
            btn = QtWidgets.QPushButton(label)
            btn.setFont(F_TOPBAR)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color:{TOPBAR_FG}; padding:5px 12px;
                    border-radius:6px; border:none; font-size:9pt;
                }}
                QPushButton:hover   {{ background:#1F2937; color:{WHITE}; }}
                QPushButton:pressed {{ background:#374151; }}
            """)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addStretch(1)

        project_badge = QtWidgets.QLabel(
            self.project_data.get("project_name", self.project_dir.name)
        )
        project_badge.setFont(F_BOLD)
        project_badge.setStyleSheet("""
            background:#F59E0B; color:#1F2937;
            border-radius:6px; padding:3px 12px; font-size:9pt; font-weight:700;
        """)
        h.addWidget(project_badge)
        return bar

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self) -> QtWidgets.QWidget:
        sidebar = QtWidgets.QWidget()
        sidebar.setFixedWidth(165)
        sidebar.setStyleSheet(f"""
            background:{WHITE};
            border-right:1px solid {GRAY_BORDER};
        """)

        v = QtWidgets.QVBoxLayout(sidebar)
        v.setContentsMargins(8, 12, 8, 12)
        v.setSpacing(4)

        nav_items = [
            ("🗂", "Vue d'ensemble", True),
            ("📄", "Documents",       False),
        ]
        self._nav_buttons: list[QtWidgets.QPushButton] = []
        for icon, label, active in nav_items:
            btn = QtWidgets.QPushButton(f"  {icon}  {label}")
            btn.setFont(F_BODY)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(active)
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align:left; padding:0 10px;
                    border-radius:8px; border:none;
                    color:{BLUE if active else GRAY_TEXT};
                    background:{BLUE_LIGHT if active else 'transparent'};
                    font-weight:{'700' if active else '400'};
                }}
                QPushButton:hover:!checked {{
                    background:{GRAY_LIGHT}; color:{DARK};
                }}
                QPushButton:checked {{
                    background:{BLUE_LIGHT}; color:{BLUE}; font-weight:700;
                }}
            """)
            self._nav_buttons.append(btn)
            v.addWidget(btn)

        v.addStretch(1)

        # Timestamp footer
        self._lbl_timestamp = _make_label("Dernière actualisation", F_TINY, GRAY_TEXT)
        self._lbl_date = _make_label("—", F_SMALL, DARK)
        v.addWidget(self._lbl_timestamp)
        v.addWidget(self._lbl_date)
        return sidebar

    # ── Main content ──────────────────────────────────────────────────────────
    def _build_content(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setStyleSheet(f"background:{BG};")
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(12, 10, 12, 8)
        v.setSpacing(8)

        v.addWidget(self._build_kpi_row())
        v.addWidget(self._build_table_section(), 1)
        return w

    # ── KPI row ───────────────────────────────────────────────────────────────
    def _build_kpi_row(self) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        row.setStyleSheet("background:transparent;")
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        self.kpi_ce = KpiCard(
            "📋", "CE", "0 %", "Complétude",
            bar_color=KPI_BAR_COLORS["CE"], icon_bg="#FEF3C7"
        )
        self.kpi_cecc = KpiCard(
            "🎁", "CECC", "0 %", "Complétude",
            bar_color=KPI_BAR_COLORS["CECC"], icon_bg="#EDE9FE"
        )
        self.kpi_dpe = KpiCard(
            "🌿", "DPE", "0 %", "Complétude",
            bar_color=KPI_BAR_COLORS["DPE"], icon_bg="#D1FAE5"
        )
        self.kpi_refs = KpiCard(
            "📄", "Références", "0", "Total", icon_bg="#DBEAFE"
        )
        self.kpi_docs = KpiCard(
            "📋", "Documents", "0", "Total", icon_bg="#D1FAE5"
        )
        for card in (self.kpi_ce, self.kpi_cecc, self.kpi_dpe, self.kpi_refs, self.kpi_docs):
            h.addWidget(card, 1)
        return row

    # ── Table section (tabs + detail panel) ───────────────────────────────────
    def _build_table_section(self) -> QtWidgets.QWidget:
        outer = QtWidgets.QWidget()
        outer.setStyleSheet("background:transparent;")
        h = QtWidgets.QHBoxLayout(outer)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        # Left: filter bar + tabs
        left = QtWidgets.QFrame()
        left.setStyleSheet(f"""
            QFrame {{
                background:{WHITE};
                border:1px solid {GRAY_CARD};
                border-radius:12px;
            }}
        """)
        lv = QtWidgets.QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(0)
        lv.addWidget(self._build_filter_row())
        lv.addWidget(_hline())
        lv.addWidget(self._build_tabs(), 1)
        lv.addWidget(self._build_statusbar())
        h.addWidget(left, 1)

        # Right: detail panel
        self.detail_panel = DetailPanel()
        self.detail_panel.clear()
        self.detail_panel.requestModify.connect(self._on_modify_row)
        self.detail_panel.requestDelete.connect(self._on_delete_row)
        self.detail_panel.requestOpenDoc.connect(self._open_file)
        h.addWidget(self.detail_panel)
        return outer

    # ── Filter row ────────────────────────────────────────────────────────────
    def _build_filter_row(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet("background:transparent;")
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(6)

        self.chip_supplier = FilterChip("Fournisseur")
        self.chip_reference = FilterChip("Référence")
        self.chip_type = FilterChip("Type")
        self.chip_completion = FilterChip("Complétude")

        self.chip_supplier.clicked.connect(
            lambda: self._open_column_filter("supplier", "Filtrer les fournisseurs")
        )
        self.chip_reference.clicked.connect(
            lambda: self._open_column_filter("reference", "Filtrer les références")
        )
        self.chip_type.clicked.connect(
            lambda: self._open_column_filter("type", "Filtrer les types")
        )
        self.chip_completion.clicked.connect(
            lambda: self._open_column_filter("completion", "Filtrer la complétude")
        )

        for chip in (self.chip_supplier, self.chip_reference,
                     self.chip_type, self.chip_completion):
            h.addWidget(chip)

        h.addStretch(1)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.VLine)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"color:{GRAY_BORDER};")
        h.addWidget(sep)

        btn_import = QtWidgets.QPushButton("＋  Importer un document")
        btn_import.setFont(F_BOLD)
        btn_import.setFixedHeight(32)
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setStyleSheet(f"""
            QPushButton {{
                background:{BLUE}; color:{WHITE};
                border:none; border-radius:8px;
                padding:0 16px; font-size:9pt;
            }}
            QPushButton:hover   {{ background:{BLUE_DARK}; }}
            QPushButton:pressed {{ background:#1E40AF; }}
        """)
        btn_import.clicked.connect(self._open_upload_from_selection)
        h.addWidget(btn_import)
        return bar

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_tabs(self) -> QtWidgets.QTabWidget:
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border:none; background:{WHITE}; margin-top:0;
            }}
            QTabBar::tab {{
                background:transparent; color:{GRAY_TEXT};
                padding:8px 20px;
                border:none; border-bottom:2px solid transparent;
                font-size:9pt;
            }}
            QTabBar::tab:selected {{
                color:{BLUE}; font-weight:700;
                border-bottom:2px solid {BLUE};
            }}
            QTabBar::tab:hover:!selected {{
                color:{DARK}; background:{GRAY_LIGHT};
            }}
            QTabBar {{ background:{WHITE}; border-bottom:1px solid {GRAY_BORDER}; }}
        """)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        tab_all = MainTab(self)
        self.tab_widgets_by_name["Tous"] = tab_all
        self.tabs.addTab(tab_all, "Tous")
        tab_all.rowSelected.connect(self._on_row_selected)

        for bdd in self.enabled_bdds:
            tab = MainTab(self)
            self.tab_widgets_by_name[bdd] = tab
            self.tabs.addTab(tab, bdd)
            tab.rowSelected.connect(self._on_row_selected)

        return self.tabs

    # ── Status bar ───────────────────────────────────────────────────────────
    def _build_statusbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(26)
        bar.setStyleSheet(f"border-top:1px solid {GRAY_BORDER}; background:transparent;")
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        self.lbl_row_count = _make_label("0 lignes", F_SMALL, GRAY_TEXT)
        h.addWidget(self.lbl_row_count)
        h.addStretch(1)
        return bar

    # ── Business logic ────────────────────────────────────────────────────────
    def _refresh_project_data(self):
        self.project_data = self.project_manager.load_project(self.project_dir) or self.project_data
        self.enabled_bdds = list(self.project_data.get("enabled_bdds", JUSTIFICATION_TYPES))

    def _normalize_requirement_code(self, code: str) -> str:
        code = str(code or "").strip()
        for sep in (" — ", " | "):
            if sep in code:
                code = code.split(sep, 1)[0].strip()
        return code

    def _code_matches(self, a: str, b: str) -> bool:
        return self._normalize_requirement_code(a) == self._normalize_requirement_code(b)

    def _is_not_applicable(self, docs: list[dict], code: str) -> bool:
        for doc in docs:
            for na_code in (doc.get("not_applicable_codes") or []):
                if self._code_matches(na_code, code):
                    return True
        return False

    def _doc_applies_to_type(self, doc: dict, justif_type: str) -> bool:
        justif_type = str(justif_type).upper()
        source_type = str(doc.get("source_justification_type", "")).upper()
        stored_bdds = [str(v).upper() for v in (doc.get("stored_in_bdds") or [])]
        return source_type == justif_type or justif_type in stored_bdds

    def _count_documents_in_folder(self, supplier: str, reference: str, justif_type: str) -> int:
        dossier_number = self.project_data.get("dossier_number", "")
        folder = (
            self.project_dir
            / f"BDD {justif_type} {dossier_number}"
            / "Documents"
            / supplier
            / reference
        )
        if not folder.exists() or not folder.is_dir():
            return 0
        return sum(1 for p in folder.iterdir() if p.is_file())

    def _compute_requirement_score(self, docs: list[dict], code: str) -> float:
        matching = [
            d for d in docs
            if any(self._code_matches(c, code) for c in (d.get("requirement_codes") or []))
        ]
        if not matching:
            return 0.0
        estimations = sum(
            1 for d in matching
            if "estimation" in (d.get("stored_filename") or "").lower()
        )
        return max(0.0, min(1.0, (len(matching) - estimations) / len(matching)))

    def _compute_ce_dpe_completion(self, docs: list[dict], req_codes: list[str]) -> float:
        if not req_codes:
            return 0.0
        applicable = [c for c in req_codes if not self._is_not_applicable(docs, c)]
        if not applicable:
            return 1.0
        return sum(self._compute_requirement_score(docs, c) for c in applicable) / len(applicable)

    def _compute_cecc_completion(self, docs: list[dict]) -> float:
        statuses = [(d.get("cecc_fields") or {}).get("status", "").strip() for d in docs]
        valides  = sum(1 for s in statuses if s == "Validé")
        total    = sum(1 for s in statuses if s in ("Validé", "Relancé", "Non conforme", "Estimation"))
        return valides / total if total else 0.0

    def _scan_supplier_reference_pairs(self) -> list[tuple[str, str]]:
        rows = self.project_data.get("rows") or []
        pairs = [
            (str(r.get("supplier", "")).strip(), str(r.get("reference", "")).strip())
            for r in rows
            if str(r.get("supplier", "")).strip()
        ]
        if pairs:
            return sorted(set(pairs), key=lambda x: (x[0].lower(), x[1].lower()))

        dossier_number = self.project_data.get("dossier_number", "")
        pairs = []
        for bdd_type in self.enabled_bdds:
            docs_dir = self.project_dir / f"BDD {bdd_type} {dossier_number}" / "Documents"
            if not docs_dir.exists():
                continue
            for sup_dir in docs_dir.iterdir():
                if sup_dir.is_dir():
                    for ref_dir in sup_dir.iterdir():
                        if ref_dir.is_dir():
                            pairs.append((sup_dir.name, ref_dir.name))
        return sorted(set(pairs), key=lambda x: (x[0].lower(), x[1].lower()))

    def _group_uploaded_documents(self):
        uploaded = get_uploaded_documents(self.project_dir)
        by_sup_ref      = defaultdict(list)
        by_sup_ref_type = defaultdict(list)
        for doc in uploaded:
            sup = doc["supplier"]
            ref = doc["reference"]
            t   = doc["source_justification_type"].upper()
            by_sup_ref[(sup, ref)].append(doc)
            by_sup_ref_type[(sup, ref, t)].append(doc)
        return by_sup_ref, by_sup_ref_type

    def _build_table_rows(self) -> list[dict]:
        pairs              = self._scan_supplier_reference_pairs()
        by_sup_ref, _      = self._group_uploaded_documents()

        # Row metadata (label / order_number from project data)
        row_meta: dict[tuple[str, str], dict] = {}
        for r in (self.project_data.get("rows") or []):
            key = (str(r.get("supplier", "")).strip(), str(r.get("reference", "")).strip())
            row_meta[key] = {
                "label":        r.get("label", ""),
                "order_number": r.get("order_number", ""),
            }

        CE_CODES  = ["2006/42/UE", "2011/65/UE", "2014/30/UE", "2014/68/UE", "AUTRES"]
        DPE_CODES = [
            "2011/65/UE", "2012/19/UE", "2006/66/CE", "1907/2006",
            "2019/1021", "1005/2009", "517/2014", "2017/852",
            "528/2012", "2013/59/Euratom", "2017/821", "2016/1628",
        ]

        rows: list[dict] = []
        for supplier, reference in pairs:
            meta = row_meta.get((supplier, reference), {})
            all_docs_for_ref = by_sup_ref.get((supplier, reference), [])

            for justif_type in self.enabled_bdds:
                docs      = [d for d in all_docs_for_ref if self._doc_applies_to_type(d, justif_type)]
                doc_count = self._count_documents_in_folder(supplier, reference, justif_type)

                if justif_type == "CE":
                    completion_value = self._compute_ce_dpe_completion(docs, CE_CODES)
                elif justif_type == "DPE":
                    completion_value = self._compute_ce_dpe_completion(docs, DPE_CODES)
                else:
                    completion_value = self._compute_cecc_completion(docs)

                rows.append({
                    "supplier":         supplier,
                    "reference":        reference,
                    "label":            meta.get("label", ""),
                    "order_number":     meta.get("order_number", ""),
                    "type":             justif_type,
                    "documents":        doc_count,
                    "documents_db":     len(docs),
                    "completion":       f"{round(completion_value * 100)} %",
                    "completion_value": completion_value,
                    "docs":             docs,
                })
        return rows

    def _apply_filters(self, rows: list[dict]) -> list[dict]:
        for key, allowed in self.column_filters.items():
            if allowed is None:
                continue
            rows = [r for r in rows if str(r.get(key, "")) in allowed]
        return rows

    def _get_column_values(self, rows: list[dict], key: str) -> list[str]:
        return sorted({str(r.get(key, "")) for r in rows}, key=str.lower)

    def _is_filter_active(self, key: str) -> bool:
        allowed = self.column_filters.get(key)
        if allowed is None:
            return False
        all_vals = set(self._get_column_values(self._all_rows_cache, key))
        return set(allowed) != all_vals

    def _update_filter_chips(self):
        self.chip_supplier.set_active(self._is_filter_active("supplier"))
        self.chip_reference.set_active(self._is_filter_active("reference"))
        self.chip_type.set_active(self._is_filter_active("type"))
        self.chip_completion.set_active(self._is_filter_active("completion"))

    def _update_kpis(self, rows: list[dict]):
        def avg_pct(lst): return round(
            sum(r.get("completion_value", 0) for r in lst) / len(lst) * 100
        ) if lst else 0

        ce_rows   = [r for r in rows if r["type"] == "CE"]
        cecc_rows = [r for r in rows if r["type"] == "CECC"]
        dpe_rows  = [r for r in rows if r["type"] == "DPE"]

        ce_pct   = avg_pct(ce_rows)
        cecc_pct = avg_pct(cecc_rows)
        dpe_pct  = avg_pct(dpe_rows)

        self.kpi_ce.set_value(f"{ce_pct} %",   ce_pct)
        self.kpi_cecc.set_value(f"{cecc_pct} %", cecc_pct)
        self.kpi_dpe.set_value(f"{dpe_pct} %",  dpe_pct)

        total_refs   = len({(r["supplier"], r["reference"]) for r in rows})
        refs_with_docs = len({
            (r["supplier"], r["reference"])
            for r in rows if r["documents"] > 0
        })
        self.kpi_refs.set_value(str(total_refs))
        self.kpi_docs.set_value(str(refs_with_docs))

    def _load_table(self, rebuild_cache: bool = True):
        if rebuild_cache:
            self._refresh_project_data()
            self._all_rows_cache = self._build_table_rows()

        self._filtered_rows_cache = self._apply_filters(self._all_rows_cache)
        self._update_kpis(self._filtered_rows_cache)

        # Distribute rows to tabs
        rows_by_tab = {"Tous": list(self._filtered_rows_cache)}
        for bdd in self.enabled_bdds:
            rows_by_tab[bdd] = [r for r in self._filtered_rows_cache if r["type"] == bdd]
        self.current_rows_by_tab = rows_by_tab

        self._load_current_tab()
        self._update_filter_chips()

        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self._lbl_date.setText(now)

    def _load_current_tab(self):
        name = self.tabs.tabText(self.tabs.currentIndex())
        tab  = self.tab_widgets_by_name.get(name)
        if not tab:
            return
        rows = self.current_rows_by_tab.get(name, [])
        tab.load_rows(rows)
        self.lbl_row_count.setText(f"{len(rows)} lignes")
        self.detail_panel.clear()

    def _build_detail_rows(self, row_data: dict) -> list[dict]:
        docs        = row_data.get("docs", [])
        justif_type = row_data.get("type", "").upper()

        if justif_type == "CE":
            expected = CE_REQUIREMENTS
        elif justif_type == "DPE":
            expected = DPE_REQUIREMENTS
        elif justif_type == "CECC":
            return self._build_cecc_rows(docs)
        else:
            return []

        latest_by_code: dict[str, dict] = {}
        for doc in sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True):
            if not self._doc_applies_to_type(doc, justif_type):
                continue
            for i, code in enumerate((doc.get("requirement_codes") or [])):
                nc = self._normalize_requirement_code(code)
                if nc not in latest_by_code:
                    labels = doc.get("requirement_labels") or []
                    latest_by_code[nc] = {
                        "filename": doc.get("stored_filename", ""),
                        "path":     str(self.project_dir / doc["relative_path"]),
                        "label":    labels[i] if i < len(labels) else "",
                    }

        detail_rows: list[dict] = []
        for code, default_label in expected:
            nc   = self._normalize_requirement_code(code)
            data = latest_by_code.get(nc)
            is_na = self._is_not_applicable(docs, code)
            label = (data["label"] if data and data.get("label") else default_label)
            detail_rows.append({
                "requirement": f"{code} | {label}",
                "applicability": "Non applicable" if is_na else "Applicable",
                "filename": "N/A" if is_na else (data["filename"] if data else "—"),
                "path":    "" if is_na else (data["path"] if data else ""),
            })
        return detail_rows

    def _build_cecc_rows(self, docs: list[dict]) -> list[dict]:
        PRETTY = {
            "manufacturer_doc":           "Fournisseur Doc / MANUFACTURER",
            "manufacturer_part_number":   "Manufacturer Part Number",
            "nom_cecc":                   "Nom : CECC",
            "cecc_classement":            "CECC Classement",
            "categorie_export":           "Catégorie export",
            "licence":                    "Licence",
            "numero_licence":             "N° Licence",
            "pays_origine_4a":            "Pays Origine 4a",
            "ear99_value_usd":            "EAR99 Value (USD)",
            "eccn_value_usd":             "ECCN value (USD)",
            "composants_controles_export":"Composants contrôlés export",
            "pays_origine":               "Pays d'origine",
            "classement_export":          "Classement à l'export",
            "code_douanier":              "Code douanier / Tariff Code",
            "cecc_etat":                  "Statut CECC",
        }
        latest_doc = max(docs, key=lambda d: d.get("uploaded_at", ""), default=None)
        fields = ((latest_doc.get("cecc_fields") or {}) if latest_doc else {})
        path   = str(self.project_dir / latest_doc["relative_path"]) if latest_doc else ""

        rows: list[dict] = []
        for key, label in PRETTY.items():
            val = str(fields.get(key, "") or "").strip()
            rows.append({
                "requirement": label,
                "filename":    val or "—",
                "path":        path if key == "nom_cecc" else "",
            })
        return rows

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_tab_changed(self, _index: int):
        self._load_current_tab()

    def _on_row_selected(self, row_data: dict):
        detail_rows = self._build_detail_rows(row_data)
        self.detail_panel.populate(row_data, detail_rows)

    def _open_column_filter(self, key: str, title: str):
        values  = self._get_column_values(self._all_rows_cache, key)
        current = self.column_filters[key] or set(values)
        dlg = FilterPopup(title=title, values=values, checked_values=current, parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            checked = dlg.get_checked_values()
            self.column_filters[key] = None if checked == set(values) else checked
            self._load_table(rebuild_cache=False)

    def _open_upload_from_selection(self):
        name = self.tabs.tabText(self.tabs.currentIndex())
        tab  = self.tab_widgets_by_name.get(name)
        if not tab:
            return
        selected = tab.selected_rows_data()
        if not selected:
            QtWidgets.QMessageBox.information(
                self, "Import", "Sélectionne au moins une ligne du tableau."
            )
            return
        types = {r["type"] for r in selected}
        if len(types) > 1:
            QtWidgets.QMessageBox.warning(
                self, "Import multiple impossible",
                "La sélection multiple doit contenir un seul type de justificatif."
            )
            return
        first = selected[0]
        dlg = UploadDocumentDialog(
            project_dir=self.project_dir,
            supplier=first["supplier"],
            reference=first["reference"],
            preset_justification_type=first["type"],
            batch_targets=[{"supplier": r["supplier"], "reference": r["reference"], "type": r["type"]}
                           for r in selected],
            parent=self,
        )
        dlg.documentSaved.connect(self._load_table)
        dlg.exec()

    def _open_project_settings(self):
        fresh = self.project_manager.load_project(self.project_dir)
        if not fresh:
            QtWidgets.QMessageBox.warning(self, "Paramétrage", "Impossible de relire le projet.")
            return
        dlg = NewProjectDialog(self, project_data=fresh)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        updated = dlg.updated_project_data
        if not updated:
            return
        self.project_data = updated
        self.enabled_bdds = list(self.project_data.get("enabled_bdds", JUSTIFICATION_TYPES))
        self._refresh_project_data()
        self._load_table()
        QtWidgets.QMessageBox.information(self, "Paramétrage", "Projet mis à jour.")

    def _export_templates(self):
        try:
            paths = export_project_templates(self.project_dir)
            QtWidgets.QMessageBox.information(
                self, "Export terminé",
                "Fichiers exportés :\n\n" + "\n".join(str(p) for p in paths),
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur export", str(e))

    def _on_modify_row(self, row_data: dict):
        self._open_upload_from_selection()

    def _on_delete_row(self, row_data: dict):
        sup = row_data.get("supplier", "")
        ref = row_data.get("reference", "")
        ans = QtWidgets.QMessageBox.question(
            self,
            "Supprimer la référence",
            f"Supprimer tous les documents de {sup} / {ref} ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if ans == QtWidgets.QMessageBox.Yes:
            from .metadata_db import delete_uploaded_documents_for_rows
            delete_uploaded_documents_for_rows(self.project_dir, [row_data])
            self._load_table()

    def _open_file(self, file_path: str):
        path = Path(file_path)
        if not path.exists():
            QtWidgets.QMessageBox.warning(
                self, "Fichier introuvable", f"Impossible d'ouvrir :\n\n{path}"
            )
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur d'ouverture", str(e))
