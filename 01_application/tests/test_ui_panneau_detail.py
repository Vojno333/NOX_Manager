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
        "introuvable": False,
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


def test_e7_vider_depuis_le_panneau(app, projet_essai, oui):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    fenetre._vider_reference(_ligne(fenetre, "BETA", "REF-010", "CE"))
    assert oui[0][0] == "Supprimer la référence"
    assert not (projet_essai / "BDD CE N999/Documents/BETA/REF-010/DPE_BETA_REF-010.pdf").exists()
    assert not (projet_essai / "BDD DPE N999/Documents/BETA/REF-010/DPE_BETA_REF-010.pdf").exists()
    for t in ("CE", "DPE"):
        assert _ligne(fenetre, "BETA", "REF-010", t).completion_texte == "0 %"


def test_e6_selection_de_plusieurs_exigences(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    fenetre._sur_ligne_selectionnee(_ligne(fenetre, "ACME", "REF-001", "CE"))
    table = fenetre.detail_panel._tbl_docs
    assert fenetre.detail_panel.codes_selectionnes(0) == ["2006/42/UE"]
    table.selectRow(0)
    mode = table.selectionModel().SelectionFlag
    table.selectionModel().select(table.model().index(4, 0), mode.Select | mode.Rows)
    assert fenetre.detail_panel.codes_selectionnes(4) == ["2006/42/UE", "2014/30/UE"]
    # Ligne cliquée hors sélection : elle seule.
    assert fenetre.detail_panel.codes_selectionnes(2) == ["2011/65/UE"]


def test_e6_clic_droit_sur_la_colonne_exigence(app, projet_essai):
    """E6 : après une sélection de deux exigences, le clic droit sur n'importe
    quelle colonne propose « Remplacer » ; rien sur une exigence sans document."""
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    fenetre._sur_ligne_selectionnee(_ligne(fenetre, "ACME", "REF-001", "CE"))
    panneau = fenetre.detail_panel
    table = panneau._tbl_docs
    table.selectRow(0)
    mode = table.selectionModel().SelectionFlag
    table.selectionModel().select(table.model().index(4, 0), mode.Select | mode.Rows)
    menu = panneau.menu_exigence(table.visualRect(table.model().index(4, 0)).center())
    assert "Remplacer le justificatif (2 exigences)…" in [a.text() for a in menu.actions()]
    table.clearSelection()
    assert panneau.menu_exigence(table.visualRect(table.model().index(2, 0)).center()) is None


def test_e12_fichier_disparu_signale(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    introuvables = completion.documents_introuvables(fenetre.projet)
    assert introuvables == {"BDD DPE N999/Documents/DELTA/REF-030/DPE_DELTA_REF-030.pdf"}
    fenetre._sur_introuvables(introuvables)
    table = fenetre.onglets_par_nom["DPE"].table
    textes = {table.item(r, 0).text(): table.item(r, 6) for r in range(table.rowCount())}
    assert textes["DELTA"].text() == "100 % ⚠"
    assert textes["DELTA"].toolTip() == "1 document(s) introuvable(s) sur le disque"
    assert textes["ACME"].text() == "0 %"
    fenetre.tabs.setCurrentIndex(3)
    assert "⚠ 1 document(s) introuvable(s)" in fenetre.lbl_row_count.text()
    ligne = _ligne(fenetre, "DELTA", "REF-030", "DPE")
    detail = completion.lignes_de_detail(ligne, projet_essai, introuvables)
    reach = next(d for d in detail if d["code"] == "1907/2006")
    assert reach["introuvable"] and reach["filename"] == "DPE_DELTA_REF-030.pdf"
    fenetre._sur_ligne_selectionnee(ligne)
    noms = [
        fenetre.detail_panel._tbl_docs.item(r, 2).text()
        for r in range(fenetre.detail_panel._tbl_docs.rowCount())
    ]
    assert "⚠ DPE_DELTA_REF-030.pdf (introuvable)" in noms
