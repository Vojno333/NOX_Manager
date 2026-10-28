"""Tâche 7 : dossiers et fichiers du projet (R5, R13, R30)."""

from __future__ import annotations

from app.dataaccess import arborescence as arbo


def test_s3_r5_structure_creee(tmp_path):
    arbo.creer_structure(tmp_path, "N123", ["CE", "DPE"], [("ACME", "REF 1"), ("B:ETA", "R/2")])
    for t in ("CE", "DPE"):
        racine = tmp_path / f"BDD {t} N123"
        assert (racine / "Documents" / "ACME" / "REF 1").is_dir()
        assert (racine / "Documents" / "B_ETA" / "R_2").is_dir()
        excel = racine / f"BDD_{t}_N123.xlsx"
        assert excel.is_file() and excel.stat().st_size == 0
    assert not (tmp_path / "BDD CECC N123").exists()


def test_nettoyage_des_noms():
    assert arbo.nom_sur('  a<b>c:d"e/f\\g|h?i*j  ') == "a_b_c_d_e_f_g_h_i_j"
    assert arbo.nom_sur("A   B") == "A B"
    assert arbo.nom_sur_partie("A  B/C") == "A_B_C"


def test_r13_collision_de_noms(tmp_path):
    source = tmp_path / "rapport.pdf"
    source.write_bytes(b"x")
    cible = tmp_path / "BDD CE N1" / "Documents" / "ACME" / "REF-001"
    noms = [arbo.copier_document(source, cible, "CE_ACME_REF-001.pdf").name for _ in range(3)]
    assert noms == ["CE_ACME_REF-001.pdf", "CE_ACME_REF-001 (1).pdf", "CE_ACME_REF-001 (2).pdf"]
    assert source.exists()


def test_r30_chemin_relatif_en_slash(tmp_path):
    chemin = arbo.dossier_documents(tmp_path, "CE", "N1", "ACME", "REF") / "a.pdf"
    assert arbo.chemin_relatif(tmp_path, chemin) == "BDD CE N1/Documents/ACME/REF/a.pdf"


def test_r6_supprimer_dossiers_article(tmp_path):
    arbo.creer_structure(tmp_path, "N1", ["CE", "DPE"], [("A", "R1"), ("A", "R2"), ("B", "R3")])
    arbo.supprimer_dossiers_article(tmp_path, "N1", ["CE", "CECC", "DPE"], "B", "R3")
    arbo.supprimer_dossiers_article(tmp_path, "N1", ["CE", "CECC", "DPE"], "A", "R1")
    docs = tmp_path / "BDD CE N1" / "Documents"
    assert not (docs / "B").exists()
    assert not (docs / "A" / "R1").exists() and (docs / "A" / "R2").exists()


def test_couples_des_dossiers(tmp_path):
    arbo.creer_structure(tmp_path, "N1", ["DPE"], [("A", "R1"), ("B", "R2")])
    assert sorted(arbo.couples_des_dossiers(tmp_path, "N1", ["CE", "CECC", "DPE"])) == [
        ("A", "R1"),
        ("B", "R2"),
    ]
