"""Projet et articles.

Repris de `v1-avant-refonte:wikidocs_qt/project_manager.py` (`_normalize_rows`,
`_normalize_enabled_bdds`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .referentiel import LIVRABLES


@dataclass
class Article:
    """Une ligne du projet : un couple fournisseur / référence et ses compléments."""

    fournisseur: str
    reference: str
    libelle: str = ""
    mnp: str = ""
    n_commande: str = ""

    @property
    def cle(self) -> tuple[str, str]:
        return (self.fournisseur, self.reference)

    def vers_dict(self) -> dict:
        """Forme enregistrée dans `project.json` → `rows`."""
        return {
            "supplier": self.fournisseur,
            "reference": self.reference,
            "label": self.libelle,
            "mnp": self.mnp,
            "order_number": self.n_commande,
        }

    @classmethod
    def depuis_ligne(cls, ligne) -> Article:
        """Une ligne de `rows` : un dictionnaire, ou un couple (fournisseur, référence)."""
        if isinstance(ligne, dict):
            return cls(
                fournisseur=str(ligne.get("supplier", "")).strip(),
                reference=str(ligne.get("reference", "")).strip(),
                libelle=str(ligne.get("label", "")).strip(),
                mnp=str(ligne.get("mnp", "")).strip(),
                n_commande=str(ligne.get("order_number", "")).strip(),
            )
        return cls(fournisseur=str(ligne[0]).strip(), reference=str(ligne[1]).strip())


def normaliser_articles(lignes) -> list[Article]:
    """Articles sans fournisseur ou sans référence retirés ; en cas de doublon
    fournisseur / référence, la première ligne gagne (R3)."""
    articles: list[Article] = []
    vus: set[tuple[str, str]] = set()
    for ligne in lignes or []:
        article = ligne if isinstance(ligne, Article) else Article.depuis_ligne(ligne)
        if not article.fournisseur or not article.reference or article.cle in vus:
            continue
        vus.add(article.cle)
        articles.append(article)
    return articles


def normaliser_livrables(valeurs) -> list[str]:
    """Livrables dans l'ordre CE, CECC, DPE ; aucun valide → les trois."""
    demandes = [str(v).strip().upper() for v in (valeurs or LIVRABLES)]
    ordonnes = [t for t in LIVRABLES if t in demandes]
    return ordonnes or list(LIVRABLES)


@dataclass
class Projet:
    """Un projet, tel que décrit par `.nox/project.json`."""

    dossier: Path
    nom: str  # n° d'affaire (`project_name`)
    numero_dossier: str
    date_code: str = ""
    articles: list[Article] = field(default_factory=list)
    livrables: list[str] = field(default_factory=lambda: list(LIVRABLES))
    # Lignes telles qu'écrites dans le fichier, doublons compris : l'export
    # les lit directement (constat C6).
    lignes_brutes: list[dict] = field(default_factory=list)
    # Contenu complet du fichier, pour conserver les clés inconnues à l'enregistrement.
    donnees: dict = field(default_factory=dict)

    def dossier_livrable(self, livrable: str) -> Path:
        return self.dossier / f"BDD {livrable} {self.numero_dossier}"

    def article(self, fournisseur: str, reference: str) -> Article | None:
        return next((a for a in self.articles if a.cle == (fournisseur, reference)), None)
