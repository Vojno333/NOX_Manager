"""Tâche 10 : complétion et indicateurs (R17, R19, R20), comparés à la référence."""

from __future__ import annotations

import json

from app.dataaccess import projet_fichier
from app.services import completion
from tests.conftest import ATTENDU


def _lignes(projet_essai):
    return completion.lignes_de_suivi(projet_fichier.lire_projet(projet_essai))


def test_r17_r19_tableau_de_suivi_identique_a_la_reference(projet_essai):
    attendu = json.loads((ATTENDU / "tableau_de_suivi.json").read_text("utf-8"))
    lignes = _lignes(projet_essai)
    obtenu = [
        {
            "supplier": ligne.fournisseur,
            "reference": ligne.reference,
            "label": ligne.libelle,
            "mnp": ligne.mnp,
            "order_number": ligne.n_commande,
            "type": ligne.livrable,
            "completion": ligne.completion_texte,
        }
        for ligne in lignes
    ]
    assert obtenu == attendu["lignes"]
    kpi = {k: f"{v} %" for k, v in completion.indicateurs(lignes).items()}
    assert kpi == attendu["indicateurs"]


def test_r20_un_filtre_change_les_indicateurs(projet_essai):
    lignes = _lignes(projet_essai)
    filtrees = completion.filtrer(lignes, {"fournisseur": {"GAMMA"}, "livrable": None})
    assert {ligne.fournisseur for ligne in filtrees} == {"GAMMA"}
    assert completion.indicateurs(filtrees) == {"CE": 0, "CECC": 100, "DPE": 0}
    assert completion.valeurs_de_colonne(lignes, "livrable") == ["CE", "CECC", "DPE"]
    assert completion.filtrer(lignes, {"completion": {"100 %"}})[0].reference == "REF-030"


def test_repli_sur_les_dossiers_sans_articles(projet_essai):
    projet = projet_fichier.lire_projet(projet_essai)
    projet.articles = []
    couples = completion.couples_du_projet(projet)
    assert ("ACME", "REF-001") in couples and len(couples) == 6


def test_e5_une_estimation_vaut_un_valide(projet_essai):
    lignes = {(lg.reference, lg.livrable): lg for lg in _lignes(projet_essai)}
    # Machine couverte par un document et une estimation : 100 % (et non ½) ;
    # Basse tension applicable sans document : 0 → (1 + 0) / 2.
    assert lignes[("REF-002", "CE")].completion_texte == "50 %"
    # Ancienne fiche au statut « Estimation » : compte comme « Validé ».
    assert lignes[("REF-040", "CECC")].completion_texte == "100 %"
    # Relancé après Validé : toujours 0 %.
    assert lignes[("REF-010", "CECC")].completion_texte == "0 %"
