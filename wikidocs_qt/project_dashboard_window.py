from __future__ import annotations

from pathlib import Path
from collections import defaultdict
from datetime import datetime

import os
import sys
import subprocess

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
from .project_settings_dialog import ProjectSettingsDialog
from .new_project_dialog import NewProjectDialog




# Palette / style
BLUE = "#1565C0"
BLUE_LIGHT = "#E8F0FE"
GREEN_OK = "#2E7D32"
ORANGE_WARN = "#E65100"
RED_KO = "#C62828"
SEL_BG = "#1565C0"
ALT_ROW = "#F7F8FA"
WHITE = "#FFFFFF"
GRAY_BORDER = "#D0D5DD"
GRAY_TEXT = "#6B7280"
DARK = "#111827"
BG = "#F3F4F6"

F_BODY = QFont("Segoe UI", 9)
F_BOLD = QFont("Segoe UI", 9, QFont.Bold)
F_SMALL = QFont("Segoe UI", 8)
F_H1 = QFont("Segoe UI", 12, QFont.Bold)


def hline() -> QtWidgets.QFrame:
    f = QtWidgets.QFrame()
    f.setFrameShape(QtWidgets.QFrame.HLine)
    f.setStyleSheet(f"color:{GRAY_BORDER}; max-height:1px; background:{GRAY_BORDER};")
    return f


class KpiWidget(QtWidgets.QWidget):
    def __init__(self, label: str, value: int = 0, bar_color: str = BLUE, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self._value = max(0, min(100, int(value)))
        self._bar_color = bar_color
        self._bar_bg: QtWidgets.QFrame | None = None
        self._bar_fill: QtWidgets.QFrame | None = None
        self._pct_label: QtWidgets.QLabel | None = None
        self._build(label)

    def _build(self, label: str):
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(8, 4, 8, 4)
        v.setSpacing(3)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(4)

        lbl = QtWidgets.QLabel(label)
        lbl.setFont(F_SMALL)
        lbl.setStyleSheet(f"color:{GRAY_TEXT};")

        self._pct_label = QtWidgets.QLabel(f"{self._value} %")
        self._pct_label.setFont(F_BOLD)
        self._pct_label.setStyleSheet(f"color:{DARK};")

        row.addWidget(lbl)
        row.addWidget(self._pct_label)
        row.addStretch()
        v.addLayout(row)

        self._bar_bg = QtWidgets.QFrame()
        self._bar_bg.setFixedHeight(4)
        self._bar_bg.setMinimumWidth(70)
        self._bar_bg.setStyleSheet("background:#E5E7EB; border-radius:2px;")
        v.addWidget(self._bar_bg)

        self._bar_fill = QtWidgets.QFrame(self._bar_bg)
        self._bar_fill.setFixedHeight(4)
        self._bar_fill.setStyleSheet(f"background:{self._bar_color}; border-radius:2px;")
        self._bar_fill.setFixedWidth(0)

    def set_value(self, value: int):
        self._value = max(0, min(100, int(value)))
        if self._pct_label:
            self._pct_label.setText(f"{self._value} %")
        self._update_fill_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_fill_width()

    def _update_fill_width(self):
        if self._bar_fill and self._bar_bg:
            w = max(0, self._bar_bg.width())
            fill = 0 if self._value <= 0 else max(4, int(w * self._value / 100))
            self._bar_fill.setFixedWidth(fill)


class FilterChip(QtWidgets.QPushButton):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.base_label = label
        self.setText(f"{label}  ▾")
        self.setFont(F_BODY)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setFixedHeight(28)
        self._refresh_style(False)

    def set_active(self, active: bool):
        self.setText(f"{self.base_label}  {'●' if active else '▾'}")
        self._refresh_style(active)

    def _refresh_style(self, active: bool):
        bg = BLUE_LIGHT if active else WHITE
        border = BLUE if active else GRAY_BORDER
        color = BLUE if active else DARK
        self.setStyleSheet(f"""
            QPushButton {{
                background:{bg}; border:1px solid {border};
                border-radius:14px; padding:3px 14px; color:{color};
                font-weight:{'700' if active else '400'};
            }}
            QPushButton:hover   {{ background:{BLUE_LIGHT}; border-color:{BLUE}; color:{BLUE}; }}
            QPushButton:pressed {{ background:#DBEAFE; }}
        """)


class DetailPanel(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(WHITE))
        self.setPalette(pal)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._build()

    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        self.lbl_title = QtWidgets.QLabel("—")
        self.lbl_title.setFont(F_H1)
        self.lbl_title.setStyleSheet(f"color:{DARK};")
        self.lbl_title.setWordWrap(True)
        root.addWidget(self.lbl_title)

        self.lbl_type = QtWidgets.QLabel("Type de justificatif : —")
        self.lbl_type.setFont(F_SMALL)
        self.lbl_type.setStyleSheet(f"color:{GRAY_TEXT};")
        root.addWidget(self.lbl_type)

        self.lbl_docs = QtWidgets.QLabel("Documents enregistrés : —")
        self.lbl_docs.setFont(F_SMALL)
        self.lbl_docs.setStyleSheet(f"color:{GRAY_TEXT};")
        root.addWidget(self.lbl_docs)

        self.sep_top = hline()
        root.addWidget(self.sep_top)

        self.tbl_fields = self._make_table(["Champ", "Valeur"])
        self.tbl_fields.setVisible(False)

        self.sep_fields = hline()
        root.addWidget(self.sep_fields)

        self.lbl_linked = QtWidgets.QLabel("Documents liés")
        self.lbl_linked.setFont(F_BOLD)
        self.lbl_linked.setStyleSheet(f"color:{DARK};")
        root.addWidget(self.lbl_linked)

        self.tbl_docs = self._make_table(["Exigence", "Nom du document"])
        self.tbl_docs.cellClicked.connect(self._handle_table_click)
        self.tbl_docs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tbl_docs.setMinimumHeight(300)

        self.tables_splitter = QtWidgets.QSplitter(Qt.Vertical)
        self.tables_splitter.setChildrenCollapsible(False)
        self.tables_splitter.addWidget(self.tbl_fields)
        self.tables_splitter.addWidget(self.tbl_docs)
        self.tables_splitter.setStretchFactor(0, 2)
        self.tables_splitter.setStretchFactor(1, 1)
        self.tables_splitter.setSizes([0, 1])

        root.addWidget(self.tables_splitter, 1)

    def _handle_table_click(self, row: int, column: int):
        # CECC = 2 colonnes : document en colonne 1
        # CE/DPE = 3 colonnes : document en colonne 2
        doc_col = 1 if self.tbl_docs.columnCount() == 2 else 2

        if column != doc_col:
            return

        item = self.tbl_docs.item(row, doc_col)
        if item is None:
            return

        file_path = item.data(QtCore.Qt.UserRole)
        if not file_path:
            return

        self._on_document_clicked(file_path)

    def _on_document_clicked(self, file_path: str):
        path = Path(file_path)

        if not path.exists():
            QtWidgets.QMessageBox.warning(
                self,
                "Fichier introuvable",
                f"Impossible d'ouvrir le fichier :\n\n{path}"
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
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur d'ouverture",
                f"Impossible d'ouvrir le fichier.\n\n{e}"
            )

    def _make_table(self, headers: list[str]) -> QtWidgets.QTableWidget:
        t = QtWidgets.QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setFont(F_BOLD)
        t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        t.setSelectionMode(QtWidgets.QTableWidget.SingleSelection)
        t.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        t.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {GRAY_BORDER}; border-radius:6px;
                font-size:9pt; background:{WHITE};
                alternate-background-color:{ALT_ROW};
            }}
            QHeaderView::section {{
                background:#F9FAFB; border:none;
                border-bottom:1px solid {GRAY_BORDER};
                padding:5px 8px; font-weight:bold; color:{DARK};
            }}
            QTableWidget::item {{ padding:5px 8px; color:{DARK}; }}
            QTableWidget::item:selected {{ background:{BLUE_LIGHT}; color:{BLUE}; }}
        """)
        return t

    def clear(self):
        self.lbl_title.setText("—")
        self.lbl_type.setText("Type de justificatif : —")
        self.lbl_docs.setText("Documents enregistrés : —")
        self.tbl_fields.setRowCount(0)
        self.tbl_docs.setRowCount(0)
        self.tbl_fields.hide()
        self.sep_fields.hide()
        self.lbl_linked.show()
        self.tbl_docs.setMinimumHeight(300)
        self.tbl_docs.setMaximumHeight(16777215)
        self.tbl_docs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tables_splitter.setSizes([0, 1])

    def set_header(self, supplier: str, reference: str, justif_type: str, nb_docs: int):
        self.lbl_title.setText(f"{supplier} / {reference} / {justif_type}")
        self.lbl_type.setText(f"Type de justificatif : {justif_type}")
        self.lbl_docs.setText(f"Documents enregistrés : {nb_docs}")

    def set_fields(self, rows: list[tuple[str, str]], type_: str = ""):
        self.tbl_fields.setRowCount(len(rows))
        for i, (label, value) in enumerate(rows):
            self.tbl_fields.setItem(i, 0, QtWidgets.QTableWidgetItem(str(label)))
            self.tbl_fields.setItem(i, 1, QtWidgets.QTableWidgetItem(str(value)))
        self.tbl_fields.resizeRowsToContents()

        has_fields = len(rows) > 0

        if type_ in ("CE", "DPE"):
            self.tbl_fields.hide()
            self.sep_fields.hide()
            self.lbl_linked.show()
            self.tbl_docs.setMinimumHeight(300)
            self.tbl_docs.setMaximumHeight(16777215)
            self.tbl_docs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.tables_splitter.setSizes([0, 1])
        elif type_ == "CECC":
            self.tbl_fields.hide()
            self.sep_fields.hide()
            self.lbl_linked.hide()
            self.tbl_docs.setMinimumHeight(300)
            self.tbl_docs.setMaximumHeight(16777215)
            self.tbl_docs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.tables_splitter.setSizes([0, 1])
        else:
            if has_fields:
                self.tbl_fields.show()
                self.sep_fields.show()
                self.lbl_linked.show()
            else:
                self.tbl_fields.hide()
                self.sep_fields.hide()
                self.lbl_linked.show()

    def set_linked_docs(self, rows: list[dict], type_: str = ""):
        is_cecc = (type_ == "CECC")

        if is_cecc:
            self.tbl_docs.setColumnCount(2)
            self.tbl_docs.setHorizontalHeaderLabels(["Champ", "Valeur"])
        else:
            self.tbl_docs.setColumnCount(3)
            self.tbl_docs.setHorizontalHeaderLabels(
                ["Exigence", "Applicabilité", "Nom du document"]
            )

        self.tbl_docs.setRowCount(len(rows))

        for i, detail in enumerate(rows):
            left_value = str(detail.get("requirement", ""))
            applicability = str(detail.get("applicability", "Applicable"))
            right_value = str(detail.get("filename", ""))

            self.tbl_docs.setItem(i, 0, QtWidgets.QTableWidgetItem(left_value))

            if not is_cecc:
                app_item = QtWidgets.QTableWidgetItem(applicability)

                if applicability == "Non applicable":
                    app_item.setForeground(QColor(ORANGE_WARN))
                elif applicability == "Applicable":
                    app_item.setForeground(QColor(GREEN_OK))

                app_item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tbl_docs.setItem(i, 1, app_item)

                doc_col = 2
            else:
                doc_col = 1

            item = QtWidgets.QTableWidgetItem(right_value)

            if is_cecc and left_value == "Nom : CECC":
                item.setForeground(QColor(BLUE))
                font = item.font()
                font.setUnderline(True)
                item.setFont(font)
                item.setToolTip("Cliquer pour ouvrir")
                item.setData(QtCore.Qt.UserRole, detail.get("path", ""))

            elif not is_cecc and right_value != "—":
                item.setForeground(QColor(BLUE))
                font = item.font()
                font.setUnderline(True)
                item.setFont(font)
                item.setToolTip("Double-cliquer pour ouvrir")
                item.setData(QtCore.Qt.UserRole, detail.get("path", ""))

            self.tbl_docs.setItem(i, doc_col, item)

        self.tbl_docs.resizeRowsToContents()

    def _normalize_requirement_code(self, code: str) -> str:
        code = str(code or "").strip()

        if " — " in code:
            code = code.split(" — ", 1)[0].strip()

        if " | " in code:
            code = code.split(" | ", 1)[0].strip()

        return code


    def _code_matches(self, a: str, b: str) -> bool:
        return self._normalize_requirement_code(a) == self._normalize_requirement_code(b)


    def _is_not_applicable(self, docs: list[dict], code: str) -> bool:
        for doc in docs:
            for na_code in doc.get("not_applicable_codes", []) or []:
                if self._code_matches(na_code, code):
                    return True
        return False


class MainTab(QtWidgets.QWidget):
    COLUMNS = ["Fournisseur", "Référence", "Type", "Nombre de documents", "Complétude"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(0)

        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(4)
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background:{GRAY_BORDER}; }}")

        self.table = QtWidgets.QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setFont(F_BOLD)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size:9pt;
                background:{WHITE}; alternate-background-color:{ALT_ROW};
            }}
            QHeaderView::section {{
                background:#F9FAFB; border:none;
                border-bottom:2px solid {GRAY_BORDER};
                padding:6px 8px; font-weight:bold; color:{DARK};
            }}
            QTableWidget::item {{ padding:6px 8px; color:{DARK}; }}
            QTableWidget::item:selected {{ background:{SEL_BG}; color:{WHITE}; }}
        """)

        self.detail = DetailPanel()
        self.detail.tbl_docs.cellDoubleClicked.connect(self._forward_detail_double_click)

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.detail)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([780, 520])

        root.addWidget(self.splitter)

    def _forward_detail_double_click(self, row: int, column: int):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_open_document_from_detail_table"):
                parent._open_document_from_detail_table(row, column)
                return
            parent = parent.parent()


class ProjectDashboardWindow(QtWidgets.QMainWindow):
    def __init__(self, project_data: dict, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.project_dir = Path(project_data["project_path"])
        self.column_filters: dict[str, set[str] | None] = {
            "supplier": None,
            "reference": None,
            "type": None,
            "completion": None,
        }
        self.active_tab_type: str | None = None
        self.current_rows_by_tab: dict[str, list[dict]] = {}
        self.project_manager = ProjectManager()
        self.enabled_bdds = list(self.project_data.get("enabled_bdds", JUSTIFICATION_TYPES))
        self.tab_widgets_by_name: dict[str, MainTab] = {}
        self._all_rows_cache: list[dict] = []
        self._filtered_rows_cache: list[dict] = []
        self.current_rows_by_tab: dict[str, list[dict]] = {}

        init_metadata_db(self.project_dir)

        self.setWindowTitle(f"NOX_Manager — {project_data.get('project_name', self.project_dir.name)}")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)

        self._build_ui()
        self._load_table()
        self._update_filter_buttons()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        central.setStyleSheet(f"background:{BG};")
        self.setCentralWidget(central)

        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_menubar())
        root.addWidget(self._build_header())
        root.addWidget(self._build_tabs(), 1)
        root.addWidget(self._build_statusbar())

    def _build_menubar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"background:{WHITE};")

        outer = QtWidgets.QVBoxLayout(bar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content = QtWidgets.QWidget(bar)
        h = QtWidgets.QHBoxLayout(content)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(2)

        for label, slot in [
            ("Paramétrage projet", self._open_project_settings),
            ("Importer", self._open_upload_from_selection),
            ("Actualiser", self._load_table),
            ("Exporter les BDD", self._export_templates),
        ]:
            btn = QtWidgets.QPushButton(label)
            btn.setFont(QtGui.QFont("Segoe UI", 9))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(f"""
                QPushButton {{ padding:4px 12px; color:{DARK}; border-radius:4px; border:none; font-size:9pt; }}
                QPushButton:hover   {{ background:{BLUE_LIGHT}; color:{BLUE}; }}
                QPushButton:pressed {{ background:#DBEAFE; }}
            """)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addStretch()
        outer.addWidget(content, 1)

        sep = QtWidgets.QFrame(bar)
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{GRAY_BORDER}; color:{GRAY_BORDER}; border:none;")
        outer.addWidget(sep)
        return bar

    def _build_header(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setStyleSheet(f"background:{WHITE}; border-bottom:1px solid {GRAY_BORDER};")
        card.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        outer = QtWidgets.QVBoxLayout(card)
        outer.setContentsMargins(16, 10, 16, 10)
        outer.setSpacing(8)

        self.project_name_label = QtWidgets.QLabel(f"Projet : {self.project_data.get('project_name', self.project_dir.name)}")
        self.project_name_label.setFont(F_H1)
        self.project_name_label.setStyleSheet(f"color:{DARK}; border:none;")
        outer.addWidget(self.project_name_label)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)

        self.lbl_refs = self._badge("Références : 0")
        self.lbl_docs_count = self._badge("Avec docs : 0")
        row.addWidget(self.lbl_refs)
        row.addWidget(self.lbl_docs_count)
        row.addWidget(self._vsep())

        self.kpi_ce = KpiWidget("CE", 0, "#F59E0B")
        self.kpi_cecc = KpiWidget("CECC", 0, "#8B5CF6")
        self.kpi_dpe = KpiWidget("DPE", 0, "#EF4444")
        for widget in (self.kpi_ce, self.kpi_cecc, self.kpi_dpe):
            row.addWidget(widget)

        row.addStretch()

        self.filter_supplier_button = FilterChip("Fournisseur")
        self.filter_supplier_button.clicked.connect(
            lambda: self._open_column_filter("supplier", "Filtrer les fournisseurs")
        )
        self.filter_supplier_button.setFixedHeight(32)

        self.filter_reference_button = FilterChip("Référence")
        self.filter_reference_button.clicked.connect(
            lambda: self._open_column_filter("reference", "Filtrer les références")
        )
        self.filter_reference_button.setFixedHeight(32)

        self.filter_type_button = FilterChip("Type")
        self.filter_type_button.clicked.connect(
            lambda: self._open_column_filter("type", "Filtrer les types")
        )
        self.filter_type_button.setFixedHeight(32)

        self.filter_completion_button = FilterChip("Complétude")
        self.filter_completion_button.clicked.connect(
            lambda: self._open_column_filter("completion", "Filtrer la complétude")
        )
        self.filter_completion_button.setFixedHeight(32)

        for chip in (
            self.filter_supplier_button,
            self.filter_reference_button,
            self.filter_type_button,
            self.filter_completion_button,
            
        ):
            row.addWidget(chip)

        row.addWidget(self._vsep())

        btn_up = QtWidgets.QPushButton("⬆  Importer un document")
        btn_up.setFont(F_BOLD)
        btn_up.setFixedHeight(32)
        btn_up.setMinimumWidth(100)
        btn_up.setCursor(Qt.PointingHandCursor)
        btn_up.setStyleSheet(f"""
            QPushButton {{
                background:{BLUE}; color:{WHITE};
                border-radius:6px; padding:0 16px; border:none;
            }}
            QPushButton:hover   {{ background:#1976D2; }}
            QPushButton:pressed {{ background:#0D47A1; }}
        """)
        btn_up.clicked.connect(self._open_upload_from_selection)
        row.addWidget(btn_up)

        outer.addLayout(row)
        return card

    def _badge(self, text: str) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text)
        lbl.setFont(F_BODY)
        lbl.setStyleSheet(f"""
            background:{ALT_ROW}; border:1px solid {GRAY_BORDER};
            border-radius:12px; padding:3px 12px; color:{DARK};
        """)
        lbl.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        return lbl

    def _vsep(self) -> QtWidgets.QFrame:
        f = QtWidgets.QFrame()
        f.setFrameShape(QtWidgets.QFrame.VLine)
        f.setFixedHeight(24)
        f.setStyleSheet(f"color:{GRAY_BORDER};")
        return f

    def _refresh_project_data(self):
        self.project_data = self.project_manager.load_project(self.project_dir) or self.project_data
        self.enabled_bdds = list(self.project_data.get("enabled_bdds", JUSTIFICATION_TYPES))

    def _get_selected_row_data(self) -> list[dict]:
        table = self._current_tab_widget().table

        selected_rows = sorted(set(index.row() for index in table.selectionModel().selectedRows()))
        results: list[dict] = []

        for row_index in selected_rows:
            first_item = table.item(row_index, 0)
            if first_item is None:
                continue

            row_data = first_item.data(QtCore.Qt.UserRole)
            if row_data:
                results.append(row_data)

        return results

    def _build_tabs(self) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QWidget()
        wrapper.setStyleSheet(f"background:{BG};")

        layout = QtWidgets.QVBoxLayout(wrapper)
        layout.setContentsMargins(12, 8, 12, 0)
        layout.setSpacing(0)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {GRAY_BORDER};
                border-radius: 8px;
                background: {WHITE};
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background: transparent; color:{GRAY_TEXT};
                padding: 8px 22px;
                border: 1px solid transparent;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                margin-right: 2px; font-size:9pt;
            }}
            QTabBar::tab:selected {{
                background: {WHITE}; color:{BLUE}; font-weight:bold;
                border: 1px solid {GRAY_BORDER}; border-bottom: 1px solid {WHITE};
            }}
            QTabBar::tab:hover:!selected {{ background:{BLUE_LIGHT}; color:{BLUE}; }}
        """)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.tab_widgets_by_name = {}

        self.tab_accueil = MainTab(self)
        self.tab_widgets_by_name["Tous"] = self.tab_accueil
        self.tabs.addTab(self.tab_accueil, "Tous")
        self.tab_accueil.table.itemSelectionChanged.connect(self._update_detail_panel)

        for livrable in self.enabled_bdds:
            tab = MainTab(self)
            self.tab_widgets_by_name[livrable] = tab
            self.tabs.addTab(tab, livrable)
            tab.table.itemSelectionChanged.connect(self._update_detail_panel)

        layout.addWidget(self.tabs)
        return wrapper

    def _build_statusbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet(f"background:{WHITE}; border-top:1px solid {GRAY_BORDER};")
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)

        self.lbl_last_update = QtWidgets.QLabel("Dernière actualisation : —")
        self.lbl_last_update.setFont(F_SMALL)
        self.lbl_last_update.setStyleSheet(f"color:{GRAY_TEXT};")

        self.lbl_row_count = QtWidgets.QLabel("0 lignes")
        self.lbl_row_count.setFont(F_SMALL)
        self.lbl_row_count.setStyleSheet(f"color:{GRAY_TEXT};")

        h.addWidget(self.lbl_last_update)
        h.addStretch()
        h.addWidget(self.lbl_row_count)
        return bar

    def _current_tab_widget(self) -> MainTab:
        tab_name = self.tabs.tabText(self.tabs.currentIndex())
        return self.tab_widgets_by_name.get(tab_name, self.tab_accueil)

    def _build_cecc_field_rows(self, cecc_fields: dict) -> list[tuple[str, str]]:
        pretty_labels = {
            "manufacturer_doc": "Fournisseur Doc / MANUFACTURER",
            "manufacturer_part_number": "Manufacturer Part Number",
            "nom_cecc": "Nom : CECC",
            "cecc_classement": "CECC Classement",
            "categorie_export": "Catégorie export",
            "licence": "Licence",
            "numero_licence": "N° Licence",
            "pays_origine_4a": "Pays Origine 4a",
            "ear99_value_usd": "EAR99 Value (USD)",
            "eccn_value_usd": "ECCN value (USD)",
            "composants_controles_export": "Composants contrôlés export",
            "pays_origine": "Pays d'origine",
            "classement_export": "Classement à l'export",
            "code_douanier": "Code douanier / Tariff Code",
            "cecc_etat": "Statut CECC",
        }

        rows: list[tuple[str, str]] = []
        for key, label in pretty_labels.items():
            value = str(cecc_fields.get(key, "") or "").strip()
            rows.append((label, value if value else "—"))

        return rows

    def _normalize_requirement_code(self, code: str) -> str:
        code = str(code or "").strip()

        if " — " in code:
            code = code.split(" — ", 1)[0].strip()

        if " | " in code:
            code = code.split(" | ", 1)[0].strip()

        return code


    def _code_matches(self, a: str, b: str) -> bool:
        return self._normalize_requirement_code(a) == self._normalize_requirement_code(b)


    def _is_not_applicable(self, docs: list[dict], code: str) -> bool:
        for doc in docs:
            for na_code in doc.get("not_applicable_codes", []) or []:
                if self._code_matches(na_code, code):
                    return True
        return False

    def _build_detail_rows(self, row_data: dict) -> list[dict]:
        docs = row_data.get("docs", [])
        justif_type = row_data.get("type", "").upper()

        if justif_type == "CE":
            expected_requirements = CE_REQUIREMENTS
        elif justif_type == "DPE":
            expected_requirements = DPE_REQUIREMENTS
        else:
            return []

        latest_by_code: dict[str, dict] = {}

        for doc in sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True):
            if not self._doc_applies_to_type(doc, justif_type):
                continue

            codes = doc.get("requirement_codes", []) or []
            labels = doc.get("requirement_labels", []) or []

            for i, code in enumerate(codes):
                normalized_code = self._normalize_requirement_code(code)

                if normalized_code not in latest_by_code:
                    latest_by_code[normalized_code] = {
                        "filename": doc.get("stored_filename", ""),
                        "path": str(self.project_dir / doc["relative_path"]),
                        "label": labels[i] if i < len(labels) else "",
                    }

        detail_rows: list[dict] = []

        for code, default_label in expected_requirements:
            normalized_code = self._normalize_requirement_code(code)
            data = latest_by_code.get(normalized_code)

            is_na = self._is_not_applicable(docs, code)
            applicability = "Non applicable" if is_na else "Applicable"

            label = data["label"] if data and data.get("label") else default_label

            detail_rows.append({
                "requirement": f"{code} | {label}",
                "applicability": applicability,
                "filename": "N/A" if is_na else (data["filename"] if data else "—"),
                "path": "" if is_na else (data["path"] if data else ""),
            })

        return detail_rows

    def _on_tab_changed(self, index: int):
        tab_name = self.tabs.tabText(index)
        self.active_tab_type = None if tab_name == "Tous" else tab_name

        self._load_current_tab_only()

        current_count = len(self.current_rows_by_tab.get(tab_name, []))
        if hasattr(self, "lbl_row_count"):
            self.lbl_row_count.setText(f"{current_count} lignes")

        self._update_detail_panel()

    def _is_filter_active(self, column_key: str) -> bool:
        allowed_values = self.column_filters.get(column_key)
        if allowed_values is None:
            return False
        all_values = set(self._get_column_values(self._all_rows_cache, column_key))
        return set(allowed_values) != all_values

    def _update_filter_buttons(self):
        mapping = {
            "supplier": self.filter_supplier_button,
            "reference": self.filter_reference_button,
            "type": self.filter_type_button,
            "completion": self.filter_completion_button,
        }
        for key, button in mapping.items():
            button.set_active(self._is_filter_active(key))

    def _export_templates(self):
        try:
            export_paths = export_project_templates(self.project_dir)
            QtWidgets.QMessageBox.information(
                self,
                "Export terminé",
                "Les fichiers ont été exportés avec succès :\n\n" + "\n".join(str(p) for p in export_paths),
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur export",
                f"Impossible d'exporter les templates.\n\n{e}",
            )

    def _apply_filters(self, rows: list[dict]) -> list[dict]:
        filtered = rows
        for key, allowed_values in self.column_filters.items():
            if allowed_values is None:
                continue
            filtered = [row for row in filtered if str(row.get(key, "")) in allowed_values]
        return filtered

    def _get_column_values(self, rows: list[dict], column_key: str) -> list[str]:
        values = []
        for row in rows:
            value = row.get(column_key, "")
            if value is None:
                value = ""
            values.append(str(value))
        return sorted(set(values), key=str.lower)

    def _open_column_filter(self, column_key: str, title: str):
        rows = self._all_rows_cache
        values = self._get_column_values(rows, column_key)
        current_checked = set(values) if self.column_filters[column_key] is None else self.column_filters[column_key]

        dialog = FilterPopup(title=title, values=values, checked_values=current_checked, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            checked = dialog.get_checked_values()
            self.column_filters[column_key] = None if set(checked) == set(values) else checked
            self._load_table(rebuild_cache=False, update_global_kpis=False)

    

    def _group_uploaded_documents(self):
        uploaded = get_uploaded_documents(self.project_dir)
        by_supplier_ref_type = defaultdict(list)
        by_supplier_ref = defaultdict(list)

        for doc in uploaded:
            supplier = doc["supplier"]
            reference = doc["reference"]
            justif_type = doc["source_justification_type"].upper()
            by_supplier_ref[(supplier, reference)].append(doc)
            by_supplier_ref_type[(supplier, reference, justif_type)].append(doc)

        return by_supplier_ref, by_supplier_ref_type

    def _scan_supplier_reference_pairs(self) -> list[tuple[str, str]]:
        rows = self.project_data.get("rows", []) or []
        pairs = []

        for row in rows:
            supplier = str(row.get("supplier", "")).strip()
            reference = str(row.get("reference", "")).strip()
            if supplier:
                pairs.append((supplier, reference))

        if pairs:
            return sorted(set(pairs), key=lambda x: (x[0].lower(), x[1].lower()))

        dossier_number = self.project_data["dossier_number"]
        pairs = []

        for bdd_type in self.enabled_bdds:
            docs_dir = self.project_dir / f"BDD {bdd_type} {dossier_number}" / "Documents"
            if not docs_dir.exists():
                continue

            for supplier_dir in docs_dir.iterdir():
                if not supplier_dir.is_dir():
                    continue

                for ref_dir in supplier_dir.iterdir():
                    if ref_dir.is_dir():
                        pairs.append((supplier_dir.name, ref_dir.name))

        return sorted(set(pairs), key=lambda x: (x[0].lower(), x[1].lower()))

    def _doc_applies_to_type(self, doc: dict, justif_type: str) -> bool:
        justif_type = str(justif_type).upper()

        source_type = str(doc.get("source_justification_type", "")).upper()

        stored_in_bdds = [
            str(v).upper()
            for v in doc.get("stored_in_bdds", [])
        ]

        return source_type == justif_type or justif_type in stored_in_bdds

    def _build_table_rows(self) -> list[dict]:
        pairs = self._scan_supplier_reference_pairs()
        by_supplier_ref, _by_supplier_ref_type = self._group_uploaded_documents()

        rows: list[dict] = []
        for supplier, reference in pairs:
            for justif_type in self.enabled_bdds:
                all_docs_for_ref = by_supplier_ref.get((supplier, reference), [])

                docs = [
                    doc for doc in all_docs_for_ref
                    if self._doc_applies_to_type(doc, justif_type)
                ]
                doc_count = self._count_documents_in_folder(supplier, reference, justif_type)
                if justif_type == "CE":
                    completion_value = self._compute_ce_dpe_completion(
                        docs,
                        ["2006/42/UE", "2011/65/UE", "2014/30/UE", "2014/68/UE", "AUTRES"],
                    )
                elif justif_type == "DPE":
                    completion_value = self._compute_ce_dpe_completion(
                        docs,
                        [
                            "2011/65/UE", "2012/19/UE", "2006/66/CE", "1907/2006",
                            "2019/1021", "1005/2009", "517/2014", "2017/852",
                            "528/2012", "2013/59/Euratom", "2017/821", "2016/1628",
                        ],
                    )
                else:
                    completion_value = self._compute_cecc_completion(docs)

                rows.append({
                    "supplier": supplier,
                    "reference": reference,
                    "type": justif_type,
                    "documents": doc_count,
                    "completion": f"{round(completion_value * 100)} %",
                    "completion_value": completion_value,
                    "docs": docs,
                })
        return rows

    def _compute_requirement_score(self, docs: list[dict], code: str) -> float:
        matching_docs = [
            doc for doc in docs
            if any(
                self._code_matches(doc_code, code)
                for doc_code in doc.get("requirement_codes", []) or []
            )
        ]
        non_empty = len(matching_docs)
        if non_empty == 0:
            return 0.0
        estimation_count = sum(
            1 for doc in matching_docs
            if "estimation" in (doc.get("stored_filename", "") or "").lower()
        )
        denominator = non_empty
        if denominator == 0:
            return 0.0
        score = (non_empty - estimation_count) / denominator
        return max(0.0, min(1.0, score))

    def _compute_ce_dpe_completion(self, docs: list[dict], requirement_codes: list[str]) -> float:
        if not requirement_codes:
            return 0.0

        applicable_codes = [
            code for code in requirement_codes
            if not self._is_not_applicable(docs, code)
        ]

        if not applicable_codes:
            return 1.0

        scores = [
            self._compute_requirement_score(docs, code)
            for code in applicable_codes
        ]

        return sum(scores) / len(scores)

    def _compute_cecc_completion(self, docs: list[dict]) -> float:
        statuses = [(doc.get("cecc_fields", {}) or {}).get("status", "").strip() for doc in docs]
        valides = sum(1 for s in statuses if s == "Validé")
        relances = sum(1 for s in statuses if s == "Relancé")
        non_conformes = sum(1 for s in statuses if s == "Non conforme")
        estimations = sum(1 for s in statuses if s == "Estimation")
        denominator = valides + relances + non_conformes + estimations
        if denominator == 0:
            return 0.0
        return valides / denominator

    def _load_rows_into_tab(self, tab: MainTab, rows: list[dict]):
        table = tab.table
        table.setSortingEnabled(False)
        table.clearContents()
        table.setRowCount(len(rows))
        table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)

        for row_index, row in enumerate(rows):
            values = [
                row["supplier"],
                row["reference"],
                row["type"],
                str(row["documents"]),
                row["completion"],
            ]
            for col_index, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                if col_index == 4:
                    pct = row.get("completion_value", 0.0)
                    color = GREEN_OK if pct >= 1.0 else (ORANGE_WARN if pct > 0 else RED_KO)
                    item.setForeground(QtGui.QBrush(QtGui.QColor(color)))
                if col_index in (3, 4):
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                else:
                    item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
                item.setData(QtCore.Qt.UserRole, row)
                table.setItem(row_index, col_index, item)

        table.resizeRowsToContents()
        table.setSortingEnabled(True)
        table.sortByColumn(0, QtCore.Qt.AscendingOrder)

        if table.rowCount() > 0:
            table.selectRow(0)
        else:
            tab.detail.clear()

    def _load_table(self, rebuild_cache: bool = True, update_global_kpis: bool = True):
        if rebuild_cache:
            self._refresh_project_data()
            self._all_rows_cache = self._build_table_rows()

            if update_global_kpis:
                self._update_global_kpis(self._all_rows_cache)

        self._filtered_rows_cache = self._apply_filters(self._all_rows_cache)

        total_refs = len({
            (row["supplier"], row["reference"])
            for row in self._filtered_rows_cache
        })

        refs_with_docs = len({
            (row["supplier"], row["reference"])
            for row in self._filtered_rows_cache
            if row["documents"] > 0
        })

        self.lbl_refs.setText(f"Références : {total_refs}")
        self.lbl_docs_count.setText(f"Avec docs : {refs_with_docs}")

        rows_by_tab = {"Tous": list(self._filtered_rows_cache)}

        for livrable in self.enabled_bdds:
            rows_by_tab[livrable] = [
                row for row in self._filtered_rows_cache
                if row["type"] == livrable
            ]

        self.current_rows_by_tab = rows_by_tab

        self._load_current_tab_only()

        current_tab_name = self.tabs.tabText(self.tabs.currentIndex())
        current_count = len(self.current_rows_by_tab.get(current_tab_name, []))

        self.lbl_last_update.setText(
            f"Dernière actualisation : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        if hasattr(self, "lbl_row_count"):
            self.lbl_row_count.setText(f"{current_count} lignes")

        self._update_filter_buttons()
        self._update_detail_panel()

    def _update_global_kpis(self, rows: list[dict]):
        ce_rows = [row for row in rows if row["type"] == "CE"]
        cecc_rows = [row for row in rows if row["type"] == "CECC"]
        dpe_rows = [row for row in rows if row["type"] == "DPE"]

        self.kpi_ce.set_value(
            round((sum(r.get("completion_value", 0.0) for r in ce_rows) / len(ce_rows)) * 100)
            if ce_rows else 0
        )

        self.kpi_cecc.set_value(
            round((sum(r.get("completion_value", 0.0) for r in cecc_rows) / len(cecc_rows)) * 100)
            if cecc_rows else 0
        )

        self.kpi_dpe.set_value(
            round((sum(r.get("completion_value", 0.0) for r in dpe_rows) / len(dpe_rows)) * 100)
            if dpe_rows else 0
        )


    def _load_current_tab_only(self):
        current_tab_name = self.tabs.tabText(self.tabs.currentIndex())
        tab_widget = self.tab_widgets_by_name.get(current_tab_name)

        if not tab_widget:
            return

        rows = self.current_rows_by_tab.get(current_tab_name, [])
        self._load_rows_into_tab(tab_widget, rows)

    def _ensure_project_structure(self, rows: list[dict], enabled_bdds: list[str]):
        dossier_number = self.project_data["dossier_number"]
        row_pairs = [(row["supplier"], row["reference"]) for row in rows]

        for bdd_type in enabled_bdds:
            bdd_dir = self.project_dir / f"BDD {bdd_type} {dossier_number}"
            docs_dir = bdd_dir / "Documents"
            bdd_dir.mkdir(parents=True, exist_ok=True)
            docs_dir.mkdir(parents=True, exist_ok=True)

            excel_path = bdd_dir / f"BDD_{bdd_type}_{dossier_number}.xlsx"
            if not excel_path.exists():
                excel_path.touch()

            create_folders_and_subfolders(docs_dir, row_pairs)

    def _remove_row_folders(self, removed_rows: list[dict]):
        dossier_number = self.project_data["dossier_number"]
        if not removed_rows:
            return

        answer = QtWidgets.QMessageBox.question(
            self,
            "Suppression de lignes",
            "Supprimer aussi les dossiers physiques associés aux lignes supprimées ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return

        import shutil

        for row in removed_rows:
            supplier = row["supplier"]
            reference = row["reference"]

            for bdd_type in self.enabled_bdds:
                target = self.project_dir / f"BDD {bdd_type} {dossier_number}" / "Documents" / supplier / reference
                if target.exists():
                    shutil.rmtree(target, ignore_errors=True)

    def _open_project_settings(self):
        fresh_project_data = self.project_manager.load_project(self.project_dir)

        if not fresh_project_data:
            QtWidgets.QMessageBox.warning(
                self,
                "Paramétrage projet",
                "Impossible de relire les données du projet."
            )
            return

        dialog = NewProjectDialog(self, project_data=fresh_project_data)

        result = dialog.exec()

        if result != QtWidgets.QDialog.Accepted:
            return

        updated_project_data = dialog.updated_project_data
        if not updated_project_data:
            return

        self.project_data = updated_project_data
        self.enabled_bdds = list(
            self.project_data.get("enabled_bdds", JUSTIFICATION_TYPES)
        )

        self._refresh_project_data()
        self._load_table()

        QtWidgets.QMessageBox.information(
            self,
            "Paramétrage projet",
            "Le paramétrage du projet a bien été mis à jour."
        )

    def _update_detail_panel(self):
        tab = self._current_tab_widget()
        table = tab.table
        detail = tab.detail

        detail.tbl_docs.setRowCount(0)
        detail.tbl_fields.setRowCount(0)
        detail.tbl_fields.hide()
        detail.sep_fields.hide()

        selected_ranges = table.selectedRanges()
        if not selected_ranges:
            detail.clear()
            detail.lbl_title.setText("Sélectionne une ligne")
            return

        row_index = selected_ranges[0].topRow()
        first_item = table.item(row_index, 0)
        if first_item is None:
            detail.clear()
            detail.lbl_title.setText("Sélectionne une ligne")
            return

        row_data = first_item.data(QtCore.Qt.UserRole)
        if not row_data:
            detail.clear()
            detail.lbl_title.setText("Sélectionne une ligne")
            return

        supplier = row_data["supplier"]
        reference = row_data["reference"]
        justif_type = row_data["type"]
        docs = row_data["docs"]

        detail.set_header(supplier, reference, justif_type, len(docs))

        if justif_type == "CECC":
            cecc_display_rows = []

            latest_doc = None
            if docs:
                docs_sorted = sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True)
                latest_doc = docs_sorted[0]

            cecc_fields = (latest_doc.get("cecc_fields", {}) if latest_doc else {}) or {}

            for label, value in self._build_cecc_field_rows(cecc_fields):
                cecc_display_rows.append({
                    "requirement": label,
                    "filename": value,
                    "path": str(self.project_dir / latest_doc["relative_path"]) if latest_doc else "",
                    "stored_filename": latest_doc.get("stored_filename", "") if latest_doc else "",
                })

            detail.set_fields([], justif_type)
            detail.set_linked_docs(cecc_display_rows, justif_type)

        else:
            detail.set_fields([], justif_type)
            detail_rows = self._build_detail_rows(row_data)
            detail.set_linked_docs(detail_rows, justif_type)

    def _open_document_from_detail_table(self, row: int, column: int):
        table = self._current_tab_widget().detail.tbl_docs

        doc_col = 1 if table.columnCount() == 2 else 2

        if column != doc_col:
            return

        item = table.item(row, doc_col)
        if item is None:
            return

        file_path = item.data(QtCore.Qt.UserRole)
        if not file_path:
            return

        path = Path(file_path)

        if not path.exists():
            QtWidgets.QMessageBox.warning(
                self,
                "Fichier introuvable",
                f"Impossible d'ouvrir le fichier :\n\n{path}"
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
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur d'ouverture",
                f"Impossible d'ouvrir le fichier.\n\n{e}"
            )

    def _count_documents_in_folder(self, supplier: str, reference: str, justif_type: str) -> int:
        dossier_number = self.project_data["dossier_number"]

        folder = (
            self.project_dir
            / f"BDD {justif_type} {dossier_number}"
            / "Documents"
            / supplier
            / reference
        )

        if not folder.exists() or not folder.is_dir():
            return 0

        return sum(1 for path in folder.iterdir() if path.is_file())


    def _open_upload_from_selection(self):
        selected_rows = self._get_selected_row_data()

        if not selected_rows:
            QtWidgets.QMessageBox.information(
                self,
                "Import",
                "Sélectionne au moins une ligne du tableau."
            )
            return

        types = {row["type"] for row in selected_rows}
        if len(types) > 1:
            QtWidgets.QMessageBox.warning(
                self,
                "Import multiple impossible",
                "La sélection multiple doit contenir un seul type de justificatif (CE, CECC ou DPE)."
            )
            return

        first_row = selected_rows[0]

        dialog = UploadDocumentDialog(
            project_dir=self.project_dir,
            supplier=first_row["supplier"],
            reference=first_row["reference"],
            preset_justification_type=first_row["type"],
            batch_targets=[
                {
                    "supplier": row["supplier"],
                    "reference": row["reference"],
                    "type": row["type"],
                }
                for row in selected_rows
            ],
            parent=self,
        )

        dialog.documentSaved.connect(self._load_table)
        dialog.exec()
