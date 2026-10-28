"""Tâche 37 : E1 (1/2), lignes multiples d'un même article — données (décision 0005)."""

from __future__ import annotations

import json

from app.dataaccess import arborescence, base_projet, projet_fichier
from app.dataaccess.etat_utilisateur import EtatUtilisateur
from app.models.enregistrement import Enregistrement
from app.models.projet import Article, normaliser_articles
from app.services import lignes
from app.services import projets as svc


def test_e1_sans_activation_r3_inchangee():
    articles = normaliser_articles(
        [Article("A", "R", n_commande="1"), Article("A", "R", n_commande="2")]
    )
    assert len(articles) == 1 and articles[0].id_ligne == ""


def test_e1_unicite_sur_la_ligne_complete():
    articles = normaliser_articles(
        [
            Article("A", "R", n_commande="1"),
            Article("A", "R", n_commande="2"),
            Article("A", "R", n_commande="1"),  # strictement identique : fusionnée
        ],
        multiples=True,
    )
    assert [a.n_commande for a in articles] == ["1", "2"]
    assert all(len(a.id_ligne) == 8 for a in articles)
    assert articles[0].id_ligne != articles[1].id_ligne


def test_e1_sous_dossiers():
    a = [
        Article("A", "R", n_commande="CMD-1"),
        Article("A", "R", n_commande="CMD-2"),
        Article("B", "S", n_commande="X"),
        Article("C", "T", n_commande="7"),
        Article("C", "T", n_commande="7"),
        Article("C", "T"),
        Article("C", "T"),
    ]
    assert arborescence.sous_dossiers(a) == ["CMD-1", "CMD-2", "", "7_1", "7_2", "_1", "_2"]


def test_e1_identifiants_conserves(lignes_multiples, fichier_projet_essai):
    projet = projet_fichier.lire_projet(fichier_projet_essai)
    acme = projet.lignes_de("ACME", "REF-001")
    assert [a.n_commande for a in acme] == ["CMD-1", "CMD-1B"]
    projet_fichier.enregistrer_projet(projet)
    brut = json.loads(projet_fichier.chemin_fichier_projet(fichier_projet_essai).read_text("utf-8"))
    ids = [r["line_id"] for r in brut["rows"]]
    relu = projet_fichier.lire_projet(fichier_projet_essai)
    assert [a.id_ligne for a in relu.articles] == ids


def test_e1_rattachement_des_enregistrements(lignes_multiples, fichier_projet_essai):
    projet = projet_fichier.lire_projet(fichier_projet_essai)
    premiere, seconde = projet.lignes_de("ACME", "REF-001")
    ancien = Enregistrement("ACME", "REF-001", "CE")  # sans identifiant : 1re ligne
    nouveau = Enregistrement("ACME", "REF-001", "CE", id_ligne=seconde.id_ligne)
    assert lignes.appartient(ancien, projet, premiere)
    assert not lignes.appartient(ancien, projet, seconde)
    assert lignes.appartient(nouveau, projet, seconde)
    assert not lignes.appartient(nouveau, projet, premiere)
    # Un article sur une seule ligne s'enregistre sans identifiant (ancienne application).
    assert lignes.id_a_enregistrer(projet, projet.article("BETA", "REF-010")) == ""
    assert lignes.id_a_enregistrer(projet, seconde) == seconde.id_ligne
    assert lignes.sous_dossier(projet, seconde) == "CMD-1B"
    assert lignes.sous_dossier(projet, projet.article("BETA", "REF-010")) == ""


def test_e1_creer_un_projet_avec_deux_lignes(lignes_multiples, tmp_path):
    saisie = svc.SaisieProjet(
        "AFF",
        str(tmp_path / "p"),
        "N1",
        "28/10/2026",
        ["CE"],
        [Article("A", "R", n_commande="C1"), Article("A", "R", n_commande="C2"), Article("B", "S")],
    )
    projet = svc.creer_projet(saisie, EtatUtilisateur(tmp_path / "e.json"))
    docs = tmp_path / "p" / "BDD CE N1" / "Documents"
    assert (docs / "A" / "R" / "C1").is_dir() and (docs / "A" / "R" / "C2").is_dir()
    assert (docs / "B" / "S").is_dir() and not any((docs / "B" / "S").iterdir())
    assert len(projet.articles) == 3


def test_e1_retirer_une_seule_ligne(lignes_multiples, projet_essai):
    projet = projet_fichier.lire_projet(projet_essai)
    premiere, seconde = projet.lignes_de("ACME", "REF-001")
    base_projet.ajouter(
        projet_essai, Enregistrement("ACME", "REF-001", "CE", id_ligne=seconde.id_ligne)
    )
    sous = arborescence.dossier_documents(projet_essai, "CE", "N999", "ACME", "REF-001", "CMD-1B")
    sous.mkdir(parents=True)
    restantes = [a for a in projet.articles if a is not seconde]
    saisie = svc.SaisieProjet(projet.nom, "", "N999", "28/10/2026", projet.livrables, restantes)
    assert svc.articles_retires(projet, restantes) == [seconde]
    nouveau = svc.modifier_projet(projet, saisie, supprimer_les_retires=True)
    assert len(nouveau.lignes_de("ACME", "REF-001")) == 1
    enrs = [e for e in base_projet.lire_tous(projet_essai) if e.reference == "REF-001"]
    assert len(enrs) == 1 and enrs[0].id_ligne == ""  # celui de la 1re ligne est gardé
    assert not sous.exists()
    assert (projet_essai / "BDD CE N999/Documents/ACME/REF-001/CE_ACME_REF-001.pdf").is_file()
