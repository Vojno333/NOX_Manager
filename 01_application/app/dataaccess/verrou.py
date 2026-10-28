"""Verrou de modification d'un projet : `.nox/verrou.json` (décision 0004, E14)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.models.verrou import Verrou

FICHIER_VERROU = "verrou.json"


def chemin_verrou(dossier: Path) -> Path:
    return dossier / ".nox" / FICHIER_VERROU


def lire(dossier: Path) -> Verrou | None:
    """Verrou en place, ou None (absent ou illisible)."""
    try:
        d = json.loads(chemin_verrou(dossier).read_text(encoding="utf-8"))
        return Verrou(d["utilisateur"], d["poste"], d["depuis"], d["rafraichi"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _contenu(verrou: Verrou) -> bytes:
    donnees = {
        "utilisateur": verrou.utilisateur,
        "poste": verrou.poste,
        "depuis": verrou.depuis,
        "rafraichi": verrou.rafraichi,
    }
    return json.dumps(donnees, indent=2, ensure_ascii=False).encode("utf-8")


def creer(dossier: Path, verrou: Verrou) -> bool:
    """Crée le verrou s'il n'existe pas ; False si quelqu'un l'a créé avant."""
    fichier = chemin_verrou(dossier)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(fichier, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "wb") as f:
        f.write(_contenu(verrou))
    return True


def ecrire(dossier: Path, verrou: Verrou) -> None:
    """Réécrit le verrou (signe de vie, ou reprise d'un verrou abandonné)."""
    chemin_verrou(dossier).write_bytes(_contenu(verrou))


def supprimer(dossier: Path) -> None:
    chemin_verrou(dossier).unlink(missing_ok=True)
