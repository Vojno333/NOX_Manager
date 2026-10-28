"""Tâche 18 : tableau de suivi (R20, R24, R27), hors écran."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.dataaccess import projet_fichier
from app.ui.tableau_de_suivi import FenetreSuivi


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_tableau_du_projet_essai(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    assert fenetre.windowTitle() == "NOX_Manager — N999"
    assert [fenetre.tabs.tabText(i) for i in range(fenetre.tabs.count())] == [
        "Tous",
        "CE",
        "CECC",
        "DPE",
    ]
    tous = fenetre.onglets_par_nom["Tous"].table
    assert tous.rowCount() == 18
    assert fenetre.lbl_row_count.text() == "18 lignes"
    assert fenetre.onglets_par_nom["CE"].table.rowCount() == 6


def test_r20_un_filtre_change_les_indicateurs(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    assert fenetre.kpi_ce._value_lbl.text() == "39 %"
    fenetre.appliquer_filtre("fournisseur", {"EPS"})
    assert fenetre.kpi_ce._value_lbl.text() == "100 %"
    assert fenetre.onglets_par_nom["Tous"].table.rowCount() == 3
    assert fenetre._filtre_actif("fournisseur")
    fenetre.appliquer_filtre("fournisseur", {"ACME", "BETA", "DELTA", "EPS", "GAMMA"})
    assert fenetre.filtres["fournisseur"] is None
    assert fenetre.kpi_ce._value_lbl.text() == "39 %"


def test_r24_r27_export_depuis_le_tableau(app, projet_essai, monkeypatch):
    messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "information",
        lambda _p, titre, texte: messages.append((titre, texte)),
    )
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    fenetre._exporter()
    titre, texte = messages[-1]
    assert titre == "Export terminé" and texte.startswith("Fichiers exportés :")
    assert (projet_essai / "BDD CE N999" / "BDD_CE_N999.xlsx").stat().st_size > 0
