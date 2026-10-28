"""Dialogue de création et de modification d'un projet (R1 à R6).

Interface reprise de `00_ancien/wikidocs_qt/new_project_dialog.py` (et non de
`new_project_dialog2.py`) ; les contrôles et l'enregistrement passent par
`services/projets.py`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from app.models.projet import Article, Projet
from app.services import projets
from app.ui.geometrie import ajuster_et_centrer
from app.ui.theme import STYLE_DIALOGUE_PROJET as STYLESHEET


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
            if isinstance(p, DialogueProjet):
                p._update_row_counter()
                break
            p = p.parent()

    def is_filled(self) -> bool:
        return any(
            [
                self.supplier_edit.text().strip(),
                self.ref_edit.text().strip(),
                self.label_edit.text().strip(),
                self.mnp_edit.text().strip(),
                self.order_edit.text().strip(),
            ]
        )

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
class DialogueProjet(QtWidgets.QDialog):
    # Projet créé, ou modifié (mode modification).
    projectCreated = QtCore.Signal(object)
    projectUpdated = QtCore.Signal(object)

    _BATCH = 10
    MAX_ROWS = projets.articles_max()  # Limite de dossiers (lignes fournisseur/référence)

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
            "Paramétrage du projet" if self.edit_mode else "Nouveau projet", w
        )
        title = self.title_label
        title.setObjectName("dialogTitle")

        sub = QtWidgets.QLabel(
            "Modifiez les livrables et les lignes fournisseurs/références du projet."
            if self.edit_mode
            else "Renseignez les informations du projet et les références fournisseurs associées.",
            w,
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
        self.ce_checkbox = QtWidgets.QCheckBox("CE", card)
        self.cecc_checkbox = QtWidgets.QCheckBox("CECC", card)
        self.dpe_checkbox = QtWidgets.QCheckBox("DPE", card)
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

        self.add_lines_button = QtWidgets.QPushButton("  +  Ajouter des lignes", header)
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
        self._tab_bulk_btn = QtWidgets.QPushButton("Import en masse", tab_bar_widget)
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

        self.add_more_button = QtWidgets.QPushButton(f"  +  Ajouter {self._BATCH} lignes", bottom)
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
        info_icon.setStyleSheet(
            "color:#2563eb; font-size:16px; font-weight:700; background:transparent; border:none;"
        )
        info_icon.setFixedWidth(20)

        info_text = QtWidgets.QLabel(
            "Collez ou saisissez vos données ci-dessous. "
            "Chaque liste doit contenir une valeur par ligne.\n",
            info_frame,
        )
        info_text.setStyleSheet(
            "color:#1e40af; font-size:12px; background:transparent; border:none;"
        )
        info_text.setWordWrap(True)

        info_lay.addWidget(info_icon)
        info_lay.addWidget(info_text, 1)
        bulk_lay.addWidget(info_frame)

        # Four text area columns
        cols_lay = QtWidgets.QHBoxLayout()
        cols_lay.setSpacing(12)

        def _bulk_col(
            label_text: str, placeholder_title: str, examples: list[str]
        ) -> QtWidgets.QPlainTextEdit:
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
            "Fournisseur",
            "Une ligne par fournisseur",
            ["VisioParts", "TechnoVis", "FixPro", "Soprema"],
        )
        self._bulk_ref_edit = _bulk_col(
            "N° de référence",
            "Une ligne par référence",
            ["VIS-001", "VIS-002", "TV-010", "TV-011"],
        )
        self._bulk_label_edit = _bulk_col(
            "Libellé",
            "Une ligne par libellé",
            [
                "Vis inox M6 x 20",
                "Écrou frein M6",
                "Rondelle plate M6",
                "Vis tête hexagonale M8 x 25",
            ],
        )
        self._bulk_mnp_edit = _bulk_col(
            "MNP",
            "Une ligne par MNP",
            ["MNP-001", "MNP-002", "MNP-003", "MNP-004"],
        )
        self._bulk_order_edit = _bulk_col(
            "N° de commande",
            "Une ligne par n° de commande",
            ["CMD-2024-0001", "CMD-2024-0002", "CMD-2024-0003", "CMD-2024-0004"],
        )

        bulk_lay.addLayout(cols_lay, 1)

        # Bottom bar: format hint + download template + import button
        bulk_bottom = QtWidgets.QHBoxLayout()
        bulk_bottom.setSpacing(12)

        fmt_label = QtWidgets.QLabel(
            "Formats acceptés : texte brut (.txt) ou CSV (.csv)", page_bulk
        )
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
        # self._add_batch_rows()
        return card

    def _switch_tab(self, index: int):
        """Bascule entre l'onglet saisie manuelle (0) et import en masse (1)."""
        self._tab_stack.setCurrentIndex(index)
        self._tab_manual_btn.setChecked(index == 0)
        self._tab_bulk_btn.setChecked(index == 1)
        # Affiche/masque les boutons du header selon l'onglet actif
        self.clear_button.setVisible(index == 0)
        self.add_lines_button.setVisible(index == 0)

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
        total = len(self._rows)
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
                "Impossible d'ajouter de nouvelles lignes.",
            )
            return

        to_add = min(self._BATCH, self.MAX_ROWS - len(self._rows))

        self._rows_layout.takeAt(self._rows_layout.count() - 1)  # retire l'espace final
        for _ in range(to_add):
            idx = len(self._rows) + 1
            alt = idx % 2 == 0
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
                f"la limite de {self.MAX_ROWS} dossiers.",
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

    def _browse_location(self):
        start_dir = self.location_edit.text().strip() or str(Path.home())
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choisir l'emplacement du projet", start_dir
        )
        if folder:
            self.location_edit.setText(folder)

    # ── Data helpers ──────────────────────────────────────────────────────────

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
        ajuster_et_centrer(dialog, 320, 280, largeur_min=280, hauteur_min=240)

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
            self.date_code_edit.setText(selected.toString("dd/MM/yyyy"))

    # ── Validation ────────────────────────────────────────────────────────────

    # ── Create project ────────────────────────────────────────────────────────

    def _clear_rows_widgets(self):
        for row in self._rows:
            self._rows_layout.removeWidget(row)
            row.deleteLater()

        self._rows.clear()
        self._update_row_counter()

    def _add_single_row(self, data: dict | None = None):
        self._rows_layout.takeAt(self._rows_layout.count() - 1)  # retire l'espace final

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

    # ── Ouverture ─────────────────────────────────────────────────────────────

    def __init__(self, parent=None, projet: Projet | None = None, etat=None):
        super().__init__(parent)
        self.projet = projet
        self.edit_mode = projet is not None
        self.setWindowTitle(
            "Paramétrage du projet — NOX_Manager"
            if self.edit_mode
            else "Nouveau projet — NOX_Manager"
        )
        ajuster_et_centrer(self, 1100, 820, largeur_min=760, hauteur_min=560)
        self.setStyleSheet(STYLESHEET)
        self.etat = etat or projets.etat_utilisateur()
        self.created_project: Projet | None = None
        self.updated_project: Projet | None = None
        self._rows: list[ReferenceRow] = []
        self._build_ui()
        if self.edit_mode:
            self._load_project_for_edit()
        else:
            self._load_defaults()

    def _load_defaults(self):
        emplacement = self.etat.emplacement_par_defaut()
        if emplacement:
            self.location_edit.setText(emplacement)
        self._add_single_row()

    def _load_project_for_edit(self):
        p = self.projet
        self.project_name_edit.setText(p.nom or p.dossier.name)
        self.location_edit.setText(str(p.dossier.parent))
        self.dossier_number_edit.setText(p.numero_dossier)
        self.date_code_edit.setText(p.date_code)
        self.project_name_edit.setReadOnly(True)
        self.location_edit.setReadOnly(True)
        self.ce_checkbox.setChecked("CE" in p.livrables)
        self.cecc_checkbox.setChecked("CECC" in p.livrables)
        self.dpe_checkbox.setChecked("DPE" in p.livrables)
        self.create_button.setText("Enregistrer les modifications")
        self._clear_rows_widgets()
        if p.articles:
            for article in p.articles:
                self._add_single_row(article.vers_dict())
        else:
            for _ in range(self._BATCH):
                self._add_single_row()
        self._reindex_rows()
        self._update_row_counter()

    # ── Saisie ────────────────────────────────────────────────────────────────

    def _lignes(self) -> list[Article]:
        return [Article.depuis_ligne(r.get_data()) for r in self._rows if r.is_filled()]

    def _saisie(self) -> projets.SaisieProjet:
        return projets.SaisieProjet(
            nom=self.project_name_edit.text(),
            emplacement=self.location_edit.text(),
            numero_dossier=self.dossier_number_edit.text(),
            date_code=self.date_code_edit.text(),
            livrables=self._selected_bdds(),
            lignes=self._lignes(),
        )

    def _validate(self) -> tuple[bool, str]:
        message = projets.verifier(self._saisie())
        return message is None, message or ""

    # ── Import en masse (R4) ──────────────────────────────────────────────────

    def _bulk_edits(self) -> list[QtWidgets.QPlainTextEdit]:
        return [
            self._bulk_supplier_edit,
            self._bulk_ref_edit,
            self._bulk_label_edit,
            self._bulk_mnp_edit,
            self._bulk_order_edit,
        ]

    def _download_bulk_template(self):
        """Propose d'enregistrer le modèle CSV."""
        chemin, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Enregistrer le modèle",
            "modele_import.csv",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)",
        )
        if not chemin:
            return
        try:
            projets.ecrire_modele_csv(Path(chemin))
        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self, "Erreur", f"Impossible d'enregistrer le modèle.\n\n{e}"
            )
            return
        QtWidgets.QMessageBox.information(
            self, "Modèle téléchargé", f"Le modèle a été enregistré :\n{chemin}"
        )

    def _import_bulk_rows(self):
        """Importe les lignes de l'onglet masse dans l'onglet saisie manuelle."""
        colonnes = [e.toPlainText() for e in self._bulk_edits()]
        importees = projets.lignes_import_masse(*colonnes)
        if not importees:
            QtWidgets.QMessageBox.information(
                self,
                "Import en masse",
                "Aucune ligne à importer.\n\nRenseignez au moins une colonne Fournisseur.",
            )
            return
        question = projets.ecart_import_masse(colonnes[0], colonnes[1])
        if question and not self._oui("Import en masse", question):
            return
        ajout = projets.nouvelles_lignes(self._lignes(), importees)
        for article in ajout:
            self._add_single_row(article.vers_dict())
        self._reindex_rows()
        self._update_row_counter()
        for e in self._bulk_edits():
            e.clear()
        self._switch_tab(0)
        QtWidgets.QMessageBox.information(
            self, "Import en masse", f"{len(ajout)} ligne(s) importée(s) avec succès."
        )

    def _oui(self, titre: str, question: str) -> bool:
        b = QtWidgets.QMessageBox.StandardButton
        return QtWidgets.QMessageBox.question(self, titre, question, b.Yes | b.No, b.No) == b.Yes

    # ── Enregistrement ────────────────────────────────────────────────────────

    def _create_project(self):
        if self.edit_mode:
            return self._update_project()
        ok, message = self._validate()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Création projet", message)
            return
        saisie = self._saisie()
        if projets.dossier_existant_non_vide(saisie.emplacement) and not self._oui(
            "Projet existant",
            "Le dossier du projet existe déjà et n'est pas vide.\n"
            "Voulez-vous continuer et compléter la structure ?",
        ):
            return
        try:
            self.created_project = projets.creer_projet(saisie, self.etat)
        except Exception as e:  # erreur disque ou réseau : affichée telle quelle
            QtWidgets.QMessageBox.critical(
                self, "Erreur de création", f"Impossible de créer le projet.\n\n{e}"
            )
            return
        self.projectCreated.emit(self.created_project)
        self.accept()

    def _choix_lignes_retirees(self, retires: list[Article]) -> str:
        """« supprimer », « conserver » ou « annuler » (R6)."""
        lignes = "\n".join(f"• {a.fournisseur} / {a.reference}" for a in retires)
        boite = QtWidgets.QMessageBox(self)
        boite.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        boite.setWindowTitle("Suppression de lignes")
        boite.setText(
            "Certaines lignes ont été supprimées du projet.\n\n"
            "Voulez-vous aussi supprimer les dossiers et les données associées ?"
        )
        boite.setInformativeText(
            f"Lignes concernées :\n{lignes}\n\n"
            "Si vous confirmez, les dossiers physiques des références seront supprimés "
            "dans les BDD CE / CECC / DPE, ainsi que les documents référencés en base de "
            "données.\n\nCette action est irréversible."
        )
        role = QtWidgets.QMessageBox.ButtonRole
        supprimer = boite.addButton("Supprimer dossiers et données", role.DestructiveRole)
        conserver = boite.addButton("Conserver les dossiers", role.AcceptRole)
        annuler = boite.addButton("Annuler l'enregistrement", role.RejectRole)
        boite.setDefaultButton(annuler)
        boite.exec()
        choix = {supprimer: "supprimer", conserver: "conserver"}
        return choix.get(boite.clickedButton(), "annuler")

    def _update_project(self):
        ok, message = self._validate()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Paramétrage projet", message)
            return
        saisie = self._saisie()
        retires = projets.articles_retires(self.projet, saisie.lignes)
        choix = self._choix_lignes_retirees(retires) if retires else "conserver"
        if choix == "annuler":
            return
        try:
            self.updated_project = projets.modifier_projet(
                self.projet, saisie, supprimer_les_retires=choix == "supprimer"
            )
        except Exception as e:  # erreur disque ou réseau : affichée telle quelle
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur de paramétrage",
                f"Impossible d'enregistrer le paramétrage du projet.\n\n{e}",
            )
            return
        self.projectUpdated.emit(self.updated_project)
        self.accept()
