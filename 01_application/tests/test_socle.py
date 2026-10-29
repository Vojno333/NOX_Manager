import pytest

from app import _taches
from app._taches import verifier_couches
from app.core.config import reglages


def test_reglages_lisibles():
    assert reglages()["nom"] == "NOX Manager"


def test_les_couches_descendent():
    assert verifier_couches() == []


def test_une_couche_violee_fait_echouer_le_controle(tmp_path, monkeypatch):
    services = tmp_path / "01_application" / "app" / "services"
    services.mkdir(parents=True)
    (services / "fautif.py").write_text("from PySide6 import QtWidgets\n", "utf-8")
    monkeypatch.setattr(_taches, "RACINE", tmp_path)
    monkeypatch.setattr(_taches, "APP", tmp_path / "01_application" / "app")

    assert len(verifier_couches()) == 1
    with pytest.raises(SystemExit) as fin:
        _taches.couches()
    assert fin.value.code == 1
