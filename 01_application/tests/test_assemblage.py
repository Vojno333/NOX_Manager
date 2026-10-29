"""Tâche 21 : assemblage accueil → tableau de suivi."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.dataaccess.etat_utilisateur import EtatUtilisateur
from app.main import relier
from app.ui.accueil import Accueil


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_ouvrir_un_projet_ouvre_son_tableau_de_suivi(app, tmp_path, projet_essai):
    accueil = Accueil(EtatUtilisateur(tmp_path / "e.json"))
    tableaux = relier(accueil)
    accueil.ouvrir_dossier(projet_essai)
    assert len(tableaux) == 1
    assert tableaux[0].windowTitle() == "NOX_Manager — N999"
    assert tableaux[0].kpi_ce._value_lbl.text() == "39 %"
    for t in tableaux:
        t.close()
