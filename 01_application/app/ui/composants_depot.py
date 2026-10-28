"""Composants du dialogue de dépôt : bascule à trois états, zone de dépôt,
pages d'exigences CE et DPE (RoHS synchronisée, compteurs, aperçu du nom).

Repris de `00_ancien/wikidocs_qt/upload_document_dialog.py` (`ThreeStateToggle`,
`RequirementRow`, `DropZone`, `CEPage`, `DPEPage`, `_link_rohs_rows`).
"""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from app.models.referentiel import EXIGENCES_CE, EXIGENCES_DPE
from app.services.applicabilite import est_rohs


# ──────────────────────────────────────────────────────────────────────────────
# ThreeStateToggle  –  N/A (0)  |  Non défini (1)  |  Applicable (2)
# ──────────────────────────────────────────────────────────────────────────────
class ThreeStateToggle(QtWidgets.QWidget):
    """
    Un interrupteur à trois positions affichées côte à côte.

    États :
        0 → N/A          (rouge   #ef4444)
        1 → Non défini   (gris    #9ca3af)
        2 → Applicable   (bleu    #2563eb)
    """

    stateChanged = QtCore.Signal(int)

    # Libellés et couleurs de chaque état
    _STATES = [
        ("N/A", "#ef4444", "#ffffff"),  # label, bg_active, text_active
        ("Non défini", "#9ca3af", "#ffffff"),
        ("Applicable", "#2563eb", "#ffffff"),
    ]

    _H = 28  # hauteur du widget
    _BTN_W = 76  # largeur d'un bouton
    _RADIUS = 7  # arrondi

    def __init__(self, state: int = 1, parent=None):
        """*state* : 0=N/A, 1=Non défini, 2=Applicable."""
        super().__init__(parent)
        self._state = max(0, min(2, state))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        total_w = self._BTN_W * 3 + 4  # +4 pour les marges internes
        self.setFixedSize(total_w, self._H)

        # Animation de la position du curseur (valeur flottante 0..2)
        self._anim_state = float(self._state)
        self._anim = QtCore.QPropertyAnimation(self, b"_anim_val", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

    # ── Propriété animée ──────────────────────────────────────────────────────

    def _get_anim_val(self) -> float:
        return self._anim_state

    def _set_anim_val(self, v: float):
        self._anim_state = v
        self.update()

    _anim_val = QtCore.Property(float, _get_anim_val, _set_anim_val)

    # ── API publique ──────────────────────────────────────────────────────────

    def get_state(self) -> int:
        return self._state

    def set_state(self, state: int, animated: bool = True):
        state = max(0, min(2, state))
        if state == self._state and not animated:
            return
        old = self._state
        self._state = state
        if animated:
            self._anim.stop()
            self._anim.setStartValue(self._anim_state)
            self._anim.setEndValue(float(state))
            self._anim.start()
        else:
            self._anim_state = float(state)
            self.update()
        if old != state:
            self.stateChanged.emit(state)

    def is_applicable(self) -> bool:
        return self._state == 2

    def is_not_applicable(self) -> bool:
        return self._state == 0

    def is_undefined(self) -> bool:
        return self._state == 1

    # ── Interactions ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            idx = self._index_at(event.position().x() if hasattr(event, "position") else event.x())
            if idx is not None:
                self.set_state(idx)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_Plus):
            self.set_state(min(2, self._state + 1))
        elif event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Minus):
            self.set_state(max(0, self._state - 1))
        else:
            super().keyPressEvent(event)

    def _index_at(self, x: float) -> int | None:
        for i in range(3):
            bx = i * self._BTN_W
            if bx <= x < bx + self._BTN_W:
                return i
        return None

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        W, H = self.width(), self._H
        r = self._RADIUS

        # Fond général (piste)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor("#f3f4f6"))
        p.drawRoundedRect(0, 0, W, H, r, r)

        # Curseur glissant (interpolé)
        cursor_x = self._anim_state * self._BTN_W
        cursor_color = QtGui.QColor(self._STATES[self._state][1])  # couleur cible nette

        p.setBrush(cursor_color)
        p.drawRoundedRect(QtCore.QRectF(cursor_x + 1, 1, self._BTN_W - 2, H - 2), r - 1, r - 1)

        # Labels
        font = self.font()
        font.setPointSize(8)
        font.setBold(False)
        p.setFont(font)

        for i, (label, _bg, fg) in enumerate(self._STATES):
            bx = i * self._BTN_W
            rect = QtCore.QRectF(bx, 0, self._BTN_W, H)

            if i == self._state:
                p.setPen(QtGui.QColor(fg))
            else:
                p.setPen(QtGui.QColor("#6b7280"))

            p.drawText(rect, QtCore.Qt.AlignCenter, label)

        p.end()

    def sizeHint(self):
        return QtCore.QSize(self._BTN_W * 3, self._H)


# ──────────────────────────────────────────────────────────────────────────────
# Requirement row widget (shared by CE and DPE pages)
# ──────────────────────────────────────────────────────────────────────────────
class RequirementRow(QtWidgets.QFrame):
    toggled = QtCore.Signal()

    # état par défaut : 1 = Non défini
    _DEFAULT_STATE = 1

    def __init__(self, code: str, description: str, default_on: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("reqRow")
        self.setFixedHeight(52)
        self._code = code

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(12)

        # Row checkbox (left) — coche « ce document couvre cette exigence »
        # (utilisé uniquement en mode Import, sans effet sur l'applicabilité)
        self._check = QtWidgets.QCheckBox(self)
        self._check.setObjectName("rowCheck")
        self._check.setToolTip("Ce document couvre cette exigence")
        self._check.setEnabled(False)
        self._check.stateChanged.connect(lambda: self.toggled.emit())

        # Name
        name_lbl = QtWidgets.QLabel(code, self)
        name_lbl.setObjectName("reqName")
        name_lbl.setMinimumWidth(180)

        # Description
        desc_lbl = QtWidgets.QLabel(description, self)
        desc_lbl.setObjectName("reqDesc")

        # Interrupteur 3 états  (N/A=0 | Non défini=1 | Applicable=2)
        # Par défaut : "Non défini" (1) — l'utilisateur doit choisir
        self._toggle = ThreeStateToggle(state=self._DEFAULT_STATE, parent=self)
        self._toggle.setToolTip(
            "N/A : non applicable à cette référence\n"
            "Non défini : à renseigner\n"
            "Applicable : couvert par ce justificatif"
        )
        self._toggle.stateChanged.connect(self._on_toggle_state_changed)

        lay.addWidget(self._check)
        lay.addWidget(name_lbl)
        lay.addWidget(desc_lbl, 1)
        lay.addWidget(self._toggle)

    @property
    def code(self) -> str:
        return self._code

    # ── Compatibilité avec le reste du code ──────────────────────────────────

    def is_applicable(self) -> bool:
        """Vrai uniquement si l'état est explicitement «Applicable»."""
        return self._toggle.is_applicable()

    def is_not_applicable(self) -> bool:
        """Vrai si l'état est «N/A»."""
        return self._toggle.is_not_applicable()

    def is_undefined(self) -> bool:
        """Vrai si l'état est «Non défini»."""
        return self._toggle.is_undefined()

    def get_state(self) -> int:
        """0=N/A, 1=Non défini, 2=Applicable."""
        return self._toggle.get_state()

    def set_state(self, state: int):
        self._toggle.set_state(state, animated=False)

    # Rétro-compatibilité avec les appels set_applicable(bool)
    def set_applicable(self, v: bool):
        """True → Applicable (2), False → N/A (0)."""
        self._toggle.set_state(2 if v else 0, animated=False)

    def is_row_checked(self) -> bool:
        return self._check.isChecked()

    def set_row_checked(self, v: bool):
        self._check.setChecked(v)

    def set_checkbox_visible(self, visible: bool):
        self._check.setVisible(visible)

    def _on_toggle_state_changed(self, state: int):
        """Synchronise la case « document couvre cette exigence » avec l'applicabilité.

        La case n'a de sens que pour une exigence Applicable : elle est
        désactivée et décochée sinon. Elle n'est PAS cochée automatiquement :
        c'est cette case (et elle seule) qui détermine si un document est
        exigé au moment de l'enregistrement.
        """
        if state == 2:  # Applicable
            self._check.setEnabled(True)
        else:
            self._check.blockSignals(True)
            self._check.setChecked(False)
            self._check.blockSignals(False)
            self._check.setEnabled(False)
        self.toggled.emit()

    def matches(self, text: str) -> bool:
        return text.lower() in self._code.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Drop zone widget
# ──────────────────────────────────────────────────────────────────────────────
class DropZone(QtWidgets.QFrame):
    fileDropped = QtCore.Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(78)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setAlignment(QtCore.Qt.AlignCenter)
        lay.setSpacing(2)

        icon = QtWidgets.QLabel("☁", self)
        icon.setAlignment(QtCore.Qt.AlignCenter)
        icon.setStyleSheet("font-size: 20px; color: #2563eb; background: transparent;")

        text = QtWidgets.QLabel("Glissez-déposez votre fichier ici", self)
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setStyleSheet("font-size: 13px; color: #374151; background: transparent;")

        self.browse_btn = QtWidgets.QPushButton("Parcourir…", self)
        self.browse_btn.setObjectName("browseButton")
        self.browse_btn.setFixedWidth(110)

        lay.addWidget(icon)
        lay.addWidget(text)
        lay.addWidget(self.browse_btn, 0, QtCore.Qt.AlignCenter)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.fileDropped.emit(Path(urls[0].toLocalFile()))


# ──────────────────────────────────────────────────────────────────────────────
# Helper – labelled field column
# ──────────────────────────────────────────────────────────────────────────────
def _field_col(
    label_text: str, required: bool = False, optional: bool = False
) -> QtWidgets.QVBoxLayout:
    col = QtWidgets.QVBoxLayout()
    col.setSpacing(5)
    lbl_row = QtWidgets.QHBoxLayout()
    lbl_row.setSpacing(3)
    obj = "fieldLabel" if required else "fieldLabelOpt"
    lbl = QtWidgets.QLabel(label_text)
    lbl.setObjectName(obj)
    lbl_row.addWidget(lbl)
    if required:
        req = QtWidgets.QLabel(" *")
        req.setObjectName("required")
        lbl_row.addWidget(req)
    if optional:
        opt = QtWidgets.QLabel(" (optionnel)")
        opt.setObjectName("hintLabel")
        lbl_row.addWidget(opt)
    lbl_row.addStretch(1)
    col.addLayout(lbl_row)
    return col


def _info_btn(parent=None, tooltip: str = "Information") -> QtWidgets.QPushButton:
    btn = QtWidgets.QPushButton("ⓘ", parent)
    btn.setObjectName("infoButton")
    btn.setToolTip(tooltip)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    return btn


# ──────────────────────────────────────────────────────────────────────────────
# CE Requirements page
# ──────────────────────────────────────────────────────────────────────────────
class CEPage(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        # ── Table header ──
        tbl_hdr = QtWidgets.QFrame(self)
        tbl_hdr.setObjectName("reqTableHeader")
        tbl_hdr.setFixedHeight(36)
        th_lay = QtWidgets.QHBoxLayout(tbl_hdr)
        th_lay.setContentsMargins(16, 0, 16, 0)
        th_lay.setSpacing(12)
        _exig = QtWidgets.QLabel("Exigence", tbl_hdr)
        _exig.setObjectName("reqHeaderLabel")
        _appl_row = QtWidgets.QHBoxLayout()
        _appl_row.setSpacing(4)
        _appl = QtWidgets.QLabel("Applicabilité", tbl_hdr)
        _appl.setObjectName("reqHeaderLabel")

        _appl_row.addWidget(_appl)
        th_lay.addWidget(_exig, 1)
        th_lay.addLayout(_appl_row)
        lay.addWidget(tbl_hdr)

        # ── Scrollable rows ──
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setObjectName("")
        rows_w = QtWidgets.QWidget()
        rows_w.setStyleSheet("background:#ffffff;")
        self._rows_lay = QtWidgets.QVBoxLayout(rows_w)
        self._rows_lay.setContentsMargins(0, 0, 0, 0)
        self._rows_lay.setSpacing(0)

        self._req_rows: list[RequirementRow] = []
        for code, desc in EXIGENCES_CE:
            row = RequirementRow(code, desc, default_on=True, parent=rows_w)
            row.toggled.connect(self.changed.emit)
            self._req_rows.append(row)
            self._rows_lay.addWidget(row)
        self._link_rohs_rows()

        self._rows_lay.addStretch(1)
        scroll.setWidget(rows_w)
        lay.addWidget(scroll, 1)

        # ── Aperçu du nom final ──
        bottom = QtWidgets.QWidget(self)
        bottom.setStyleSheet("background:#ffffff; border-top: 1px solid #e5e7eb;")
        bot_lay = QtWidgets.QHBoxLayout(bottom)
        bot_lay.setContentsMargins(20, 8, 20, 8)
        bot_lay.setSpacing(8)

        self._preview_lbl = QtWidgets.QLabel("Nom final : —", bottom)
        self._preview_lbl.setObjectName("previewLabel")
        self._preview_lbl.setStyleSheet("font-size:11px; color:#6b7280; padding:0;")
        bot_lay.addWidget(self._preview_lbl)
        lay.addWidget(bottom)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_not_applicable_codes(self, codes: list[str]):
        codes_set = set(codes or [])
        for row in self._req_rows:
            if row.code in codes_set:
                row.set_state(0)  # N/A
            else:
                row.set_state(2)  # Applicable

    def not_applicable_requirements(self) -> tuple[list[str], list[str]]:
        codes, labels = [], []
        for row in self._req_rows:
            if row.is_not_applicable():
                codes.append(row.code)
                labels.append(row.code)
        return codes, labels

    def applicable_count(self) -> int:
        return sum(1 for r in self._req_rows if r.is_applicable())

    def set_preview(self, text: str):
        self._preview_lbl.setText(f"Nom final : {text}")

    def selected_requirements(self) -> tuple[list[str], list[str]]:
        codes, labels = [], []
        for row in self._req_rows:
            if row.is_applicable():
                codes.append(row.code)
                labels.append(row.code)
        return codes, labels

    def checked_applicable_requirements(self) -> tuple[list[str], list[str]]:
        """Exigences Applicable ET cochées (couvertes par le document importé)."""
        codes, labels = [], []
        for row in self._req_rows:
            if row.is_applicable() and row.is_row_checked():
                codes.append(row.code)
                labels.append(row.code)
        return codes, labels

    def set_checkboxes_visible(self, visible: bool):
        for row in self._req_rows:
            row.set_checkbox_visible(visible)

    # ── Private ───────────────────────────────────────────────────────────────

    def _filter(self, text: str):
        for row in self._req_rows:
            row.setVisible(row.matches(text) if text else True)

    def _select_all(self):
        """Passe toutes les exigences visibles à «Applicable» (état 2)."""
        for row in self._req_rows:
            if row.isVisible():
                row.set_state(2)

    def _deselect_all(self):
        """Passe toutes les exigences visibles à «N/A» (état 0)."""
        for row in self._req_rows:
            if row.isVisible():
                row.set_state(0)

    def unknown_applicability_requirements(self) -> list[str]:
        return [row.code for row in self._req_rows if row.is_undefined()]

    def _link_rohs_rows(self):
        """2011/65/UE et 2015/863 forment une seule exigence RoHS : l'état
        d'applicabilité et la case « couvert » de l'une sont recopiés sur l'autre."""
        linked = [r for r in self._req_rows if est_rohs(r.code)]
        for row in linked:
            others = [r for r in linked if r is not row]
            # set_state / setChecked n'émettent rien si la valeur est déjà
            # la bonne : pas de boucle infinie entre les lignes liées.
            row._toggle.stateChanged.connect(
                lambda state, o=others: [r.set_state(state) for r in o]
            )
            row._check.stateChanged.connect(
                lambda _s, src=row, o=others: [r.set_row_checked(src.is_row_checked()) for r in o]
            )


# ──────────────────────────────────────────────────────────────────────────────
# DPE Requirements page
# ──────────────────────────────────────────────────────────────────────────────
class DPEPage(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Table header ──
        tbl_hdr = QtWidgets.QFrame(self)
        tbl_hdr.setObjectName("reqTableHeader")
        tbl_hdr.setFixedHeight(36)
        th_lay = QtWidgets.QHBoxLayout(tbl_hdr)
        th_lay.setContentsMargins(16, 0, 16, 0)
        th_lay.setSpacing(12)
        _exig = QtWidgets.QLabel("Exigence", tbl_hdr)
        _exig.setObjectName("reqHeaderLabel")
        _appl_row = QtWidgets.QHBoxLayout()
        _appl_row.setSpacing(4)
        _appl = QtWidgets.QLabel("Applicable", tbl_hdr)
        _appl.setObjectName("reqHeaderLabel")
        _appl_row.addWidget(_appl)
        th_lay.addWidget(_exig, 1)
        th_lay.addLayout(_appl_row)
        lay.addWidget(tbl_hdr)

        # ── Scrollable rows ──
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        rows_w = QtWidgets.QWidget()
        rows_w.setStyleSheet("background:#ffffff;")
        self._rows_lay = QtWidgets.QVBoxLayout(rows_w)
        self._rows_lay.setContentsMargins(0, 0, 0, 0)
        self._rows_lay.setSpacing(0)

        self._req_rows: list[RequirementRow] = []

        # Defaults from mockup: first 3 + last one = ON, rest = OFF
        # Par défaut : toutes les exigences DPE sont applicables
        for code, desc in EXIGENCES_DPE:
            full = f"{code} — {desc}" if "—" not in code else code
            row = RequirementRow(full, desc, default_on=True, parent=rows_w)
            row.toggled.connect(self._on_toggle)
            self._req_rows.append(row)
            self._rows_lay.addWidget(row)

        self._rows_lay.addStretch(1)
        scroll.setWidget(rows_w)
        lay.addWidget(scroll, 1)

        # ── Counter ──
        bottom = QtWidgets.QWidget(self)
        bottom.setStyleSheet("background:#ffffff; border-top: 1px solid #e5e7eb;")
        bot_lay = QtWidgets.QHBoxLayout(bottom)
        bot_lay.setContentsMargins(20, 8, 20, 10)
        self._counter_lbl = QtWidgets.QLabel("", bottom)
        self._counter_lbl.setObjectName("reqCountLabel")
        bot_lay.addWidget(self._counter_lbl)
        bot_lay.addStretch(1)
        lay.addWidget(bottom)

        self._refresh_counter()

    # ── Public ────────────────────────────────────────────────────────────────

    def set_not_applicable_codes(self, codes: list[str]):
        codes_set = set(codes or [])
        for row in self._req_rows:
            if row.code in codes_set:
                row.set_state(0)  # N/A
            else:
                row.set_state(2)  # Applicable
        self._refresh_counter()

    def not_applicable_requirements(self) -> tuple[list[str], list[str]]:
        codes, labels = [], []
        for row in self._req_rows:
            if row.is_not_applicable():
                codes.append(row.code)
                labels.append(row.code)
        return codes, labels

    def applicable_count(self) -> int:
        return sum(1 for r in self._req_rows if r.is_applicable())

    def selected_requirements(self) -> tuple[list[str], list[str]]:
        codes, labels = [], []
        for row in self._req_rows:
            if row.is_applicable():
                codes.append(row.code)
                labels.append(row.code)
        return codes, labels

    def checked_applicable_requirements(self) -> tuple[list[str], list[str]]:
        """Exigences Applicable ET cochées (couvertes par le document importé)."""
        codes, labels = [], []
        for row in self._req_rows:
            if row.is_applicable() and row.is_row_checked():
                codes.append(row.code)
                labels.append(row.code)
        return codes, labels

    def set_checkboxes_visible(self, visible: bool):
        for row in self._req_rows:
            row.set_checkbox_visible(visible)

    # ── Private ───────────────────────────────────────────────────────────────

    def _on_toggle(self):
        self._refresh_counter()
        self.changed.emit()

    def _refresh_counter(self):
        applicable = sum(1 for r in self._req_rows if r.is_applicable())
        na = sum(1 for r in self._req_rows if r.is_not_applicable())
        undefined = sum(1 for r in self._req_rows if r.is_undefined())
        total = len(self._req_rows)
        self._counter_lbl.setText(
            f"{applicable} applicable(s) · {na} N/A · {undefined} non défini(s)"
            f"  —  {total} exigences"
        )

    def _filter(self, text: str):
        for row in self._req_rows:
            row.setVisible(row.matches(text) if text else True)

    def _select_all(self):
        """Passe toutes les exigences visibles à «Applicable» (état 2)."""
        for row in self._req_rows:
            if row.isVisible():
                row.set_state(2)

    def _deselect_all(self):
        """Passe toutes les exigences visibles à «N/A» (état 0)."""
        for row in self._req_rows:
            if row.isVisible():
                row.set_state(0)

    def unknown_applicability_requirements(self) -> list[str]:
        return [row.code for row in self._req_rows if row.is_undefined()]
