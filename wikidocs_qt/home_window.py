from __future__ import annotations

from pathlib import Path
from datetime import datetime
import getpass

from PySide6 import QtCore, QtGui, QtWidgets

from .project_manager import ProjectManager
from .new_project_dialog import NewProjectDialog
from .project_dashboard_window import ProjectDashboardWindow
from .window_geometry import fit_and_center
from .utils import human_size


# ──────────────────────────────────────────────────────────────────────────────
# Stylesheet
# ──────────────────────────────────────────────────────────────────────────────
STYLESHEET = """
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


# ──────────────────────────────────────────────────────────────────────────────
# Icon helpers  (SVG → QIcon / QPixmap without external files)
# ──────────────────────────────────────────────────────────────────────────────
def _svg_icon(svg_body: str, size: int = 16) -> QtGui.QIcon:
    """Render an inline SVG string into a QIcon."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'{svg_body}</svg>'
    )
    renderer = QtGui.QImageReader()
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    renderer_svg = QtSvg_renderer(svg.encode(), size)
    if renderer_svg:
        painter = QtGui.QPainter(pixmap)
        renderer_svg.render(painter)
        painter.end()
    return QtGui.QIcon(pixmap)


def _make_folder_icon(color: str = "#2563eb", size: int = 18) -> QtGui.QPixmap:
    """Return a simple folder pixmap drawn with QPainter."""
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    pen = QtGui.QPen(QtGui.QColor(color))
    pen.setWidthF(1.6)
    p.setPen(pen)
    p.setBrush(QtCore.Qt.NoBrush)
    # bottom rect
    p.drawRoundedRect(1, 6, size - 2, size - 8, 2, 2)
    # tab
    tab = QtGui.QPainterPath()
    tab.moveTo(1, 7)
    tab.lineTo(1, 4)
    tab.lineTo(7, 4)
    tab.lineTo(9, 6)
    tab.lineTo(size - 1, 6)
    p.drawPath(tab)
    p.end()
    return pm


def _make_icon_pixmap(color: str, paths: list[str], size: int = 16) -> QtGui.QPixmap:
    """Generic QPainter icon from a list of SVG-like path strings (very simplified)."""
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.transparent)
    return pm

def get_windows_username() -> str:
    """Retourne le nom de l'utilisateur Windows courant."""
    try:
        return getpass.getuser()
    except Exception:
        return "Utilisateur"


# ──────────────────────────────────────────────────────────────────────────────
# Info row widget
# ──────────────────────────────────────────────────────────────────────────────
class InfoRow(QtWidgets.QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(8)

        self.key_label = QtWidgets.QLabel(label, self)
        self.key_label.setObjectName("infoKey")

        self.val_label = QtWidgets.QLabel("—", self)
        self.val_label.setObjectName("infoValue")
        self.val_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        lay.addWidget(self.key_label)
        lay.addStretch(1)
        lay.addWidget(self.val_label)

        # bottom divider
        self.setAutoFillBackground(False)

    def set_value(self, value: str):
        self.val_label.setText(value or "—")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QColor("#f3f4f6"))
        painter.drawLine(20, self.height() - 1, self.width() - 20, self.height() - 1)


# ──────────────────────────────────────────────────────────────────────────────
# Search overlay label (magnifier icon inside QLineEdit)
# ──────────────────────────────────────────────────────────────────────────────
class SearchLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchBox")
        self.setPlaceholderText("Rechercher un projet…")
        self._icon_label = QtWidgets.QLabel(self)
        self._icon_label.setText("🔍")
        self._icon_label.setStyleSheet("font-size:12px; color:#9ca3af; background:transparent;")
        self._icon_label.move(8, 0)
        self._icon_label.setFixedSize(20, 32)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._icon_label.move(8, (self.height() - self._icon_label.height()) // 2)


# ──────────────────────────────────────────────────────────────────────────────
# HomeWindow
# ──────────────────────────────────────────────────────────────────────────────
class HomeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOX_Manager")
        fit_and_center(self, 1360, 860, min_w=1000, min_h=620)
        self.setStyleSheet(STYLESHEET)

        self.project_manager = ProjectManager()
        self.project_windows: list[ProjectDashboardWindow] = []

        self._build_ui()
        self._load_recent_projects()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QtWidgets.QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_hero())

        content = QtWidgets.QWidget(self)
        content_lay = QtWidgets.QVBoxLayout(content)
        content_lay.setContentsMargins(28, 20, 28, 0)
        content_lay.setSpacing(16)

        content_lay.addLayout(self._build_actions_row())
        content_lay.addLayout(self._build_main_area(), 1)

        root.addWidget(content, 1)
        root.addWidget(self._build_status_bar())


    # ── Hero ──────────────────────────────────────────────────────────────────

    def _build_hero(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame(self)
        frame.setObjectName("heroFrame")
        frame.setFixedHeight(80)

        lay = QtWidgets.QHBoxLayout(frame)
        lay.setContentsMargins(32, 0, 32, 0)
        lay.setSpacing(0)

        # left: title + subtitle
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(2)
        title = QtWidgets.QLabel("NOX_Manager", self)
        title.setObjectName("heroTitle")
        subtitle = QtWidgets.QLabel("Gestionnaire de projets documentaires", self)
        subtitle.setObjectName("heroSubtitle")
        left.addWidget(title)
        left.addWidget(subtitle)

        lay.addLayout(left)
        lay.addStretch(1)

        # right: version + user
        right = QtWidgets.QHBoxLayout()
        right.setSpacing(20)

        version = QtWidgets.QLabel("ⓘ  Version 1.1.0", self)
        version.setObjectName("versionLabel")
        right.addWidget(version)

        username = get_windows_username()
        self.user_button = QtWidgets.QPushButton(f"👤  Utilisateur : {username} ", self)
        self.user_button.setObjectName("userButton")
        right.addWidget(self.user_button)

        lay.addLayout(right)
        return frame

    # ── Actions row ───────────────────────────────────────────────────────────

    def _build_actions_row(self) -> QtWidgets.QHBoxLayout:
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)

        self.new_project_button = QtWidgets.QPushButton("  +  Nouveau projet", self)
        self.new_project_button.setObjectName("primaryButton")
        self.new_project_button.clicked.connect(self._create_new_project)

        self.open_project_button = QtWidgets.QPushButton("  🗁  Ouvrir un projet", self)
        self.open_project_button.setObjectName("outlineButton")
        self.open_project_button.clicked.connect(self._open_existing_project)

        row.addWidget(self.new_project_button)
        row.addWidget(self.open_project_button)
        row.addStretch(1)
        return row

    # ── Main area (left panel + right panel) ──────────────────────────────────

    def _build_main_area(self) -> QtWidgets.QHBoxLayout:
        area = QtWidgets.QHBoxLayout()
        area.setSpacing(16)
        area.addWidget(self._build_left_panel(), 1)
        area.addWidget(self._build_right_panel())
        return area

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame(self)
        frame.setObjectName("panelLeft")

        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header row
        header = QtWidgets.QWidget(frame)
        header_lay = QtWidgets.QHBoxLayout(header)
        header_lay.setContentsMargins(20, 16, 16, 12)
        header_lay.setSpacing(12)

        panel_title = QtWidgets.QLabel("Projets récents", frame)
        panel_title.setObjectName("panelTitle")
        header_lay.addWidget(panel_title)
        header_lay.addStretch(1)

        self.search_edit = SearchLineEdit(frame)
        self.search_edit.textChanged.connect(self._filter_projects)
        header_lay.addWidget(self.search_edit)

        lay.addWidget(header)

        # Tree
        self.recent_list = QtWidgets.QTreeWidget(frame)
        self.recent_list.setObjectName("projectTree")
        self.recent_list.setColumnCount(4)
        self.recent_list.setHeaderLabels(["Numéro de dossier", "Emplacement", "Dernière ouverture", ""])
        self.recent_list.setRootIsDecorated(False)
        self.recent_list.setAlternatingRowColors(True)
        self.recent_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.recent_list.setIndentation(0)
        self.recent_list.setUniformRowHeights(True)
        self.recent_list.itemDoubleClicked.connect(self._open_selected_recent_project)
        self.recent_list.itemSelectionChanged.connect(self._on_selection_changed)

        hdr = self.recent_list.header()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        hdr.resizeSection(3, 36)
        hdr.setStretchLastSection(False)

        lay.addWidget(self.recent_list, 1)

        # Hint
        hint = QtWidgets.QLabel("  ⓘ  Double-cliquez sur un projet pour l'ouvrir", frame)
        hint.setObjectName("hintLabel")
        sep1 = QtWidgets.QFrame(frame)
        sep1.setObjectName("hLine")
        sep1.setFrameShape(QtWidgets.QFrame.HLine)
        lay.addWidget(sep1)
        lay.addWidget(hint)

        # Footer buttons
        sep2 = QtWidgets.QFrame(frame)
        sep2.setObjectName("hLine")
        sep2.setFrameShape(QtWidgets.QFrame.HLine)
        lay.addWidget(sep2)

        footer = QtWidgets.QWidget(frame)
        footer_lay = QtWidgets.QHBoxLayout(footer)
        footer_lay.setContentsMargins(16, 10, 16, 14)
        footer_lay.setSpacing(10)

        self.open_recent_button = QtWidgets.QPushButton("  🗁  Ouvrir", frame)
        self.open_recent_button.setObjectName("openFooterButton")
        self.open_recent_button.clicked.connect(self._open_selected_recent_project)

        self.refresh_button = QtWidgets.QPushButton("  ↻  Actualiser", frame)
        self.refresh_button.setObjectName("ghostButton")
        self.refresh_button.clicked.connect(self._load_recent_projects)

        self.delete_button = QtWidgets.QPushButton("  🗑  Supprimer", frame)
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self._delete_selected_project)

        self.footer_status = QtWidgets.QLabel("Aucun projet sélectionné", frame)
        self.footer_status.setObjectName("footerStatus")

        footer_lay.addWidget(self.open_recent_button)
        footer_lay.addWidget(self.refresh_button)
        footer_lay.addWidget(self.delete_button)
        footer_lay.addStretch(1)
        footer_lay.addWidget(self.footer_status)

        lay.addWidget(footer)
        return frame

    # ── Right panel ───────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame(self)
        frame.setObjectName("panelRight")
        frame.setFixedWidth(310)

        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        title = QtWidgets.QLabel("Informations projet", frame)
        title.setObjectName("infoPanelTitle")
        lay.addWidget(title)

        sep = QtWidgets.QFrame(frame)
        sep.setObjectName("hLine")
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        lay.addWidget(sep)

        # Stack: placeholder vs details
        self.info_stack = QtWidgets.QStackedWidget(frame)

        # Page 0: placeholder
        placeholder = QtWidgets.QWidget()
        ph_lay = QtWidgets.QVBoxLayout(placeholder)
        ph_lay.setAlignment(QtCore.Qt.AlignCenter)
        ph_lay.setSpacing(12)

        icon_wrap = QtWidgets.QLabel(placeholder)
        icon_wrap.setFixedSize(72, 72)
        icon_wrap.setAlignment(QtCore.Qt.AlignCenter)
        icon_wrap.setStyleSheet(
            "background:#eff6ff; border-radius:36px; font-size:28px;"
        )
        icon_wrap.setText("🗁")

        ph_title = QtWidgets.QLabel("Sélectionnez un projet", placeholder)
        ph_title.setObjectName("infoPlaceholderTitle")
        ph_title.setAlignment(QtCore.Qt.AlignCenter)

        ph_sub = QtWidgets.QLabel("Les informations détaillées\ns'afficheront ici.", placeholder)
        ph_sub.setObjectName("infoPlaceholderSub")
        ph_sub.setAlignment(QtCore.Qt.AlignCenter)

        ph_lay.addStretch(1)
        ph_lay.addWidget(icon_wrap, 0, QtCore.Qt.AlignCenter)
        ph_lay.addWidget(ph_title)
        ph_lay.addWidget(ph_sub)
        ph_lay.addStretch(1)

        self.info_stack.addWidget(placeholder)

        # Page 1: details
        details_widget = QtWidgets.QWidget()
        details_lay = QtWidgets.QVBoxLayout(details_widget)
        details_lay.setContentsMargins(0, 0, 0, 0)
        details_lay.setSpacing(0)

        self._row_created   = InfoRow("Créé le :",         details_widget)
        self._row_opened    = InfoRow("Dernière ouverture :", details_widget)
        self._row_refs      = InfoRow("Références :",       details_widget)
        self._row_docs      = InfoRow("Documents :",        details_widget)
        self._row_size      = InfoRow("Taille du projet :", details_widget)

        for row in (self._row_created, self._row_opened, self._row_refs,
                    self._row_docs, self._row_size):
            details_lay.addWidget(row)

        details_lay.addStretch(1)
        self.info_stack.addWidget(details_widget)

        lay.addWidget(self.info_stack, 1)
        return frame

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_status_bar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget(self)
        bar_lay = QtWidgets.QHBoxLayout(bar)
        bar_lay.setContentsMargins(32, 0, 32, 12)

        self.status_label = QtWidgets.QLabel("", bar)
        self.status_label.setObjectName("statusBar")
        bar_lay.addWidget(self.status_label)
        return bar

    # ── Data loading ──────────────────────────────────────────────────────────

    def _format_datetime(self, iso_text: str) -> str:
        if not iso_text:
            return "—"
        try:
            dt = datetime.fromisoformat(iso_text)
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return iso_text

    def _load_recent_projects(self):
        self.recent_list.clear()
        self._show_info_placeholder()

        projects = self.project_manager.get_recent_projects()

        for project in projects:
            name           = project.get("name", "Projet sans nom")
            dossier_number = project.get("dossier_number") or name
            path           = project.get("path", "")
            last_opened    = self._format_datetime(project.get("last_opened", ""))

            item = QtWidgets.QTreeWidgetItem([dossier_number, path, last_opened, "⋮"])
            item.setData(0, QtCore.Qt.UserRole, path)
            item.setData(0, QtCore.Qt.UserRole + 1, project)  # full project data

            # Folder icon on column 0
            folder_pm = _make_folder_icon("#2563eb", 18)
            item.setIcon(0, QtGui.QIcon(folder_pm))

            # Style the path column
            item.setForeground(1, QtGui.QColor("#6b7280"))

            # Centre the menu column
            item.setTextAlignment(3, QtCore.Qt.AlignCenter)

            self.recent_list.addTopLevelItem(item)

        self.footer_status.setText("Aucun projet sélectionné")
        self.status_label.setText(f"  🖥  {len(projects)} projet(s) récent(s) chargé(s).")

    # ── Filtering ─────────────────────────────────────────────────────────────

    def _filter_projects(self, text: str):
        text = text.lower()
        for i in range(self.recent_list.topLevelItemCount()):
            item = self.recent_list.topLevelItem(i)
            project = item.data(0, QtCore.Qt.UserRole + 1) or {}
            visible = (
                text in item.text(0).lower()
                or text in item.text(1).lower()
                or text in str(project.get("name", "")).lower()
            )
            item.setHidden(not visible)

    # ── Selection ─────────────────────────────────────────────────────────────

    def _on_selection_changed(self):
        item = self.recent_list.currentItem()
        if not item:
            self._show_info_placeholder()
            self.footer_status.setText("Aucun projet sélectionné")
            return

        name = item.text(0)
        project_data: dict = item.data(0, QtCore.Qt.UserRole + 1) or {}

        self.footer_status.setText(name)
        self._show_project_info(project_data)

    def _show_info_placeholder(self):
        self.info_stack.setCurrentIndex(0)

    def _show_project_info(self, data: dict):
        project_dir = Path(data.get("path", "")) if data.get("path") else None
        if project_dir and project_dir.exists():
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                stats = self._compute_project_stats(project_dir)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
        else:
            stats = {}

        self._row_created.set_value(
            self._format_datetime(stats.get("created_at", "")) or "—"
        )
        self._row_opened.set_value(
            self._format_datetime(data.get("last_opened", "")) or "—"
        )
        self._row_refs.set_value(str(stats.get("references_count", "—")))
        self._row_docs.set_value(str(stats.get("documents_count", "—")))
        self._row_size.set_value(stats.get("size", "—"))
        self.info_stack.setCurrentIndex(1)

    def _compute_project_stats(self, project_dir: Path) -> dict:
        """Infos calculées à la volée à partir du dossier projet (lu sur
        disque, jamais mises en cache : reflètent toujours l'état réel)."""
        stats: dict = {}

        project_data = self.project_manager.load_project(project_dir)
        stats["created_at"] = (project_data or {}).get("created_at", "")
        stats["references_count"] = len((project_data or {}).get("rows", []) or [])

        doc_count = 0
        total_size = 0
        try:
            for f in project_dir.rglob("*"):
                if not f.is_file():
                    continue
                try:
                    total_size += f.stat().st_size
                except OSError:
                    continue
                if "Documents" in f.parts:
                    doc_count += 1
        except OSError:
            pass

        stats["documents_count"] = doc_count
        stats["size"] = human_size(total_size)
        return stats

    # ── Actions ───────────────────────────────────────────────────────────────

    def _create_new_project(self):
        dialog = NewProjectDialog(self)
        dialog.projectCreated.connect(self._open_project_from_data)
        dialog.exec()
        self._load_recent_projects()

    def _open_existing_project(self):
        start_dir = self.project_manager.get_default_location() or str(Path.home())
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Choisir un dossier projet NOX_Manager",
            start_dir,
        )
        if not folder:
            return
        self._open_project_folder(Path(folder))

    def _open_selected_recent_project(self):
        item = self.recent_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(
                self, "Ouvrir un projet", "Sélectionne un projet dans la liste."
            )
            return
        path = item.data(0, QtCore.Qt.UserRole)
        if not path:
            return
        self._open_project_folder(Path(path))

    def _delete_selected_project(self):
        item = self.recent_list.currentItem()

        if not item:
            QtWidgets.QMessageBox.information(
                self,
                "Supprimer",
                "Sélectionne un projet dans la liste."
            )
            return

        name = item.text(0)
        path = item.data(0, QtCore.Qt.UserRole)

        if not path:
            return

        path = Path(path)

        # ─────────────────────────────
        # Message avec 3 choix
        # ─────────────────────────────

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Gestion du projet")

        msg.setText(
            f"Que souhaitez-vous faire avec ce projet ?\n\n"
            f"Projet : {name}"
        )

        msg.setInformativeText(
            "• Retirer des projets récents\n"
            "  Le projet restera sur le disque.\n\n"
            "• Supprimer définitivement le dossier\n"
            "  Le projet sera supprimé du disque.\n"
            "  Cette action est irréversible."
        )

        # Boutons personnalisés
        keep_btn = msg.addButton(
            "Retirer des projets récents",
            QtWidgets.QMessageBox.AcceptRole
        )

        delete_btn = msg.addButton(
            "Supprimer définitivement",
            QtWidgets.QMessageBox.DestructiveRole
        )

        cancel_btn = msg.addButton(
            "Annuler",
            QtWidgets.QMessageBox.RejectRole
        )

        msg.setDefaultButton(cancel_btn)

        msg.exec()

        clicked = msg.clickedButton()

        # ─────────────────────────────
        # Choix utilisateur
        # ─────────────────────────────

        if clicked == cancel_btn:
            return

        # Retirer seulement des récents
        if clicked == keep_btn:
            self.project_manager.remove_recent_project(path)

        # Supprimer complètement
        elif clicked == delete_btn:

            confirm = QtWidgets.QMessageBox.warning(
                self,
                "Confirmation requise",
                f"Voulez-vous vraiment supprimer définitivement le dossier :\n\n"
                f"{path}\n\n"
                "Cette action est irréversible.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            if confirm == QtWidgets.QMessageBox.Yes:

                try:
                    import shutil
                    shutil.rmtree(path)

                    self.project_manager.remove_recent_project(path)

                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Erreur de suppression",
                        f"Impossible de supprimer le dossier.\n\n{e}"
                    )
                    return

        # Rafraîchissement UI
        self._load_recent_projects()

        self.footer_status.setText("Aucun projet sélectionné")
        self.status_label.setText(
            f"  🗑  Projet traité : {name}"
        )

    def _open_project_folder(self, project_dir: Path):
        project_data = self.project_manager.load_project(project_dir)
        if not project_data:
            QtWidgets.QMessageBox.warning(
                self,
                "Projet invalide",
                "Le dossier sélectionné ne contient pas de fichier .nox_project.json valide.",
            )
            return
        self._open_project_from_data(project_data)

    def _open_project_from_data(self, project_data: dict):
        try:
            project_path = Path(project_data["project_path"])
            project_name = project_data.get("project_name", project_path.name)
            dossier_number = project_data.get("dossier_number", "")

            self.project_manager.add_recent_project(project_name, project_path, dossier_number)
            self.project_manager.add_recent_location(project_path.parent)

            window = ProjectDashboardWindow(project_data=project_data)
            window.setWindowTitle(f"NOX_Manager — {dossier_number or project_name}")
            window.showMaximized()

            self.project_windows.append(window)
            self._cleanup_windows()

            self.status_label.setText(f"  🖥  Projet ouvert : {project_name}")
            self._load_recent_projects()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur d'ouverture",
                f"Impossible d'ouvrir le projet.\n\n{e}",
            )

    def _cleanup_windows(self):
        self.project_windows = [
            w for w in self.project_windows if w is not None and w.isVisible()
        ]


