from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil

from PySide6 import QtCore, QtGui, QtWidgets

from .project_manager import ProjectManager
from .project_structure import create_folders_and_subfolders
from .document_rules import JUSTIFICATION_TYPES
from .metadata_db import delete_uploaded_documents_for_rows
from .window_geometry import fit_and_center


# ──────────────────────────────────────────────────────────────────────────────
# Stylesheet
# ──────────────────────────────────────────────────────────────────────────────
STYLESHEET = """
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


# ──────────────────────────────────────────────────────────────────────────────
# Reference row widget
# ──────────────────────────────────────────────────────────────────────────────
class ReferenceRow(QtWidgets.QFrame):
    deleteRequested = QtCore.Signal(object)

    def __init__(self, index: int, alt: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("tableRowAlt" if alt else "tableRow")
        self.setFixedHeight(52)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(10)

        self.index_label = QtWidgets.QLabel(str(index), self)
        self.index_label.setObjectName("rowIndex")
        self.index_label.setFixedWidth(24)
        self.index_label.setAlignment(QtCore.Qt.AlignCenter)

        self.supplier_edit = QtWidgets.QLineEdit(self)
        self.supplier_edit.setPlaceholderText("Fournisseur")
        self.supplier_edit.setMinimumWidth(180)
        self.supplier_edit.textChanged.connect(self._on_changed)

        self.ref_edit = QtWidgets.QLineEdit(self)
        self.ref_edit.setPlaceholderText("N° Référence")
        self.ref_edit.setMinimumWidth(110)
        self.ref_edit.textChanged.connect(self._on_changed)

        self.label_edit = QtWidgets.QLineEdit(self)
        self.label_edit.setPlaceholderText("Libellé")
        self.label_edit.setMinimumWidth(160)
        self.label_edit.textChanged.connect(self._on_changed)

        self.mnp_edit = QtWidgets.QLineEdit(self)
        self.mnp_edit.setPlaceholderText("MNP")
        self.mnp_edit.setMinimumWidth(120)
        self.mnp_edit.textChanged.connect(self._on_changed)

        self.order_edit = QtWidgets.QLineEdit(self)
        self.order_edit.setPlaceholderText("N° de commande")
        self.order_edit.setMinimumWidth(140)
        self.order_edit.textChanged.connect(self._on_changed)

        del_btn = QtWidgets.QPushButton("🗑", self)
        del_btn.setObjectName("deleteRowButton")
        del_btn.setToolTip("Supprimer cette ligne")
        del_btn.clicked.connect(lambda: self.deleteRequested.emit(self))

        lay.addWidget(self.index_label)
        lay.addWidget(self.supplier_edit, 2)
        lay.addWidget(self.ref_edit, 1)
        lay.addWidget(self.label_edit, 2)
        lay.addWidget(self.mnp_edit, 1)
        lay.addWidget(self.order_edit, 2)
        lay.addWidget(del_btn)

    def _on_changed(self):
        p = self.parent()
        while p is not None:
            if isinstance(p, NewProjectDialog):
                p._update_row_counter()
                break
            p = p.parent()

    def is_filled(self) -> bool:
        return any([
            self.supplier_edit.text().strip(),
            self.ref_edit.text().strip(),
            self.label_edit.text().strip(),
            self.mnp_edit.text().strip(),
            self.order_edit.text().strip(),
        ])

    def is_valid_minimum(self) -> bool:
        return bool(self.supplier_edit.text().strip()) and bool(self.ref_edit.text().strip())

    def get_data(self) -> dict:
        return {
            "supplier": self.supplier_edit.text().strip(),
            "reference": self.ref_edit.text().strip(),
            "label": self.label_edit.text().strip(),
            "mnp": self.mnp_edit.text().strip(),
            "order_number": self.order_edit.text().strip(),
        }

    def clear_data(self):
        self.supplier_edit.clear()
        self.ref_edit.clear()
        self.label_edit.clear()
        self.order_edit.clear()
        self.mnp_edit.clear()

    def set_index(self, n: int):
        self.index_label.setText(str(n))


# ──────────────────────────────────────────────────────────────────────────────
# NewProjectDialog
# ──────────────────────────────────────────────────────────────────────────────
class NewProjectDialog(QtWidgets.QDialog):
    projectCreated = QtCore.Signal(dict)
    projectUpdated = QtCore.Signal(dict)

    _BATCH = 10
    MAX_ROWS = 1000  # Limite de dossiers (lignes fournisseur/référence) créables

    def __init__(self, parent=None, project_data: dict | None = None):
        super().__init__(parent)

        self.project_data = project_data or {}
        self.edit_mode = bool(project_data)

        self.setWindowTitle(
            "Paramétrage du projet — NOX_Manager"
            if self.edit_mode
            else "Nouveau projet — NOX_Manager"
        )
        fit_and_center(self, 1100, 820, min_w=760, min_h=560)
        self.setStyleSheet(STYLESHEET)

        self.project_manager = ProjectManager()
        self.created_project_data: dict | None = None
        self.updated_project_data: dict | None = None
        self._rows: list[ReferenceRow] = []

        self._build_ui()

        if self.edit_mode:
            self._load_project_for_edit()
        else:
            self._load_defaults()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        root.addWidget(self._build_header())
        root.addWidget(self._build_info_section())
        root.addWidget(self._build_references_section(), 1)
        root.addLayout(self._build_footer())

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget(self)
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 4)
        lay.setSpacing(2)

        self.title_label = QtWidgets.QLabel(
            "Paramétrage du projet" if self.edit_mode else "Nouveau projet",
            w
        )
        title = self.title_label
        title.setObjectName("dialogTitle")

        sub = QtWidgets.QLabel(
            "Modifiez les livrables et les lignes fournisseurs/références du projet."
            if self.edit_mode
            else "Renseignez les informations du projet et les références fournisseurs associées.",
            w
        )
        sub.setObjectName("dialogSubtitle")

        lay.addWidget(title)
        lay.addWidget(sub)
        return w

    # ── Info section ─────────────────────────────────────────────────────────

    def _build_info_section(self) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame(self)
        card.setObjectName("sectionCard")

        outer = QtWidgets.QVBoxLayout(card)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.setSpacing(14)

        section_title = QtWidgets.QLabel("Informations du projet", card)
        section_title.setObjectName("sectionTitle")
        outer.addWidget(section_title)

        # Row 1: Nom + Emplacement + Livrables
        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(16)

        # Nom du projet
        nom_col = self._field_col("Numéro de l'affaire", required=True)
        self.project_name_edit = QtWidgets.QLineEdit(card)
        self.project_name_edit.setPlaceholderText("Ex. Document test")
        nom_col.addWidget(self.project_name_edit)
        row1.addLayout(nom_col, 3)

        # Emplacement
        emp_col = self._field_col("Emplacement", required=True)
        emp_row = QtWidgets.QHBoxLayout()
        emp_row.setSpacing(8)
        self.location_edit = QtWidgets.QLineEdit(card)
        self.location_edit.setPlaceholderText("Choisir l'emplacement racine")
        emp_row.addWidget(self.location_edit, 1)
        emp_col.addLayout(emp_row)
        row1.addLayout(emp_col, 4)

        # Livrables
        liv_col = self._field_col("Livrables attendus", required=True)
        cb_row = QtWidgets.QHBoxLayout()
        cb_row.setSpacing(14)
        self.ce_checkbox   = QtWidgets.QCheckBox("CE",   card)
        self.cecc_checkbox = QtWidgets.QCheckBox("CECC", card)
        self.dpe_checkbox  = QtWidgets.QCheckBox("DPE",  card)
        for cb in (self.ce_checkbox, self.cecc_checkbox, self.dpe_checkbox):
            cb.setChecked(True)
            cb_row.addWidget(cb)
        cb_row.addStretch(1)
        liv_col.addLayout(cb_row)
        row1.addLayout(liv_col, 3)

        outer.addLayout(row1)

        # Row 2: Numéro dossier + Date fichier
        row2 = QtWidgets.QHBoxLayout()
        row2.setSpacing(16)

        num_col = self._field_col("Numéro dossier", required=True)
        self.dossier_number_edit = QtWidgets.QLineEdit(card)
        self.dossier_number_edit.setPlaceholderText("Ex. N023")
        num_col.addWidget(self.dossier_number_edit)
        row2.addLayout(num_col, 3)

        date_col = self._field_col("Date fichier", required=True)
        date_row = QtWidgets.QHBoxLayout()
        date_row.setSpacing(8)
        self.date_code_edit = QtWidgets.QLineEdit(card)
        self.date_code_edit.setPlaceholderText("JJ/MM/AAAA")
        self.date_code_edit.setText(datetime.now().strftime("%d/%m/%Y"))
        # Calendar icon button (decorative)
        cal_btn = QtWidgets.QPushButton("📅", card)
        cal_btn.setObjectName("browseButton")
        cal_btn.setFixedWidth(38)
        cal_btn.setToolTip("Choisir une date")
        cal_btn.clicked.connect(self._open_calendar)
        date_row.addWidget(self.date_code_edit, 1)
        date_row.addWidget(cal_btn)
        date_col.addLayout(date_row)
        row2.addLayout(date_col, 4)

        # Spacer to align with livrables column
        row2.addStretch(3)

        outer.addLayout(row2)
        return card

    # ── References section ───────────────────────────────────────────────────

    def _build_references_section(self) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame(self)
        card.setObjectName("sectionCard")

        outer = QtWidgets.QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Section header ──
        header = QtWidgets.QWidget(card)
        header.setFixedHeight(52)
        header_lay = QtWidgets.QHBoxLayout(header)
        header_lay.setContentsMargins(20, 0, 16, 0)
        header_lay.setSpacing(12)

        sec_title = QtWidgets.QLabel("Références à ajouter", header)
        sec_title.setObjectName("sectionTitle")
        header_lay.addWidget(sec_title)
        header_lay.addStretch(1)

        # Ces boutons ne s'affichent qu'en onglet saisie manuelle
        self.clear_button = QtWidgets.QPushButton("  🗑  Effacer tout", header)
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._clear_all_rows)

        self.add_lines_button = QtWidgets.QPushButton(
            f"  +  Ajouter des lignes", header
        )
        self.add_lines_button.setObjectName("addRowsButton")
        self.add_lines_button.clicked.connect(self._add_batch_rows)

        header_lay.addWidget(self.clear_button)
        header_lay.addWidget(self.add_lines_button)

        outer.addWidget(header)

        # ── Tab bar ──
        tab_bar_widget = QtWidgets.QWidget(card)
        tab_bar_widget.setFixedHeight(40)
        tab_bar_widget.setStyleSheet("background: #f9fafb; border-bottom: 1px solid #e5e7eb;")
        tab_bar_lay = QtWidgets.QHBoxLayout(tab_bar_widget)
        tab_bar_lay.setContentsMargins(16, 0, 16, 0)
        tab_bar_lay.setSpacing(0)

        self._tab_manual_btn = QtWidgets.QPushButton("Saisie manuelle", tab_bar_widget)
        self._tab_manual_btn.setFixedSize(160, 32)
        self._tab_bulk_btn   = QtWidgets.QPushButton("Import en masse", tab_bar_widget)
        self._tab_bulk_btn.setFixedSize(160, 32)

        for btn in (self._tab_manual_btn, self._tab_bulk_btn):
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-bottom: 3px solid transparent;
                    border-radius: 0px;
                    font-size: 13px;
                    font-weight: 500;
                    color: #6b7280;
                    padding: 0 18px;
                    min-height: 38px;
                }
                QPushButton:checked {
                    color: #2563eb;
                    font-weight: 700;
                    border-bottom: 3px solid #2563eb;
                }
                QPushButton:hover:!checked {
                    color: #374151;
                    background: #f3f4f6;
                }
            """)

        self._tab_manual_btn.setChecked(True)
        self._tab_manual_btn.clicked.connect(lambda: self._switch_tab(0))
        self._tab_bulk_btn.clicked.connect(lambda: self._switch_tab(1))

        tab_bar_lay.addWidget(self._tab_manual_btn)
        tab_bar_lay.addWidget(self._tab_bulk_btn)
        tab_bar_lay.addStretch(1)
        outer.addWidget(tab_bar_widget)

        # ── Stacked widget: page 0 = saisie manuelle, page 1 = import en masse ──
        self._tab_stack = QtWidgets.QStackedWidget(card)
        outer.addWidget(self._tab_stack, 1)

        # ── PAGE 0 : saisie manuelle ──────────────────────────────────────────
        page_manual = QtWidgets.QWidget()
        manual_lay = QtWidgets.QVBoxLayout(page_manual)
        manual_lay.setContentsMargins(0, 0, 0, 0)
        manual_lay.setSpacing(0)

        # Table column header
        col_header = QtWidgets.QFrame(page_manual)
        col_header.setObjectName("tableHeaderFrame")
        col_header.setFixedHeight(36)
        col_lay = QtWidgets.QHBoxLayout(col_header)
        col_lay.setContentsMargins(16, 0, 12, 0)
        col_lay.setSpacing(10)

        def _th(text, stretch=1, fixed_w=None):
            lbl = QtWidgets.QLabel(text, col_header)
            lbl.setObjectName("tableHeaderLabel")
            if fixed_w:
                lbl.setFixedWidth(fixed_w)
            col_lay.addWidget(lbl, stretch)

        _th("#", fixed_w=24)
        _th("Fournisseur *", 2)
        _th("Référence *", 1)
        _th("Libellé équipement", 2)
        _th("MNP", 1)
        _th("N° de commande", 2)
        _th("Actions", fixed_w=40)
        manual_lay.addWidget(col_header)

        # Scroll area for rows
        self._scroll_area = QtWidgets.QScrollArea(page_manual)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self._rows_container = QtWidgets.QWidget()
        self._rows_container.setStyleSheet("background: #ffffff;")
        self._rows_layout = QtWidgets.QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch(1)

        self._scroll_area.setWidget(self._rows_container)
        manual_lay.addWidget(self._scroll_area, 1)

        # Bottom bar
        bottom = QtWidgets.QWidget(page_manual)
        bottom.setFixedHeight(44)
        bottom_lay = QtWidgets.QHBoxLayout(bottom)
        bottom_lay.setContentsMargins(16, 0, 16, 0)
        bottom_lay.setSpacing(12)

        self.add_more_button = QtWidgets.QPushButton(
            f"  +  Ajouter {self._BATCH} lignes", bottom
        )
        self.add_more_button.setObjectName("addRowsButton")
        self.add_more_button.clicked.connect(self._add_batch_rows)
        bottom_lay.addWidget(self.add_more_button)
        bottom_lay.addStretch(1)

        self.row_counter_label = QtWidgets.QLabel("", bottom)
        self.row_counter_label.setObjectName("rowCounter")
        bottom_lay.addWidget(self.row_counter_label)

        sep = QtWidgets.QFrame(page_manual)
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background:#e5e7eb; max-height:1px; border:none;")

        manual_lay.addWidget(sep)
        manual_lay.addWidget(bottom)

        self._tab_stack.addWidget(page_manual)

        # ── PAGE 1 : import en masse ──────────────────────────────────────────
        page_bulk = QtWidgets.QWidget()
        bulk_lay = QtWidgets.QVBoxLayout(page_bulk)
        bulk_lay.setContentsMargins(20, 16, 20, 16)
        bulk_lay.setSpacing(14)

        # Info banner
        info_frame = QtWidgets.QFrame(page_bulk)
        info_frame.setStyleSheet(
            "QFrame { background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; }"
        )
        info_lay = QtWidgets.QHBoxLayout(info_frame)
        info_lay.setContentsMargins(14, 10, 14, 10)
        info_lay.setSpacing(10)

        info_icon = QtWidgets.QLabel("ℹ", info_frame)
        info_icon.setStyleSheet("color:#2563eb; font-size:16px; font-weight:700; background:transparent; border:none;")
        info_icon.setFixedWidth(20)

        info_text = QtWidgets.QLabel(
            "Collez ou saisissez vos données ci-dessous. Chaque liste doit contenir une valeur par ligne.\n",
            info_frame,
        )
        info_text.setStyleSheet("color:#1e40af; font-size:12px; background:transparent; border:none;")
        info_text.setWordWrap(True)

        info_lay.addWidget(info_icon)
        info_lay.addWidget(info_text, 1)
        bulk_lay.addWidget(info_frame)

        # Four text area columns
        cols_lay = QtWidgets.QHBoxLayout()
        cols_lay.setSpacing(12)

        def _bulk_col(label_text: str, placeholder_title: str, examples: list[str]) -> QtWidgets.QPlainTextEdit:
            col_w = QtWidgets.QWidget(page_bulk)
            col_lay = QtWidgets.QVBoxLayout(col_w)
            col_lay.setContentsMargins(0, 0, 0, 0)
            col_lay.setSpacing(6)

            lbl_row = QtWidgets.QHBoxLayout()
            lbl = QtWidgets.QLabel(label_text, col_w)
            lbl.setObjectName("fieldLabel")
            req = QtWidgets.QLabel(" *", col_w)
            req.setObjectName("required")
            lbl_row.addWidget(lbl)
            lbl_row.addWidget(req)
            lbl_row.addStretch(1)
            col_lay.addLayout(lbl_row)

            placeholder_lines = [f"{placeholder_title}", "", "Ex.:"] + examples
            placeholder = "\n".join(placeholder_lines)

            edit = QtWidgets.QPlainTextEdit(col_w)
            edit.setPlaceholderText(placeholder)
            edit.setStyleSheet("""
                QPlainTextEdit {
                    background: #ffffff;
                    border: 1.5px solid #d1d5db;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 13px;
                    color: #111827;
                }
                QPlainTextEdit:focus { border-color: #2563eb; }
            """)
            col_lay.addWidget(edit, 1)
            cols_lay.addWidget(col_w, 1)
            return edit

        self._bulk_supplier_edit = _bulk_col(
            "Fournisseur", "Une ligne par fournisseur",
            ["VisioParts", "TechnoVis", "FixPro", "Soprema"],
        )
        self._bulk_ref_edit = _bulk_col(
            "N° de référence", "Une ligne par référence",
            ["VIS-001", "VIS-002", "TV-010", "TV-011"],
        )
        self._bulk_label_edit = _bulk_col(
            "Libellé", "Une ligne par libellé",
            ["Vis inox M6 x 20", "Écrou frein M6", "Rondelle plate M6", "Vis tête hexagonale M8 x 25"],
        )
        self._bulk_mnp_edit = _bulk_col(
            "MNP", "Une ligne par MNP",
            ["MNP-001", "MNP-002", "MNP-003", "MNP-004"],
        )
        self._bulk_order_edit = _bulk_col(
            "N° de commande", "Une ligne par n° de commande",
            ["CMD-2024-0001", "CMD-2024-0002", "CMD-2024-0003", "CMD-2024-0004"],
        )

        bulk_lay.addLayout(cols_lay, 1)

        # Bottom bar: format hint + download template + import button
        bulk_bottom = QtWidgets.QHBoxLayout()
        bulk_bottom.setSpacing(12)

        fmt_label = QtWidgets.QLabel("Formats acceptés : texte brut (.txt) ou CSV (.csv)", page_bulk)
        fmt_label.setStyleSheet("color:#9ca3af; font-size:11px;")
        bulk_bottom.addWidget(fmt_label)
        bulk_bottom.addStretch(1)
        
        self._import_bulk_btn = QtWidgets.QPushButton("  ⬆  Importer les lignes", page_bulk)
        self._import_bulk_btn.setObjectName("primaryButton")
        self._import_bulk_btn.setFixedHeight(36)
        self._import_bulk_btn.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 20px;
                min-height: 34px;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:pressed { background: #1e40af; }
        """)
        self._import_bulk_btn.clicked.connect(self._import_bulk_rows)
        bulk_bottom.addWidget(self._import_bulk_btn)

        bulk_lay.addLayout(bulk_bottom)

        self._tab_stack.addWidget(page_bulk)

        # Initial batch for manual tab
        #self._add_batch_rows()
        return card

    def _switch_tab(self, index: int):
        """Bascule entre l'onglet saisie manuelle (0) et import en masse (1)."""
        self._tab_stack.setCurrentIndex(index)
        self._tab_manual_btn.setChecked(index == 0)
        self._tab_bulk_btn.setChecked(index == 1)
        # Affiche/masque les boutons du header selon l'onglet actif
        self.clear_button.setVisible(index == 0)
        self.add_lines_button.setVisible(index == 0)

    def _download_bulk_template(self):
        """Propose de télécharger un fichier CSV modèle."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Enregistrer le modèle",
            "modele_import.csv",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)",
        )
        if not path:
            return
        try:
            content = (
                "Fournisseur;Reference;Libelle;MNP;N_commande\n"
                "VisioParts;VIS-001;Vis inox M6 x 20;MNP-001;CMD-2024-0001\n"
                "TechnoVis;VIS-002;Écrou frein M6;MNP-002;CMD-2024-0002\n"
                "FixPro;TV-010;Rondelle plate M6;MNP-003;CMD-2024-0003\n"
                "Soprema;TV-011;Vis tête hexagonale M8 x 25;MNP-004;CMD-2024-0004\n"
            )
            Path(path).write_text(content, encoding="utf-8-sig")
            QtWidgets.QMessageBox.information(
                self,
                "Modèle téléchargé",
                f"Le modèle a été enregistré :\n{path}",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer le modèle.\n\n{e}")

    @staticmethod
    def _split_bulk_column(edit: QtWidgets.QPlainTextEdit) -> list[str]:
        """Découpe une colonne de l'import en masse en conservant la position des lignes.

        Une ligne vide au milieu du texte doit rester une valeur vide à son
        index (pas de décalage des lignes suivantes vers le haut) : seules
        les lignes vides en fin de texte (saut de ligne final, etc.) sont
        ignorées.
        """
        lines = [l.strip() for l in edit.toPlainText().splitlines()]
        while lines and not lines[-1]:
            lines.pop()
        return lines

    def _parse_bulk_lines(self) -> list[dict]:
        """Parse les 5 colonnes de l'onglet import en masse et retourne une liste de dicts.

        Les lignes sont assemblées par index (ligne 1 de chaque colonne → ligne 1
        du dossier, etc.) afin qu'une cellule vide reste vide sans décaler les
        autres colonnes. Les lignes totalement vides (aucune donnée dans aucune
        colonne) ne sont pas filtrées ici : c'est `_import_bulk_rows` /
        `is_filled()` qui s'en charge une fois l'alignement garanti.
        """
        suppliers  = self._split_bulk_column(self._bulk_supplier_edit)
        references = self._split_bulk_column(self._bulk_ref_edit)
        labels     = self._split_bulk_column(self._bulk_label_edit)
        mnps       = self._split_bulk_column(self._bulk_mnp_edit)
        orders     = self._split_bulk_column(self._bulk_order_edit)

        if not any([suppliers, references, labels, mnps, orders]):
            return []

        max_len = max(len(suppliers), len(references), len(labels), len(mnps), len(orders))
        rows = []
        for i in range(max_len):
            supplier  = suppliers[i]  if i < len(suppliers)  else ""
            reference = references[i] if i < len(references) else ""
            label     = labels[i]     if i < len(labels)     else ""
            mnp       = mnps[i]       if i < len(mnps)       else ""
            order     = orders[i]     if i < len(orders)     else ""
            rows.append({
                "supplier":      supplier,
                "reference":     reference,
                "label":         label,
                "mnp":           mnp,
                "order_number":  order,
            })
        return rows

    def _import_bulk_rows(self):
        """Importe les lignes de l'onglet masse dans l'onglet saisie manuelle."""
        parsed = self._parse_bulk_lines()

        # Les lignes totalement vides (aucune donnée dans aucune colonne) ne sont
        # pas importées : on ne les retire qu'une fois l'alignement par index
        # garanti ci-dessus, pour ne jamais décaler une colonne par rapport
        # aux autres.
        parsed = [data for data in parsed if any(data.values())]

        if not parsed:
            QtWidgets.QMessageBox.information(
                self,
                "Import en masse",
                "Aucune ligne à importer.\n\nRenseignez au moins une colonne Fournisseur.",
            )
            return

        # Vérification longueurs incohérentes (optionnelle, avertissement doux)
        suppliers  = self._split_bulk_column(self._bulk_supplier_edit)
        references = self._split_bulk_column(self._bulk_ref_edit)
        if references and len(suppliers) != len(references):
            answer = QtWidgets.QMessageBox.question(
                self,
                "Import en masse",
                f"Le nombre de fournisseurs ({len(suppliers)}) et de références ({len(references)}) "
                f"ne correspondent pas.\n\nContinuer quand même ?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return

        # Déduplique par rapport aux lignes existantes
        existing_keys = {
            (r.get_data()["supplier"], r.get_data()["reference"])
            for r in self._rows
            if r.is_filled()
        }

        added = 0
        for data in parsed:
            key = (data["supplier"], data["reference"])
            if key in existing_keys:
                continue
            existing_keys.add(key)
            self._add_single_row(data)
            added += 1

        self._reindex_rows()
        self._update_row_counter()

        # Vide les zones de texte après import réussi
        self._bulk_supplier_edit.clear()
        self._bulk_ref_edit.clear()
        self._bulk_label_edit.clear()
        self._bulk_mnp_edit.clear()
        self._bulk_order_edit.clear()

        # Bascule vers l'onglet saisie manuelle pour vérification
        self._switch_tab(0)

        QtWidgets.QMessageBox.information(
            self,
            "Import en masse",
            f"{added} ligne(s) importée(s) avec succès.",
        )

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self) -> QtWidgets.QHBoxLayout:
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(12)
        lay.addStretch(1)

        self.cancel_button = QtWidgets.QPushButton("Annuler", self)
        self.cancel_button.setObjectName("outlineButton")
        self.cancel_button.clicked.connect(self.reject)

        self.create_button = QtWidgets.QPushButton("Créer le projet", self)
        self.create_button.setObjectName("primaryButton")
        self.create_button.clicked.connect(self._create_project)

        lay.addWidget(self.cancel_button)
        lay.addWidget(self.create_button)
        return lay

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _field_col(label_text: str, required: bool = False) -> QtWidgets.QVBoxLayout:
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(5)

        lbl_row = QtWidgets.QHBoxLayout()
        lbl_row.setSpacing(3)
        lbl = QtWidgets.QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        lbl_row.addWidget(lbl)
        if required:
            req = QtWidgets.QLabel(" *")
            req.setObjectName("required")
            lbl_row.addWidget(req)
        lbl_row.addStretch(1)
        col.addLayout(lbl_row)
        return col

    def _reindex_rows(self):
        for i, row in enumerate(self._rows):
            row.set_index(i + 1)
            row.setObjectName("tableRowAlt" if i % 2 else "tableRow")
            row.setStyleSheet(
                "background:#fafafa; border-bottom:1px solid #f3f4f6;"
                if i % 2
                else "background:#ffffff; border-bottom:1px solid #f3f4f6;"
            )

    def _update_row_counter(self):
        filled = sum(1 for r in self._rows if r.is_filled())
        total  = len(self._rows)
        self.row_counter_label.setText(
            f"{filled} ligne(s) renseignée(s) sur {total}  (limite : {self.MAX_ROWS})"
        )

    # ── Row management ────────────────────────────────────────────────────────

    def _add_batch_rows(self):
        if len(self._rows) >= self.MAX_ROWS:
            QtWidgets.QMessageBox.warning(
                self,
                "Limite atteinte",
                f"Le nombre maximal de dossiers pour un projet est de {self.MAX_ROWS}.\n"
                "Impossible d'ajouter de nouvelles lignes."
            )
            return

        to_add = min(self._BATCH, self.MAX_ROWS - len(self._rows))

        stretch_item = self._rows_layout.takeAt(self._rows_layout.count() - 1)
        for _ in range(to_add):
            idx = len(self._rows) + 1
            alt = (idx % 2 == 0)
            row = ReferenceRow(idx, alt=alt, parent=self._rows_container)
            row.deleteRequested.connect(self._delete_row)
            self._rows.append(row)
            self._rows_layout.addWidget(row)
        self._rows_layout.addStretch(1)
        self._update_row_counter()

        if to_add < self._BATCH:
            QtWidgets.QMessageBox.information(
                self,
                "Limite atteinte",
                f"Seules {to_add} ligne(s) ont pu être ajoutées pour respecter "
                f"la limite de {self.MAX_ROWS} dossiers."
            )
        # Scroll to bottom
        QtCore.QTimer.singleShot(
            50,
            lambda: self._scroll_area.verticalScrollBar().setValue(
                self._scroll_area.verticalScrollBar().maximum()
            ),
        )

    def _delete_row(self, row: ReferenceRow):
        if row in self._rows:
            self._rows.remove(row)
            self._rows_layout.removeWidget(row)
            row.deleteLater()
            self._reindex_rows()
            self._update_row_counter()

    def _clear_all_rows(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Effacer tout",
            "Effacer toutes les lignes saisies ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            for row in self._rows:
                row.clear_data()
            self._update_row_counter()

    # ── Defaults ──────────────────────────────────────────────────────────────

    def _load_defaults(self):
        default_location = self.project_manager.get_default_location()
        if default_location:
            self.location_edit.setText(default_location)
        self._add_single_row()

    def _browse_location(self):
        start_dir = self.location_edit.text().strip() or str(Path.home())
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choisir l'emplacement du projet", start_dir
        )
        if folder:
            self.location_edit.setText(folder)

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _get_rows_data(self) -> list[dict]:
        return [r.get_data() for r in self._rows if r.is_filled()]

    def _parse_rows_for_structure(self) -> list[tuple[str, str]]:
        return [
            (d["supplier"], d["reference"])
            for d in self._get_rows_data()
            if d["supplier"] and d["reference"]
        ]

    def _selected_bdds(self) -> list[str]:
        selected = []
        if self.ce_checkbox.isChecked():
            selected.append("CE")
        if self.cecc_checkbox.isChecked():
            selected.append("CECC")
        if self.dpe_checkbox.isChecked():
            selected.append("DPE")
        return selected


    def _open_calendar(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Choisir une date")
        fit_and_center(dialog, 320, 280, min_w=280, min_h=240)

        layout = QtWidgets.QVBoxLayout(dialog)

        calendar = QtWidgets.QCalendarWidget(dialog)
        calendar.setGridVisible(True)

        current_text = self.date_code_edit.text().strip()
        try:
            current_date = datetime.strptime(current_text, "%d/%m/%Y")
            calendar.setSelectedDate(
                QtCore.QDate(current_date.year, current_date.month, current_date.day)
            )
        except Exception:
            calendar.setSelectedDate(QtCore.QDate.currentDate())

        layout.addWidget(calendar)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)

        cancel_btn = QtWidgets.QPushButton("Annuler", dialog)
        ok_btn = QtWidgets.QPushButton("Valider", dialog)
        ok_btn.setObjectName("primaryButton")

        cancel_btn.clicked.connect(dialog.reject)
        ok_btn.clicked.connect(dialog.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)
        layout.addLayout(buttons)

        if dialog.exec() == QtWidgets.QDialog.Accepted:
            selected = calendar.selectedDate()
            self.date_code_edit.setText(
                selected.toString("dd/MM/yyyy")
            )

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self) -> tuple[bool, str]:
        if not self.project_name_edit.text().strip():
            return False, "Le Numéro de l'affaire est obligatoire."

        if not self.location_edit.text().strip():
            return False, "L'emplacement est obligatoire."

        if not self.dossier_number_edit.text().strip():
            return False, "Le numéro de dossier est obligatoire."

        date_code = self.date_code_edit.text().strip()
        try:
            datetime.strptime(date_code, "%d/%m/%Y")
        except ValueError:
            return False, "La date doit être au format JJ/MM/AAAA (ex. 24/04/2026)."

        if not self._selected_bdds():
            return False, "Sélectionnez au moins un livrable (CE, CECC ou DPE)."

        filled_rows = [r for r in self._rows if r.is_filled()]

        if not filled_rows:
            return False, "Ajoutez au moins une ligne avec un fournisseur et un N° de référence."

        if len(filled_rows) > self.MAX_ROWS:
            return False, (
                f"Le nombre de dossiers à créer ({len(filled_rows)}) dépasse "
                f"la limite autorisée de {self.MAX_ROWS}."
            )

        for i, row in enumerate(filled_rows, start=1):
            if not row.is_valid_minimum():
                return False, (
                    f"La ligne {i} est incomplète.\n\n"
                    "Les champs obligatoires sont : Fournisseur et N° Référence."
                )

        return True, ""

    # ── Create project ────────────────────────────────────────────────────────

    def _clear_rows_widgets(self):
        for row in self._rows:
            self._rows_layout.removeWidget(row)
            row.deleteLater()

        self._rows.clear()
        self._update_row_counter()


    def _add_single_row(self, data: dict | None = None):
        stretch_item = self._rows_layout.takeAt(self._rows_layout.count() - 1)

        idx = len(self._rows) + 1
        alt = idx % 2 == 0

        row = ReferenceRow(idx, alt=alt, parent=self._rows_container)
        row.deleteRequested.connect(self._delete_row)

        if data:
            row.supplier_edit.setText(data.get("supplier", ""))
            row.ref_edit.setText(data.get("reference", ""))
            row.label_edit.setText(data.get("label", ""))
            row.mnp_edit.setText(data.get("mnp", ""))
            row.order_edit.setText(data.get("order_number", ""))

        self._rows.append(row)
        self._rows_layout.addWidget(row)
        self._rows_layout.addStretch(1)

        self._update_row_counter()


    def _load_project_for_edit(self):
        project_path = Path(self.project_data.get("project_path", ""))
        project_name = self.project_data.get("project_name", project_path.name)

        self.project_name_edit.setText(project_name)
        self.location_edit.setText(str(project_path.parent))
        self.dossier_number_edit.setText(self.project_data.get("dossier_number", ""))
        self.date_code_edit.setText(self.project_data.get("date_code", ""))

        self.project_name_edit.setReadOnly(True)
        self.location_edit.setReadOnly(True)

        enabled_bdds = set(self.project_data.get("enabled_bdds", []))
        self.ce_checkbox.setChecked("CE" in enabled_bdds)
        self.cecc_checkbox.setChecked("CECC" in enabled_bdds)
        self.dpe_checkbox.setChecked("DPE" in enabled_bdds)

        self.create_button.setText("Enregistrer les modifications")

        self._clear_rows_widgets()

        rows = self.project_data.get("rows", [])

        if rows:
            for row_data in rows:
                self._add_single_row(row_data)
        else:
            for _ in range(self._BATCH):
                self._add_single_row()

        self._reindex_rows()
        self._update_row_counter()

    def _create_project(self):
        if self.edit_mode:
            return self._update_project()
        ok, message = self._validate()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Création projet", message)
            return

        project_name   = self.project_name_edit.text().strip()
        location       = Path(self.location_edit.text().strip())
        dossier_number = self.dossier_number_edit.text().strip().upper()
        date_code      = self.date_code_edit.text().strip()
        rows           = self._parse_rows_for_structure()
        enabled_bdds   = self._selected_bdds()
        rows_data      = self._get_rows_data()
        # L'emplacement choisi accueille directement .nox et les dossiers BDD,
        # sans dossier intermédiaire nommé d'après le numéro de l'affaire.
        project_dir    = location

        if project_dir.exists() and any(project_dir.iterdir()):
            answer = QtWidgets.QMessageBox.question(
                self,
                "Projet existant",
                "Le dossier du projet existe déjà et n'est pas vide.\n"
                "Voulez-vous continuer et compléter la structure ?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return

        try:
            project_dir.mkdir(parents=True, exist_ok=True)

            for bdd_type in enabled_bdds:
                bdd_dir  = project_dir / f"BDD {bdd_type} {dossier_number}"
                docs_dir = bdd_dir / "Documents"
                bdd_dir.mkdir(parents=True, exist_ok=True)
                docs_dir.mkdir(parents=True, exist_ok=True)

                excel_path = bdd_dir / f"BDD_{bdd_type}_{dossier_number}.xlsx"
                if not excel_path.exists():
                    excel_path.touch()

                create_folders_and_subfolders(
                    docs_dir,
                    [(d["supplier"], d["reference"]) for d in rows_data]
                )

            self.project_manager.create_project_file(
                project_dir=project_dir,
                project_name=project_name,
                dossier_number=dossier_number,
                date_code=date_code,
                rows=rows_data,
                enabled_bdds=enabled_bdds,
            )

            project_data = self.project_manager.load_project(project_dir)
            if not project_data:
                raise RuntimeError("Impossible de relire le fichier projet créé.")

            self.created_project_data = project_data
            self.projectCreated.emit(project_data)
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur de création",
                f"Impossible de créer le projet.\n\n{e}",
            )

    def _update_project(self):
        ok, message = self._validate()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Paramétrage projet", message)
            return

        try:
            project_dir = Path(self.project_data["project_path"])
            dossier_number = self.dossier_number_edit.text().strip().upper()

            old_rows = self.project_data.get("rows", []) or []
            new_rows = self._get_rows_data()
            enabled_bdds = self._selected_bdds()

            old_keys = {
                (
                    str(row.get("supplier", "")).strip(),
                    str(row.get("reference", "")).strip(),
                )
                for row in old_rows
                if row.get("supplier") and row.get("reference")
            }

            new_keys = {
                (
                    str(row.get("supplier", "")).strip(),
                    str(row.get("reference", "")).strip(),
                )
                for row in new_rows
                if row.get("supplier") and row.get("reference")
            }

            removed_keys = old_keys - new_keys

            removed_rows = [
                row for row in old_rows
                if (
                    str(row.get("supplier", "")).strip(),
                    str(row.get("reference", "")).strip(),
                ) in removed_keys
            ]

            if removed_rows:
                txt_rows = "\n".join(
                    f"• {r.get('supplier', '')} / {r.get('reference', '')}"
                    for r in removed_rows
                )

                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("Suppression de lignes")
                msg.setText(
                    "Certaines lignes ont été supprimées du projet.\n\n"
                    "Voulez-vous aussi supprimer les dossiers et les données associées ?"
                )
                msg.setInformativeText(
                    f"Lignes concernées :\n{txt_rows}\n\n"
                    "Si vous confirmez, les dossiers physiques des références seront supprimés "
                    "dans les BDD CE / CECC / DPE, ainsi que les documents référencés en base de données.\n\n"
                    "Cette action est irréversible."
                )

                delete_btn = msg.addButton(
                    "Supprimer dossiers et données",
                    QtWidgets.QMessageBox.DestructiveRole
                )
                keep_btn = msg.addButton(
                    "Conserver les dossiers",
                    QtWidgets.QMessageBox.AcceptRole
                )
                cancel_btn = msg.addButton(
                    "Annuler l'enregistrement",
                    QtWidgets.QMessageBox.RejectRole
                )

                msg.setDefaultButton(cancel_btn)
                msg.exec()

                clicked = msg.clickedButton()

                if clicked == cancel_btn:
                    return

                if clicked == delete_btn:
                    for row in removed_rows:
                        supplier = str(row.get("supplier", "")).strip()
                        reference = str(row.get("reference", "")).strip()

                        if not supplier or not reference:
                            continue

                        for bdd_type in JUSTIFICATION_TYPES:
                            target = (
                                project_dir
                                / f"BDD {bdd_type} {dossier_number}"
                                / "Documents"
                                / supplier
                                / reference
                            )

                            if target.exists():
                                shutil.rmtree(target, ignore_errors=True)

                            # Supprime aussi le dossier fournisseur s'il est devenu vide
                            supplier_dir = (
                                project_dir
                                / f"BDD {bdd_type} {dossier_number}"
                                / "Documents"
                                / supplier
                            )

                            if supplier_dir.exists() and not any(supplier_dir.iterdir()):
                                shutil.rmtree(supplier_dir, ignore_errors=True)

                    delete_uploaded_documents_for_rows(project_dir, removed_rows)

            for bdd_type in enabled_bdds:
                bdd_dir = project_dir / f"BDD {bdd_type} {dossier_number}"
                docs_dir = bdd_dir / "Documents"

                bdd_dir.mkdir(parents=True, exist_ok=True)
                docs_dir.mkdir(parents=True, exist_ok=True)

                excel_path = bdd_dir / f"BDD_{bdd_type}_{dossier_number}.xlsx"
                if not excel_path.exists():
                    excel_path.touch()

                create_folders_and_subfolders(
                    docs_dir,
                    [(d["supplier"], d["reference"]) for d in new_rows]
                )

            updated_data = {
                "project_name": self.project_name_edit.text().strip(),
                "dossier_number": dossier_number,
                "date_code": self.date_code_edit.text().strip(),
                "rows": new_rows,
                "enabled_bdds": enabled_bdds,
            }

            self.project_manager.save_project(project_dir, updated_data)

            project_data = self.project_manager.load_project(project_dir)
            if not project_data:
                raise RuntimeError("Impossible de relire le projet après modification.")

            self.updated_project_data = project_data
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur de paramétrage",
                f"Impossible d'enregistrer le paramétrage du projet.\n\n{e}",
            )