"""Éléments visuels du tableau de suivi : palette, polices, carte d'indicateur,
pastilles, badge de complétion, en-tête de colonne filtrable.

Repris de `00_ancien/wikidocs_qt/project_dashboard_window.py`.
"""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtSvg import QSvgRenderer

from app.core.config import ressource

# ── Palette ───────────────────────────────────────────────────────────────────
TOPBAR_BG = "#111827"
TOPBAR_FG = "#CBD5E1"
WHITE = "#FFFFFF"
BG = "#F6F8FB"
BLUE = "#2563EB"
BLUE_LIGHT = "#EFF6FF"
BLUE_DARK = "#1D4ED8"
GREEN_OK = "#059669"
GREEN_BG = "#D1FAE5"
ORANGE_WARN = "#D97706"
ORANGE_BG = "#FEF3C7"
RED_KO = "#DC2626"
RED_BG = "#FEE2E2"
PURPLE = "#7C3AED"
PURPLE_BG = "#EDE9FE"
GRAY_BORDER = "#E5E7EB"
GRAY_CARD = "#D9E2EC"
GRAY_TEXT = "#6B7280"
GRAY_LIGHT = "#F8FAFC"
DARK = "#111827"
ALT_ROW = "#F8FAFC"
SEL_BG = "#EFF6FF"
SEL_FG = BLUE

# Type badge colours  (bg, fg)
TYPE_COLORS: dict[str, tuple[str, str]] = {
    "CE": (ORANGE_BG, "#92400E"),
    "CECC": (PURPLE_BG, "#5B21B6"),
    "DPE": (GREEN_BG, "#065F46"),
}

# KPI bar colours
KPI_BAR_COLORS: dict[str, str] = {
    "CE": ORANGE_WARN,
    "CECC": PURPLE,
    "DPE": GREEN_OK,
}

# ── Fonts ─────────────────────────────────────────────────────────────────────
F_BODY = QFont("Segoe UI", 9)
F_BOLD = QFont("Segoe UI", 9, QFont.Bold)
F_SMALL = QFont("Segoe UI", 8)
F_TINY = QFont("Segoe UI", 7)
F_H1 = QFont("Segoe UI", 13, QFont.Bold)
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
EU_ICON_PATH = ressource("eu_icon.svg")
DPE_ICON_PATH = ressource("dpe_icon.svg")


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

    def __init__(
        self,
        icon: str | QtGui.QPixmap,
        title: str,
        value: str = "—",
        subtitle: str = "",
        bar_color: str = "",
        icon_bg: str = "#F0F4FF",
        parent=None,
    ):
        super().__init__(parent)
        self._bar_color = bar_color
        self._bar_fill: QtWidgets.QFrame | None = None
        self._bar_bg: QtWidgets.QFrame | None = None
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
        bg = BLUE_LIGHT if active else WHITE
        border = BLUE if active else GRAY_BORDER
        color = BLUE if active else DARK
        fw = "700" if active else "400"
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
        bg, fg = GREEN_BG, "#065F46"
    elif val == 0:
        bg, fg = RED_BG, "#991B1B"
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
            self._ICON_W,
            self._ICON_W,
        )

    def paintSection(self, painter, rect, logical_index):
        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()
        if logical_index in self.FILTER_COLS and rect.width() > 34:
            active = logical_index in self._active_filters
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
            rect = QtCore.QRect(sec_x, 0, sec_w, self.height())
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
