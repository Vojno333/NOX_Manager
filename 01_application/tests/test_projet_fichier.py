"""Tâche 4 : fichier projet (R3, R31)."""

from __future__ import annotations

import json

from app.dataaccess import projet_fichier
from app.models.projet import Article, normaliser_articles, normaliser_livrables


def test_r31_ouvrir_le_projet_essai(fichier_projet_essai):
    projet = projet_fichier.lire_projet(fichier_projet_essai)
    assert (projet.nom, projet.numero_dossier, projet.date_code) == (
        "AFF-ESSAI",
        "N999",
        "28/10/2026",
    )
    assert projet.livrables == ["CE", "CECC", "DPE"]
    assert len(projet.articles) == 6


def test_r3_doublon_le_premier_gagne(fichier_projet_essai):
    projet = projet_fichier.lire_projet(fichier_projet_essai)
    acme = projet.article("ACME", "REF-001")
    assert acme.n_commande == "CMD-1"
    # Les lignes brutes gardent le doublon (lu par l'export, constat C6).
    assert [r["order_number"] for r in projet.lignes_brutes[:2]] == ["CMD-1", "CMD-1B"]


def test_r3_lignes_incompletes_retirees():
    articles = normaliser_articles(
        [{"supplier": " A ", "reference": "R1"}, {"supplier": "B"}, ["C", "R3"], ("", "R4")]
    )
    assert [a.cle for a in articles] == [("A", "R1"), ("C", "R3")]


def test_livrables_ordonnes_et_repli():
    assert normaliser_livrables(["dpe", "ce"]) == ["CE", "DPE"]
    assert normaliser_livrables([]) == ["CE", "CECC", "DPE"]
    assert normaliser_livrables(["X"]) == ["CE", "CECC", "DPE"]


def test_r31_ancien_fichier_lu_en_repli(tmp_path):
    (tmp_path / ".nox_project.json").write_text(
        json.dumps({"project_name": "A", "dossier_number": "N1", "rows": [["F", "R"]]}), "utf-8"
    )
    projet = projet_fichier.lire_projet(tmp_path)
    assert projet.articles == [Article("F", "R")]
    assert projet.livrables == ["CE", "CECC", "DPE"]


def test_dossier_sans_projet(tmp_path):
    assert projet_fichier.lire_projet(tmp_path) is None
    assert not (tmp_path / ".nox").exists()


def test_creer_puis_enregistrer_conserve_les_cles_inconnues(tmp_path):
    (tmp_path / ".nox_project.json").write_text("{}", "utf-8")
    projet = projet_fichier.creer_fichier_projet(
        tmp_path, "AFF", "N5", "01/01/2026", [Article("F", "R"), Article("F", "R")], ["DPE"]
    )
    assert not (tmp_path / ".nox_project.json").exists()
    assert projet.articles == [Article("F", "R")] and projet.livrables == ["DPE"]

    fichier = projet_fichier.chemin_fichier_projet(tmp_path)
    brut = json.loads(fichier.read_text("utf-8"))
    brut["cle_maison"] = 42
    fichier.write_text(json.dumps(brut), "utf-8")

    projet.nom = "AFF2"
    projet.articles.append(Article("G", "S", libelle="Écrou"))
    projet_fichier.enregistrer_projet(projet)
    relu = json.loads(fichier.read_text("utf-8"))
    assert relu["cle_maison"] == 42 and relu["project_name"] == "AFF2"
    assert relu["project_file_version"] == 3
    assert relu["rows"][1] == {
        "supplier": "G",
        "reference": "S",
        "label": "Écrou",
        "mnp": "",
        "order_number": "",
    }
    assert "Écrou" in fichier.read_text("utf-8")  # ensure_ascii=False
