"""Jeu d'essai partagé : `tests/reference/projet_essai`, reconstruit sans l'ancien code.

Les articles et les enregistrements viennent de
`tests/reference/construire_reference.py` (source unique) ; seul l'outil
d'écriture change : le nouveau code au lieu de l'ancien.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

from app.core.config import RACINE_DEPOT

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_spec = importlib.util.spec_from_file_location(
    "construire_reference", RACINE_DEPOT / "tests" / "reference" / "construire_reference.py"
)
reference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reference)

ATTENDU = RACINE_DEPOT / "tests" / "reference" / "attendu"


def ecrire_fichier_projet_essai(racine):
    """`.nox/project.json` et dossiers d'articles du projet d'essai."""
    (racine / ".nox").mkdir(parents=True)
    donnees = {
        "project_name": reference.AFFAIRE,
        "project_path": str(racine),
        "dossier_number": reference.DOSSIER,
        "date_code": "28/10/2026",
        "created_at": "2026-01-01T08:00:00",
        "updated_at": "2026-01-01T08:00:00",
        "project_meta_dir": ".nox",
        "project_file_version": 3,
        "rows": reference.ROWS,
        "enabled_bdds": ["CE", "CECC", "DPE"],
    }
    (racine / ".nox" / "project.json").write_text(
        json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for t in ("CE", "CECC", "DPE"):
        for row in reference.ROWS:
            dossier = racine / f"BDD {t} {reference.DOSSIER}" / "Documents"
            (dossier / row["supplier"] / row["reference"]).mkdir(parents=True, exist_ok=True)
    return racine


@pytest.fixture
def fichier_projet_essai(tmp_path):
    return ecrire_fichier_projet_essai(tmp_path / "projet_essai")


def construire_projet_essai(racine):
    """Projet d'essai complet : fichier projet, base et documents (sauf le fichier disparu)."""
    from app.dataaccess import base_projet
    from app.models.enregistrement import Enregistrement

    ecrire_fichier_projet_essai(racine)
    base_projet.initialiser(racine)
    for rec in reference._records():
        base_projet.ajouter(racine, Enregistrement.depuis_dict(rec))
        if rec["relative_path"] and rec["stored_filename"] not in reference.MISSING_FILES:
            f = racine / rec["relative_path"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"%PDF-1.4\n% document d'essai NOX\n")
    return racine


@pytest.fixture
def projet_essai(tmp_path):
    return construire_projet_essai(tmp_path / "projet_essai")
