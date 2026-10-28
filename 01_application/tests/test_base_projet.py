"""Tâche 5 : base des enregistrements (R31)."""

from __future__ import annotations

import sqlite3

from app.dataaccess import base_projet
from app.models.enregistrement import Enregistrement


def test_r31_lecture_du_projet_essai(projet_essai):
    enrs = base_projet.lire_tous(projet_essai)
    assert len(enrs) == 14
    acme1 = [e for e in enrs if (e.fournisseur, e.reference) == ("ACME", "REF-001")]
    assert len(acme1) == 1 and acme1[0].codes_couverts == ["2006/42/UE", "2014/30/UE"]
    # Ordre : fournisseur, référence, puis du plus récent au plus ancien.
    acme2 = [e.depose_le for e in enrs if e.reference == "REF-002"]
    assert acme2 == sorted(acme2, reverse=True)
    assert base_projet.chemin_base(projet_essai).exists()


def test_applicabilite_seule_sans_fichier(projet_essai):
    eps = base_projet.lire_derniers(projet_essai, "EPS", "REF-040", "ce")
    assert len(eps) == 1 and not eps[0].a_un_fichier and len(eps[0].codes_na) == 6


def test_derniere_fiche_cecc(projet_essai):
    fiche = base_projet.derniere_fiche_cecc(projet_essai, "GAMMA", "REF-020")
    assert fiche["cecc_etat"] == "Validé" and fiche["manufacturer_part_number"] == "MPN-GAMMA"
    assert base_projet.derniere_fiche_cecc(projet_essai, "ACME", "REF-001") == {}


def test_modifier_detacher_supprimer(tmp_path):
    i = base_projet.ajouter(
        tmp_path,
        Enregistrement(
            "F",
            "R",
            "CE",
            ["CE"],
            ["A"],
            ["A"],
            nom_stocke="x.pdf",
            chemin_relatif="BDD CE N1/x.pdf",
            depose_le="2026-01-01T00:00:00",
        ),
    )
    base_projet.modifier_listes_de_codes(tmp_path, i, {"codes_couverts": [], "inconnu": ["x"]})
    base_projet.detacher_fichier(tmp_path, i)
    (enr,) = base_projet.lire_tous(tmp_path)
    assert enr.codes_couverts == [] and enr.libelles_couverts == ["A"]
    assert (enr.nom_stocke, enr.chemin_relatif) == ("", "") and not enr.a_un_fichier

    base_projet.ajouter(tmp_path, Enregistrement("G", "S", "DPE", depose_le="2026-01-02"))
    base_projet.supprimer_pour_articles(tmp_path, [("F", "R")])
    assert [(e.fournisseur, e.reference) for e in base_projet.lire_tous(tmp_path)] == [("G", "S")]
    base_projet.supprimer(tmp_path, [base_projet.lire_tous(tmp_path)[0].id])
    assert base_projet.lire_tous(tmp_path) == []


def test_migration_tolerante_d_une_ancienne_base(tmp_path):
    fichier = base_projet.chemin_base(tmp_path)
    fichier.parent.mkdir()
    conn = sqlite3.connect(fichier)
    conn.execute(
        "CREATE TABLE uploaded_documents (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "supplier TEXT NOT NULL, reference TEXT NOT NULL, source_justification_type TEXT "
        "NOT NULL, stored_in_bdds_json TEXT NOT NULL, requirement_codes_json TEXT NOT NULL, "
        "requirement_labels_json TEXT NOT NULL, cecc_fields_json TEXT NOT NULL, "
        "original_filename TEXT NOT NULL, stored_filename TEXT NOT NULL, "
        "relative_path TEXT NOT NULL, uploaded_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO uploaded_documents VALUES (1,'F','R','CE','[\"CE\"]','[]','[]','{}',"
        "'a.pdf','a.pdf','p/a.pdf','2025-01-01')"
    )
    conn.commit()
    conn.close()
    (enr,) = base_projet.lire_tous(tmp_path)
    assert enr.codes_na == [] and enr.codes_applicables == [] and enr.a_un_fichier
