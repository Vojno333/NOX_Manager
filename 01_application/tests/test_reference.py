"""Tâche 16 : référence de comportement automatisée (R31, S27).

Sur une copie du projet d'essai, le nouveau code doit produire exactement
`tests/reference/attendu/` : tableau de suivi, exports Excel, arborescence.

Deux sources :
- « reconstruit » : le projet d'essai écrit par le nouveau code (toujours joué) ;
- « ancien » : une copie de `tests/reference/projet_essai`, écrit par l'ancienne
  application (`construire_reference.py`), quand il est présent sur le poste.
  Il prouve que le nouveau code lit les projets existants tels quels.
"""

from __future__ import annotations

import json
import shutil

import pytest

from app.dataaccess import projet_fichier
from app.services import completion, export
from tests.conftest import ATTENDU, RACINE_DEPOT, construire_projet_essai
from tests.test_export import relever

PROJET_ANCIEN = RACINE_DEPOT / "tests" / "reference" / "projet_essai"


def _attendu(nom: str):
    return json.loads((ATTENDU / nom).read_text("utf-8"))


@pytest.fixture(params=["reconstruit", "ancien"])
def projet(request, tmp_path):
    cible = tmp_path / "projet_essai"
    if request.param == "reconstruit":
        return construire_projet_essai(cible)
    if not (PROJET_ANCIEN / ".nox" / "nox_metadata.db").exists():
        pytest.skip("projet d'essai de l'ancienne application absent (construire_reference.py)")
    shutil.copytree(PROJET_ANCIEN, cible)
    for ancien_export in cible.glob("BDD */BDD_*.xlsx"):
        ancien_export.unlink()
    for archives in cible.glob("BDD */OLD"):
        shutil.rmtree(archives)
    return cible


def test_s27_r31_reference_complete(projet):
    # Tableau de suivi et indicateurs
    p = projet_fichier.lire_projet(projet)
    lignes = completion.lignes_de_suivi(p)
    obtenu = [
        {
            "supplier": ligne.fournisseur,
            "reference": ligne.reference,
            "label": ligne.libelle,
            "mnp": ligne.mnp,
            "order_number": ligne.n_commande,
            "type": ligne.livrable,
            "completion": ligne.completion_texte,
        }
        for ligne in lignes
    ]
    suivi = _attendu("tableau_de_suivi.json")
    assert obtenu == suivi["lignes"]
    assert {k: f"{v} %" for k, v in completion.indicateurs(lignes).items()} == suivi["indicateurs"]

    # Exports
    exports = _attendu("exports.json")
    resultats = export.exporter(projet)
    assert {c.name: relever(c, projet) for c, _ in resultats} == exports

    # Arborescence après l'export
    arborescence = sorted(
        c.relative_to(projet).as_posix() + ("/" if c.is_dir() else "")
        for c in projet.rglob("*")
        if ".nox" not in c.parts
    )
    assert arborescence == _attendu("arborescence.json")
