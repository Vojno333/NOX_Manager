"""Contenu d'un export Excel, décidé par les services et écrit par `dataaccess`."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Cellule:
    valeur: object
    lien: Path | None = None  # fichier ciblé par le lien hypertexte


@dataclass
class ContenuExport:
    livrable: str
    sortie: Path
    titre: str
    onglet: str
    # Une liste par ligne du tableau : (colonne, cellule), dans l'ordre d'écriture.
    lignes: list[list[tuple[str, Cellule]]] = field(default_factory=list)
