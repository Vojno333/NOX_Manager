"""Ce que la personne a saisi dans le dialogue de dépôt."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

IMPORT = "import"
APPLICABILITE = "applicability"


@dataclass
class SaisieDepot:
    dossier: Path  # dossier du projet
    livrable: str  # CE, CECC ou DPE
    cibles: list[tuple[str, str]]  # articles (fournisseur, référence) concernés
    mode: str = IMPORT  # IMPORT : dépôt d'un document ; APPLICABILITE : applicabilité seule
    fichier: Path | None = None
    nom_saisi: str = ""  # nom final saisi ; vide → nom automatique
    # CE / DPE : état de chaque exigence de la page (code → NA, NON_DEFINI, APPLICABLE),
    # dans l'ordre d'affichage, et exigences cochées comme couvertes par le document.
    etats: dict[str, int] = field(default_factory=dict)
    coches: set[str] = field(default_factory=set)
    champs_cecc: dict[str, str] = field(default_factory=dict)
