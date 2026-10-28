"""Point d'entrée de NOX Manager.

Repris de `00_ancien/qt_main.py`.
"""

from __future__ import annotations

import sys

from PySide6 import QtGui, QtWidgets

from app.core.config import ressource
from app.models.projet import Projet
from app.ui.accueil import Accueil
from app.ui.dialogue_projet import DialogueProjet
from app.ui.tableau_de_suivi import FenetreSuivi
from app.ui.theme import appliquer_theme

try:  # écran de démarrage : présent seulement dans l'exécutable fabriqué
    import pyi_splash
except ImportError:
    pyi_splash = None


def _identifiant_windows() -> None:
    """Identifiant d'application dédié : Windows affiche la bonne icône dans la
    barre des tâches au lieu de celle de Python."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NOX_Manager.WikidocsQt.1")
    except Exception:  # noqa: S110 — sans conséquence : seule l'icône de la barre des tâches change
        pass


def _icone() -> QtGui.QIcon:
    try:
        return QtGui.QIcon(str(ressource("LOGO_Nox.ico")))
    except FileNotFoundError:
        return QtGui.QIcon()


def relier(accueil: Accueil, icone: QtGui.QIcon | None = None) -> list[FenetreSuivi]:
    """Accueil → tableau de suivi (ouverture) et dialogue de projet (création).

    Retourne la liste des tableaux ouverts, gardés en vie par l'appelant.
    """
    fenetres: list[FenetreSuivi] = []

    def ouvrir(projet: Projet):
        fenetre = FenetreSuivi(projet)
        if icone is not None and not icone.isNull():
            fenetre.setWindowIcon(icone)
        fenetre.showMaximized()
        fenetres[:] = [f for f in fenetres if f.isVisible()] + [fenetre]

    def creer():
        dialogue = DialogueProjet(accueil, etat=accueil.etat)
        dialogue.projectCreated.connect(accueil.ouvrir_projet)
        dialogue.exec()
        accueil.charger_projets_recents()

    accueil.projetOuvert.connect(ouvrir)
    accueil.nouveauProjetDemande.connect(creer)
    return fenetres


def run() -> int:
    _identifiant_windows()
    app = QtWidgets.QApplication(sys.argv)
    appliquer_theme(app)
    icone = _icone()
    if not icone.isNull():
        app.setWindowIcon(icone)

    accueil = Accueil()
    if not icone.isNull():
        accueil.setWindowIcon(icone)
    tableaux = relier(accueil, icone)  # noqa: F841 — gardés en vie pendant la session
    accueil.showMaximized()
    app.processEvents()

    if pyi_splash and pyi_splash.is_alive():
        pyi_splash.close()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
