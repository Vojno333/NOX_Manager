"""Projet et articles.

Repris de `v1-avant-refonte:wikidocs_qt/project_manager.py` (`_normalize_rows`,
`_normalize_enabled_bdds`).
"""

from __future__ import annotations

import uuid
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
    id_ligne: str = ""  # E1 : identifiant stable de la ligne (lignes multiples activées)

    @property
    def cle(self) -> tuple[str, str]:
        return (self.fournisseur, self.reference)

    @property
    def contenu(self) -> tuple[str, str, str, str, str]:
        """La ligne entière : ce qui doit être unique quand les lignes multiples sont activées."""
        return (self.fournisseur, self.reference, self.libelle, self.mnp, self.n_commande)

    def vers_dict(self) -> dict:
        """Forme enregistrée dans `project.json` → `rows`."""
        return {
            "supplier": self.fournisseur,
            "reference": self.reference,
            "label": self.libelle,
            "mnp": self.mnp,
            "order_number": self.n_commande,
        } | ({"line_id": self.id_ligne} if self.id_ligne else {})

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
                id_ligne=str(ligne.get("line_id", "") or "").strip(),
            )
        return cls(fournisseur=str(ligne[0]).strip(), reference=str(ligne[1]).strip())


def normaliser_articles(lignes, multiples: bool = False) -> list[Article]:
    """Articles sans fournisseur ou sans référence retirés.

    Sans lignes multiples : en cas de doublon fournisseur / référence, la première
    ligne gagne (R3). Avec (E1, décision 0005) : seules les lignes strictement
    identiques sont fusionnées, et chaque ligne reçoit un identifiant stable.
    """
    articles: list[Article] = []
    vus: set[tuple] = set()
    for ligne in lignes or []:
        article = ligne if isinstance(ligne, Article) else Article.depuis_ligne(ligne)
        cle = article.contenu if multiples else article.cle
        if not article.fournisseur or not article.reference or cle in vus:
            continue
        vus.add(cle)
        if multiples and not article.id_ligne:
            article.id_ligne = uuid.uuid4().hex[:8]
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
        """Première ligne de l'article."""
        return next((a for a in self.articles if a.cle == (fournisseur, reference)), None)

    def lignes_de(self, fournisseur: str, reference: str) -> list[Article]:
        """Toutes les lignes de l'article, dans l'ordre du projet (E1)."""
        return [a for a in self.articles if a.cle == (fournisseur, reference)]
