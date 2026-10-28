"""Dossiers et fichiers d'un projet : `BDD <type> <n°>/Documents/<F>/<R>/`.

Repris de `v1-avant-refonte:wikidocs_qt/project_structure.py`,
`upload_document_dialog.py` (`_safe_name_part`, `_unique_target_path`,
`_target_folders_for`) et `new_project_dialog.py` (création des dossiers).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

_INTERDITS = '<>:"/\\|?*'


def nom_sur(valeur: str) -> str:
    """Caractères interdits → `_`, espaces multiples réduits (noms de dossiers)."""
    nettoye = "".join("_" if c in _INTERDITS else c for c in str(valeur or "").strip())
    return " ".join(nettoye.split())


def nom_sur_partie(valeur: str) -> str:
    """Comme `nom_sur`, espaces → `_` (morceau d'un nom de fichier automatique)."""
    return nom_sur(valeur).replace(" ", "_")


def dossier_livrable(dossier_projet: Path, livrable: str, numero_dossier: str) -> Path:
    return dossier_projet / f"BDD {livrable} {numero_dossier}"


def dossier_documents(
    dossier_projet: Path, livrable: str, numero_dossier: str, fournisseur: str, reference: str
) -> Path:
    """Dossier où sont rangés les documents d'un article.

    Comme l'ancienne application, les noms saisis sont utilisés tels quels
    ici, alors que la création de la structure les nettoie (`nom_sur`).
    """
    docs = dossier_livrable(dossier_projet, livrable, numero_dossier) / "Documents"
    return docs / fournisseur / reference


def nom_export(livrable: str, numero_dossier: str) -> str:
    return f"BDD_{livrable}_{numero_dossier}.xlsx"


def creer_structure(
    dossier_projet: Path,
    numero_dossier: str,
    livrables: Iterable[str],
    articles: Iterable[tuple[str, str]],
) -> None:
    """Pour chaque livrable : son dossier, `Documents/`, le fichier Excel vide
    s'il n'existe pas, et un dossier par fournisseur et par référence (R5)."""
    articles = list(articles)
    dossier_projet.mkdir(parents=True, exist_ok=True)
    for livrable in livrables:
        racine = dossier_livrable(dossier_projet, livrable, numero_dossier)
        docs = racine / "Documents"
        docs.mkdir(parents=True, exist_ok=True)
        excel = racine / nom_export(livrable, numero_dossier)
        if not excel.exists():
            excel.touch()
        for fournisseur, reference in articles:
            f, r = nom_sur(fournisseur), nom_sur(reference)
            if not f:
                continue
            (docs / f / r if r else docs / f).mkdir(parents=True, exist_ok=True)


def chemin_libre(dossier: Path, nom: str) -> Path:
    """`nom` s'il est libre, sinon `nom (1)`, `nom (2)`… avant l'extension (R13)."""
    candidat = dossier / nom
    if not candidat.exists():
        return candidat
    tige, suffixe = Path(nom).stem, Path(nom).suffix
    i = 1
    while (dossier / f"{tige} ({i}){suffixe}").exists():
        i += 1
    return dossier / f"{tige} ({i}){suffixe}"


def copier_document(source: Path, dossier: Path, nom: str) -> Path:
    """Copie `source` dans `dossier` sous un nom libre ; retourne le chemin créé."""
    dossier.mkdir(parents=True, exist_ok=True)
    cible = chemin_libre(dossier, nom)
    shutil.copy2(source, cible)
    return cible


def chemin_relatif(dossier_projet: Path, chemin: Path) -> str:
    """Chemin enregistré en base : relatif au projet, séparateur `/`."""
    return chemin.relative_to(dossier_projet).as_posix()


def existe(chemin: Path) -> bool:
    return chemin.exists()


def supprimer_fichier(chemin: Path) -> None:
    """Supprime le fichier s'il existe ; une erreur (fichier ouvert…) remonte."""
    chemin.unlink(missing_ok=True)


def fichiers_du_dossier(dossier: Path) -> list[Path]:
    """Fichiers directement dans `dossier` ; dossier absent → liste vide."""
    try:
        return [p for p in dossier.iterdir() if p.is_file()]
    except OSError:
        return []


def supprimer_dossiers_article(
    dossier_projet: Path,
    numero_dossier: str,
    livrables: Iterable[str],
    fournisseur: str,
    reference: str,
) -> None:
    """Supprime le dossier de l'article dans chaque livrable, et le dossier du
    fournisseur s'il est devenu vide (R6)."""
    for livrable in livrables:
        cible = dossier_documents(dossier_projet, livrable, numero_dossier, fournisseur, reference)
        if cible.exists():
            shutil.rmtree(cible, ignore_errors=True)
        dossier_fournisseur = cible.parent
        if dossier_fournisseur.exists() and not any(dossier_fournisseur.iterdir()):
            shutil.rmtree(dossier_fournisseur, ignore_errors=True)


def ecrire_texte(chemin: Path, contenu: str, encodage: str = "utf-8") -> None:
    chemin.write_text(contenu, encoding=encodage)


def dossier_non_vide(dossier: Path) -> bool:
    return dossier.exists() and any(dossier.iterdir())


def supprimer_projet(dossier_projet: Path) -> None:
    """Supprime définitivement le dossier entier du projet (R29)."""
    shutil.rmtree(dossier_projet)


def couples_des_dossiers(
    dossier_projet: Path, numero_dossier: str, livrables: Iterable[str]
) -> list[tuple[str, str]]:
    """Couples (fournisseur, référence) lus dans les dossiers `Documents/` du
    premier livrable qui en contient (repli pour les anciens projets)."""
    couples: list[tuple[str, str]] = []
    for livrable in livrables:
        docs = dossier_livrable(dossier_projet, livrable, numero_dossier) / "Documents"
        if not docs.exists():
            continue
        for fournisseur in docs.iterdir():
            if fournisseur.is_dir():
                couples += [(fournisseur.name, r.name) for r in fournisseur.iterdir() if r.is_dir()]
        if couples:
            break
    return couples


def statistiques_disque(dossier_projet: Path) -> tuple[int, int]:
    """(nombre de fichiers sous un dossier « Documents », taille totale en octets).

    `os.scandir` plutôt que `rglob` + `stat` : sous Windows, taille et type
    arrivent avec la liste du dossier (décisif sur un partage réseau). À
    appeler hors du fil de l'interface.
    """
    nb_documents = 0
    taille = 0
    pile: list[tuple[str, bool]] = [(str(dossier_projet), False)]
    while pile:
        dossier, dans_documents = pile.pop()
        try:
            with os.scandir(dossier) as entrees:
                for entree in entrees:
                    try:
                        if entree.is_dir(follow_symlinks=False):
                            pile.append((entree.path, dans_documents or entree.name == "Documents"))
                        elif entree.is_file(follow_symlinks=False):
                            taille += entree.stat(follow_symlinks=False).st_size
                            nb_documents += dans_documents
                    except OSError:
                        continue
        except OSError:
            continue
    return nb_documents, taille


def ouvrir_avec_l_application(chemin: Path) -> None:
    """Ouvre le fichier avec l'application associée du poste."""
    if sys.platform.startswith("win"):
        os.startfile(str(chemin))  # noqa: S606 — chemin d'un document du projet
    elif sys.platform == "darwin":
        subprocess.run(["open", str(chemin)], check=False)  # noqa: S603, S607
    else:
        subprocess.run(["xdg-open", str(chemin)], check=False)  # noqa: S603, S607
