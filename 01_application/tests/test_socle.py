from app._taches import verifier_couches
from app.core.config import reglages


def test_reglages_lisibles():
    assert reglages()["nom"] == "NOX Manager"


def test_les_couches_descendent():
    assert verifier_couches() == []
