"""Tâche 14 : écran d'accueil (R28, R29), hors écran."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.dataaccess.etat_utilisateur import EtatUtilisateur
from app.ui.accueil import Accueil


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_s24_r28_projets_recents_et_recherche(app, tmp_path, projet_essai):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    for i in range(11):
        etat.ajouter_projet_recent(f"AFF-{i}", tmp_path / f"p{i}", f"N{i}")
    accueil = Accueil(etat)
    assert accueil.liste.topLevelItemCount() == 10
    assert accueil.barre_etat.text() == "  🖥  10 projet(s) récent(s) chargé(s)."
    accueil.recherche.setText("n10")
    visibles = [
        accueil.liste.topLevelItem(i).text(0)
        for i in range(10)
        if not accueil.liste.topLevelItem(i).isHidden()
    ]
    assert visibles == ["N10"]


def test_r31_ouvrir_un_projet_existant(app, tmp_path, projet_essai):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    accueil = Accueil(etat)
    ouverts = []
    accueil.projetOuvert.connect(ouverts.append)
    accueil.ouvrir_dossier(projet_essai)
    assert ouverts[0].numero_dossier == "N999"
    assert accueil.liste.topLevelItem(0).text(0) == "N999"
    accueil.liste.setCurrentItem(accueil.liste.topLevelItem(0))
    assert accueil._references.valeur.text() == "6"
