"""Tâche 2 : thème et géométrie des fenêtres (Qt hors écran)."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtGui, QtWidgets  # noqa: E402

from app.core.config import RACINE_DEPOT  # noqa: E402
from app.ui import theme  # noqa: E402
from app.ui.geometrie import ajuster_et_centrer  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_feuille_de_style_identique_a_l_ancienne():
    ancien = Path(RACINE_DEPOT, "00_ancien", "wikidocs_qt", "theme.py")
    if not ancien.exists():
        pytest.skip("00_ancien/ supprimé : la reprise est terminée")
    css = re.search(r'return """(.*?)"""', ancien.read_text("utf-8"), re.S).group(1)
    assert theme.FEUILLE_DE_STYLE == css


def test_appliquer_theme(app):
    theme.appliquer_theme(app)
    assert app.palette().color(QtGui.QPalette.ColorRole.Highlight).name() == "#2563eb"
    assert app.styleSheet() == theme.FEUILLE_DE_STYLE
    # Sous une feuille de style, Qt masque le nom du style : on la retire pour le lire.
    app.setStyleSheet("")
    assert app.style().name().lower() == "fusion"


def test_fenetre_reduite_a_l_ecran_et_centree(app):
    fenetre = QtWidgets.QWidget()
    dispo = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    ajuster_et_centrer(fenetre, dispo.width() * 3, dispo.height() * 3, 400, 300)
    assert fenetre.width() == int(dispo.width() * 0.92)
    assert fenetre.height() == int(dispo.height() * 0.92)
    assert dispo.contains(fenetre.geometry())
    assert fenetre.minimumWidth() == 400 and fenetre.minimumHeight() == 300


def test_petite_fenetre_garde_sa_taille(app):
    fenetre = QtWidgets.QWidget()
    ajuster_et_centrer(fenetre, 300, 200)
    assert (fenetre.width(), fenetre.height()) == (300, 200)
