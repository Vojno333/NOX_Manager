"""Lignes multiples d'un même article (E1, décision 0005).

Un enregistrement appartient à la ligne dont il porte l'identifiant ; sans
identifiant, il appartient à la première ligne de son couple fournisseur /
référence (enregistrements existants, ou faits par l'ancienne application).
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import lignes_multiples
from app.dataaccess import arborescence, base_projet, projet_fichier
from app.models.enregistrement import Enregistrement
from app.models.projet import Article, Projet


def _meme_ligne(a: Article, b: Article) -> bool:
    if a.id_ligne and b.id_ligne:
        return a.id_ligne == b.id_ligne
    return a is b or a.contenu == b.contenu


def est_premiere(projet: Projet, article: Article) -> bool:
    lignes = projet.lignes_de(article.fournisseur, article.reference)
    return not lignes or _meme_ligne(lignes[0], article)


def appartient(enr: Enregistrement, projet: Projet, article: Article) -> bool:
    """L'enregistrement est-il celui de cette ligne ?"""
    if (enr.fournisseur, enr.reference) != article.cle:
        return False
    if enr.id_ligne:
        return enr.id_ligne == article.id_ligne
    return est_premiere(projet, article)


def id_a_enregistrer(projet: Projet, article: Article) -> str:
    """Identifiant à mettre sur un nouvel enregistrement : vide tant que l'article
    n'a qu'une ligne, pour rester lisible par l'ancienne application."""
    if len(projet.lignes_de(article.fournisseur, article.reference)) < 2:
        return ""
    return article.id_ligne


def sous_dossier(projet: Projet, article: Article) -> str:
    """Sous-dossier de la ligne sous `<F>/<R>/` ; vide pour un article sur une seule ligne."""
    for a, nom in zip(projet.articles, arborescence.sous_dossiers(projet.articles), strict=True):
        if _meme_ligne(a, article):
            return nom
    return ""


def ligne_cible(projet: Projet, fournisseur: str, reference: str, id_ligne: str = ""):
    """La ligne d'identifiant `id_ligne`, sinon la première ligne de l'article."""
    lignes = projet.lignes_de(fournisseur, reference)
    if id_ligne:
        trouvee = next((a for a in lignes if a.id_ligne == id_ligne), None)
        if trouvee:
            return trouvee
    return lignes[0] if lignes else None


def enregistrements_de_la_ligne(
    dossier: Path, fournisseur: str, reference: str, id_ligne: str = ""
) -> list[Enregistrement]:
    """Enregistrements de l'article ; avec les lignes multiples, ceux de la ligne seulement."""
    enrs = [
        e
        for e in base_projet.lire_tous(dossier)
        if (e.fournisseur, e.reference) == (fournisseur, reference)
    ]
    if not lignes_multiples():
        return enrs
    projet = projet_fichier.lire_projet(dossier)
    article = ligne_cible(projet, fournisseur, reference, id_ligne) if projet else None
    if article is None:
        return enrs
    return [e for e in enrs if appartient(e, projet, article)]


def sous_dossier_de(dossier: Path, fournisseur: str, reference: str, id_ligne: str = "") -> str:
    if not lignes_multiples():
        return ""
    projet = projet_fichier.lire_projet(dossier)
    article = ligne_cible(projet, fournisseur, reference, id_ligne) if projet else None
    return sous_dossier(projet, article) if article else ""
