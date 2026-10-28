"""Lignes multiples d'un même article (E1, décision 0005).

Un enregistrement appartient à la ligne dont il porte l'identifiant ; sans
identifiant, il appartient à la première ligne de son couple fournisseur /
référence (enregistrements existants, ou faits par l'ancienne application).
"""

from __future__ import annotations

from app.dataaccess import arborescence
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
