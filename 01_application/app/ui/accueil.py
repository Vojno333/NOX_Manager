"""Écran d'accueil : projets récents, recherche, ouvrir, créer, supprimer.

Repris de `00_ancien/wikidocs_qt/home_window.py`. L'ouverture du tableau de
suivi et du dialogue de projet est reliée par `main.py` (signaux).
"""

from __future__ import annotations

import getpass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from app.core.format import date_lisible, taille_lisible
from app.models.projet import Projet
from app.services import projets
from app.ui.geometrie import ajuster_et_centrer
from app.ui.theme import STYLE_ACCUEIL

VERSION = "1.1.0"


def _icone_dossier(couleur: str = "#2563eb", taille: int = 18) -> QtGui.QPixmap:
    """Petit dossier dessiné au pinceau."""
    pm = QtGui.QPixmap(taille, taille)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    stylo = QtGui.QPen(QtGui.QColor(couleur))
    stylo.setWidthF(1.6)
    p.setPen(stylo)
    p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(1, 6, taille - 2, taille - 8, 2, 2)
    onglet = QtGui.QPainterPath()
    onglet.moveTo(1, 7)
    onglet.lineTo(1, 4)
    onglet.lineTo(7, 4)
    onglet.lineTo(9, 6)
    onglet.lineTo(taille - 1, 6)
    p.drawPath(onglet)
    p.end()
    return pm


def nom_utilisateur_windows() -> str:
    try:
        return getpass.getuser()
    except Exception:  # aucun nom disponible
        return "Utilisateur"


class LigneInfo(QtWidgets.QWidget):
    def __init__(self, libelle: str, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(8)
        self.cle = QtWidgets.QLabel(libelle, self)
        self.cle.setObjectName("infoKey")
        self.valeur = QtWidgets.QLabel("—", self)
        self.valeur.setObjectName("infoValue")
        self.valeur.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        lay.addWidget(self.cle)
        lay.addStretch(1)
        lay.addWidget(self.valeur)

    def set_valeur(self, valeur: str):
        self.valeur.setText(valeur or "—")

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QtGui.QPainter(self)
        p.setPen(QtGui.QColor("#f3f4f6"))
        p.drawLine(20, self.height() - 1, self.width() - 20, self.height() - 1)


class ChampRecherche(QtWidgets.QLineEdit):
    """Champ de recherche avec une loupe à gauche."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchBox")
        self.setPlaceholderText("Rechercher un projet…")
        self._loupe = QtWidgets.QLabel(self)
        self._loupe.setText("🔍")
        self._loupe.setStyleSheet("font-size:12px; color:#9ca3af; background:transparent;")
        self._loupe.move(8, 0)
        self._loupe.setFixedSize(20, 32)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._loupe.move(8, (self.height() - self._loupe.height()) // 2)


class Accueil(QtWidgets.QMainWindow):
    # Projet à ouvrir dans un tableau de suivi ; création demandée.
    projetOuvert = QtCore.Signal(object)
    nouveauProjetDemande = QtCore.Signal()
    # (clé projet, nb documents, taille) — émis depuis un fil de calcul.
    # Taille en « object » : un int Qt 32 bits déborderait au-delà de 2 Go.
    _statistiques_pretes = QtCore.Signal(str, int, object)

    def __init__(self, etat=None):
        super().__init__()
        self.setWindowTitle("NOX_Manager")
        ajuster_et_centrer(self, 1360, 860, largeur_min=1000, hauteur_min=620)
        self.setStyleSheet(STYLE_ACCUEIL)
        self.etat = etat or projets.etat_utilisateur()
        self._cache_stats: dict[str, tuple[int, int]] = {}
        self._stats_attendues = ""
        self._statistiques_pretes.connect(self._sur_statistiques)
        self._construire()
        self.charger_projets_recents()

    # ── Construction ──
    def _construire(self):
        central = QtWidgets.QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        racine = QtWidgets.QVBoxLayout(central)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.setSpacing(0)
        racine.addWidget(self._bandeau())
        contenu = QtWidgets.QWidget(self)
        lay = QtWidgets.QVBoxLayout(contenu)
        lay.setContentsMargins(28, 20, 28, 0)
        lay.setSpacing(16)
        lay.addLayout(self._ligne_actions())
        zone = QtWidgets.QHBoxLayout()
        zone.setSpacing(16)
        zone.addWidget(self._panneau_gauche(), 1)
        zone.addWidget(self._panneau_droit())
        lay.addLayout(zone, 1)
        racine.addWidget(contenu, 1)
        racine.addWidget(self._barre_d_etat())

    def _bandeau(self) -> QtWidgets.QFrame:
        cadre = QtWidgets.QFrame(self)
        cadre.setObjectName("heroFrame")
        cadre.setFixedHeight(80)
        lay = QtWidgets.QHBoxLayout(cadre)
        lay.setContentsMargins(32, 0, 32, 0)
        lay.setSpacing(0)
        gauche = QtWidgets.QVBoxLayout()
        gauche.setSpacing(2)
        titre = QtWidgets.QLabel("NOX_Manager", self)
        titre.setObjectName("heroTitle")
        sous_titre = QtWidgets.QLabel("Gestionnaire de projets documentaires", self)
        sous_titre.setObjectName("heroSubtitle")
        gauche.addWidget(titre)
        gauche.addWidget(sous_titre)
        lay.addLayout(gauche)
        lay.addStretch(1)
        droite = QtWidgets.QHBoxLayout()
        droite.setSpacing(20)
        version = QtWidgets.QLabel(f"ⓘ  Version {VERSION}", self)
        version.setObjectName("versionLabel")
        droite.addWidget(version)
        self.bouton_utilisateur = QtWidgets.QPushButton(
            f"👤  Utilisateur : {nom_utilisateur_windows()} ", self
        )
        self.bouton_utilisateur.setObjectName("userButton")
        droite.addWidget(self.bouton_utilisateur)
        lay.addLayout(droite)
        return cadre

    def _ligne_actions(self) -> QtWidgets.QHBoxLayout:
        ligne = QtWidgets.QHBoxLayout()
        ligne.setSpacing(12)
        self.bouton_nouveau = QtWidgets.QPushButton("  +  Nouveau projet", self)
        self.bouton_nouveau.setObjectName("primaryButton")
        self.bouton_nouveau.clicked.connect(self.nouveauProjetDemande.emit)
        self.bouton_ouvrir = QtWidgets.QPushButton("  🗁  Ouvrir un projet", self)
        self.bouton_ouvrir.setObjectName("outlineButton")
        self.bouton_ouvrir.clicked.connect(self._ouvrir_un_dossier)
        ligne.addWidget(self.bouton_nouveau)
        ligne.addWidget(self.bouton_ouvrir)
        ligne.addStretch(1)
        return ligne

    def _separateur(self, parent) -> QtWidgets.QFrame:
        sep = QtWidgets.QFrame(parent)
        sep.setObjectName("hLine")
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        return sep

    def _panneau_gauche(self) -> QtWidgets.QFrame:
        cadre = QtWidgets.QFrame(self)
        cadre.setObjectName("panelLeft")
        lay = QtWidgets.QVBoxLayout(cadre)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        entete = QtWidgets.QWidget(cadre)
        entete_lay = QtWidgets.QHBoxLayout(entete)
        entete_lay.setContentsMargins(20, 16, 16, 12)
        entete_lay.setSpacing(12)
        titre = QtWidgets.QLabel("Projets récents", cadre)
        titre.setObjectName("panelTitle")
        entete_lay.addWidget(titre)
        entete_lay.addStretch(1)
        self.recherche = ChampRecherche(cadre)
        self.recherche.textChanged.connect(self._filtrer)
        entete_lay.addWidget(self.recherche)
        lay.addWidget(entete)

        self.liste = QtWidgets.QTreeWidget(cadre)
        self.liste.setObjectName("projectTree")
        self.liste.setColumnCount(4)
        self.liste.setHeaderLabels(["Numéro de dossier", "Emplacement", "Dernière ouverture", ""])
        self.liste.setRootIsDecorated(False)
        self.liste.setAlternatingRowColors(True)
        self.liste.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.liste.setIndentation(0)
        self.liste.setUniformRowHeights(True)
        self.liste.itemDoubleClicked.connect(self._ouvrir_la_selection)
        self.liste.itemSelectionChanged.connect(self._sur_selection)
        entete_liste = self.liste.header()
        mode = QtWidgets.QHeaderView.ResizeMode
        entete_liste.setSectionResizeMode(0, mode.ResizeToContents)
        entete_liste.setSectionResizeMode(1, mode.Stretch)
        entete_liste.setSectionResizeMode(2, mode.ResizeToContents)
        entete_liste.setSectionResizeMode(3, mode.Fixed)
        entete_liste.resizeSection(3, 36)
        entete_liste.setStretchLastSection(False)
        lay.addWidget(self.liste, 1)

        astuce = QtWidgets.QLabel("  ⓘ  Double-cliquez sur un projet pour l'ouvrir", cadre)
        astuce.setObjectName("hintLabel")
        lay.addWidget(self._separateur(cadre))
        lay.addWidget(astuce)
        lay.addWidget(self._separateur(cadre))

        pied = QtWidgets.QWidget(cadre)
        pied_lay = QtWidgets.QHBoxLayout(pied)
        pied_lay.setContentsMargins(16, 10, 16, 14)
        pied_lay.setSpacing(10)
        self.bouton_ouvrir_recent = QtWidgets.QPushButton("  🗁  Ouvrir", cadre)
        self.bouton_ouvrir_recent.setObjectName("openFooterButton")
        self.bouton_ouvrir_recent.clicked.connect(self._ouvrir_la_selection)
        self.bouton_actualiser = QtWidgets.QPushButton("  ↻  Actualiser", cadre)
        self.bouton_actualiser.setObjectName("ghostButton")
        self.bouton_actualiser.clicked.connect(self.charger_projets_recents)
        self.bouton_supprimer = QtWidgets.QPushButton("  🗑  Supprimer", cadre)
        self.bouton_supprimer.setObjectName("dangerButton")
        self.bouton_supprimer.clicked.connect(self._supprimer_la_selection)
        self.etat_pied = QtWidgets.QLabel("Aucun projet sélectionné", cadre)
        self.etat_pied.setObjectName("footerStatus")
        for b in (self.bouton_ouvrir_recent, self.bouton_actualiser, self.bouton_supprimer):
            pied_lay.addWidget(b)
        pied_lay.addStretch(1)
        pied_lay.addWidget(self.etat_pied)
        lay.addWidget(pied)
        return cadre

    def _panneau_droit(self) -> QtWidgets.QFrame:
        cadre = QtWidgets.QFrame(self)
        cadre.setObjectName("panelRight")
        cadre.setFixedWidth(310)
        lay = QtWidgets.QVBoxLayout(cadre)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        titre = QtWidgets.QLabel("Informations projet", cadre)
        titre.setObjectName("infoPanelTitle")
        lay.addWidget(titre)
        lay.addWidget(self._separateur(cadre))

        self.pile_infos = QtWidgets.QStackedWidget(cadre)
        vide = QtWidgets.QWidget()
        vide_lay = QtWidgets.QVBoxLayout(vide)
        vide_lay.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vide_lay.setSpacing(12)
        icone = QtWidgets.QLabel(vide)
        icone.setFixedSize(72, 72)
        icone.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("background:#eff6ff; border-radius:36px; font-size:28px;")
        icone.setText("🗁")
        vide_titre = QtWidgets.QLabel("Sélectionnez un projet", vide)
        vide_titre.setObjectName("infoPlaceholderTitle")
        vide_titre.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vide_sous = QtWidgets.QLabel("Les informations détaillées\ns'afficheront ici.", vide)
        vide_sous.setObjectName("infoPlaceholderSub")
        vide_sous.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vide_lay.addStretch(1)
        vide_lay.addWidget(icone, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        vide_lay.addWidget(vide_titre)
        vide_lay.addWidget(vide_sous)
        vide_lay.addStretch(1)
        self.pile_infos.addWidget(vide)

        details = QtWidgets.QWidget()
        details_lay = QtWidgets.QVBoxLayout(details)
        details_lay.setContentsMargins(0, 0, 0, 0)
        details_lay.setSpacing(0)
        self._cree_le = LigneInfo("Créé le :", details)
        self._ouvert_le = LigneInfo("Dernière ouverture :", details)
        self._references = LigneInfo("Références :", details)
        self._documents = LigneInfo("Documents :", details)
        self._taille = LigneInfo("Taille du projet :", details)
        for ligne in (self._cree_le, self._ouvert_le, self._references, self._documents):
            details_lay.addWidget(ligne)
        details_lay.addWidget(self._taille)
        details_lay.addStretch(1)
        self.pile_infos.addWidget(details)
        lay.addWidget(self.pile_infos, 1)
        return cadre

    def _barre_d_etat(self) -> QtWidgets.QWidget:
        barre = QtWidgets.QWidget(self)
        lay = QtWidgets.QHBoxLayout(barre)
        lay.setContentsMargins(32, 0, 32, 12)
        self.barre_etat = QtWidgets.QLabel("", barre)
        self.barre_etat.setObjectName("statusBar")
        lay.addWidget(self.barre_etat)
        return barre

    # ── Projets récents (R28) ──
    def charger_projets_recents(self):
        self.liste.clear()
        self.pile_infos.setCurrentIndex(0)
        recents = self.etat.projets_recents()
        for p in recents:
            numero = p.numero_dossier or p.nom or "Projet sans nom"
            item = QtWidgets.QTreeWidgetItem([numero, p.chemin, date_lisible(p.ouvert_le), "⋮"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, p)
            item.setIcon(0, QtGui.QIcon(_icone_dossier("#2563eb", 18)))
            item.setForeground(1, QtGui.QColor("#6b7280"))
            item.setTextAlignment(3, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.liste.addTopLevelItem(item)
        self.etat_pied.setText("Aucun projet sélectionné")
        self.barre_etat.setText(f"  🖥  {len(recents)} projet(s) récent(s) chargé(s).")

    def _filtrer(self, texte: str):
        texte = texte.lower()
        for i in range(self.liste.topLevelItemCount()):
            item = self.liste.topLevelItem(i)
            p = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            visible = (
                texte in item.text(0).lower()
                or texte in item.text(1).lower()
                or texte in str(p.nom if p else "").lower()
            )
            item.setHidden(not visible)

    def _recent_selectionne(self):
        item = self.liste.currentItem()
        return item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item else None

    def _sur_selection(self):
        recent = self._recent_selectionne()
        if recent is None:
            self.pile_infos.setCurrentIndex(0)
            self.etat_pied.setText("Aucun projet sélectionné")
            return
        self.etat_pied.setText(self.liste.currentItem().text(0))
        self._afficher_infos(recent)

    def _afficher_infos(self, recent):
        dossier = Path(recent.chemin) if recent.chemin else None
        projet = projets.lire_projet(dossier) if dossier else None
        self._cree_le.set_valeur(
            date_lisible(projet.donnees.get("created_at", "")) if projet else "—"
        )
        self._ouvert_le.set_valeur(date_lisible(recent.ouvert_le))
        self._references.set_valeur(str(len(projet.articles)) if projet else "—")
        self.pile_infos.setCurrentIndex(1)
        if not projet:
            self._documents.set_valeur("—")
            self._taille.set_valeur("—")
            return
        # Parcours du disque en arrière-plan : plusieurs secondes sur le partage.
        cle = str(dossier)
        connu = self._cache_stats.get(cle)
        suffixe = "  (actualisation…)"
        self._documents.set_valeur(f"{connu[0]}{suffixe}" if connu else "Calcul…")
        self._taille.set_valeur(f"{taille_lisible(connu[1])}{suffixe}" if connu else "Calcul…")
        self._stats_attendues = cle
        QtCore.QThreadPool.globalInstance().start(
            lambda: self._statistiques_pretes.emit(cle, *projets.statistiques_disque(dossier))
        )

    def _sur_statistiques(self, cle: str, nb_documents: int, taille: int):
        self._cache_stats[cle] = (nb_documents, taille)
        if cle != self._stats_attendues:
            return  # la sélection a changé entre-temps
        self._documents.set_valeur(str(nb_documents))
        self._taille.set_valeur(taille_lisible(taille))

    # ── Actions ──
    def _ouvrir_un_dossier(self):
        depart = self.etat.emplacement_par_defaut() or str(Path.home())
        dossier = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choisir un dossier projet NOX_Manager", depart
        )
        if dossier:
            self.ouvrir_dossier(Path(dossier))

    def _ouvrir_la_selection(self, *_):
        recent = self._recent_selectionne()
        if recent is None:
            QtWidgets.QMessageBox.information(
                self, "Ouvrir un projet", "Sélectionne un projet dans la liste."
            )
            return
        if recent.chemin:
            self.ouvrir_dossier(Path(recent.chemin))

    def ouvrir_dossier(self, dossier: Path):
        """Ouvre le projet du dossier (R31) et le fait passer en tête des récents."""
        try:
            projet = projets.ouvrir_projet(dossier, self.etat)
        except Exception as e:  # erreur disque ou réseau : affichée telle quelle
            QtWidgets.QMessageBox.critical(
                self, "Erreur d'ouverture", f"Impossible d'ouvrir le projet.\n\n{e}"
            )
            return
        if projet is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Projet invalide",
                "Le dossier sélectionné ne contient pas de fichier .nox_project.json valide.",
            )
            return
        self.ouvrir_projet(projet)

    def ouvrir_projet(self, projet: Projet):
        self.projetOuvert.emit(projet)
        self.barre_etat.setText(f"  🖥  Projet ouvert : {projet.nom or projet.dossier.name}")
        self.charger_projets_recents()

    def _supprimer_la_selection(self):
        recent = self._recent_selectionne()
        if recent is None:
            QtWidgets.QMessageBox.information(
                self, "Supprimer", "Sélectionne un projet dans la liste."
            )
            return
        nom = self.liste.currentItem().text(0)
        if not recent.chemin:
            return
        dossier = Path(recent.chemin)
        choix = self._demander_suppression(nom)
        if choix == "annuler":
            return
        if choix == "retirer":
            projets.retirer_des_recents(dossier, self.etat)
        elif self._confirmer_suppression(dossier):
            try:
                projets.supprimer_definitivement(dossier, self.etat)
            except OSError as e:
                QtWidgets.QMessageBox.critical(
                    self, "Erreur de suppression", f"Impossible de supprimer le dossier.\n\n{e}"
                )
                return
        self.charger_projets_recents()
        self.etat_pied.setText("Aucun projet sélectionné")
        self.barre_etat.setText(f"  🗑  Projet traité : {nom}")

    def _demander_suppression(self, nom: str) -> str:
        """Trois choix (R29) : « retirer », « supprimer » ou « annuler »."""
        boite = QtWidgets.QMessageBox(self)
        boite.setWindowTitle("Gestion du projet")
        boite.setText(f"Que souhaitez-vous faire avec ce projet ?\n\nProjet : {nom}")
        boite.setInformativeText(
            "• Retirer des projets récents\n"
            "  Le projet restera sur le disque.\n\n"
            "• Supprimer définitivement le dossier\n"
            "  Le projet sera supprimé du disque.\n"
            "  Cette action est irréversible."
        )
        role = QtWidgets.QMessageBox.ButtonRole
        retirer = boite.addButton("Retirer des projets récents", role.AcceptRole)
        supprimer = boite.addButton("Supprimer définitivement", role.DestructiveRole)
        annuler = boite.addButton("Annuler", role.RejectRole)
        boite.setDefaultButton(annuler)
        boite.exec()
        clic = boite.clickedButton()
        return {retirer: "retirer", supprimer: "supprimer"}.get(clic, "annuler")

    def _confirmer_suppression(self, dossier: Path) -> bool:
        b = QtWidgets.QMessageBox.StandardButton
        reponse = QtWidgets.QMessageBox.warning(
            self,
            "Confirmation requise",
            f"Voulez-vous vraiment supprimer définitivement le dossier :\n\n{dossier}\n\n"
            "Cette action est irréversible.",
            b.Yes | b.No,
            b.No,
        )
        return reponse == b.Yes
