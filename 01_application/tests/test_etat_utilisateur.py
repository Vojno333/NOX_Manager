"""Tâche 6 : préférences de l'utilisateur (R28)."""

from __future__ import annotations

from app.dataaccess.etat_utilisateur import EtatUtilisateur


def test_r28_onzieme_projet_le_plus_ancien_sort(tmp_path):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    for i in range(11):
        etat.ajouter_projet_recent(f"AFF-{i}", tmp_path / f"p{i}", f"N{i}")
    recents = etat.projets_recents()
    assert len(recents) == 10
    assert recents[0].nom == "AFF-10" and recents[-1].nom == "AFF-1"


def test_r28_rouvrir_remonte_en_tete_sans_doublon(tmp_path):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    etat.ajouter_projet_recent("A", tmp_path / "a")
    etat.ajouter_projet_recent("B", tmp_path / "b")
    etat.ajouter_projet_recent("A", tmp_path / "a")
    assert [p.nom for p in etat.projets_recents()] == ["A", "B"]
    etat.retirer_projet_recent(tmp_path / "a")
    assert [p.nom for p in etat.projets_recents()] == ["B"]


def test_emplacements_et_emplacement_par_defaut(tmp_path):
    etat = EtatUtilisateur(tmp_path / "etat.json")
    etat.ajouter_emplacement_recent(tmp_path / "x")
    etat.ajouter_emplacement_recent(tmp_path / "y")
    assert etat.emplacements_recents() == [str(tmp_path / "y"), str(tmp_path / "x")]
    assert etat.emplacement_par_defaut() == str(tmp_path / "y")


def test_fichier_corrompu_valeurs_par_defaut(tmp_path):
    fichier = tmp_path / "etat.json"
    fichier.write_text("{pas du json", "utf-8")
    etat = EtatUtilisateur(fichier)
    assert etat.projets_recents() == [] and etat.emplacement_par_defaut() == ""
    etat.ajouter_projet_recent("A", tmp_path / "a")
    assert len(etat.projets_recents()) == 1
