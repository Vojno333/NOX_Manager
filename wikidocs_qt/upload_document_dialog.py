from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .document_rules import (
    JUSTIFICATION_TYPES,
    DPE_REQUIREMENTS,
    CE_REQUIREMENTS,
    CECC_FREE_FIELDS,
    CECC_STATUSES,
    is_rohs_code,
    requirement_state,
)
from .project_manager import get_project_file_path
from .metadata_db import insert_uploaded_document, get_latest_cecc_fields, get_uploaded_documents
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

/* ── Cards ── */
QFrame#sectionCard {
    background: #ffffff;
    border: 1px solid #e2e5ea;
    border-radius: 10px;
}

/* ── Labels ── */
QLabel#dialogTitle {
    font-size: 17px;
    font-weight: 700;
    color: #1a1d23;
}
QLabel#dialogSubtitle {
    font-size: 12px;
    color: #6b7280;
}
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #1a1d23;
}
QLabel#fieldLabel {
    font-size: 12px;
    color: #374151;
    font-weight: 500;
}
QLabel#fieldLabelOpt {
    font-size: 12px;
    color: #374151;
    font-weight: 400;
}
QLabel#required {
    font-size: 12px;
    color: #dc2626;
}
QLabel#hintLabel {
    font-size: 11px;
    color: #6b7280;
}
QLabel#formatHint {
    font-size: 11px;
    color: #2563eb;
}
QLabel#infoIcon {
    font-size: 13px;
    color: #9ca3af;
}
QLabel#previewLabel {
    font-size: 12px;
    color: #374151;
    padding: 4px 0;
}
QLabel#reqCountLabel {
    font-size: 12px;
    color: #374151;
    padding: 6px 0;
}

/* ── Line edits / ComboBox ── */
QLineEdit {
    background: #ffffff;
    border: 1.5px solid #d1d5db;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 13px;
    color: #1a1d23;
    min-height: 34px;
}
QLineEdit:focus { border-color: #2563eb; }
QLineEdit:disabled { background: #f9fafb; color: #9ca3af; }
QLineEdit[readOnly="true"] { background: #f9fafb; }

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
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { width: 12px; height: 12px; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    selection-background-color: #eff6ff;
    selection-color: #1a1d23;
    outline: none;
    padding: 4px;
}

/* ── Drop zone ── */
QFrame#dropZone {
    background: #f8faff;
    border: 2px dashed #bfdbfe;
    border-radius: 10px;
}
QFrame#dropZone:hover { background: #eff6ff; border-color: #2563eb; }

/* ── Search box ── */
QLineEdit#searchBox {
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    padding: 6px 10px 6px 32px;
    min-height: 32px;
}
QLineEdit#searchBox:focus { border-color: #2563eb; background: #ffffff; }

/* ── Requirements table ── */
QFrame#reqTableHeader {
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    border-left: none;
    border-right: none;
}
QLabel#reqHeaderLabel {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
}
QFrame#reqRow {
    background: #ffffff;
    border-bottom: 1px solid #f3f4f6;
    border-left: none;
    border-right: none;
    border-top: none;
}
QLabel#reqName {
    font-size: 13px;
    font-weight: 500;
    color: #1a1d23;
}
QLabel#reqDesc {
    font-size: 12px;
    color: #9ca3af;
}

/* ── Toggle switch ── */
QCheckBox#toggleSwitch {
    spacing: 0px;
}
QCheckBox#toggleSwitch::indicator {
    width: 42px;
    height: 24px;
    border-radius: 12px;
    background: #d1d5db;
    border: none;
}
QCheckBox#toggleSwitch::indicator:checked {
    background: #2563eb;
}

/* ── Row checkbox ── */
QCheckBox#rowCheck::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox#rowCheck::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
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
QPushButton#outlineButton:hover { background: #f9fafb; }

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

QPushButton#ghostSmallButton {
    background: #ffffff;
    color: #374151;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 500;
    padding: 0 14px;
    min-height: 34px;
}
QPushButton#ghostSmallButton:hover { background: #f9fafb; }

QPushButton#infoButton {
    background: transparent;
    border: 1.5px solid #e5e7eb;
    border-radius: 7px;
    color: #9ca3af;
    font-size: 14px;
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0;
}
QPushButton#infoButton:hover { background: #f3f4f6; }

/* ── Scroll ── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent; width: 8px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #d1d5db; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
CECC_FIELD_HELP = {
    "Fournisseur Doc / MANUFACTURER": "Nom du fournisseur ou distributeur mentionné sur le document.",
    "Manufacturer Part Number": "Manufacturer Part Number mentionné sur le document.",
    "Statut CECC": "Statuts possibles : A demander, Demandé, Relancé, Non conforme, Validé.",
    "CECC : Date": "Date du CECC.",
    "Nom : CECC": "Nom du CECC.",
    "CECC Classement": "Valeurs possibles : NC, DU, DI (Défense item).",
    "Catégorie (EAR99 / Code ECCN / Code ML ITAR)": (
        "NC\n"
        "DU Hors USA = Code ECCN\n"
        "DU USA = EAR99 ou ECCN Code\n"
        "DI = Code ML ITAR"
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

COUNTRY_ORIGIN_4A = """
AF-Afghanistan
AX-Îles Åland
AL-Albanie
DZ-Algérie
AS-Samoa américaines
AD-Andorre
AO-Angola
AI-Anguilla
AQ-Antarctique
AG-Antigua-et-Barbuda
AR-Argentine
AM-Arménie
AW-Aruba
AU-Australie
AT-Autriche
AZ-Azerbaïdjan
BS-Bahamas
BH-Bahreïn
BD-Bangladesh
BB-Barbade
BY-Biélorussie
BE-Belgique
BZ-Belize
BJ-Bénin
BM-Bermudes
BT-Bhoutan
BO-Bolivie
BA-Bosnie-Herzégovine
BW-Botswana
BV-Île Bouvet
BR-Brésil
VG-British Virgin Islands
IO-Territoire britannique de l’Océan Indien
BN-Brunei Darussalam
BG-Bulgarie
BF-Burkina Faso
BI-Burundi
KH-Cambodge
CM-Cameroun
CA-Canada
CV-Cap-Vert
KY-Iles Cayman
CF-République centrafricaine
TD-Tchad
CL-Chili
CN-Chine
HK-Hong Kong
MO-Macao
FR-France
DE-Allemagne
GB-Royaume-Uni
US-États-Unis
JP-Japon
IT-Italie
ES-Espagne
CH-Suisse
BE-Belgique
NL-Pays-Bas
PT-Portugal
PL-Pologne
RO-Roumanie
RU-Russie
UA-Ukraine
CN-Chine
KR-Corée du Sud
TW-Taiwan
VN-Viêt Nam
IN-Inde
MX-Mexique
MA-Maroc
TN-Tunisie
DZ-Algérie
ZA-Afrique du Sud
ZW-Zimbabwe
""".strip().splitlines()

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
        ("N/A",        "#ef4444", "#ffffff"),   # label, bg_active, text_active
        ("Non défini", "#9ca3af", "#ffffff"),
        ("Applicable", "#2563eb", "#ffffff"),
    ]

    _H = 28          # hauteur du widget
    _BTN_W = 76      # largeur d'un bouton
    _RADIUS = 7      # arrondi

    def __init__(self, state: int = 1, parent=None):
        """*state* : 0=N/A, 1=Non défini, 2=Applicable."""
        super().__init__(parent)
        self._state = max(0, min(2, state))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        total_w = self._BTN_W * 3 + 4          # +4 pour les marges internes
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
            idx = self._index_at(event.position().x() if hasattr(event, 'position') else event.x())
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
        color_a = QtGui.QColor(self._STATES[max(0, round(self._anim_state) - 1)][1]
                               if self._anim_state > 0 else self._STATES[0][1])
        color_b = QtGui.QColor(self._STATES[min(2, round(self._anim_state))][1])
        # Couleur interpolée entre les deux états adjacents
        t = self._anim_state - int(self._anim_state)
        r_c = int(color_a.red()   * (1 - t) + color_b.red()   * t)
        g_c = int(color_a.green() * (1 - t) + color_b.green() * t)
        b_c = int(color_a.blue()  * (1 - t) + color_b.blue()  * t)
        cursor_color = QtGui.QColor(self._STATES[self._state][1])  # couleur cible nette

        p.setBrush(cursor_color)
        p.drawRoundedRect(
            QtCore.QRectF(cursor_x + 1, 1, self._BTN_W - 2, H - 2),
            r - 1, r - 1
        )

        # Labels
        font = self.font()
        font.setPointSize(8)
        font.setBold(False)
        p.setFont(font)

        for i, (label, bg, fg) in enumerate(self._STATES):
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

    def __init__(self, code: str, description: str,
                 default_on: bool = True, parent=None):
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
def _field_col(label_text: str, required: bool = False,
               optional: bool = False) -> QtWidgets.QVBoxLayout:
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
        for code, desc in CE_REQUIREMENTS:
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
                row.set_state(0)   # N/A
            else:
                row.set_state(2)   # Applicable

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
        return [
            row.code
            for row in self._req_rows
            if row.is_undefined()
        ]

    def _link_rohs_rows(self):
        """2011/65/UE et 2015/863 forment une seule exigence RoHS : l'état
        d'applicabilité et la case « couvert » de l'une sont recopiés sur l'autre."""
        linked = [r for r in self._req_rows if is_rohs_code(r.code)]
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
        for code, desc in DPE_REQUIREMENTS:
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
                row.set_state(0)   # N/A
            else:
                row.set_state(2)   # Applicable
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
            f"{applicable} applicable(s) · {na} N/A · {undefined} non défini(s)  —  {total} exigences"
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
        return [
            row.code
            for row in self._req_rows
            if row.is_undefined()
        ]


# ──────────────────────────────────────────────────────────────────────────────
# CECC Informations page
# ──────────────────────────────────────────────────────────────────────────────
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

        def _row(left_label, left_key, right_label, right_key, right_is_combo=False, combo_items=None,
         left_is_combo=False, left_combo_items=None):
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

                ib = _info_btn(tooltip=CECC_FIELD_HELP.get(label_text, "Information non disponible."))
                label_row.addWidget(ib)

                label_row.addStretch(1)
                col.addLayout(label_row)

                if is_combo:
                    w = QtWidgets.QComboBox()
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

            row_lay.addLayout(
                make_field(left_label, left_key, left_is_combo, left_combo_items),
                1
            )
            row_lay.addLayout(
                make_field(right_label, right_key, right_is_combo, combo_items),
                1
            )

            inner_lay.addLayout(row_lay)

        def _row_full(label_text, key):
            row_lay = QtWidgets.QVBoxLayout()
            row_lay.setSpacing(5)

            label_row = QtWidgets.QHBoxLayout()
            label_row.setSpacing(4)

            lbl = QtWidgets.QLabel(label_text)
            lbl.setObjectName("fieldLabelOpt")
            label_row.addWidget(lbl)

            ib = _info_btn(
                tooltip=CECC_FIELD_HELP.get(
                    label_text,
                    "Information non disponible."
                )
            )
            label_row.addWidget(ib)

            label_row.addStretch(1)
            row_lay.addLayout(label_row)

            w = QtWidgets.QLineEdit()
            w.textChanged.connect(lambda _text: self.changed.emit())

            self._edits[key] = w
            row_lay.addWidget(w)

            inner_lay.addLayout(row_lay)

        _row(
            "Fournisseur Doc / MANUFACTURER", "manufacturer_doc",
            "Licence Oui / Non", "licence_yn",
            right_is_combo=True,
            combo_items=["Oui", "Non"]
        )

        _row(
            "Manufacturer Part Number", "manufacturer_part_number",
            "N° Licence", "licence_number"
        )

        _row(
            "Statut CECC", "cecc_etat",
            "CECC : Date", "cecc_date",
            left_is_combo=True,
            left_combo_items=["A demander", "Demandé", "Relancé", "Non conforme", "Validé"]
        )

        _row(
            "Nom : CECC", "nom_cecc",
            "Pays Origine 4a", "pays_origine",
            right_is_combo=True,
            combo_items=COUNTRY_ORIGIN_4A
        )

        _row(
            "CECC Classement", "cecc_classement",
            "EAR99 Value (USD)", "ear99_value",
            left_is_combo=True,
            left_combo_items=["NC", "DU", "DI (Défense item)"]
        )

        _row(
            "Catégorie (EAR99 / Code ECCN / Code ML ITAR)", "categorie",
            "ECCN value (USD)", "eccn_value"
        )

        _row_full(
            "Composant contrôlés à l'export et intégrés ds l'article (10.1)",
            "composant_export_10_1"
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
class UploadDocumentDialog(QtWidgets.QDialog):
    documentSaved = QtCore.Signal()

    def __init__(
        self,
        project_dir: Path,
        supplier: str,
        reference: str,
        preset_justification_type: str | None = None,
        batch_targets: list[dict] | None = None,
        mode: str = "import",
        parent=None,
    ):
        """*mode* : "import" (import de document, applicabilité modifiable)
        ou "applicability" (gestion de l'applicabilité seule, sans document)."""
        super().__init__(parent)
        self.project_dir = project_dir
        self.supplier = supplier
        self.reference = reference
        self.preset_justification_type = preset_justification_type
        self.mode = mode if mode in ("import", "applicability") else "import"
        self.selected_file: Path | None = None
        self.batch_targets = batch_targets or [
            {"supplier": supplier, "reference": reference,
             "type": preset_justification_type or ""}
        ]

        self._setup_window()
        self._build_ui()
        self._init_type()
        self._prefill_existing_cecc_fields()
        self._prefill_existing_applicability()
        self._update_form_visibility()
        self._update_preview()
        # Calculé après la construction de l'UI (polices réelles, contenu
        # réel) pour que rien ne soit rogné : le pied de page (boutons) et
        # le champ « Nom final » doivent toujours rester visibles, jamais
        # écrasés par la hauteur imposée à la zone des exigences. `min_h`
        # est le strict minimum requis (plancher dur, protège le pied de
        # page) ; la hauteur visée ajoute une marge généreuse dédiée à la
        # zone des exigences (seule zone avec stretch=1, elle absorbe tout
        # ce surplus) pour qu'elle reste la zone dominante de la page.
        self.layout().activate()
        needed = self.layout().minimumSize()
        fit_and_center(
            self,
            max(860, needed.width()),
            max(900, needed.height() + 260),
            min_w=needed.width(),
            min_h=needed.height(),
        )

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        jtype = self.preset_justification_type or ""
        action = "Gérer l'applicabilité" if self.mode == "applicability" else "Importer un justificatif"
        if jtype:
            self.setWindowTitle(f"{action} {jtype}")
        else:
            self.setWindowTitle(action)
        self.setStyleSheet(STYLESHEET)

    def _prefill_existing_applicability(self):
        """
        Recharge l'état d'applicabilité déjà enregistré pour la référence,
        exigence par exigence (dernier enregistrement mentionnant le code,
        même règle que le dashboard et l'export). Une exigence jamais
        renseignée reste «Non défini».
        """
        try:
            docs = get_uploaded_documents(self.project_dir)
        except Exception:
            return

        for jtype, page in (("CE", self._ce_page), ("DPE", self._dpe_page)):
            matching = [
                d for d in docs
                if str(d.get("supplier", "")) == str(self.supplier)
                and str(d.get("reference", "")) == str(self.reference)
                and (
                    str(d.get("source_justification_type", "")).upper() == jtype
                    or jtype in [str(b).upper() for b in (d.get("stored_in_bdds") or [])]
                )
            ]
            if not matching:
                continue
            for row in page._req_rows:
                row.set_state(requirement_state(matching, row.code))

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
        action = "Gérer l'applicabilité" if self.mode == "applicability" else "Importer un justificatif"
        title_txt = f"{action} {jtype}".strip()
        title = QtWidgets.QLabel(title_txt, w)
        title.setObjectName("dialogTitle")

        if self.mode == "applicability":
            sub_txt = "Indiquez l'applicabilité de chaque exigence, sans fournir de document."
        else:
            subtitles = {
                "CE":   "Importez un document et cochez les exigences CE qu'il couvre.",
                "CECC": "Importez un document CECC pour la référence sélectionnée.",
                "DPE":  "Importez un document et cochez les exigences qu'il couvre.",
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
        type_choices = [t for t in JUSTIFICATION_TYPES if t != "CECC"] if self.mode == "applicability" else list(JUSTIFICATION_TYPES)
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

        self._ce_page   = CEPage(self._stack)
        self._dpe_page  = DPEPage(self._stack)
        self._cecc_page = CECCPage(self._stack)

        self._ce_page.changed.connect(self._update_preview)
        self._dpe_page.changed.connect(self._update_preview)
        self._cecc_page.changed.connect(self._update_preview)

        self._stack.addWidget(self._ce_page)    # index 0
        self._stack.addWidget(self._cecc_page)  # index 1
        self._stack.addWidget(self._dpe_page)   # index 2

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

    def _prefill_existing_cecc_fields(self):
        try:
            latest = get_latest_cecc_fields(self.project_dir, self.supplier, self.reference)
            if latest:
                self._cecc_page.prefill(latest)
        except Exception:
            pass

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

    def _choose_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choisir un justificatif", str(Path.home()),
            "Documents (*.pdf *.docx *.xlsx *.PDF *.DOCX *.XLSX)"
        )
        if path:
            self._apply_file(Path(path))

    def _apply_file(self, path: Path):
        self.selected_file = path
        # Update drop zone label
        lbl = self._drop_zone.findChild(QtWidgets.QLabel)
        # Update the text widgets inside the drop zone
        for child in self._drop_zone.findChildren(QtWidgets.QLabel):
            if "Glissez" in child.text():
                child.setText(path.name)
                child.setStyleSheet(
                    "font-size:12px; color:#2563eb; background:transparent;"
                )
        # Autofill CECC nom
        self._cecc_page.set_nom_cecc(path.name)
        self._update_preview()

    def _current_type(self) -> str:
        return self.type_combo.currentText().strip().upper()

    @staticmethod
    def _safe_name_part(value: str) -> str:
        forbidden = '<>:"/\\|?*'
        cleaned = "".join("_" if c in forbidden else c for c in str(value or "").strip())
        cleaned = " ".join(cleaned.split())
        return cleaned.replace(" ", "_")

    def _auto_name(self, supplier: str | None = None, reference: str | None = None) -> str:
        """Nommage automatique : Type_Fournisseur_Reference."""
        sup = supplier if supplier is not None else self.supplier
        ref = reference if reference is not None else self.reference
        parts = [self._current_type(), self._safe_name_part(sup), self._safe_name_part(ref)]
        return "_".join(p for p in parts if p)

    def _build_final_filename(self, supplier: str | None = None, reference: str | None = None) -> str:
        if not self.selected_file:
            return "—"
        custom = self._final_name_edit.text().strip()
        if custom:
            return custom if "." in custom else custom + self.selected_file.suffix
        return self._auto_name(supplier, reference) + self.selected_file.suffix

    def _update_preview(self):
        name = self._build_final_filename()

        current = self._current_type()

        if current == "CE":
            count = self._ce_page.applicable_count()
            self._ce_page.set_preview(
                f"{name} — {count} exigence(s) applicable(s)"
            )

        elif current == "DPE":
            count = self._dpe_page.applicable_count()
            self._dpe_page._counter_lbl.setText(
                f"Nom final : {name} — {count} exigence(s) applicable(s)"
            )

        else:
            self._cecc_page.set_preview(name)

    # ── Backend helpers (unchanged logic) ─────────────────────────────────────

    def _selected_ce_requirements(self) -> tuple[list[str], list[str]]:
        return self._ce_page.selected_requirements()

    def _selected_dpe_requirements(self) -> tuple[list[str], list[str]]:
        return self._dpe_page.selected_requirements()

    def _cecc_fields_data(self) -> dict[str, str]:
        data = self._cecc_page.get_fields()
        if self.selected_file:
            data["nom_cecc"] = data.get("nom_cecc") or self.selected_file.name
        return data

    def _selected_requirements(self) -> tuple[list[str], list[str]]:
        """Exigences à enregistrer pour ce document.

        Mode "applicability" : toutes les exigences Applicable (pas de document).
        Mode "import" : uniquement les exigences Applicable ET cochées
        (« couvertes » par le document en cours d'import).
        """
        t = self._current_type()
        if self.mode == "applicability":
            if t == "CE":
                return self._selected_ce_requirements()
            if t == "DPE":
                return self._selected_dpe_requirements()
            return [], []

        if t == "CE":
            return self._ce_page.checked_applicable_requirements()
        if t == "DPE":
            return self._dpe_page.checked_applicable_requirements()
        return [], []

    def _all_applicable_requirements(self) -> tuple[list[str], list[str]]:
        """Toutes les exigences Applicable, sans filtrer sur la case cochée."""
        t = self._current_type()
        if t == "CE":
            return self._selected_ce_requirements()
        if t == "DPE":
            return self._selected_dpe_requirements()
        return [], []

    def _has_rohs(self, include_applicability: bool = False) -> bool:
        """RoHS est couvert par le document (ou, avec *include_applicability*,
        simplement renseigné : Applicable ou N/A)."""
        codes, _ = self._selected_requirements()
        if include_applicability:
            codes = codes + self._all_applicable_requirements()[0] + self._not_applicable_requirements()[0]
        return any(is_rohs_code(c) for c in codes)

    def _project_dossier_number(self) -> str:
        project_file = get_project_file_path(self.project_dir)
        data = json.loads(project_file.read_text(encoding="utf-8"))
        return data["dossier_number"]

    def _enabled_bdds(self) -> list[str]:
        project_file = get_project_file_path(self.project_dir)
        data = json.loads(project_file.read_text(encoding="utf-8"))
        return [str(v).strip().upper() for v in data.get("enabled_bdds", JUSTIFICATION_TYPES)]

    def _storage_types(self, include_applicability: bool = False) -> list[str]:
        """BDD concernées. Par défaut : dossiers où copier le fichier (RoHS
        couvert → CE et DPE). Avec *include_applicability* : BDD où
        l'enregistrement s'applique, RoHS renseigné suffisant pour que l'état
        RoHS (Applicable / N/A) soit repris par l'autre BDD."""
        current = self._current_type()
        enabled = set(self._enabled_bdds())
        if current == "CE" and self._has_rohs(include_applicability):
            return [b for b in ["CE", "DPE"] if b in enabled]
        if current == "DPE" and self._has_rohs(include_applicability):
            return [b for b in ["DPE", "CE"] if b in enabled]
        return [current] if current in enabled else []

    def _target_folders_for(self, supplier: str, reference: str) -> list[Path]:
        dossier_number = self._project_dossier_number()
        return [
            self.project_dir / f"BDD {t} {dossier_number}" / "Documents" / supplier / reference
            for t in self._storage_types()
        ]

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self) -> tuple[bool, str]:
        current = self._current_type()

        if current not in self._enabled_bdds():
            return False, f"Le livrable {current} n'est pas activé sur ce projet."

        if current in ("CE", "DPE"):
            if self.mode == "applicability":
                # Aucun document requis : on enregistre l'état d'applicabilité
                # actuel, même partiel. Les exigences encore «Non défini»
                # restent simplement inchangées.
                return True, ""

            # Mode import : le document n'est requis QUE si au moins une
            # exigence a été cochée. Si seule l'applicabilité est renseignée
            # (aucune case cochée), aucun document n'est nécessaire et la
            # sauvegarde peut être partielle.
            codes, _ = self._selected_requirements()

            if codes and not self.selected_file:
                return False, (
                    "Un document doit être fourni : au moins une exigence "
                    "applicable est cochée."
                )

            if self.selected_file and not codes:
                return False, (
                    "Un fichier a été sélectionné mais aucune exigence n'est cochée. "
                    "Coche au moins une exigence «Applicable» pour l'associer à ce "
                    "document, ou retire le fichier pour n'enregistrer que "
                    "l'applicabilité."
                )

            if self.selected_file and codes:
                # On importe réellement un document pour des exigences
                # précises : celles-ci (et le reste du tableau) doivent être
                # clairement tranchées avant de finaliser l'import.
                undefined_count = 0
                if current == "CE":
                    undefined_count = sum(1 for r in self._ce_page._req_rows if r.is_undefined())
                elif current == "DPE":
                    undefined_count = sum(1 for r in self._dpe_page._req_rows if r.is_undefined())

                if undefined_count > 0:
                    return False, (
                        f"{undefined_count} exigence(s) sont encore «Non défini(es)». "
                        f"Veuillez indiquer «Applicable» ou «N/A» pour chacune avant "
                        f"d'importer ce document."
                    )

        elif current == "CECC":
            if self.mode == "applicability":
                return False, (
                    "La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC."
                )

            if not self.selected_file or not self.selected_file.exists():
                return False, "Merci de choisir un fichier."

            data = self._cecc_fields_data()
            required = ["manufacturer_doc", "manufacturer_part_number", "nom_cecc"]
            if any(not data.get(k) for k in required):
                return False, (
                    "Pour un justificatif CECC, renseignez au minimum "
                    "Fournisseur Doc, Manufacturer Part Number et Nom : CECC."
                )

        return True, ""

    def _unique_target_path(self, target_dir: Path, filename: str) -> Path:
        candidate = target_dir / filename
        if not candidate.exists():
            return candidate
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        i = 1
        while True:
            candidate = target_dir / f"{stem} ({i}){suffix}"
            if not candidate.exists():
                return candidate
            i += 1

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save_document(self):
        ok, msg = self._validate()
        if not ok:
            title = "Applicabilité" if self.mode == "applicability" else "Import"
            QtWidgets.QMessageBox.warning(self, title, msg)
            return

        source_type = self._current_type()
        stored_bdds = self._storage_types(include_applicability=True)
        codes, labels = self._selected_requirements()
        not_applicable_codes, not_applicable_labels = self._not_applicable_requirements()
        cecc_fields = self._cecc_fields_data() if source_type == "CECC" else {}

        # En mode import, si aucune exigence n'est cochée, il n'y a pas de
        # document à associer : seule l'applicabilité est enregistrée.
        applicability_only = self.mode == "applicability" or (
            self.mode == "import" and source_type in ("CE", "DPE") and not codes
        )

        # L'applicabilité est stockée à part (`applicable_codes`) :
        # `requirement_codes` ne liste QUE les exigences couvertes par un
        # fichier. Sinon un enregistrement sans document masquerait, dans le
        # dashboard et l'export, les documents déjà déposés.
        applicable_codes, _ = self._all_applicable_requirements()
        if applicability_only:
            codes, labels = [], []

        try:
            saved = 0

            for target in self.batch_targets:
                sup = str(target["supplier"])
                ref = str(target["reference"])

                if applicability_only:
                    # Aucun document : on enregistre uniquement l'état d'applicabilité.
                    insert_uploaded_document(
                        project_dir=self.project_dir,
                        supplier=sup,
                        reference=ref,
                        source_justification_type=source_type,
                        stored_in_bdds=stored_bdds,
                        requirement_codes=codes,
                        requirement_labels=labels,
                        cecc_fields=cecc_fields,
                        original_filename="",
                        stored_filename="",
                        not_applicable_codes=not_applicable_codes,
                        not_applicable_labels=not_applicable_labels,
                        applicable_codes=applicable_codes,
                        relative_path="",
                        uploaded_at=datetime.now().isoformat(),
                    )
                else:
                    final_name = self._build_final_filename(sup, ref)

                    for tdir in self._target_folders_for(sup, ref):
                        tdir.mkdir(parents=True, exist_ok=True)
                        tpath = self._unique_target_path(tdir, final_name)
                        shutil.copy2(self.selected_file, tpath)

                        insert_uploaded_document(
                            project_dir=self.project_dir,
                            supplier=sup,
                            reference=ref,
                            source_justification_type=source_type,
                            stored_in_bdds=stored_bdds,
                            requirement_codes=codes,
                            requirement_labels=labels,
                            cecc_fields=cecc_fields,
                            original_filename=self.selected_file.name,
                            stored_filename=tpath.name,
                            not_applicable_codes=not_applicable_codes,
                            not_applicable_labels=not_applicable_labels,
                            applicable_codes=applicable_codes,
                            relative_path=str(tpath.relative_to(self.project_dir)).replace("\\", "/"),
                            uploaded_at=datetime.now().isoformat(),
                        )

                saved += 1

            self.documentSaved.emit()

            if applicability_only:
                QtWidgets.QMessageBox.information(
                    self,
                    "Applicabilité enregistrée",
                    f"L'applicabilité a été mise à jour pour {saved} ligne(s)."
                )
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "Import terminé",
                    f"Les modifications ont été appliquées à {saved} ligne(s)."
                )
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur d'enregistrement",
                f"Impossible d'enregistrer les modifications.\n\n{e}"
            )


    def _not_applicable_requirements(self) -> tuple[list[str], list[str]]:
        t = self._current_type()

        if t == "CE":
            return self._ce_page.not_applicable_requirements()

        if t == "DPE":
            return self._dpe_page.not_applicable_requirements()

        return [], []