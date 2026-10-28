"""Créer, modifier, ouvrir et supprimer un projet.

Repris de `v1-avant-refonte:wikidocs_qt/new_project_dialog.py` (`_validate`,
`_split_bulk_column`, `_parse_bulk_lines`, `_import_bulk_rows`,
`_download_bulk_template`, `_create_project`, `_update_project`) et
`home_window.py` (`_delete_selected_project`, `_open_project_from_data`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.core.config import reglages
from app.dataaccess import arborescence, base_projet, projet_fichier
from app.dataaccess.etat_utilisateur import EtatUtilisateur
from app.models.projet import Article, Projet
from app.models.referentiel import LIVRABLES

MODELE_CSV = (
    "Fournisseur;Reference;Libelle;MNP;N_commande\n"
    "VisioParts;VIS-001;Vis inox M6 x 20;MNP-001;CMD-2024-0001\n"
    "TechnoVis;VIS-002;Écrou frein M6;MNP-002;CMD-2024-0002\n"
    "FixPro;TV-010;Rondelle plate M6;MNP-003;CMD-2024-0003\n"
    "Soprema;TV-011;Vis tête hexagonale M8 x 25;MNP-004;CMD-2024-0004\n"
)


def articles_max() -> int:
    return int(reglages()["articles_max"])


@dataclass
class SaisieProjet:
    """Ce que l'utilisateur a saisi dans le dialogue de projet."""

    nom: str
    emplacement: str
    numero_dossier: str
    date_code: str
    livrables: list[str]
    # Lignes renseignées (au moins un champ non vide), dans l'ordre de saisie.
    lignes: list[Article] = field(default_factory=list)


def ligne_renseignee(article: Article) -> bool:
    return any(
        [article.fournisseur, article.reference, article.libelle, article.mnp, article.n_commande]
    )


def verifier(saisie: SaisieProjet) -> str | None:
    """Message de refus, ou None si la saisie est acceptable (R1, R2)."""
    if not saisie.nom.strip():
        return "Le Numéro de l'affaire est obligatoire."
    if not saisie.emplacement.strip():
        return "L'emplacement est obligatoire."
    if not saisie.numero_dossier.strip():
        return "Le numéro de dossier est obligatoire."
    try:
        datetime.strptime(saisie.date_code.strip(), "%d/%m/%Y")
    except ValueError:
        return "La date doit être au format JJ/MM/AAAA (ex. 24/04/2026)."
    if not saisie.livrables:
        return "Sélectionnez au moins un livrable (CE, CECC ou DPE)."
    lignes = [a for a in saisie.lignes if ligne_renseignee(a)]
    if not lignes:
        return "Ajoutez au moins une ligne avec un fournisseur et un N° de référence."
    if len(lignes) > articles_max():
        return (
            f"Le nombre de dossiers à créer ({len(lignes)}) dépasse "
            f"la limite autorisée de {articles_max()}."
        )
    for i, a in enumerate(lignes, start=1):
        if not (a.fournisseur and a.reference):
            return (
                f"La ligne {i} est incomplète.\n\n"
                "Les champs obligatoires sont : Fournisseur et N° Référence."
            )
    return None


# ── Import en masse (R4) ──
def decouper_colonne(texte: str) -> list[str]:
    """Une valeur par ligne ; une ligne vide au milieu reste une valeur vide à
    sa place, seules les lignes vides finales sont ignorées."""
    lignes = [ligne.strip() for ligne in texte.splitlines()]
    while lignes and not lignes[-1]:
        lignes.pop()
    return lignes


def lignes_import_masse(
    fournisseurs: str, references: str, libelles: str, mnps: str, commandes: str
) -> list[Article]:
    """Assemble les cinq colonnes ligne à ligne ; les lignes entièrement vides sont retirées."""
    colonnes = [decouper_colonne(t) for t in (fournisseurs, references, libelles, mnps, commandes)]
    if not any(colonnes):
        return []
    hauteur = max(len(c) for c in colonnes)
    articles = [Article(*(c[i] if i < len(c) else "" for c in colonnes)) for i in range(hauteur)]
    return [a for a in articles if ligne_renseignee(a)]


def ecart_import_masse(fournisseurs: str, references: str) -> str | None:
    """Question à poser quand les colonnes fournisseur et référence n'ont pas la même hauteur."""
    f, r = decouper_colonne(fournisseurs), decouper_colonne(references)
    if r and len(f) != len(r):
        return (
            f"Le nombre de fournisseurs ({len(f)}) et de références ({len(r)}) "
            f"ne correspondent pas.\n\nContinuer quand même ?"
        )
    return None


def nouvelles_lignes(existantes: list[Article], importees: list[Article]) -> list[Article]:
    """Lignes importées absentes des lignes déjà saisies (même fournisseur / référence)."""
    vus = {a.cle for a in existantes if ligne_renseignee(a)}
    ajout = []
    for a in importees:
        if a.cle in vus:
            continue
        vus.add(a.cle)
        ajout.append(a)
    return ajout


def ecrire_modele_csv(chemin: Path) -> None:
    arborescence.ecrire_texte(chemin, MODELE_CSV, "utf-8-sig")


# ── Création, modification ──
def dossier_existant_non_vide(emplacement: str) -> bool:
    return arborescence.dossier_non_vide(Path(emplacement.strip()))


def _couples(lignes: list[Article]) -> list[tuple[str, str]]:
    return [(a.fournisseur, a.reference) for a in lignes if ligne_renseignee(a)]


def creer_projet(saisie: SaisieProjet, etat: EtatUtilisateur) -> Projet:
    """Crée l'arborescence et le fichier projet (R5) ; le projet entre dans les récents.

    L'emplacement choisi accueille directement `.nox` et les dossiers BDD.
    """
    dossier = Path(saisie.emplacement.strip())
    numero = saisie.numero_dossier.strip().upper()
    lignes = [a for a in saisie.lignes if ligne_renseignee(a)]
    arborescence.creer_structure(dossier, numero, saisie.livrables, _couples(lignes))
    projet = projet_fichier.creer_fichier_projet(
        dossier, saisie.nom.strip(), numero, saisie.date_code.strip(), lignes, saisie.livrables
    )
    etat.ajouter_projet_recent(projet.nom, dossier, numero)
    etat.ajouter_emplacement_recent(dossier.parent)
    return projet


def articles_retires(projet: Projet, lignes: list[Article]) -> list[Article]:
    """Articles du projet qui ne figurent plus dans la nouvelle saisie (R6)."""
    gardes = {a.cle for a in lignes if a.fournisseur and a.reference}
    return [a for a in projet.articles if a.cle not in gardes]


def modifier_projet(
    projet: Projet, saisie: SaisieProjet, supprimer_les_retires: bool = False
) -> Projet:
    """Enregistre la nouvelle saisie. Avec `supprimer_les_retires`, les dossiers
    et les enregistrements des articles retirés sont supprimés (R6)."""
    numero = saisie.numero_dossier.strip().upper()
    lignes = [a for a in saisie.lignes if ligne_renseignee(a)]
    if supprimer_les_retires:
        retires = articles_retires(projet, lignes)
        for a in retires:
            arborescence.supprimer_dossiers_article(
                projet.dossier, numero, LIVRABLES, a.fournisseur, a.reference
            )
        base_projet.supprimer_pour_articles(projet.dossier, [a.cle for a in retires])
    arborescence.creer_structure(projet.dossier, numero, saisie.livrables, _couples(lignes))
    projet.nom = saisie.nom.strip()
    projet.numero_dossier = numero
    projet.date_code = saisie.date_code.strip()
    projet.articles = lignes
    projet.livrables = list(saisie.livrables)
    return projet_fichier.enregistrer_projet(projet)


# ── Ouverture, suppression (R28, R29, R31) ──
def ouvrir_projet(dossier: Path, etat: EtatUtilisateur) -> Projet | None:
    """Lit le projet ; s'il est valide, il passe en tête des récents."""
    projet = projet_fichier.lire_projet(dossier) if dossier.exists() else None
    if projet is None:
        return None
    etat.ajouter_projet_recent(projet.nom or dossier.name, dossier, projet.numero_dossier)
    etat.ajouter_emplacement_recent(dossier.parent)
    return projet


def retirer_des_recents(dossier: Path, etat: EtatUtilisateur) -> None:
    etat.retirer_projet_recent(dossier)


def supprimer_definitivement(dossier: Path, etat: EtatUtilisateur) -> None:
    """Efface le dossier entier du projet, puis le retire des récents (R29)."""
    arborescence.supprimer_projet(dossier)
    etat.retirer_projet_recent(dossier)


def lire_projet(dossier: Path) -> Projet | None:
    """Projet du dossier, sans le faire entrer dans les récents."""
    return projet_fichier.lire_projet(dossier) if dossier.exists() else None


def statistiques_disque(dossier: Path) -> tuple[int, int]:
    """(nombre de documents, taille du projet).

    Long sur le partage réseau : à appeler hors du fil de l'interface.
    """
    return arborescence.statistiques_disque(dossier)


def etat_utilisateur() -> EtatUtilisateur:
    """Préférences de l'utilisateur courant (projets récents, emplacements)."""
    return EtatUtilisateur()


def ouvrir_document(chemin: Path) -> tuple[str, str] | None:
    """Ouvre un document du projet ; (titre, message) d'erreur, ou None."""
    if not arborescence.existe(chemin):
        return "Fichier introuvable", f"Impossible d'ouvrir :\n\n{chemin}"
    try:
        arborescence.ouvrir_avec_l_application(chemin)
    except Exception as e:  # application absente, droits… : message système affiché
        return "Erreur d'ouverture", str(e)
    return None
