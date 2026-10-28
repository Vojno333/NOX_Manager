"""Tâche 11 : export Excel (R24 à R27), comparé à la référence."""

from __future__ import annotations

import json
import sys

import pytest
from openpyxl import load_workbook

from app.services import export
from tests.conftest import ATTENDU


def relever(chemin, racine) -> dict:
    """Même relevé que `construire_reference.relever_exports`."""
    ws = load_workbook(chemin).worksheets[0]
    cellules = {}
    for row in ws.iter_rows():
        for c in row:
            if c.value is None and not c.hyperlink:
                continue
            v = {"valeur": c.value}
            if c.hyperlink:
                v["lien"] = (c.hyperlink.target or "").replace(racine.as_posix(), "<PROJET>")
            cellules[c.coordinate] = v
    return {"onglet": ws.title, "cellules": cellules}


def test_r24_r27_exports_identiques_a_la_reference(projet_essai):
    attendu = json.loads((ATTENDU / "exports.json").read_text("utf-8"))
    resultats = export.exporter(projet_essai)
    assert [p.name for p, _ in resultats] == list(attendu)
    assert all(archive is None for _, archive in resultats)
    for chemin, _ in resultats:
        assert relever(chemin, projet_essai) == attendu[chemin.name], chemin.name


def test_s22_r27_deux_exports_de_suite(projet_essai):
    export.exporter(projet_essai)
    resultats = export.exporter(projet_essai)
    for chemin, archive in resultats:
        assert archive.parent == chemin.parent / "OLD"
        assert archive.name.startswith(chemin.stem + "_V_") and archive.suffix == ".xlsx"
    message = export.message_de_fin(resultats)
    assert message.startswith("Fichiers exportés :\n\n")
    assert "Anciennes versions déplacées dans OLD :" in message


@pytest.mark.skipif(sys.platform != "win32", reason="verrou de fichier Windows")
def test_s23_r27_export_ouvert_rien_n_est_ecrit(projet_essai):
    import ctypes

    export.exporter(projet_essai)
    ce = projet_essai / "BDD CE N999" / "BDD_CE_N999.xlsx"
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.restype = ctypes.c_void_p
    # Ouverture exclusive, comme Excel : aucun partage autorisé.
    poignee = kernel32.CreateFileW(str(ce), 0x80000000, 0, None, 3, 0, None)
    try:
        with pytest.raises(PermissionError) as erreur:
            export.exporter(projet_essai)
        assert "Impossible d'archiver l'ancien export" in str(erreur.value)
        assert "fermez-le puis relancez l'export." in str(erreur.value)
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(poignee))
    assert not (ce.parent / "OLD").exists()
    assert not (projet_essai / "BDD CECC N999" / "OLD").exists()


def test_e8_colonnes_d_et_h_distinctes_en_cecc(projet_essai):
    (cecc,) = [c for c, _ in export.exporter(projet_essai) if "CECC" in c.name]
    cellules = relever(cecc, projet_essai)["cellules"]
    # GAMMA : D = MNP de l'article, H = MPN de la fiche.
    assert cellules["D10"]["valeur"] == "MNP-020" and cellules["H10"]["valeur"] == "MPN-GAMMA"
    # EPS : pas de MNP saisi → D vide, même si la fiche a un MPN.
    assert "D9" not in cellules and cellules["H9"]["valeur"] == "MPN-EPS"
    # ACME / REF-001 : pas de fiche → H vide.
    assert cellules["D5"]["valeur"] == "MNP-001" and "H5" not in cellules


def test_e9_titre_et_onglet_au_numero_de_dossier(projet_essai):
    for chemin, _ in export.exporter(projet_essai):
        releve = relever(chemin, projet_essai)
        livrable = chemin.name.split("_")[1]
        assert releve["onglet"] == f"BDD {livrable} N999"
        assert releve["cellules"]["B2"]["valeur"] == f"BASE DE DONNEES {livrable} - N999"


def test_e11_chaque_export_pointe_vers_son_dossier(projet_essai):
    exports = {c.name: relever(c, projet_essai) for c, _ in export.exporter(projet_essai)}
    lien_ce = exports["BDD_CE_N999.xlsx"]["cellules"]["J7"]["lien"]
    lien_dpe = exports["BDD_DPE_N999.xlsx"]["cellules"]["H7"]["lien"]
    # Liens relatifs à l'export (E13) : chacun vise la copie de son propre dossier.
    assert lien_ce == lien_dpe == "Documents/BETA/REF-010/DPE_BETA_REF-010.pdf"


def test_e13_liens_relatifs_valables_apres_deplacement(projet_essai, tmp_path):
    import shutil

    export.exporter(projet_essai)
    deplace = tmp_path / "ailleurs" / "projet renommé"
    shutil.move(str(projet_essai), str(deplace))
    ce = deplace / "BDD CE N999" / "BDD_CE_N999.xlsx"
    ws = load_workbook(ce).worksheets[0]
    cible = ws["H5"].hyperlink.target
    assert not cible.startswith(("<", "/")) and ":" not in cible
    assert (ce.parent / cible).is_file()


def test_e13_liens_de_l_export_archive_toujours_valables(projet_essai):
    export.exporter(projet_essai)
    (_, archive), *_ = export.exporter(projet_essai)
    cible = load_workbook(archive).worksheets[0]["H5"].hyperlink.target
    assert cible.startswith("../Documents/")
    assert (archive.parent / cible).resolve().is_file()
