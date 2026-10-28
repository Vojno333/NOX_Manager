"""Tâche 9 : créer, modifier, supprimer un projet (R1, R2, R4, R5, R6, R29)."""

from __future__ import annotations

import pytest

from app.dataaccess import base_projet, projet_fichier
from app.dataaccess.etat_utilisateur import EtatUtilisateur
from app.models.projet import Article
from app.services import projets as svc


def _saisie(tmp_path, **kw):
    valeurs = dict(
        nom="AFF-1",
        emplacement=str(tmp_path / "p"),
        numero_dossier="n123",
        date_code="28/10/2026",
        livrables=["CE", "DPE"],
        lignes=[Article("ACME", "REF-1", "Vis"), Article("BETA", "REF-2")],
    )
    valeurs.update(kw)
    return svc.SaisieProjet(**valeurs)


@pytest.mark.parametrize(
    ("champ", "valeur", "message"),
    [
        ("nom", " ", "Le Numéro de l'affaire est obligatoire."),
        ("emplacement", "", "L'emplacement est obligatoire."),
        ("numero_dossier", "", "Le numéro de dossier est obligatoire."),
        ("date_code", "2026-10-28", "La date doit être au format JJ/MM/AAAA (ex. 24/04/2026)."),
        ("livrables", [], "Sélectionnez au moins un livrable (CE, CECC ou DPE)."),
        ("lignes", [], "Ajoutez au moins une ligne avec un fournisseur et un N° de référence."),
    ],
)
def test_s1_r1_messages_de_refus(tmp_path, champ, valeur, message):
    assert svc.verifier(_saisie(tmp_path, **{champ: valeur})) == message


def test_s2_r2_ligne_incomplete_et_limite(tmp_path):
    lignes = [Article("A", "R1"), Article("", "", libelle="seul")]
    assert svc.verifier(_saisie(tmp_path, lignes=lignes)) == (
        "La ligne 2 est incomplète.\n\nLes champs obligatoires sont : Fournisseur et N° Référence."
    )
    trop = [Article("A", f"R{i}") for i in range(1001)]
    assert svc.verifier(_saisie(tmp_path, lignes=trop)) == (
        "Le nombre de dossiers à créer (1001) dépasse la limite autorisée de 1000."
    )
    assert svc.verifier(_saisie(tmp_path, lignes=[Article("", "")] + lignes[:1])) is None


def test_s4_r4_ecart_fournisseurs_references():
    assert svc.ecart_import_masse("A\nB\nC", "R1\nR2") == (
        "Le nombre de fournisseurs (3) et de références (2) ne correspondent pas."
        "\n\nContinuer quand même ?"
    )
    assert svc.ecart_import_masse("A\nB\n\n", "R1\nR2") is None


def test_s5_r4_colonnes_alignees_ligne_vide_ignoree():
    lignes = svc.lignes_import_masse("A\nB\n\nD", "R1\n\n\nR4", "L1\nL2\n\nL4", "", "C1")
    assert [(a.fournisseur, a.reference, a.libelle, a.n_commande) for a in lignes] == [
        ("A", "R1", "L1", "C1"),
        ("B", "", "L2", ""),
        ("D", "R4", "L4", ""),
    ]


def test_r4_import_sans_doublon_avec_l_existant():
    existantes = [Article("A", "R1")]
    importees = [Article("A", "R1"), Article("B", "R2"), Article("B", "R2")]
    assert [a.cle for a in svc.nouvelles_lignes(existantes, importees)] == [("B", "R2")]


def test_modele_csv(tmp_path):
    svc.ecrire_modele_csv(tmp_path / "m.csv")
    contenu = (tmp_path / "m.csv").read_bytes()
    entete = b"\xef\xbb\xbfFournisseur;Reference;Libelle;MNP;N_commande"
    # Fins de ligne du système, comme l'ancienne application (write_text).
    assert contenu.replace(b"\r\n", b"\n").startswith(entete + b"\nVisioParts;")


def test_r5_creer_projet(tmp_path):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    projet = svc.creer_projet(_saisie(tmp_path), etat)
    racine = tmp_path / "p"
    assert projet.numero_dossier == "N123" and projet.dossier == racine
    assert (racine / "BDD CE N123" / "Documents" / "ACME" / "REF-1").is_dir()
    assert (racine / "BDD DPE N123" / "BDD_DPE_N123.xlsx").is_file()
    assert not (racine / "BDD CECC N123").exists()
    assert etat.projets_recents()[0].chemin == str(racine.resolve())
    assert etat.emplacement_par_defaut() == str(tmp_path.resolve())


def test_s6_r6_retirer_un_article_avec_suppression(projet_essai):
    projet = projet_fichier.lire_projet(projet_essai)
    lignes = [a for a in projet.articles if a.cle != ("ACME", "REF-002")]
    saisie = svc.SaisieProjet(
        projet.nom, str(projet_essai), "n999", "28/10/2026", ["CE", "CECC", "DPE"], lignes
    )
    assert [a.cle for a in svc.articles_retires(projet, lignes)] == [("ACME", "REF-002")]
    nouveau = svc.modifier_projet(projet, saisie, supprimer_les_retires=True)
    assert nouveau.article("ACME", "REF-002") is None
    assert not (projet_essai / "BDD CE N999" / "Documents" / "ACME" / "REF-002").exists()
    assert (projet_essai / "BDD CE N999" / "Documents" / "ACME" / "REF-001").exists()
    assert all(e.reference != "REF-002" for e in base_projet.lire_tous(projet_essai))


def test_r6_retirer_un_article_en_conservant(projet_essai):
    projet = projet_fichier.lire_projet(projet_essai)
    lignes = [a for a in projet.articles if a.cle != ("ACME", "REF-002")]
    saisie = svc.SaisieProjet(projet.nom, "", "N999", "28/10/2026", ["CE"], lignes)
    svc.modifier_projet(projet, saisie)
    assert (projet_essai / "BDD CE N999" / "Documents" / "ACME" / "REF-002").exists()
    assert any(e.reference == "REF-002" for e in base_projet.lire_tous(projet_essai))
    assert projet_fichier.lire_projet(projet_essai).livrables == ["CE"]


def test_s25_s26_r29_retirer_des_recents_ou_supprimer(tmp_path):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    svc.creer_projet(_saisie(tmp_path), etat)
    racine = tmp_path / "p"
    svc.retirer_des_recents(racine, etat)
    assert etat.projets_recents() == [] and racine.exists()
    assert svc.ouvrir_projet(racine, etat).nom == "AFF-1"
    svc.supprimer_definitivement(racine, etat)
    assert not racine.exists() and etat.projets_recents() == []
    assert svc.ouvrir_projet(racine, etat) is None
