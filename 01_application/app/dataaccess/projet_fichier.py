"""Lecture et écriture de `.nox/project.json` (version 3), repli sur l'ancien `.nox_project.json`.

Repris de `v1-avant-refonte:wikidocs_qt/project_manager.py` (`load_project`,
`save_project`, `create_project_file`).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.models.projet import Article, Projet, normaliser_articles, normaliser_livrables

DOSSIER_CACHE = ".nox"
FICHIER_PROJET = "project.json"
ANCIEN_FICHIER_PROJET = ".nox_project.json"
VERSION_FICHIER = 3


def chemin_fichier_projet(dossier: Path) -> Path:
    return dossier / DOSSIER_CACHE / FICHIER_PROJET


def est_un_projet(dossier: Path) -> bool:
    return chemin_fichier_projet(dossier).is_file() or (dossier / ANCIEN_FICHIER_PROJET).is_file()


def _ecrire(dossier: Path, donnees: dict) -> Path:
    fichier = chemin_fichier_projet(dossier)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")
    return fichier


def _lire_brut(dossier: Path) -> dict | None:
    for fichier in (chemin_fichier_projet(dossier), dossier / ANCIEN_FICHIER_PROJET):
        if not fichier.exists():
            continue
        try:
            return json.loads(fichier.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return None


def _vers_projet(dossier: Path, brut: dict) -> Projet:
    lignes = brut.get("rows") or []
    donnees = dict(brut)
    donnees.setdefault("project_path", str(dossier.resolve()))
    donnees.setdefault("project_file_version", VERSION_FICHIER)
    articles = normaliser_articles(lignes)
    livrables = normaliser_livrables(brut.get("enabled_bdds"))
    donnees["rows"] = [a.vers_dict() for a in articles]
    donnees["enabled_bdds"] = livrables
    return Projet(
        dossier=dossier,
        nom=str(brut.get("project_name", "")),
        numero_dossier=str(brut.get("dossier_number", "")),
        date_code=str(brut.get("date_code", "")),
        articles=articles,
        livrables=livrables,
        lignes_brutes=[
            ligne if isinstance(ligne, dict) else Article.depuis_ligne(ligne).vers_dict()
            for ligne in lignes
        ],
        donnees=donnees,
    )


def lire_projet(dossier: Path) -> Projet | None:
    """Projet du dossier, ou None si aucun fichier projet lisible."""
    brut = _lire_brut(dossier)
    return _vers_projet(dossier, brut) if brut is not None else None


def creer_fichier_projet(
    dossier: Path,
    nom: str,
    numero_dossier: str,
    date_code: str,
    articles: list[Article],
    livrables: list[str],
) -> Projet:
    """Écrit un nouveau `project.json` et retire l'ancien fichier s'il existe."""
    dossier.mkdir(parents=True, exist_ok=True)
    maintenant = datetime.now().isoformat()
    _ecrire(
        dossier,
        {
            "project_name": nom,
            "project_path": str(dossier.resolve()),
            "dossier_number": numero_dossier,
            "date_code": date_code,
            "created_at": maintenant,
            "updated_at": maintenant,
            "project_meta_dir": DOSSIER_CACHE,
            "project_file_version": VERSION_FICHIER,
            "rows": [a.vers_dict() for a in normaliser_articles(articles)],
            "enabled_bdds": normaliser_livrables(livrables),
        },
    )
    ancien = dossier / ANCIEN_FICHIER_PROJET
    if ancien.exists():
        try:
            ancien.unlink()
        except OSError:
            pass
    return lire_projet(dossier)


def enregistrer_projet(projet: Projet) -> Projet:
    """Fusionne le projet dans le fichier existant (clés inconnues conservées)."""
    existant = _lire_brut(projet.dossier) or {}
    existant = _vers_projet(projet.dossier, existant).donnees if existant else {}
    donnees = dict(existant)
    donnees.update(
        {
            "project_name": projet.nom,
            "dossier_number": projet.numero_dossier,
            "date_code": projet.date_code,
            "rows": [a.vers_dict() for a in normaliser_articles(projet.articles)],
            "enabled_bdds": normaliser_livrables(projet.livrables),
            "project_path": str(projet.dossier.resolve()),
            "updated_at": datetime.now().isoformat(),
            "project_file_version": max(int(existant.get("project_file_version", 2)), 3),
        }
    )
    _ecrire(projet.dossier, donnees)
    return lire_projet(projet.dossier)
