"""Tâche 20 : panneau de détail (R21, R22, R23), hors écran."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.dataaccess import projet_fichier
from app.services import completion
from app.ui.tableau_de_suivi import FenetreSuivi


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def oui(monkeypatch):
    b = QtWidgets.QMessageBox.StandardButton
    vus = []

    def repondre(_p, titre, texte, *a, **k):
        vus.append((titre, texte))
        return b.Yes

    for nom in ("question", "warning", "information"):
        monkeypatch.setattr(QtWidgets.QMessageBox, nom, repondre)
    return vus


def _ligne(fenetre, f, r, t):
    return next(
        lg
        for lg in fenetre._toutes_les_lignes
        if (lg.fournisseur, lg.reference, lg.livrable) == (f, r, t)
    )


def test_detail_des_exigences(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    ligne = _ligne(fenetre, "ACME", "REF-001", "CE")
    detail = completion.lignes_de_detail(ligne, projet_essai)
    par_code = {d["code"]: d for d in detail}
    assert par_code["2006/42/UE"]["applicability"] == "Applicable"
    assert par_code["2006/42/UE"]["filename"] == "CE_ACME_REF-001.pdf"
    assert par_code["2014/35/UE"]["applicability"] == "Non applicable"
    assert par_code["2011/65/UE"] == {
        "code": "2011/65/UE",
        "requirement": "2011/65/UE | RoHS",
        "applicability": "Applicable",
        "filename": "",
        "path": "",
    }
    fenetre._sur_ligne_selectionnee(ligne)
    panneau = fenetre.detail_panel
    assert panneau._lbl_title.text() == "ACME  –  REF-001"
    assert panneau._tbl_docs.rowCount() == 6 and panneau._btn_delete.isEnabled()


def test_detail_cecc(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    detail = completion.lignes_de_detail(_ligne(fenetre, "EPS", "REF-040", "CECC"), projet_essai)
    statut = next(d for d in detail if d["requirement"] == "Statut CECC")
    assert statut["filename"] == "Estimation"


def test_s17_r21_retirer_depuis_le_panneau(app, projet_essai, oui):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    fenetre._retirer_justificatif(_ligne(fenetre, "ACME", "REF-001", "CE"), "2014/30/UE")
    assert oui[0][0] == "Supprimer le justificatif"
    assert _ligne(fenetre, "ACME", "REF-001", "CE").completion_texte == "33 %"


def test_s21_r23_vider_depuis_le_panneau(app, projet_essai, oui):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    fenetre._vider_reference(_ligne(fenetre, "BETA", "REF-010", "CE"))
    assert oui[0][0] == "Supprimer la référence"
    assert not (projet_essai / "BDD CE N999/Documents/BETA/REF-010/DPE_BETA_REF-010.pdf").exists()
    assert _ligne(fenetre, "BETA", "REF-010", "DPE").completion_texte == "50 %"
