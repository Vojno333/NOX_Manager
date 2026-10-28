"""Complétion des articles et indicateurs du tableau de suivi.

Repris de `v1-avant-refonte:wikidocs_qt/project_dashboard_window.py`
(`_build_table_rows`, `_compute_ce_dpe_completion`, `_compute_requirement_score`,
`_compute_cecc_completion`, `_scan_supplier_reference_pairs`, `_apply_filters`,
`_update_kpis`).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.dataaccess import arborescence, base_projet
from app.models.enregistrement import Enregistrement
from app.models.projet import Projet
from app.models.referentiel import (
    CHAMPS_CECC,
    EXIGENCES_CE,
    EXIGENCES_DPE,
    STATUT_ESTIMATION,
    STATUT_VALIDE,
)
from app.models.suivi import LigneSuivi
from app.services import applicabilite as ap

# 2015/863 est un alias de 2011/65/UE : RoHS ne compte qu'une fois.
CODES_CE = [c for c, _ in EXIGENCES_CE if c != "2015/863"]
CODES_DPE = [c for c, _ in EXIGENCES_DPE]


def score_exigence(enrs: list[Enregistrement], code: str) -> float:
    """1 si au moins un document couvre l'exigence, estimation ou non, sinon 0 (R17, E5).

    Seuls les enregistrements avec un fichier couvrent une exigence. L'export
    Excel garde, lui, la distinction prouvé / estimé (R18, R26).
    """
    return 1.0 if any(e.a_un_fichier and ap.couvre(e, code) for e in enrs) else 0.0


def completion_ce_dpe(enrs: list[Enregistrement], codes: list[str]) -> float:
    """Moyenne des scores des exigences qui ne sont pas N/A ; tout N/A → 100 % (R17)."""
    if not codes:
        return 0.0
    applicables = [c for c in codes if ap.etat_exigence(enrs, c) != ap.NA]
    if not applicables:
        return 1.0
    return sum(score_exigence(enrs, c) for c in applicables) / len(applicables)


def completion_cecc(enrs: list[Enregistrement]) -> float:
    """100 % si le statut CECC le plus récent est « Validé » ou « Estimation » (R19, E5)."""
    avec_statut = [e for e in enrs if ap.statut_cecc(e.champs_cecc)]
    dernier = max(avec_statut, key=lambda e: e.depose_le or "", default=None)
    valides = (STATUT_VALIDE, STATUT_ESTIMATION)
    return 1.0 if dernier and ap.statut_cecc(dernier.champs_cecc) in valides else 0.0


def _trier(couples) -> list[tuple[str, str]]:
    return sorted(set(couples), key=lambda x: (x[0].lower(), x[1].lower()))


def couples_du_projet(projet: Projet) -> list[tuple[str, str]]:
    """Articles du projet, triés ; à défaut, ceux trouvés dans les dossiers."""
    couples = [a.cle for a in projet.articles if a.fournisseur]
    if couples:
        return _trier(couples)
    return _trier(
        arborescence.couples_des_dossiers(projet.dossier, projet.numero_dossier, projet.livrables)
    )


def lignes_de_suivi(projet: Projet, enrs: list[Enregistrement] | None = None) -> list[LigneSuivi]:
    """Une ligne par article et par livrable suivi, avec sa complétion."""
    if enrs is None:
        enrs = base_projet.lire_tous(projet.dossier)
    par_article: dict[tuple[str, str], list[Enregistrement]] = defaultdict(list)
    for e in enrs:
        par_article[(e.fournisseur, e.reference)].append(e)

    lignes = []
    for fournisseur, reference in couples_du_projet(projet):
        article = projet.article(fournisseur, reference)
        tous = par_article.get((fournisseur, reference), [])
        for livrable in projet.livrables:
            docs = [e for e in tous if ap.vaut_pour_livrable(e, livrable)]
            if livrable == "CE":
                valeur = completion_ce_dpe(docs, CODES_CE)
            elif livrable == "DPE":
                valeur = completion_ce_dpe(docs, CODES_DPE)
            else:
                valeur = completion_cecc(docs)
            lignes.append(
                LigneSuivi(
                    fournisseur=fournisseur,
                    reference=reference,
                    libelle=article.libelle if article else "",
                    n_commande=article.n_commande if article else "",
                    mnp=article.mnp if article else "",
                    livrable=livrable,
                    completion=valeur,
                    enregistrements=docs,
                )
            )
    return lignes


# ── Filtres et indicateurs (R20) ──
def filtrer(lignes: list[LigneSuivi], filtres: dict[str, set[str] | None]) -> list[LigneSuivi]:
    """Garde les lignes dont chaque colonne filtrée a une valeur autorisée."""
    for colonne, autorisees in filtres.items():
        if autorisees is None:
            continue
        lignes = [ligne for ligne in lignes if ligne.valeur(colonne) in autorisees]
    return lignes


def valeurs_de_colonne(lignes: list[LigneSuivi], colonne: str) -> list[str]:
    return sorted({ligne.valeur(colonne) for ligne in lignes}, key=str.lower)


def indicateurs(lignes: list[LigneSuivi]) -> dict[str, int]:
    """Moyenne arrondie des complétions, par livrable, en pourcentage."""
    resultat = {}
    for livrable in ("CE", "CECC", "DPE"):
        valeurs = [ligne.completion for ligne in lignes if ligne.livrable == livrable]
        resultat[livrable] = round(sum(valeurs) / len(valeurs) * 100) if valeurs else 0
    return resultat


# ── Détail d'une ligne (panneau de droite) ──
def lignes_de_detail(
    ligne: LigneSuivi, dossier: Path, introuvables: set[str] | None = None
) -> list[dict]:
    """Une ligne par exigence (CE / DPE) ou par champ de fiche (CECC).

    CE / DPE : code, « code | libellé », applicabilité, document le plus récent
    qui la couvre et son chemin. CECC : champs de la dernière fiche ; le nom
    CECC porte le chemin du document.
    """
    enrs = ligne.enregistrements
    livrable = ligne.livrable.upper()
    if livrable == "CECC":
        return _detail_cecc(enrs, dossier)
    attendues = {"CE": EXIGENCES_CE, "DPE": EXIGENCES_DPE}.get(livrable)
    if attendues is None:
        return []
    derniers: dict[str, dict] = {}
    for e in ap.plus_recents_d_abord(enrs):
        if not ap.vaut_pour_livrable(e, livrable) or not e.a_un_fichier:
            continue
        for code in e.codes_couverts:
            code_normal = ap.normaliser_code(code)
            if code_normal not in derniers:
                derniers[code_normal] = {
                    "filename": e.nom_stocke,
                    "path": str(dossier / e.chemin_relatif),
                    "introuvable": e.chemin_relatif in (introuvables or set()),
                }
    detail = []
    for code, libelle in attendues:
        doc = derniers.get(ap.normaliser_code(code))
        etat = ap.etat_exigence(enrs, code)
        na = etat == ap.NA
        if na:
            applicabilite = "Non applicable"
        elif doc or etat == ap.APPLICABLE:
            applicabilite = "Applicable"
        else:
            applicabilite = "Non défini"
        detail.append(
            {
                "code": code,
                "requirement": f"{code} | {libelle}",
                "applicability": applicabilite,
                "filename": "" if na or not doc else doc["filename"],
                "path": "" if na or not doc else doc["path"],
                "introuvable": bool(doc and not na and doc["introuvable"]),
            }
        )
    return detail


def _detail_cecc(enrs: list[Enregistrement], dossier: Path) -> list[dict]:
    dernier = max(enrs, key=lambda e: e.depose_le or "", default=None)
    champs = dernier.champs_cecc if dernier else {}
    chemin = str(dossier / dernier.chemin_relatif) if dernier else ""
    return [
        {
            "requirement": libelle,
            "filename": ap.valeur_cecc(champs, cle),
            "path": chemin if cle == "nom_cecc" else "",
        }
        for cle, libelle, _ in CHAMPS_CECC
    ]


# ── Fichiers disparus (E12) ──
def documents_introuvables(projet: Projet, enrs: list[Enregistrement] | None = None) -> set[str]:
    """Chemins enregistrés dont le fichier n'est plus sur le disque.

    Parcourt les dossiers du projet : long sur le partage, à appeler hors du fil
    de l'interface.
    """
    if enrs is None:
        enrs = base_projet.lire_tous(projet.dossier)
    presents = arborescence.fichiers_presents(projet.dossier)
    return {e.chemin_relatif for e in enrs if e.a_un_fichier and e.chemin_relatif not in presents}


def nb_introuvables(ligne: LigneSuivi, introuvables: set[str]) -> int:
    return len(
        {e.chemin_relatif for e in ligne.enregistrements if e.chemin_relatif in introuvables}
    )
