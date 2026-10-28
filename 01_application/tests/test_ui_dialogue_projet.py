"""Tâche 15 : dialogue de projet (R1 à R6), hors écran."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.dataaccess import projet_fichier
from app.dataaccess.etat_utilisateur import EtatUtilisateur
from app.ui.dialogue_projet import DialogueProjet


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _remplir(d: DialogueProjet, tmp_path):
    d.project_name_edit.setText("AFF-1")
    d.location_edit.setText(str(tmp_path / "p"))
    d.dossier_number_edit.setText("n123")
    d.date_code_edit.setText("28/10/2026")
    d.ce_checkbox.setChecked(True)
    d._rows[0].supplier_edit.setText("ACME")
    d._rows[0].ref_edit.setText("REF-1")


def test_s1_refus_affiche_le_message_du_service(app, tmp_path):
    d = DialogueProjet(etat=EtatUtilisateur(tmp_path / "e.json"))
    assert d._validate() == (False, "Le Numéro de l'affaire est obligatoire.")
    _remplir(d, tmp_path)
    d.date_code_edit.setText("2026-10-28")
    assert d._validate()[1] == "La date doit être au format JJ/MM/AAAA (ex. 24/04/2026)."


def test_s3_creation_depuis_le_dialogue(app, tmp_path):
    etat = EtatUtilisateur(tmp_path / "e.json")
    d = DialogueProjet(etat=etat)
    _remplir(d, tmp_path)
    crees = []
    d.projectCreated.connect(crees.append)
    d._create_project()
    assert crees and crees[0].numero_dossier == "N123"
    assert (tmp_path / "p" / "BDD CE N123" / "Documents" / "ACME" / "REF-1").is_dir()


def test_s5_import_en_masse(app, tmp_path, monkeypatch):
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *a, **k: None)
    d = DialogueProjet(etat=EtatUtilisateur(tmp_path / "e.json"))
    d._bulk_supplier_edit.setPlainText("A\nB\n\nD")
    d._bulk_ref_edit.setPlainText("R1\nR2\n\nR4")
    d._import_bulk_rows()
    remplies = [r.get_data()["supplier"] for r in d._rows if r.is_filled()]
    assert remplies == ["A", "B", "D"]


def test_mode_modification(app, tmp_path, projet_essai):
    projet = projet_fichier.lire_projet(projet_essai)
    d = DialogueProjet(projet=projet, etat=EtatUtilisateur(tmp_path / "e.json"))
    assert d.windowTitle() == "Paramétrage du projet — NOX_Manager"
    assert d.create_button.text() == "Enregistrer les modifications"
    assert sum(1 for r in d._rows if r.is_filled()) == 6
    assert d.project_name_edit.isReadOnly()
