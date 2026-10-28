"""Tableau de suivi d'un projet : onglets Tous / par livrable, indicateurs,
filtres par colonne, import, applicabilité, paramétrage et export.

Interface reprise de `00_ancien/wikidocs_qt/project_dashboard_window.py`
(`MainTab`, `ProjectDashboardWindow`) ; les calculs passent par
`services/completion.py` et l'export par `services/export.py`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from app.models.projet import Projet
from app.models.suivi import LigneSuivi
from app.services import completion, corrections, depot, export, projets
from app.ui.elements_suivi import (
    ALT_ROW,
    BG,
    BLUE,
    BLUE_DARK,
    DARK,
    DPE_ICON_PATH,
    EU_ICON_PATH,
    F_BOLD,
    F_SMALL,
    F_TOPBAR,
    GRAY_BORDER,
    GRAY_CARD,
    GRAY_LIGHT,
    GRAY_TEXT,
    GREEN_OK,
    KPI_BAR_COLORS,
    ORANGE_BG,
    ORANGE_WARN,
    RED_KO,
    SEL_BG,
    TOPBAR_BG,
    TOPBAR_FG,
    WHITE,
    FilterableHeader,
    KpiCard,
    _hline,
    _make_label,
    _svg_pixmap,
)
from app.ui.filtre import FilterPopup
from app.ui.geometrie import ajuster_et_centrer
from app.ui.panneau_detail import DetailPanel

# Colonne du tableau → (colonne filtrable de LigneSuivi, titre de la fenêtre de filtre)
_FILTRES = {
    0: ("fournisseur", "Filtrer les fournisseurs"),
    1: ("reference", "Filtrer les références"),
    2: ("libelle", "Filtrer les libellés"),
    5: ("livrable", "Filtrer les types"),
    6: ("completion", "Filtrer la complétude"),
}


class MainTab(QtWidgets.QWidget):
    COLUMNS = [
        "Fournisseur",
        "Référence",
        "Libellé équipement",
        "MNP",
        "N° de commande",
        "Type",
        "Complétude",
    ]

    rowSelected = QtCore.Signal(object)  # LigneSuivi

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.table = QtWidgets.QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setHorizontalHeader(FilterableHeader(Qt.Horizontal, self.table))
        hh = self.table.horizontalHeader()
        hh.setFont(F_BOLD)

        mode = QtWidgets.QHeaderView
        # (mode, largeur initiale, largeur minimale) par colonne
        config = [
            (mode.Interactive, 120, 80),  # Fournisseur
            (mode.Interactive, 110, 80),  # Référence
            (mode.Stretch, 0, 140),  # Libellé (étire l'espace libre)
            (mode.Interactive, 65, 50),  # MNP
            (mode.Interactive, 120, 80),  # N° commande
            (mode.Interactive, 75, 60),  # Type
            (mode.Interactive, 100, 80),  # Complétude
        ]
        self._col_min_widths = [c[2] for c in config]
        for i, (m, largeur, _) in enumerate(config):
            hh.setSectionResizeMode(i, m)
            if m == mode.Interactive and largeur:
                hh.resizeSection(i, largeur)
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

    def _on_section_resized(self, index: int, _ancienne: int, taille: int):
        minimum = self._col_min_widths[index] if index < len(self._col_min_widths) else 50
        if taille < minimum:
            self.table.horizontalHeader().resizeSection(index, minimum)

    def _on_selection_changed(self):
        idxs = self.table.selectedIndexes()
        if not idxs:
            return
        item = self.table.item(idxs[0].row(), 0)
        ligne = item.data(Qt.UserRole) if item else None
        if ligne:
            self.rowSelected.emit(ligne)

    def load_rows(self, lignes: list[LigneSuivi]):
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(lignes))
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        gauche = Qt.AlignLeft | Qt.AlignVCenter
        for ri, ligne in enumerate(lignes):
            pct = ligne.completion
            couleur = GREEN_OK if pct >= 1.0 else ORANGE_WARN if pct > 0 else RED_KO
            valeurs = [
                (ligne.fournisseur, gauche),
                (ligne.reference, gauche),
                (ligne.libelle, gauche),
                (ligne.mnp, Qt.AlignCenter),
                (ligne.n_commande, Qt.AlignCenter),
                (ligne.livrable, Qt.AlignCenter),
                (ligne.completion_texte, Qt.AlignCenter),
            ]
            for ci, (valeur, alignement) in enumerate(valeurs):
                item = QtWidgets.QTableWidgetItem(str(valeur))
                item.setTextAlignment(alignement)
                item.setData(Qt.UserRole, ligne)
                if ci == 6:  # Complétude
                    item.setForeground(QtGui.QBrush(QColor(couleur)))
                    police = item.font()
                    police.setBold(True)
                    item.setFont(police)
                self.table.setItem(ri, ci, item)
        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.setSortingEnabled(True)

    def selected_rows_data(self) -> list[LigneSuivi]:
        lignes, vues = [], set()
        for idx in self.table.selectedIndexes():
            r = idx.row()
            if r in vues:
                continue
            vues.add(r)
            item = self.table.item(r, 0)
            ligne = item.data(Qt.UserRole) if item else None
            if ligne:
                lignes.append(ligne)
        return lignes


class FenetreSuivi(QtWidgets.QMainWindow):
    """Tableau de suivi d'un projet ouvert."""

    def __init__(self, projet: Projet, parent=None):
        super().__init__(parent)
        self.projet = projet
        self.filtres: dict[str, set[str] | None] = {c: None for c, _ in _FILTRES.values()}
        self.onglets_par_nom: dict[str, MainTab] = {}
        self._toutes_les_lignes: list[LigneSuivi] = []
        self._lignes_filtrees: list[LigneSuivi] = []
        self.lignes_par_onglet: dict[str, list[LigneSuivi]] = {}
        self.setWindowTitle(f"NOX_Manager — {self._nom_affiche()}")
        ajuster_et_centrer(self, 1400, 860, largeur_min=1000, hauteur_min=620)
        self._build_ui()
        self.charger()

    def _nom_affiche(self) -> str:
        return self.projet.numero_dossier or self.projet.nom or self.projet.dossier.name

    # ── Construction ──────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QtWidgets.QWidget()
        central.setStyleSheet(f"background:{BG};")
        self.setCentralWidget(central)
        racine = QtWidgets.QVBoxLayout(central)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.setSpacing(0)
        racine.addWidget(self._build_topbar())
        self._lbl_date = _make_label("—", F_SMALL, DARK)  # horodatage (non affiché)
        contenu = QtWidgets.QWidget()
        contenu.setStyleSheet(f"background:{BG};")
        v = QtWidgets.QVBoxLayout(contenu)
        v.setContentsMargins(12, 10, 12, 8)
        v.setSpacing(8)
        v.addWidget(self._build_kpi_row())
        v.addWidget(self._build_table_section(), 1)
        racine.addWidget(contenu, 1)

    def _build_topbar(self) -> QtWidgets.QWidget:
        barre = QtWidgets.QWidget()
        barre.setFixedHeight(44)
        barre.setStyleSheet(f"background:{TOPBAR_BG};")
        h = QtWidgets.QHBoxLayout(barre)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(2)
        marque = QtWidgets.QLabel("NOX Manager")
        marque.setFont(QFont("Segoe UI", 10, QFont.Bold))
        marque.setStyleSheet(f"color:{WHITE}; background:transparent;")
        h.addWidget(marque)
        h.addSpacing(12)
        actions = [
            ("⚙  Paramétrage", self._parametrer),
            ("📥  Importer", lambda: self._ouvrir_depot("import")),
            ("↺  Actualiser", self.charger),
            ("📊  Exporter BDD", self._exporter),
        ]
        for libelle, action in actions:
            bouton = QtWidgets.QPushButton(libelle)
            bouton.setFont(F_TOPBAR)
            bouton.setCursor(Qt.PointingHandCursor)
            bouton.setFlat(True)
            bouton.setStyleSheet(f"""
                QPushButton {{
                    color:{TOPBAR_FG}; padding:5px 12px;
                    border-radius:6px; border:none; font-size:9pt;
                }}
                QPushButton:hover   {{ background:#1F2937; color:{WHITE}; }}
                QPushButton:pressed {{ background:#374151; }}
            """)
            bouton.clicked.connect(lambda _=False, a=action: a())
            h.addWidget(bouton)
        h.addStretch(1)
        self._badge_projet = QtWidgets.QLabel(self._nom_affiche())
        self._badge_projet.setFont(F_BOLD)
        self._badge_projet.setStyleSheet("""
            background:#F59E0B; color:#1F2937;
            border-radius:6px; padding:3px 12px; font-size:9pt; font-weight:700;
        """)
        h.addWidget(self._badge_projet)
        return barre

    def _build_kpi_row(self) -> QtWidgets.QWidget:
        ligne = QtWidgets.QWidget()
        ligne.setStyleSheet("background:transparent;")
        h = QtWidgets.QHBoxLayout(ligne)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        self.kpi_ce = KpiCard(
            _svg_pixmap(EU_ICON_PATH, 20),
            "CE",
            "0 %",
            "Complétude",
            bar_color=KPI_BAR_COLORS["CE"],
            icon_bg="#F5F1DE",
        )
        self.kpi_cecc = KpiCard(
            "📋", "CECC", "0 %", "Complétude", bar_color=KPI_BAR_COLORS["CECC"], icon_bg="#EDE9FE"
        )
        self.kpi_dpe = KpiCard(
            _svg_pixmap(DPE_ICON_PATH, 20),
            "DPE",
            "0 %",
            "Complétude",
            bar_color=KPI_BAR_COLORS["DPE"],
            icon_bg="#D1FAE5",
        )
        for carte in (self.kpi_ce, self.kpi_cecc, self.kpi_dpe):
            h.addWidget(carte, 1)
        h.addStretch(2)
        return ligne

    def _build_table_section(self) -> QtWidgets.QWidget:
        exterieur = QtWidgets.QWidget()
        exterieur.setStyleSheet("background:transparent;")
        lay = QtWidgets.QHBoxLayout(exterieur)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.separateur = QtWidgets.QSplitter(Qt.Horizontal)
        self.separateur.setChildrenCollapsible(False)
        self.separateur.setHandleWidth(6)
        self.separateur.setStyleSheet(f"""
            QSplitter::handle {{
                background:{GRAY_BORDER};
                border-radius:3px;
            }}
            QSplitter::handle:hover {{
                background:{BLUE};
            }}
        """)
        lay.addWidget(self.separateur, 1)

        gauche = QtWidgets.QFrame()
        gauche.setStyleSheet(f"""
            QFrame {{
                background:{WHITE};
                border:1px solid {GRAY_CARD};
                border-radius:12px;
            }}
        """)
        lv = QtWidgets.QVBoxLayout(gauche)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(0)
        lv.addWidget(self._build_filter_row())
        lv.addWidget(_hline())
        lv.addWidget(self._build_tabs(), 1)
        lv.addWidget(self._build_statusbar())
        self.separateur.addWidget(gauche)

        self.detail_panel = self._creer_panneau_detail()
        self.separateur.addWidget(self.detail_panel)
        self.separateur.setStretchFactor(0, 4)
        self.separateur.setStretchFactor(1, 1)
        self.separateur.setSizes([1000, 340])
        return exterieur

    def _creer_panneau_detail(self) -> DetailPanel:
        panneau = DetailPanel()
        panneau.clear()
        panneau.requestModify.connect(lambda _ligne: self._ouvrir_depot("import"))
        panneau.requestDelete.connect(self._vider_reference)
        panneau.requestOpenDoc.connect(self._ouvrir_document)
        panneau.requestReplaceJustif.connect(self._remplacer_justificatif)
        panneau.requestDeleteJustif.connect(self._retirer_justificatif)
        return panneau

    def _build_filter_row(self) -> QtWidgets.QWidget:
        barre = QtWidgets.QWidget()
        barre.setFixedHeight(48)
        barre.setStyleSheet("background:transparent;")
        h = QtWidgets.QHBoxLayout(barre)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(6)
        astuce = _make_label(
            "💡  Clique sur le ▾ d'une colonne (Fournisseur, Référence, Libellé, Type, "
            "Complétude) pour filtrer",
            F_SMALL,
            GRAY_TEXT,
        )
        h.addWidget(astuce)
        h.addStretch(1)

        applicabilite = QtWidgets.QPushButton("Applicabilité")
        applicabilite.setFont(F_BOLD)
        applicabilite.setFixedHeight(34)
        applicabilite.setMinimumWidth(140)
        applicabilite.setCursor(Qt.PointingHandCursor)
        applicabilite.setStyleSheet(f"""
            QPushButton {{
                background:{ORANGE_BG}; color:{ORANGE_WARN};
                border:1px solid {ORANGE_WARN}; border-radius:8px;
                padding:0 18px; font-size:9pt; font-weight:700;
            }}
            QPushButton:hover   {{ background:#FDE8C8; }}
            QPushButton:pressed {{ background:#FBDBA7; }}
        """)
        applicabilite.setToolTip(
            "Définir l'applicabilité (Applicable / N/A) des exigences, sans importer de document."
        )
        applicabilite.clicked.connect(lambda: self._ouvrir_depot("applicability"))
        h.addWidget(applicabilite)

        importer = QtWidgets.QPushButton("＋  Importer un document")
        importer.setFont(F_BOLD)
        importer.setFixedHeight(34)
        importer.setCursor(Qt.PointingHandCursor)
        importer.setStyleSheet(f"""
            QPushButton {{
                background:{BLUE}; color:{WHITE};
                border:none; border-radius:8px;
                padding:0 16px; font-size:9pt;
            }}
            QPushButton:hover   {{ background:{BLUE_DARK}; }}
            QPushButton:pressed {{ background:#1E40AF; }}
        """)
        importer.setToolTip("Importer un document et cocher les exigences qu'il couvre.")
        importer.clicked.connect(lambda: self._ouvrir_depot("import"))
        h.addWidget(importer)
        return barre

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
        for nom in ["Tous", *self.projet.livrables]:
            onglet = MainTab(self)
            self.onglets_par_nom[nom] = onglet
            self.tabs.addTab(onglet, nom)
            onglet.rowSelected.connect(self._sur_ligne_selectionnee)
            onglet.table.horizontalHeader().filterRequested.connect(self._sur_demande_filtre)
        self.tabs.currentChanged.connect(lambda _i: self._charger_onglet_courant())
        return self.tabs

    def _build_statusbar(self) -> QtWidgets.QWidget:
        barre = QtWidgets.QWidget()
        barre.setFixedHeight(26)
        barre.setStyleSheet(f"border-top:1px solid {GRAY_BORDER}; background:transparent;")
        h = QtWidgets.QHBoxLayout(barre)
        h.setContentsMargins(14, 0, 14, 0)
        self.lbl_row_count = _make_label("0 lignes", F_SMALL, GRAY_TEXT)
        h.addWidget(self.lbl_row_count)
        h.addStretch(1)
        return barre

    # ── Chargement, filtres, indicateurs (R17 à R20) ─────────────────────────
    def charger(self, recalculer: bool = True):
        if recalculer:
            self.projet = projets.lire_projet(self.projet.dossier) or self.projet
            self._toutes_les_lignes = completion.lignes_de_suivi(self.projet)
        self._lignes_filtrees = completion.filtrer(self._toutes_les_lignes, self.filtres)
        self._maj_indicateurs(self._lignes_filtrees)
        self.lignes_par_onglet = {"Tous": list(self._lignes_filtrees)}
        for livrable in self.projet.livrables:
            self.lignes_par_onglet[livrable] = [
                ligne for ligne in self._lignes_filtrees if ligne.livrable == livrable
            ]
        self.setUpdatesEnabled(False)
        try:
            for nom, onglet in self.onglets_par_nom.items():
                onglet.load_rows(self.lignes_par_onglet.get(nom, []))
        finally:
            self.setUpdatesEnabled(True)
        self._charger_onglet_courant()
        self._maj_entetes_filtres()
        self._lbl_date.setText(datetime.now().strftime("%d/%m/%Y %H:%M"))

    def _maj_indicateurs(self, lignes: list[LigneSuivi]):
        valeurs = completion.indicateurs(lignes)
        for livrable, carte in (
            ("CE", self.kpi_ce),
            ("CECC", self.kpi_cecc),
            ("DPE", self.kpi_dpe),
        ):
            carte.set_value(f"{valeurs[livrable]} %", valeurs[livrable])

    def _charger_onglet_courant(self):
        nom = self.tabs.tabText(self.tabs.currentIndex())
        if nom not in self.onglets_par_nom:
            return
        self.lbl_row_count.setText(f"{len(self.lignes_par_onglet.get(nom, []))} lignes")
        self.detail_panel.clear()

    def _filtre_actif(self, colonne: str) -> bool:
        autorisees = self.filtres.get(colonne)
        if autorisees is None:
            return False
        return set(autorisees) != set(
            completion.valeurs_de_colonne(self._toutes_les_lignes, colonne)
        )

    def _maj_entetes_filtres(self):
        for onglet in self.onglets_par_nom.values():
            entete = onglet.table.horizontalHeader()
            if isinstance(entete, FilterableHeader):
                for c, (colonne, _) in _FILTRES.items():
                    entete.set_active(c, self._filtre_actif(colonne))

    def _sur_demande_filtre(self, colonne_tableau: int):
        if colonne_tableau in _FILTRES:
            self.ouvrir_filtre(*_FILTRES[colonne_tableau])

    def ouvrir_filtre(self, colonne: str, titre: str):
        valeurs = completion.valeurs_de_colonne(self._toutes_les_lignes, colonne)
        actuelles = self.filtres[colonne] or set(valeurs)
        fenetre = FilterPopup(title=titre, values=valeurs, checked_values=actuelles, parent=self)
        if fenetre.exec() == QtWidgets.QDialog.Accepted:
            self.appliquer_filtre(colonne, fenetre.get_checked_values())

    def appliquer_filtre(self, colonne: str, cochees: set[str]):
        valeurs = set(completion.valeurs_de_colonne(self._toutes_les_lignes, colonne))
        self.filtres[colonne] = None if cochees == valeurs else cochees
        self.charger(recalculer=False)

    def _sur_ligne_selectionnee(self, ligne: LigneSuivi):
        self.detail_panel.populate(ligne, completion.lignes_de_detail(ligne, self.projet.dossier))

    # ── Actions ───────────────────────────────────────────────────────────────
    def _onglet_courant(self) -> MainTab | None:
        return self.onglets_par_nom.get(self.tabs.tabText(self.tabs.currentIndex()))

    def _ouvrir_depot(self, mode: str = "import"):
        onglet = self._onglet_courant()
        if not onglet:
            return
        selection = onglet.selected_rows_data()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "Sélection", "Sélectionne au moins une ligne du tableau."
            )
            return
        refus = depot.verifier_selection([ligne.livrable for ligne in selection], mode)
        if refus:
            titre, message = refus
            if titre == "Applicabilité":
                QtWidgets.QMessageBox.information(self, titre, message)
            else:
                QtWidgets.QMessageBox.warning(self, titre, message)
            return
        from app.ui.dialogue_depot import DialogueDepot  # dialogue lourd : chargé à la demande

        fenetre = DialogueDepot(
            projet=self.projet,
            livrable=selection[0].livrable,
            cibles=[(ligne.fournisseur, ligne.reference) for ligne in selection],
            mode=mode,
            parent=self,
        )
        fenetre.documentSaved.connect(self.recharger)
        fenetre.exec()

    def recharger(self):
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.charger()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _parametrer(self):
        from app.ui.dialogue_projet import DialogueProjet

        frais = projets.lire_projet(self.projet.dossier)
        if not frais:
            QtWidgets.QMessageBox.warning(self, "Paramétrage", "Impossible de relire le projet.")
            return
        fenetre = DialogueProjet(self, projet=frais)
        if fenetre.exec() != QtWidgets.QDialog.Accepted or not fenetre.updated_project:
            return
        # Comme l'ancienne application, les onglets restent ceux de l'ouverture.
        self.projet = fenetre.updated_project
        self.charger()
        QtWidgets.QMessageBox.information(self, "Paramétrage", "Projet mis à jour.")

    def _exporter(self):
        try:
            resultats = export.exporter(self.projet.dossier)
        except Exception as e:  # message de l'export (fichier ouvert…) affiché tel quel
            QtWidgets.QMessageBox.critical(self, "Erreur export", str(e))
            return
        QtWidgets.QMessageBox.information(self, "Export terminé", export.message_de_fin(resultats))

    # ── Corrections depuis le panneau de détail (R21 à R23) ───────────────────
    def _oui(self, titre: str, question: str, avertissement: bool = False) -> bool:
        b = QtWidgets.QMessageBox.StandardButton
        boite = QtWidgets.QMessageBox.warning if avertissement else QtWidgets.QMessageBox.question
        return boite(self, titre, question, b.Yes | b.No, b.No) == b.Yes

    def _ouvrir_document(self, chemin: str):
        erreur = projets.ouvrir_document(Path(chemin))
        if erreur:
            titre, message = erreur
            if titre == "Fichier introuvable":
                QtWidgets.QMessageBox.warning(self, titre, message)
            else:
                QtWidgets.QMessageBox.critical(self, titre, message)

    def _signaler(self, erreurs: list[str]):
        for erreur in erreurs:
            QtWidgets.QMessageBox.warning(self, "Suppression du fichier", erreur)

    def _retirer_justificatif(self, ligne: LigneSuivi, code: str):
        f, r, dossier = ligne.fournisseur, ligne.reference, self.projet.dossier
        docs = corrections.documents_justifiant(dossier, f, r, ligne.livrable, code)
        if not docs:
            return
        if not self._oui(
            "Supprimer le justificatif", corrections.message_retrait(f, r, code, docs)
        ):
            return
        _, erreurs = corrections.retirer_exigences(dossier, docs, [code])
        self._signaler(erreurs)
        self._recharger_et_reselectionner(ligne)

    def _remplacer_justificatif(self, ligne: LigneSuivi, code: str):
        from app.ui.dialogue_depot import DialogueDepot

        fenetre = DialogueDepot(
            projet=self.projet,
            livrable=ligne.livrable,
            cibles=[(ligne.fournisseur, ligne.reference)],
            codes_coches=[code],
            parent=self,
        )
        if fenetre.exec() != QtWidgets.QDialog.Accepted:
            return
        # Le nouveau document remplace les anciens pour toutes les exigences qu'il couvre.
        _, erreurs = corrections.remplacer_apres_depot(
            self.projet.dossier, ligne.fournisseur, ligne.reference, fenetre.debut
        )
        self._signaler(erreurs)
        self._recharger_et_reselectionner(ligne)

    def _vider_reference(self, ligne: LigneSuivi):
        plan = corrections.preparer_vidage(
            self.projet.dossier,
            self.projet.numero_dossier,
            ligne.fournisseur,
            ligne.reference,
            ligne.livrable,
        )
        if plan.vide:
            QtWidgets.QMessageBox.information(self, "Supprimer la référence", plan.message_rien())
            return
        if not self._oui("Supprimer la référence", plan.message_confirmation(), True):
            return
        echecs = corrections.vider(self.projet.dossier, plan)
        if echecs:
            QtWidgets.QMessageBox.warning(
                self, "Suppression incomplète", corrections.message_echecs_vidage(echecs)
            )
        self._recharger_et_reselectionner(ligne)

    def _recharger_et_reselectionner(self, ligne: LigneSuivi):
        """Recharge le tableau puis réaffiche le détail de la même ligne."""
        self.recharger()
        cle = (ligne.fournisseur, ligne.reference, ligne.livrable)
        fraiche = next(
            (
                lg
                for lg in self._toutes_les_lignes
                if (lg.fournisseur, lg.reference, lg.livrable) == cle
            ),
            None,
        )
        if fraiche:
            self._sur_ligne_selectionnee(fraiche)
