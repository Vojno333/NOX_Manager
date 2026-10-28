"""Tâche 19 : dialogue de dépôt (R7 à R13), hors écran."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.dataaccess import base_projet, projet_fichier
from app.services import applicabilite as ap
from app.ui.dialogue_depot import DialogueDepot


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def messages(monkeypatch):
    vus = []
    for nom in ("information", "warning", "critical"):
        monkeypatch.setattr(
            QtWidgets.QMessageBox, nom, lambda _p, titre, texte, *a, **k: vus.append((titre, texte))
        )
    return vus


def _dialogue(projet_essai, livrable, cibles, mode="import"):
    projet = projet_fichier.lire_projet(projet_essai)
    return DialogueDepot(projet=projet, livrable=livrable, cibles=cibles, mode=mode)


def test_r10_r11_etats_existants_recharges(app, projet_essai):
    d = _dialogue(projet_essai, "CE", [("ACME", "REF-001")])
    etats = {row.code: row.get_state() for row in d._ce_page._req_rows}
    assert etats["2006/42/UE"] == ap.APPLICABLE and etats["2014/35/UE"] == ap.NA
    assert d.windowTitle() == "Importer un justificatif CE"


def test_s12_fiche_cecc_pre_remplie(app, projet_essai):
    d = _dialogue(projet_essai, "CECC", [("GAMMA", "REF-020")])
    champs = d._cecc_page.get_fields()
    assert champs["cecc_etat"] == "Validé" and champs["manufacturer_part_number"] == "MPN-GAMMA"


def test_s13_import_ce_depuis_le_dialogue(app, projet_essai, tmp_path, messages):
    fichier = tmp_path / "rapport.pdf"
    fichier.write_bytes(b"%PDF")
    d = _dialogue(projet_essai, "CE", [("ACME", "REF-001")])
    d._apply_file(fichier)
    machine = next(r for r in d._ce_page._req_rows if r.code == "2006/42/UE")
    machine.set_row_checked(True)
    assert d._build_final_filename() == "CE_ACME_REF-001.pdf"
    d._save_document()
    assert messages[-1] == ("Import terminé", "Les modifications ont été appliquées à 1 ligne(s).")
    assert (projet_essai / "BDD CE N999/Documents/ACME/REF-001/CE_ACME_REF-001 (1).pdf").is_file()


def test_s9_refus_affiche(app, projet_essai, tmp_path, messages):
    fichier = tmp_path / "rapport.pdf"
    fichier.write_bytes(b"%PDF")
    d = _dialogue(projet_essai, "CE", [("DELTA", "REF-030")])
    d._apply_file(fichier)
    machine = next(r for r in d._ce_page._req_rows if r.code == "2006/42/UE")
    machine.set_state(ap.APPLICABLE)
    machine.set_row_checked(True)
    avant = len(base_projet.lire_tous(projet_essai))
    d._save_document()
    titre, texte = messages[-1]
    assert titre == "Import" and "exigence(s) sont encore «Non défini(es)»" in texte
    assert len(base_projet.lire_tous(projet_essai)) == avant


def test_applicabilite_seule_sans_cecc(app, projet_essai):
    d = _dialogue(projet_essai, "CE", [("DELTA", "REF-030")], mode="applicability")
    assert [d.type_combo.itemText(i) for i in range(d.type_combo.count())] == ["CE", "DPE"]
    assert d.windowTitle() == "Gérer l'applicabilité CE"
