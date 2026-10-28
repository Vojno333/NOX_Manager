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
from PySide6.QtSvg import QSvgRenderer

from .filter_popup import FilterPopup
from .metadata_db import (
    init_metadata_db, get_uploaded_documents, delete_uploaded_documents,
    set_document_requirements, set_document_code_lists, detach_document_file,
)
from .upload_document_dialog import UploadDocumentDialog
from .export_templates import export_project_templates
from .document_rules import (
    CE_REQUIREMENTS, DPE_REQUIREMENTS, JUSTIFICATION_TYPES,
    CECC_FREE_FIELDS, REQ_APPLICABLE, REQ_NA, cecc_field, cecc_status, code_matches, doc_has_file, is_rohs_code,
    normalize_requirement_code, requirement_state,
)
from .project_manager import ProjectManager
from .project_structure import create_folders_and_subfolders
from .new_project_dialog import NewProjectDialog
from .window_geometry import fit_and_center

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

# ── Icônes (SVG → QPixmap) ───────────────────────────────────────────────────
ICONS_DIR = Path(__file__).parent
EU_ICON_PATH = ICONS_DIR / "eu_icon.svg"
DPE_ICON_PATH = ICONS_DIR / "dpe_icon.svg"

def _svg_pixmap(svg_path: Path, size: int = 20) -> QtGui.QPixmap:
    """Rend un fichier SVG en QPixmap."""
    renderer = QSvgRenderer(str(svg_path))
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


# ── KPI card ──────────────────────────────────────────────────────────────────
class KpiCard(QtWidgets.QFrame):
    """White card with icon, value, subtitle and optional progress bar."""

    def __init__(self, icon: str | QtGui.QPixmap, title: str, value: str = "—",
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
        if isinstance(icon, QtGui.QPixmap):
            icon_lbl = QtWidgets.QLabel(icon_frame)
            icon_lbl.setPixmap(icon)
        else:
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

# ── Filterable header ─────────────────────────────────────────────────────────
class FilterableHeader(QtWidgets.QHeaderView):
    """Header with a clickable filter button on designated columns."""
    filterRequested = QtCore.Signal(int)

    FILTER_COLS = {0, 1, 2, 5, 6}  # Fournisseur, Référence, Libellé, Type, Complétude
    _ICON_W = 22
    _ICON_MARGIN = 4

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._active_filters: set[int] = set()
        self._hovered_col: int = -1
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        self.setMouseTracking(True)

    def set_active(self, col: int, active: bool):
        if active:
            self._active_filters.add(col)
        else:
            self._active_filters.discard(col)
        self.viewport().update()

    def _icon_rect(self, rect: QtCore.QRect) -> QtCore.QRect:
        return QtCore.QRect(
            rect.right() - self._ICON_W - self._ICON_MARGIN,
            rect.top() + (rect.height() - self._ICON_W) // 2,
            self._ICON_W, self._ICON_W,
        )

    def paintSection(self, painter, rect, logical_index):
        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()
        if logical_index in self.FILTER_COLS and rect.width() > 34:
            active  = logical_index in self._active_filters
            hovered = logical_index == self._hovered_col
            icon_rect = self._icon_rect(rect)

            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            if active:
                bg, fg = QColor(BLUE), QColor(WHITE)
            elif hovered:
                bg, fg = QColor(GRAY_BORDER), QColor(DARK)
            else:
                bg, fg = QColor("#EEF1F5"), QColor("#9CA3AF")
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(icon_rect, 5, 5)
            painter.setPen(fg)
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(icon_rect, Qt.AlignCenter, "▾")
            painter.restore()

    def _icon_col_at(self, pos) -> int:
        col = self.logicalIndexAt(pos)
        if col in self.FILTER_COLS:
            sec_x = self.sectionViewportPosition(col)
            sec_w = self.sectionSize(col)
            rect  = QtCore.QRect(sec_x, 0, sec_w, self.height())
            # Agrandit la zone de survol/clic pour le confort, mais SANS empiéter
            # sur le bord droit de la section : cette bande reste réservée à la
            # poignée native de redimensionnement (sinon l'icône de filtre la
            # recouvre et le redimensionnement de la colonne devient erratique).
            if self._icon_rect(rect).adjusted(-4, -4, 0, 4).contains(pos):
                return col
        return -1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            col = self._icon_col_at(event.pos())
            if col != -1:
                self.filterRequested.emit(col)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Laisse d'abord QHeaderView gérer son curseur natif (redimensionnement
        # au survol d'un bord de colonne) avant d'imposer le curseur « main »
        # sur l'icône de filtre : sinon ce dernier écrase en permanence le
        # curseur de redimensionnement et celui-ci n'apparaît jamais.
        super().mouseMoveEvent(event)

        col = self._icon_col_at(event.pos())
        if col != self._hovered_col:
            self._hovered_col = col
            self.viewport().update()

        if col != -1:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()

    def leaveEvent(self, event):
        if self._hovered_col != -1:
            self._hovered_col = -1
            self.viewport().update()
        self.unsetCursor()
        super().leaveEvent(event)

# ── Detail panel ──────────────────────────────────────────────────────────────
class DetailPanel(QtWidgets.QFrame):
    requestModify  = QtCore.Signal(dict)   # emits row_data
    requestDelete  = QtCore.Signal(dict)   # emits row_data
    requestOpenDoc = QtCore.Signal(str)    # emits file path
    requestReplaceJustif = QtCore.Signal(dict, str)   # emits row_data, requirement code
    requestDeleteJustif  = QtCore.Signal(dict, str)   # emits row_data, requirement code

    _CODE_ROLE = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(360)
        self.resize(500, self.height())
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
        self._body.addWidget(self._tbl_docs, 1)

        self._body.addWidget(_hline())

        self._lbl_info_title = _make_label("Informations", F_BOLD, DARK)
        self._body.addWidget(self._lbl_info_title)

        self._info_widget = QtWidgets.QWidget()
        self._info_widget.setStyleSheet("background:transparent;")
        self._info_lay = QtWidgets.QVBoxLayout(self._info_widget)
        self._info_lay.setContentsMargins(0, 0, 0, 0)
        self._info_lay.setSpacing(4)
        self._body.addWidget(self._info_widget)

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
        self._btn_delete.setToolTip(
            "Supprime les informations et les documents de cette référence "
            "pour la BDD affichée uniquement (CE, DPE ou CECC)"
        )
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

    def _reset_doc_table(self):
        rows = self._tbl_docs.rowCount()
        cols = self._tbl_docs.columnCount()

        for r in range(rows):
            for c in range(cols):
                self._tbl_docs.removeCellWidget(r, c)

        self._tbl_docs.clearContents()
        self._tbl_docs.setRowCount(0)

    def _make_doc_table(self) -> QtWidgets.QTableWidget:
        t = QtWidgets.QTableWidget(0, 3)
        t.setHorizontalHeaderLabels(["Exigence", "Applicabilité", "Nom du document"])
        t.horizontalHeader().setFont(F_BOLD)
        t.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        t.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        t.setColumnWidth(1, 115)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        t.setSelectionMode(QtWidgets.QTableWidget.NoSelection)
        t.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        t.setMinimumHeight(300)
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
        t.setContextMenuPolicy(Qt.CustomContextMenu)
        t.customContextMenuRequested.connect(self._on_doc_context_menu)
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
        self._reset_doc_table()
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
            self._tbl_docs.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            self._tbl_docs.setColumnWidth(1, 115)

        self._tbl_docs.setRowCount(len(detail_rows))
        for i, detail in enumerate(detail_rows):
            applicability = str(detail.get("applicability", "Applicable"))
            req_item = QtWidgets.QTableWidgetItem(str(detail.get("requirement", "")))
            req_item.setData(Qt.UserRole, detail.get("path", ""))
            self._tbl_docs.setItem(i, 0, req_item)

            if not is_cecc:
                app_label = QtWidgets.QLabel(applicability)
                app_label.setAlignment(Qt.AlignCenter)
                app_label.setStyleSheet("background:transparent; font-weight:700;")

                if applicability == "Applicable":
                    app_label.setStyleSheet(f"color:{GREEN_OK}; background:transparent; font-weight:700;")
                elif applicability == "Non applicable":
                    app_label.setStyleSheet(f"color:{GRAY_TEXT}; background:transparent; font-weight:700;")
                else:
                    app_label.setStyleSheet(f"color:{RED_KO}; background:transparent; font-weight:700;")

                self._tbl_docs.setCellWidget(i, 1, app_label)
                doc_col = 2
            else:
                doc_col = 1

            filename = str(detail.get("filename", "") or "")
            file_item = QtWidgets.QTableWidgetItem(filename)
            if filename:
                file_item.setForeground(QColor(BLUE))
                font = file_item.font()
                font.setUnderline(True)
                file_item.setFont(font)
                file_item.setToolTip(
                    "Cliquer pour ouvrir" if is_cecc
                    else "Cliquer pour ouvrir · clic droit pour remplacer ou supprimer"
                )
            file_item.setData(Qt.UserRole, detail.get("path", ""))
            file_item.setData(self._CODE_ROLE, detail.get("code", ""))
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

    def _on_doc_context_menu(self, pos: QtCore.QPoint):
        """Clic droit sur un nom de document (CE / DPE uniquement)."""
        if not self._row_data or self._tbl_docs.columnCount() != 3:
            return
        index = self._tbl_docs.indexAt(pos)
        if not index.isValid() or index.column() != 2:
            return
        item = self._tbl_docs.item(index.row(), 2)
        if not item or not item.text():
            return
        path = str(item.data(Qt.UserRole) or "")
        code = str(item.data(self._CODE_ROLE) or "")
        if not code:
            return

        menu = QtWidgets.QMenu(self._tbl_docs)
        # Fond explicite : sinon le menu hérite du « background:transparent »
        # du panneau et s'affiche sur fond noir.
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setFont(F_BODY)
        menu.setStyleSheet(f"""
            QMenu {{
                background:{WHITE}; color:{DARK};
                border:1px solid {GRAY_CARD}; border-radius:8px;
                padding:4px;
            }}
            QMenu::item {{
                background:transparent; color:{DARK};
                padding:7px 18px 7px 12px; border-radius:6px;
            }}
            QMenu::item:selected {{ background:{BLUE_LIGHT}; color:{BLUE}; }}
            QMenu::item:disabled {{ color:{GRAY_TEXT}; }}
            QMenu::separator {{ height:1px; background:{GRAY_BORDER}; margin:4px 6px; }}
        """)
        row_data = self._row_data
        act_open = menu.addAction("Ouvrir le document")
        act_open.setEnabled(bool(path))
        act_open.triggered.connect(lambda: self.requestOpenDoc.emit(path))
        menu.addAction("Remplacer le justificatif…").triggered.connect(
            lambda: self.requestReplaceJustif.emit(row_data, code)
        )
        menu.addSeparator()

        # Action destructive en rouge : QMenu::item ne permet pas de styler
        # une action précise, d'où un QLabel dans un QWidgetAction.
        delete_lbl = QtWidgets.QLabel("Supprimer le justificatif")
        delete_lbl.setFont(F_BODY)
        delete_lbl.setStyleSheet(f"""
            QLabel {{ color:{RED_KO}; background:transparent; padding:7px 18px 7px 12px; border-radius:6px; }}
            QLabel:hover {{ background:{RED_BG}; }}
        """)
        act_delete = QtWidgets.QWidgetAction(menu)
        act_delete.setDefaultWidget(delete_lbl)
        act_delete.triggered.connect(lambda: self.requestDeleteJustif.emit(row_data, code))
        menu.addAction(act_delete)

        def _on_delete_clicked(_event):
            menu.close()
            # Après la fermeture du menu : la confirmation est modale.
            QtCore.QTimer.singleShot(0, act_delete.trigger)
        delete_lbl.mouseReleaseEvent = _on_delete_clicked

        menu.exec(self._tbl_docs.viewport().mapToGlobal(pos))

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
         "Complétude",
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

        fh = FilterableHeader(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(fh)

        hh = self.table.horizontalHeader()
        hh.setFont(F_BOLD)

        # Tailles initiales et minimales par colonne
        _col_cfg = [
            # (mode,                                  default_w, min_w)
            (QtWidgets.QHeaderView.Interactive, 120,  80),   # 0 Fournisseur
            (QtWidgets.QHeaderView.Interactive, 110,  80),   # 1 Référence
            (QtWidgets.QHeaderView.Stretch,       0, 140),   # 2 Libellé (étire l'espace libre)
            (QtWidgets.QHeaderView.Interactive,  65,  50),   # 3 MNP
            (QtWidgets.QHeaderView.Interactive, 120,  80),   # 4 N° commande
            (QtWidgets.QHeaderView.Interactive,  75,  60),   # 5 Type
            (QtWidgets.QHeaderView.Interactive, 100,  80),   # 6 Complétude
        ]
        self._col_min_widths = [cfg[2] for cfg in _col_cfg]

        for i, (mode, default_w, _) in enumerate(_col_cfg):
            hh.setSectionResizeMode(i, mode)
            if mode == QtWidgets.QHeaderView.Interactive and default_w:
                hh.resizeSection(i, default_w)

        hh.setMinimumSectionSize(50)
        hh.sectionResized.connect(self._on_section_resized)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border:none; font-size:9pt;
                background:{WHITE}; alternate-background-color:{ALT_ROW};
            }}
            QHeaderView::section {{
                background:{GRAY_LIGHT}; color:{GRAY_TEXT};
                border:none;
                border-right:1px solid {GRAY_BORDER};
                border-bottom:2px solid {GRAY_BORDER};
                padding:7px 8px; font-weight:700; font-size:8pt;
            }}
            QHeaderView::section:last {{
                border-right:none;
            }}
            QTableWidget::item {{
                padding:6px 8px; color:{DARK};
                border-right:1px solid {GRAY_BORDER};
                border-bottom:1px solid {GRAY_BORDER};
            }}
            QTableWidget::item:selected {{
                background:{SEL_BG}; color:{BLUE};
                border-right:1px solid #BFDBFE;
                border-bottom:1px solid #BFDBFE;
            }}
        """)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        h.addWidget(self.table, 1)

    def _on_section_resized(self, logical_index: int, _old: int, new_size: int):
        min_w = self._col_min_widths[logical_index] if logical_index < len(self._col_min_widths) else 50
        if new_size < min_w:
            self.table.horizontalHeader().resizeSection(logical_index, min_w)

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
    (row.get("reference", ""),      Qt.AlignLeft  | Qt.AlignVCenter),
    (row.get("label", ""),          Qt.AlignLeft  | Qt.AlignVCenter),
    (row.get("mnp", ""),            Qt.AlignCenter),
    (row.get("order_number", ""),   Qt.AlignCenter),
    (row.get("type", ""),           Qt.AlignCenter),
    (row.get("completion", "—"),    Qt.AlignCenter),
]

            for ci, (val, align) in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(val))
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, row)
                if ci == 6:  # Complétude column
                    item.setForeground(QtGui.QBrush(QColor(c_color)))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(ri, ci, item)

        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.setSortingEnabled(True)
        #self.table.sortByColumn(0, Qt.AscendingOrder)

        #if self.table.rowCount() > 0:
        #    self.table.selectRow(0)

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
            "supplier": None, "reference": None, "label": None,
            "type": None,     "completion": None,
        }
        self.tab_widgets_by_name: dict[str, MainTab] = {}
        self._all_rows_cache:      list[dict] = []
        self._filtered_rows_cache: list[dict] = []
        self.current_rows_by_tab:  dict[str, list[dict]] = {}

        init_metadata_db(self.project_dir)
        self.setWindowTitle(
            f"NOX_Manager — {project_data.get('dossier_number') or project_data.get('project_name', self.project_dir.name)}"
        )
        fit_and_center(self, 1400, 860, min_w=1000, min_h=620)

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

        self._lbl_date = _make_label("—", F_SMALL, DARK)  # timestamp (non affiché)
        root.addWidget(self._build_content(), 1)

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
            self.project_data.get("dossier_number") or self.project_data.get("project_name", self.project_dir.name)
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
            _svg_pixmap(EU_ICON_PATH, 20), "CE", "0 %", "Complétude",
            bar_color=KPI_BAR_COLORS["CE"], icon_bg="#F5F1DE"
        )
        self.kpi_cecc = KpiCard(
            "📋", "CECC", "0 %", "Complétude",
            bar_color=KPI_BAR_COLORS["CECC"], icon_bg="#EDE9FE"
        )
        self.kpi_dpe = KpiCard(
            _svg_pixmap(DPE_ICON_PATH, 20), "DPE", "0 %", "Complétude",
            bar_color=KPI_BAR_COLORS["DPE"], icon_bg="#D1FAE5"
        )
        for card in (self.kpi_ce, self.kpi_cecc, self.kpi_dpe):
            h.addWidget(card, 1)

        h.addStretch(2)
        return row

    # ── Table section (tabs + detail panel) ───────────────────────────────────
    def _build_table_section(self) -> QtWidgets.QWidget:
        outer = QtWidgets.QWidget()
        outer.setStyleSheet("background:transparent;")

        layout = QtWidgets.QHBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QtWidgets.QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background:{GRAY_BORDER};
                border-radius:3px;
            }}
            QSplitter::handle:hover {{
                background:{BLUE};
            }}
        """)

        layout.addWidget(splitter, 1)

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

        splitter.addWidget(left)

        # Right: detail panel
        self.detail_panel = DetailPanel()
        self.detail_panel.clear()
        self.detail_panel.requestModify.connect(self._on_modify_row)
        self.detail_panel.requestDelete.connect(self._on_delete_row)
        self.detail_panel.requestOpenDoc.connect(self._open_file)
        self.detail_panel.requestReplaceJustif.connect(self._on_replace_justif)
        self.detail_panel.requestDeleteJustif.connect(self._on_delete_justif)

        splitter.addWidget(self.detail_panel)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([1000, 340])

        return outer

    # ── Filter row ────────────────────────────────────────────────────────────
    def _build_filter_row(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet("background:transparent;")
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(6)

        hint = _make_label(
            "💡  Clique sur le ▾ d'une colonne (Fournisseur, Référence, Libellé, Type, Complétude) pour filtrer",
            F_SMALL, GRAY_TEXT,
        )
        h.addWidget(hint)

        h.addStretch(1)

        btn_applicability = QtWidgets.QPushButton("Applicabilité")
        btn_applicability.setFont(F_BOLD)
        btn_applicability.setFixedHeight(34)
        btn_applicability.setMinimumWidth(140)
        btn_applicability.setCursor(Qt.PointingHandCursor)
        btn_applicability.setStyleSheet(f"""
            QPushButton {{
                background:{ORANGE_BG}; color:{ORANGE_WARN};
                border:1px solid {ORANGE_WARN}; border-radius:8px;
                padding:0 18px; font-size:9pt; font-weight:700;
            }}
            QPushButton:hover   {{ background:#FDE8C8; }}
            QPushButton:pressed {{ background:#FBDBA7; }}
        """)
        btn_applicability.setToolTip(
            "Définir l'applicabilité (Applicable / N/A) des exigences, sans importer de document."
        )
        btn_applicability.clicked.connect(lambda: self._open_upload_from_selection(mode="applicability"))
        h.addWidget(btn_applicability)

        btn_import = QtWidgets.QPushButton("＋  Importer un document")
        btn_import.setFont(F_BOLD)
        btn_import.setFixedHeight(34)
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
        btn_import.setToolTip(
            "Importer un document et cocher les exigences qu'il couvre."
        )
        btn_import.clicked.connect(lambda: self._open_upload_from_selection(mode="import"))
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
        tab_all = MainTab(self)
        self.tab_widgets_by_name["Tous"] = tab_all
        self.tabs.addTab(tab_all, "Tous")
        tab_all.rowSelected.connect(self._on_row_selected)
        tab_all.table.horizontalHeader().filterRequested.connect(self._on_column_filter_requested)

        for bdd in self.enabled_bdds:
            tab = MainTab(self)
            self.tab_widgets_by_name[bdd] = tab
            self.tabs.addTab(tab, bdd)
            tab.rowSelected.connect(self._on_row_selected)
            tab.table.horizontalHeader().filterRequested.connect(self._on_column_filter_requested)

        self.tabs.currentChanged.connect(self._on_tab_changed)
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

    def _is_rohs_code(self, code: str) -> bool:
        return is_rohs_code(code)

    def _normalize_requirement_code(self, code: str) -> str:
        return normalize_requirement_code(code)

    def _code_matches(self, a: str, b: str) -> bool:
        return code_matches(a, b)

    def _is_not_applicable(self, docs: list[dict], code: str) -> bool:
        """Statut N/A du code selon le DERNIER enregistrement le mentionnant
        (règle commune avec l'export, cf. `document_rules.requirement_state`)."""
        return requirement_state(docs, code) == REQ_NA

    def _doc_applies_to_type(self, doc: dict, justif_type: str) -> bool:
        justif_type = str(justif_type).upper()
        source_type = str(doc.get("source_justification_type", "")).upper()
        stored_bdds = [str(v).upper() for v in (doc.get("stored_in_bdds") or [])]

        if source_type == justif_type or justif_type in stored_bdds:
            return True

        # Cas particulier : RoHS est commun CE / DPE
        req_codes = doc.get("requirement_codes") or []
        has_rohs = any(self._is_rohs_code(c) for c in req_codes)

        if has_rohs and justif_type in ("CE", "DPE") and source_type in ("CE", "DPE"):
            return True

        return False

    def _compute_requirement_score(self, docs: list[dict], code: str) -> float:
        # Seuls les enregistrements avec un fichier couvrent une exigence :
        # un enregistrement « applicabilité seule » ne prouve rien.
        matching = [
            d for d in docs
            if doc_has_file(d)
            and any(self._code_matches(c, code) for c in (d.get("requirement_codes") or []))
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
        """100 % si le statut CECC le plus récent est « Validé », 0 % sinon.
        Seul le dernier statut compte : un ancien « Relancé » ne doit pas
        diviser par deux une référence validée depuis."""
        latest = max(
            (d for d in docs if cecc_status(d.get("cecc_fields"))),
            key=lambda d: d.get("uploaded_at", ""),
            default=None,
        )
        return 1.0 if latest and cecc_status(latest.get("cecc_fields")) == "Validé" else 0.0

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
                "mnp":          r.get("mnp", ""),
            }

        # 2015/863 est un alias de 2011/65/UE : RoHS n'est compté qu'une fois.
        CE_CODES  = ["2006/42/UE", "2014/35/UE", "2011/65/UE", "2014/30/UE", "2014/68/UE"]
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
                docs = [d for d in all_docs_for_ref if self._doc_applies_to_type(d, justif_type)]

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
                    "mnp":              meta.get("mnp", ""),
                    "type":             justif_type,
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

    _COL_TO_FILTER = {
        0: ("supplier",   "Filtrer les fournisseurs"),
        1: ("reference",  "Filtrer les références"),
        2: ("label",      "Filtrer les libellés"),
        5: ("type",       "Filtrer les types"),
        6: ("completion", "Filtrer la complétude"),
    }

    def _on_column_filter_requested(self, col: int):
        if col in self._COL_TO_FILTER:
            key, title = self._COL_TO_FILTER[col]
            self._open_column_filter(key, title)

    def _update_filter_chips(self):
        col_key_map = {0: "supplier", 1: "reference", 2: "label", 5: "type", 6: "completion"}
        for tab in self.tab_widgets_by_name.values():
            hdr = tab.table.horizontalHeader()
            if isinstance(hdr, FilterableHeader):
                for c, k in col_key_map.items():
                    hdr.set_active(c, self._is_filter_active(k))

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

        
    def _load_table(self, rebuild_cache: bool = True):
        if rebuild_cache:
            self._refresh_project_data()
            self._all_rows_cache = self._build_table_rows()

        self._filtered_rows_cache = self._apply_filters(self._all_rows_cache)
        self._update_kpis(self._filtered_rows_cache)

        rows_by_tab = {"Tous": list(self._filtered_rows_cache)}
        for bdd in self.enabled_bdds:
            rows_by_tab[bdd] = [r for r in self._filtered_rows_cache if r["type"] == bdd]
        self.current_rows_by_tab = rows_by_tab

        self.setUpdatesEnabled(False)
        try:
            for name, tab in self.tab_widgets_by_name.items():
                rows = self.current_rows_by_tab.get(name, [])
                tab.load_rows(rows)
                tab._already_loaded = True
        finally:
            self.setUpdatesEnabled(True)

        self._load_current_tab()
        self._update_filter_chips()

        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self._lbl_date.setText(now)

    def _load_current_tab(self):
        name = self.tabs.tabText(self.tabs.currentIndex())
        tab = self.tab_widgets_by_name.get(name)
        if not tab:
            return

        rows = self.current_rows_by_tab.get(name, [])

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
            if not self._doc_applies_to_type(doc, justif_type) or not doc_has_file(doc):
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
            state = requirement_state(docs, code)
            is_na = state == REQ_NA
            label = default_label
            detail_rows.append({
                "code":        code,
                "requirement": f"{code} | {label}",
                "applicability": (
                    "Non applicable" if is_na
                    else "Applicable" if (data or state == REQ_APPLICABLE)
                    else "Non défini"
                ),
                "filename": "" if is_na else (data["filename"] if data else ""),
                "path":    "" if is_na else (data["path"] if data else ""),
            })
        return detail_rows

    def _build_cecc_rows(self, docs: list[dict]) -> list[dict]:
        latest_doc = max(docs, key=lambda d: d.get("uploaded_at", ""), default=None)
        fields = ((latest_doc.get("cecc_fields") or {}) if latest_doc else {})
        path   = str(self.project_dir / latest_doc["relative_path"]) if latest_doc else ""

        rows: list[dict] = []
        for key, label, _col in CECC_FREE_FIELDS:
            val = cecc_field(fields, key)
            rows.append({
                "requirement": label,
                "filename":    val,
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

    def _open_upload_from_selection(self, mode: str = "import"):
        name = self.tabs.tabText(self.tabs.currentIndex())
        tab  = self.tab_widgets_by_name.get(name)
        if not tab:
            return
        selected = tab.selected_rows_data()
        if not selected:
            QtWidgets.QMessageBox.information(
                self, "Sélection", "Sélectionne au moins une ligne du tableau."
            )
            return
        types = {r["type"] for r in selected}
        if len(types) > 1:
            QtWidgets.QMessageBox.warning(
                self, "Import multiple impossible",
                "La sélection multiple doit contenir un seul type de justificatif."
            )
            return

        if mode == "applicability" and "CECC" in types:
            QtWidgets.QMessageBox.information(
                self, "Applicabilité",
                "La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC. "
                "Utilise «Importer un document» pour ce type."
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
            mode=mode,
            parent=self,
        )
        dlg.documentSaved.connect(self._reload_after_import)
        dlg.exec()

    def _reload_after_import(self):
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._load_table(rebuild_cache=True)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

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
            results = export_project_templates(self.project_dir)
            msg = "Fichiers exportés :\n\n" + "\n".join(str(p) for p, _ in results)
            archived = [a for _, a in results if a]
            if archived:
                msg += "\n\nAnciennes versions déplacées dans OLD :\n\n" + "\n".join(a.name for a in archived)
            QtWidgets.QMessageBox.information(self, "Export terminé", msg)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur export", str(e))

    def _on_modify_row(self, row_data: dict):
        self._open_upload_from_selection()

    def _on_delete_row(self, row_data: dict):
        """Vide la référence pour la SEULE BDD de la ligne (CE, DPE ou CECC) :
        enregistrements en base et fichiers du dossier de cette BDD. Les
        autres BDD et la ligne du projet (`project.json`) sont conservées."""
        sup   = row_data.get("supplier", "")
        ref   = row_data.get("reference", "")
        jtype = str(row_data.get("type", "")).upper()
        bdd_dirname = f"BDD {jtype} {self.project_data.get('dossier_number', '')}"

        # Enregistrements de cette BDD : ceux dont le fichier est rangé dans
        # son dossier, et les enregistrements « applicabilité seule » saisis
        # depuis elle. La copie RoHS rangée dans l'autre BDD est conservée,
        # mais réduite à RoHS (`to_trim`) : saisie depuis cette BDD, elle y
        # compterait encore pour toutes ses exigences (ex. Machine).
        to_delete, to_trim = [], []
        for d in get_uploaded_documents(self.project_dir):
            if d["supplier"] != sup or d["reference"] != ref:
                continue
            from_this_bdd = str(d.get("source_justification_type", "")).upper() == jtype
            if doc_has_file(d) and Path(d["relative_path"]).parts[0] == bdd_dirname:
                to_delete.append(d)
            elif from_this_bdd and not doc_has_file(d):
                to_delete.append(d)
            elif from_this_bdd:
                to_trim.append(d)

        # Fichiers : ceux des enregistrements supprimés + tout fichier resté
        # dans le dossier de la référence pour cette BDD.
        files = {self.project_dir / d["relative_path"] for d in to_delete if doc_has_file(d)}
        ref_dir = self.project_dir / bdd_dirname / "Documents" / sup / ref
        try:
            files |= {p for p in ref_dir.iterdir() if p.is_file()}
        except OSError:
            pass
        files = {f for f in files if f.exists()}

        if not to_delete and not files:
            QtWidgets.QMessageBox.information(
                self, "Supprimer la référence",
                f"Aucune information ni aucun document {jtype} pour {sup} / {ref}."
            )
            return

        names = sorted(f.name for f in files)
        shown = "\n".join(f"• {n}" for n in names[:15])
        if len(names) > 15:
            shown += f"\n• … et {len(names) - 15} autre(s)"
        msg = (
            f"Supprimer les informations {jtype} de {sup} / {ref} ?\n\n"
            f"• {len(to_delete)} enregistrement(s) {jtype} (exigences, applicabilité"
            f"{', champs CECC' if jtype == 'CECC' else ''})\n"
            f"• {len(files)} fichier(s) du dossier « {bdd_dirname} »"
            + (f" :\n{shown}" if shown else "")
            + "\n\nLes autres BDD ne sont pas touchées. Cette action est irréversible."
        )
        if jtype in ("CE", "DPE"):
            msg += ("\n\nRoHS est commun au CE et au DPE : un justificatif RoHS "
                    "rangé dans l'autre BDD restera visible ici.")
        ans = QtWidgets.QMessageBox.warning(
            self, "Supprimer la référence", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if ans != QtWidgets.QMessageBox.Yes:
            return

        delete_uploaded_documents(self.project_dir, [d["id"] for d in to_delete])
        for d in to_trim:
            self._keep_only_rohs(d)
        still_used = {
            (self.project_dir / d["relative_path"]).resolve()
            for d in get_uploaded_documents(self.project_dir) if doc_has_file(d)
        }
        failed = []
        for f in files:
            if f.resolve() in still_used:
                continue
            try:
                f.unlink(missing_ok=True)
            except OSError as e:
                failed.append(f"{f.name} : {e}")
        if failed:
            QtWidgets.QMessageBox.warning(
                self, "Suppression incomplète",
                "Certains fichiers n'ont pas pu être supprimés (ouverts ailleurs ?) :\n\n"
                + "\n".join(failed)
            )
        self._reload_and_reselect(row_data)

    def _keep_only_rohs(self, doc: dict):
        """Réduit un enregistrement à ses codes RoHS (seule exigence commune
        CE / DPE), labels gardés alignés sur leurs codes."""
        def rohs_pairs(codes_key: str, labels_key: str | None):
            codes  = list(doc.get(codes_key) or [])
            labels = list(doc.get(labels_key) or []) if labels_key else []
            kept = [i for i, c in enumerate(codes) if self._is_rohs_code(c)]
            return [codes[i] for i in kept], [labels[i] for i in kept if i < len(labels)]

        req_codes, req_labels = rohs_pairs("requirement_codes", "requirement_labels")
        na_codes, na_labels   = rohs_pairs("not_applicable_codes", "not_applicable_labels")
        set_document_code_lists(self.project_dir, doc["id"], {
            "requirement_codes":     req_codes,
            "requirement_labels":    req_labels,
            "applicable_codes":      rohs_pairs("applicable_codes", None)[0],
            "not_applicable_codes":  na_codes,
            "not_applicable_labels": na_labels,
        })
        if not req_codes and doc_has_file(doc):
            # Ne justifie plus rien : même traitement qu'un justificatif retiré.
            self._detach_and_delete_file(doc)

    # ── Justificatif d'une exigence (clic droit dans le panneau de détail) ──
    def _justif_docs_for_code(self, row_data: dict, code: str, before: str | None = None) -> list[dict]:
        """Enregistrements AVEC fichier de la ligne (fournisseur / référence /
        BDD) qui couvrent *code*. *before* : seulement ceux déposés avant."""
        sup, ref, jtype = row_data["supplier"], row_data["reference"], row_data["type"]
        return [
            d for d in get_uploaded_documents(self.project_dir)
            if d["supplier"] == sup and d["reference"] == ref
            and self._doc_applies_to_type(d, jtype)
            and doc_has_file(d)
            and any(self._code_matches(c, code) for c in (d.get("requirement_codes") or []))
            and (before is None or d.get("uploaded_at", "") < before)
        ]

    def _remove_justif_for_codes(self, docs: list[dict], removed_codes: list[str]) -> list[str]:
        """Retire *removed_codes* des exigences couvertes par *docs* (en une
        seule écriture par enregistrement). Un enregistrement qui ne couvre
        plus rien garde son applicabilité mais perd son fichier, supprimé du
        disque s'il n'est plus référencé. Renvoie les fichiers supprimés."""
        removed_files: list[str] = []
        for doc in docs:
            codes  = list(doc.get("requirement_codes") or [])
            labels = list(doc.get("requirement_labels") or [])
            kept = [
                i for i, c in enumerate(codes)
                if not any(self._code_matches(c, r) for r in removed_codes)
            ]
            if len(kept) == len(codes):
                continue
            new_codes  = [codes[i] for i in kept]
            new_labels = [labels[i] for i in kept if i < len(labels)]
            set_document_requirements(self.project_dir, doc["id"], new_codes, new_labels)
            if not new_codes:
                removed = self._detach_and_delete_file(doc)
                if removed:
                    removed_files.append(removed)
        return removed_files

    def _detach_and_delete_file(self, doc: dict) -> str | None:
        """L'enregistrement perd son fichier (il garde son applicabilité) ;
        le fichier est supprimé du disque s'il n'est plus référencé.
        Renvoie le nom du fichier supprimé."""
        detach_document_file(self.project_dir, doc["id"])
        rel = doc["relative_path"]
        if any(d["relative_path"] == rel for d in get_uploaded_documents(self.project_dir)):
            return None
        try:
            (self.project_dir / rel).unlink(missing_ok=True)
        except OSError as e:
            QtWidgets.QMessageBox.warning(
                self, "Suppression du fichier",
                f"Impossible de supprimer le fichier :\n\n{self.project_dir / rel}\n\n{e}"
            )
            return None
        return doc.get("stored_filename") or Path(rel).name

    def _on_delete_justif(self, row_data: dict, code: str):
        docs = self._justif_docs_for_code(row_data, code)
        if not docs:
            return
        names = sorted({d.get("stored_filename", "") for d in docs})
        msg = (
            f"Retirer le justificatif de l'exigence {code} pour "
            f"{row_data['supplier']} / {row_data['reference']} ?\n\n"
            + "\n".join(f"• {n}" for n in names)
            + "\n\nL'exigence reste «Applicable», sans document. Un fichier qui "
              "ne justifie plus aucune exigence est supprimé du dossier projet."
        )
        if self._is_rohs_code(code):
            msg += "\n\nRoHS est commun au CE et au DPE : le retrait s'applique aux deux."
        ans = QtWidgets.QMessageBox.question(
            self, "Supprimer le justificatif", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if ans != QtWidgets.QMessageBox.Yes:
            return
        self._remove_justif_for_codes(docs, [code])
        self._reload_and_reselect(row_data)

    def _on_replace_justif(self, row_data: dict, code: str):
        started_at = datetime.now().isoformat()
        dlg = UploadDocumentDialog(
            project_dir=self.project_dir,
            supplier=row_data["supplier"],
            reference=row_data["reference"],
            preset_justification_type=row_data["type"],
            preset_checked_codes=[code],
            parent=self,
        )
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return

        # Le nouveau document remplace les anciens pour TOUTES les exigences
        # qu'il couvre : celle du clic droit, mais aussi celles cochées en plus
        # dans le dialogue (ou seulement celles-ci si elle a été décochée).
        sup, ref = row_data["supplier"], row_data["reference"]
        file_docs = [
            d for d in get_uploaded_documents(self.project_dir)
            if d["supplier"] == sup and d["reference"] == ref and doc_has_file(d)
        ]
        new_docs = [d for d in file_docs if d.get("uploaded_at", "") >= started_at]
        new_codes = [c for d in new_docs for c in (d.get("requirement_codes") or [])]
        new_types = {str(d.get("source_justification_type", "")).upper() for d in new_docs}
        old_docs = [
            d for d in file_docs
            if d.get("uploaded_at", "") < started_at
            and any(self._doc_applies_to_type(d, t) for t in new_types)
        ]
        if new_codes:
            self._remove_justif_for_codes(old_docs, new_codes)
        self._reload_and_reselect(row_data)

    def _reload_and_reselect(self, row_data: dict):
        """Recharge le tableau puis réaffiche le détail de la même ligne."""
        self._reload_after_import()
        key = (row_data["supplier"], row_data["reference"], row_data["type"])
        fresh = next(
            (r for r in self._all_rows_cache
             if (r["supplier"], r["reference"], r["type"]) == key),
            None,
        )
        if fresh:
            self._on_row_selected(fresh)

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