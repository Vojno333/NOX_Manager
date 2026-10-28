"""Dialogue de dépôt d'un justificatif, ou de réglage de l'applicabilité seule (R7 à R13).

Interface reprise de `00_ancien/wikidocs_qt/upload_document_dialog.py`
(`CECCPage`, `UploadDocumentDialog`, `CECC_FIELD_HELP`) ; contrôles et
enregistrement par `services/depot.py`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from app.models.depot import SaisieDepot
from app.models.projet import Projet
from app.models.referentiel import LIVRABLES, PAYS_ORIGINE_4A
from app.services import depot
from app.services.applicabilite import codes_egaux
from app.ui.composants_depot import CEPage, DPEPage, DropZone, _field_col, _info_btn
from app.ui.geometrie import ajuster_et_centrer
from app.ui.theme import STYLE_DEPOT as STYLESHEET

CECC_FIELD_HELP = {
    "Fournisseur Doc / MANUFACTURER": (
        "Nom du fournisseur ou distributeur mentionné sur le document."
    ),
    "Manufacturer Part Number": "Manufacturer Part Number mentionné sur le document.",
    "Statut CECC": "Statuts possibles : A demander, Demandé, Relancé, Non conforme, Validé.",
    "CECC : Date": "Date du CECC.",
    "Nom : CECC": "Nom du CECC.",
    "CECC Classement": "Valeurs possibles : NC, DU, DI (Défense item).",
    "Catégorie (EAR99 / Code ECCN / Code ML ITAR)": (
        "NC\nDU Hors USA = Code ECCN\nDU USA = EAR99 ou ECCN Code\nDI = Code ML ITAR"
    ),
    "Licence Oui / Non": "Indiquer Oui ou Non selon le CECC.",
    "N° Licence": "Numéro de licence si applicable.",
    "Pays Origine 4a": "Pays d’origine mentionné au point 4a du CECC.",
    "EAR99 Value (USD)": "À renseigner si mentionné au point 11 du CECC.",
    "ECCN value (USD)": "À renseigner si mentionné au point 11 du CECC.",
    "Composant contrôlés à l'export et intégrés ds l'article (10.1)": (
        "Indiquer les composants contrôlés à l’export mentionnés au point 10.1 du CECC."
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# CECC Informations page
# ──────────────────────────────────────────────────────────────────────────────
class _NoWheelComboBox(QtWidgets.QComboBox):
    """Liste déroulante insensible à la molette tant qu'elle n'a pas été
    cliquée : survoler la liste en faisant défiler la page ne change plus la
    valeur choisie (la molette fait alors défiler la page)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # StrongFocus : le focus s'obtient au clic ou au clavier, pas à la molette.
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()  # remonte à la zone de défilement parente


class CECCPage(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)

        inner = QtWidgets.QWidget()
        inner.setStyleSheet("background:#ffffff;")
        inner_lay = QtWidgets.QVBoxLayout(inner)
        inner_lay.setContentsMargins(20, 16, 20, 20)
        inner_lay.setSpacing(14)

        # Section title
        title = QtWidgets.QLabel("Informations CECC", inner)
        title.setObjectName("sectionTitle")
        sub = QtWidgets.QLabel("Renseignez les informations du document CECC.", inner)
        sub.setObjectName("hintLabel")
        inner_lay.addWidget(title)
        inner_lay.addWidget(sub)

        # ── Grid 2-col ──
        self._edits: dict[str, QtWidgets.QWidget] = {}

        def _row(
            left_label,
            left_key,
            right_label,
            right_key,
            right_is_combo=False,
            combo_items=None,
            left_is_combo=False,
            left_combo_items=None,
        ):
            row_lay = QtWidgets.QHBoxLayout()
            row_lay.setSpacing(20)

            def make_field(label_text, key, is_combo=False, items=None):
                col = QtWidgets.QVBoxLayout()
                col.setSpacing(5)

                label_row = QtWidgets.QHBoxLayout()
                label_row.setSpacing(4)

                lbl = QtWidgets.QLabel(label_text)
                lbl.setObjectName("fieldLabelOpt")
                label_row.addWidget(lbl)

                ib = _info_btn(
                    tooltip=CECC_FIELD_HELP.get(label_text, "Information non disponible.")
                )
                label_row.addWidget(ib)

                label_row.addStretch(1)
                col.addLayout(label_row)

                if is_combo:
                    w = _NoWheelComboBox()
                    w.setEditable(False)
                    w.addItem("Sélectionner…")
                    if items:
                        w.addItems(items)
                    w.currentTextChanged.connect(lambda _text: self.changed.emit())
                else:
                    w = QtWidgets.QLineEdit()
                    w.textChanged.connect(lambda _text: self.changed.emit())

                self._edits[key] = w
                col.addWidget(w)
                return col

            row_lay.addLayout(make_field(left_label, left_key, left_is_combo, left_combo_items), 1)
            row_lay.addLayout(make_field(right_label, right_key, right_is_combo, combo_items), 1)

            inner_lay.addLayout(row_lay)

        def _row_full(label_text, key):
            row_lay = QtWidgets.QVBoxLayout()
            row_lay.setSpacing(5)

            label_row = QtWidgets.QHBoxLayout()
            label_row.setSpacing(4)

            lbl = QtWidgets.QLabel(label_text)
            lbl.setObjectName("fieldLabelOpt")
            label_row.addWidget(lbl)

            ib = _info_btn(tooltip=CECC_FIELD_HELP.get(label_text, "Information non disponible."))
            label_row.addWidget(ib)

            label_row.addStretch(1)
            row_lay.addLayout(label_row)

            w = QtWidgets.QLineEdit()
            w.textChanged.connect(lambda _text: self.changed.emit())

            self._edits[key] = w
            row_lay.addWidget(w)

            inner_lay.addLayout(row_lay)

        _row(
            "Fournisseur Doc / MANUFACTURER",
            "manufacturer_doc",
            "Licence Oui / Non",
            "licence_yn",
            right_is_combo=True,
            combo_items=["Oui", "Non"],
        )

        _row("Manufacturer Part Number", "manufacturer_part_number", "N° Licence", "licence_number")

        _row(
            "Statut CECC",
            "cecc_etat",
            "CECC : Date",
            "cecc_date",
            left_is_combo=True,
            left_combo_items=["A demander", "Demandé", "Relancé", "Non conforme", "Validé"],
        )

        _row(
            "Nom : CECC",
            "nom_cecc",
            "Pays Origine 4a",
            "pays_origine",
            right_is_combo=True,
            combo_items=list(PAYS_ORIGINE_4A),
        )

        _row(
            "CECC Classement",
            "cecc_classement",
            "EAR99 Value (USD)",
            "ear99_value",
            left_is_combo=True,
            left_combo_items=["NC", "DU", "DI (Défense item)"],
        )

        _row(
            "Catégorie (EAR99 / Code ECCN / Code ML ITAR)",
            "categorie",
            "ECCN value (USD)",
            "eccn_value",
        )

        _row_full(
            "Composant contrôlés à l'export et intégrés ds l'article (10.1)",
            "composant_export_10_1",
        )

        inner_lay.addStretch(1)
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)

        # ── Preview bar ──
        bottom = QtWidgets.QWidget(self)
        bottom.setStyleSheet("background:#ffffff; border-top: 1px solid #e5e7eb;")
        bot_lay = QtWidgets.QHBoxLayout(bottom)
        bot_lay.setContentsMargins(20, 8, 20, 10)
        self._preview_lbl = QtWidgets.QLabel("Nom final : —", bottom)
        self._preview_lbl.setObjectName("previewLabel")
        bot_lay.addWidget(self._preview_lbl)
        bot_lay.addStretch(1)
        lay.addWidget(bottom)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_preview(self, text: str):
        self._preview_lbl.setText(f"Nom final : {text}")

    def get_fields(self) -> dict[str, str]:
        result = {}
        for key, w in self._edits.items():
            if isinstance(w, QtWidgets.QComboBox):
                txt = w.currentText().strip()
                result[key] = "" if txt == "Sélectionner…" else txt
            else:
                result[key] = w.text().strip()
        return result

    def prefill(self, data: dict):
        for key, w in self._edits.items():
            val = data.get(key, "")
            if not val:
                continue
            if isinstance(w, QtWidgets.QComboBox):
                idx = w.findText(val)
                if idx >= 0:
                    w.setCurrentIndex(idx)
            else:
                w.setText(val)

    def set_nom_cecc(self, filename: str):
        w = self._edits.get("nom_cecc")
        if isinstance(w, QtWidgets.QLineEdit):
            w.setText(filename)


# ──────────────────────────────────────────────────────────────────────────────
# Main dialog
# ──────────────────────────────────────────────────────────────────────────────
class DialogueDepot(QtWidgets.QDialog):
    documentSaved = QtCore.Signal()

    def __init__(
        self,
        projet: Projet,
        livrable: str,
        cibles: list[tuple[str, str]],
        mode: str = "import",
        codes_coches: list[str] | None = None,
        parent=None,
    ):
        """*mode* : "import" (import de document, applicabilité modifiable)
        ou "applicability" (gestion de l'applicabilité seule, sans document).

        *codes_coches* : exigences pré-cochées (passées à «Applicable») à
        l'ouverture, ex. remplacement du justificatif d'une exigence."""
        super().__init__(parent)
        self.projet = projet
        self.project_dir = projet.dossier
        self.supplier, self.reference = cibles[0]
        self.preset_justification_type = livrable
        self.mode = mode if mode in ("import", "applicability") else "import"
        self.selected_file: Path | None = None
        self.cibles = list(cibles)
        self.debut = datetime.now().isoformat()

        self._setup_window()
        self._build_ui()
        self._init_type()
        self._prefill_existing_cecc_fields()
        self._prefill_existing_applicability()
        self._preset_checked(codes_coches or [])
        self._update_form_visibility()
        self._update_preview()
        # Calculé après la construction (polices et contenu réels) : le pied de
        # page et le champ « Nom final » restent toujours visibles ; la zone des
        # exigences absorbe le surplus de hauteur.
        self.layout().activate()
        needed = self.layout().minimumSize()
        ajuster_et_centrer(
            self,
            max(860, needed.width()),
            max(900, needed.height() + 260),
            largeur_min=needed.width(),
            hauteur_min=needed.height(),
        )

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        jtype = self.preset_justification_type or ""
        action = (
            "Gérer l'applicabilité" if self.mode == "applicability" else "Importer un justificatif"
        )
        if jtype:
            self.setWindowTitle(f"{action} {jtype}")
        else:
            self.setWindowTitle(action)
        self.setStyleSheet(STYLESHEET)

    def _preset_checked(self, codes: list[str]):
        if self.mode != "import" or not codes:
            return
        for page in (self._ce_page, self._dpe_page):
            for row in page._req_rows:
                if any(codes_egaux(row.code, c) for c in codes):
                    row.set_state(2)  # la case n'est active qu'en «Applicable»
                    row.set_row_checked(True)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        window_layout = QtWidgets.QVBoxLayout(self)
        window_layout.setContentsMargins(24, 16, 24, 16)
        window_layout.setSpacing(12)

        window_layout.addWidget(self._build_header())
        window_layout.addWidget(self._build_context_card())
        # Zone centrale : la liste des exigences occupe tout l'espace
        # vertical restant (elle gère son propre défilement interne).
        window_layout.addWidget(self._build_specifics_area(), 1)
        self._file_card = self._build_file_card()
        window_layout.addWidget(self._file_card)
        window_layout.addLayout(self._build_footer())

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget(self)
        w.setStyleSheet("background:transparent;")
        lay = QtWidgets.QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        icon = QtWidgets.QLabel("🛡", w)
        icon.setStyleSheet("font-size:20px;")

        text_col = QtWidgets.QVBoxLayout()
        text_col.setSpacing(2)

        jtype = self.preset_justification_type or ""
        action = (
            "Gérer l'applicabilité" if self.mode == "applicability" else "Importer un justificatif"
        )
        title_txt = f"{action} {jtype}".strip()
        title = QtWidgets.QLabel(title_txt, w)
        title.setObjectName("dialogTitle")

        if self.mode == "applicability":
            sub_txt = "Indiquez l'applicabilité de chaque exigence, sans fournir de document."
        else:
            subtitles = {
                "CE": "Importez un document et cochez les exigences CE qu'il couvre.",
                "CECC": "Importez un document CECC pour la référence sélectionnée.",
                "DPE": "Importez un document et cochez les exigences qu'il couvre.",
            }
            sub_txt = subtitles.get(jtype, "Importez un justificatif pour ce projet.")
        sub = QtWidgets.QLabel(sub_txt, w)
        sub.setObjectName("dialogSubtitle")

        text_col.addWidget(title)
        text_col.addWidget(sub)

        lay.addWidget(icon)
        lay.addLayout(text_col)
        lay.addStretch(1)

        return w

    # ── Context card ──────────────────────────────────────────────────────────

    def _build_context_card(self) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame(self)
        card.setObjectName("sectionCard")
        outer = QtWidgets.QVBoxLayout(card)
        outer.setContentsMargins(20, 14, 20, 16)
        outer.setSpacing(10)

        title = QtWidgets.QLabel("Contexte", card)
        title.setObjectName("sectionTitle")
        outer.addWidget(title)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(16)

        # Fournisseur
        sup_col = _field_col("Fournisseur", required=True)
        self._supplier_combo = QtWidgets.QComboBox(card)
        self._supplier_combo.addItem(self.supplier or "Sélectionner…")
        sup_col.addWidget(self._supplier_combo)
        row.addLayout(sup_col, 2)

        # Référence
        ref_col = _field_col("Référence", required=True)
        self._ref_edit = QtWidgets.QLineEdit(card)
        self._ref_edit.setText(self.reference or "")
        ref_col.addWidget(self._ref_edit)
        row.addLayout(ref_col, 1)

        outer.addLayout(row)
        return card

    # ── File info card ────────────────────────────────────────────────────────

    def _build_file_card(self) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame(self)
        card.setObjectName("sectionCard")
        outer = QtWidgets.QVBoxLayout(card)
        outer.setContentsMargins(20, 14, 20, 16)
        outer.setSpacing(10)

        title = QtWidgets.QLabel(
            "Applicabilité uniquement (aucun document)"
            if self.mode == "applicability"
            else "Informations du justificatif",
            card,
        )
        title.setObjectName("sectionTitle")
        outer.addWidget(title)

        cols = QtWidgets.QHBoxLayout()
        cols.setSpacing(20)

        # Left: drop zone (masqué en mode Applicabilité)
        self._file_left_container = QtWidgets.QWidget(card)
        left_col = QtWidgets.QVBoxLayout(self._file_left_container)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)
        file_lbl_row = QtWidgets.QHBoxLayout()
        file_lbl_row.setSpacing(3)
        fl = QtWidgets.QLabel("Fichier", card)
        fl.setObjectName("fieldLabel")
        fr = QtWidgets.QLabel(" *", card)
        fr.setObjectName("required")
        file_lbl_row.addWidget(fl)
        file_lbl_row.addWidget(fr)
        file_lbl_row.addStretch(1)
        left_col.addLayout(file_lbl_row)

        self._drop_zone = DropZone(card)
        self._drop_zone.fileDropped.connect(self._apply_file)
        self._drop_zone.browse_btn.clicked.connect(self._choose_file)
        left_col.addWidget(self._drop_zone)

        fmt_lbl = QtWidgets.QLabel("Formats acceptés : PDF, DOCX, XLSX (max. 50 Mo)", card)
        fmt_lbl.setObjectName("formatHint")
        left_col.addWidget(fmt_lbl)

        cols.addWidget(self._file_left_container, 2)

        # Right: type + nom final
        right_col = QtWidgets.QVBoxLayout()
        right_col.setSpacing(12)

        type_col = _field_col("Type de justificatif", required=True)
        self.type_combo = QtWidgets.QComboBox(card)
        type_choices = (
            [t for t in LIVRABLES if t != "CECC"]
            if self.mode == "applicability"
            else list(LIVRABLES)
        )
        self.type_combo.addItems(type_choices)
        self.type_combo.currentTextChanged.connect(lambda _text: self._on_type_changed())
        type_col.addWidget(self.type_combo)
        right_col.addLayout(type_col)

        self._name_field_container = QtWidgets.QWidget(card)
        name_col = QtWidgets.QVBoxLayout(self._name_field_container)
        name_col.setContentsMargins(0, 0, 0, 0)
        name_col.setSpacing(5)
        name_lbl_row = QtWidgets.QHBoxLayout()
        name_lbl_row.setSpacing(3)
        nl = QtWidgets.QLabel("Nom final", card)
        nl.setObjectName("fieldLabelOpt")
        no = QtWidgets.QLabel(" (optionnel)", card)
        no.setObjectName("hintLabel")
        name_lbl_row.addWidget(nl)
        name_lbl_row.addWidget(no)
        name_lbl_row.addStretch(1)
        name_col.addLayout(name_lbl_row)

        self._final_name_edit = QtWidgets.QLineEdit(card)
        jtype = self.preset_justification_type or "CE"
        self._final_name_edit.setPlaceholderText(
            f"Auto : {jtype}_{self.supplier or 'Fournisseur'}_{self.reference or 'Reference'}"
        )
        name_col.addWidget(self._final_name_edit)
        right_col.addWidget(self._name_field_container)
        right_col.addStretch(1)

        cols.addLayout(right_col, 1)
        outer.addLayout(cols)

        if self.mode == "applicability":
            self._file_left_container.setVisible(False)
            self._name_field_container.setVisible(False)

        return card

    # ── Specifics area (stacked: CE / CECC / DPE) ────────────────────────────

    def _build_specifics_area(self) -> QtWidgets.QFrame:
        self._spec_card = QtWidgets.QFrame(self)
        self._spec_card.setObjectName("sectionCard")
        # Plancher volontairement modeste : la zone des exigences est déjà
        # prioritaire (stretch=1 dans la mise en page) et devient la zone
        # dominante dès qu'il y a de la place. Ce plancher ne sert qu'à
        # garantir l'en-tête + quelques lignes visibles ; il ne doit jamais
        # pousser le pied de page (boutons) ou la carte fichier hors champ
        # sur un écran plus petit — c'est elle qui doit rétrécir (avec son
        # propre défilement interne), jamais l'inverse.
        self._spec_card.setMinimumHeight(160)
        spec_lay = QtWidgets.QVBoxLayout(self._spec_card)
        spec_lay.setContentsMargins(0, 0, 0, 0)
        spec_lay.setSpacing(0)

        self._stack = QtWidgets.QStackedWidget(self._spec_card)

        self._ce_page = CEPage(self._stack)
        self._dpe_page = DPEPage(self._stack)
        self._cecc_page = CECCPage(self._stack)

        self._ce_page.changed.connect(self._update_preview)
        self._dpe_page.changed.connect(self._update_preview)
        self._cecc_page.changed.connect(self._update_preview)

        self._stack.addWidget(self._ce_page)  # index 0
        self._stack.addWidget(self._cecc_page)  # index 1
        self._stack.addWidget(self._dpe_page)  # index 2

        checkboxes_visible = self.mode == "import"
        self._ce_page.set_checkboxes_visible(checkboxes_visible)
        self._dpe_page.set_checkboxes_visible(checkboxes_visible)

        spec_lay.addWidget(self._stack)
        return self._spec_card

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self) -> QtWidgets.QHBoxLayout:
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(12)
        lay.addStretch(1)

        self.cancel_button = QtWidgets.QPushButton("Annuler", self)
        self.cancel_button.setObjectName("outlineButton")
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QtWidgets.QPushButton("  💾  Enregistrer", self)
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._save_document)

        lay.addWidget(self.cancel_button)
        lay.addWidget(self.save_button)
        return lay

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_type(self):
        if self.preset_justification_type:
            idx = self.type_combo.findText(self.preset_justification_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_type_changed(self):
        self._update_form_visibility()
        self._update_preview()

    def _update_form_visibility(self):
        t = self._current_type()
        if t == "CE":
            self._stack.setCurrentIndex(0)
        elif t == "CECC":
            self._stack.setCurrentIndex(1)
        elif t == "DPE":
            self._stack.setCurrentIndex(2)

    def _apply_file(self, path: Path):
        self.selected_file = path
        # Update the text widgets inside the drop zone
        for child in self._drop_zone.findChildren(QtWidgets.QLabel):
            if "Glissez" in child.text():
                child.setText(path.name)
                child.setStyleSheet("font-size:12px; color:#2563eb; background:transparent;")
        # Autofill CECC nom
        self._cecc_page.set_nom_cecc(path.name)
        self._update_preview()

    def _current_type(self) -> str:
        return self.type_combo.currentText().strip().upper()

    def _update_preview(self):
        name = self._build_final_filename()

        current = self._current_type()

        if current == "CE":
            count = self._ce_page.applicable_count()
            self._ce_page.set_preview(f"{name} — {count} exigence(s) applicable(s)")

        elif current == "DPE":
            count = self._dpe_page.applicable_count()
            self._dpe_page._counter_lbl.setText(
                f"Nom final : {name} — {count} exigence(s) applicable(s)"
            )

        else:
            self._cecc_page.set_preview(name)

    # ── Pré-remplissage ───────────────────────────────────────────────────────

    def _prefill_existing_cecc_fields(self):
        """La fiche CECC reprend la dernière fiche de l'article (R12)."""
        try:
            fiche = depot.fiche_cecc_existante(self.project_dir, self.supplier, self.reference)
        except Exception:  # base illisible : fiche laissée vide, comme l'ancienne application
            return
        if fiche:
            self._cecc_page.prefill(fiche)

    def _prefill_existing_applicability(self):
        """Recharge l'état déjà enregistré de chaque exigence ; une exigence
        jamais renseignée reste « Non défini »."""
        for livrable, page in (("CE", self._ce_page), ("DPE", self._dpe_page)):
            codes = [row.code for row in page._req_rows]
            try:
                etats = depot.etats_existants(
                    self.project_dir, self.supplier, self.reference, livrable, codes
                )
            except Exception:  # base illisible : exigences laissées « Non défini »
                return
            if etats is None:
                continue
            for row in page._req_rows:
                row.set_state(etats[row.code])

    # ── Fichier ───────────────────────────────────────────────────────────────

    def _choose_file(self):
        chemin, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Choisir un justificatif",
            str(Path.home()),
            "Documents (*.pdf *.docx *.xlsx *.PDF *.DOCX *.XLSX)",
        )
        if chemin:
            self._apply_file(Path(chemin))

    def _build_final_filename(self, supplier: str | None = None, reference: str | None = None):
        return depot.nom_final(
            self._saisie(),
            self.supplier if supplier is None else supplier,
            self.reference if reference is None else reference,
        )

    # ── Saisie ────────────────────────────────────────────────────────────────

    def _page_courante(self):
        return {"CE": self._ce_page, "DPE": self._dpe_page}.get(self._current_type())

    def _saisie(self) -> SaisieDepot:
        page = self._page_courante()
        rows = page._req_rows if page else []
        return SaisieDepot(
            dossier=self.project_dir,
            livrable=self._current_type(),
            cibles=self.cibles,
            mode=self.mode,
            fichier=self.selected_file,
            nom_saisi=self._final_name_edit.text(),
            etats={row.code: row.get_state() for row in rows},
            coches={row.code for row in rows if row.is_row_checked()},
            champs_cecc=self._cecc_page.get_fields() if self._current_type() == "CECC" else {},
        )

    # ── Enregistrement ────────────────────────────────────────────────────────

    def _save_document(self):
        saisie = self._saisie()
        refus = depot.verifier(saisie, self.projet.livrables)
        if refus:
            titre = "Applicabilité" if self.mode == "applicability" else "Import"
            QtWidgets.QMessageBox.warning(self, titre, refus)
            return
        try:
            nombre = depot.enregistrer(saisie)
        except Exception as e:  # erreur disque ou réseau : affichée telle quelle
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur d'enregistrement",
                f"Impossible d'enregistrer les modifications.\n\n{e}",
            )
            return
        self.documentSaved.emit()
        QtWidgets.QMessageBox.information(self, *depot.message_de_fin(saisie, nombre))
        self.accept()
