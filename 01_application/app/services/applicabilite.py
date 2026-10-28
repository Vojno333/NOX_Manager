"""Règles d'applicabilité, communes au tableau de suivi, au dépôt et à l'export.

Repris de `00_ancien/wikidocs_qt/document_rules.py` et
`project_dashboard_window.py` (`_doc_applies_to_type`, `_compute_requirement_score`).
"""

from __future__ import annotations

from app.models.enregistrement import Enregistrement
from app.models.referentiel import ALIAS_CODES, ANCIENNES_CLES_CECC, CODE_ROHS

# États d'une exigence (bascule à trois états).
NA = 0
NON_DEFINI = 1
APPLICABLE = 2


def normaliser_code(code: str) -> str:
    """« 1907/2006 — REACh » ou « 1907/2006 | REACh » → « 1907/2006 » ;
    alias ramenés à leur code de référence (2015/863 → 2011/65/UE) (R14, R16)."""
    code = str(code or "").strip()
    for separateur in (" — ", " | "):
        if separateur in code:
            code = code.split(separateur, 1)[0].strip()
    return ALIAS_CODES.get(code, code)


def codes_egaux(a: str, b: str) -> bool:
    return normaliser_code(a) == normaliser_code(b)


def est_rohs(code: str) -> bool:
    return normaliser_code(code) == CODE_ROHS or "rohs" in str(code or "").lower()


def plus_recents_d_abord(enrs: list[Enregistrement]) -> list[Enregistrement]:
    return sorted(enrs, key=lambda e: e.depose_le or "", reverse=True)


def etat_exigence(enrs: list[Enregistrement], code: str) -> int:
    """État d'après le DERNIER enregistrement qui mentionne l'exigence (R15).

    Applicable si le code figure dans les codes applicables ou couverts,
    N/A s'il figure dans les codes N/A ; aucune mention → non défini.
    """
    for enr in plus_recents_d_abord(enrs):
        if any(codes_egaux(c, code) for c in enr.codes_applicables + enr.codes_couverts):
            return APPLICABLE
        if any(codes_egaux(c, code) for c in enr.codes_na):
            return NA
    return NON_DEFINI


def couvre(enr: Enregistrement, code: str) -> bool:
    return any(codes_egaux(c, code) for c in enr.codes_couverts)


def vaut_pour_livrable(enr: Enregistrement, livrable: str) -> bool:
    """L'enregistrement compte pour ce livrable : déposé depuis lui, rangé dans
    lui, ou document RoHS (commun au CE et au DPE, R14)."""
    livrable = str(livrable).upper()
    source = str(enr.livrable_source).upper()
    if source == livrable or livrable in [str(v).upper() for v in enr.livrables_rangement]:
        return True
    rohs = any(est_rohs(c) for c in enr.codes_couverts)
    return rohs and livrable in ("CE", "DPE") and source in ("CE", "DPE")


def est_estimation(enr: Enregistrement) -> bool:
    """Une estimation se repère au nom du fichier (R18)."""
    return "estimation" in (enr.nom_stocke or "").lower()


def valeur_cecc(champs: dict | None, cle: str) -> str:
    """Valeur d'un champ de fiche CECC, en lisant les anciennes clés en repli."""
    champs = champs or {}
    for k in (cle, *ANCIENNES_CLES_CECC.get(cle, ())):
        valeur = str(champs.get(k) or "").strip()
        if valeur:
            return valeur
    return ""


def statut_cecc(champs: dict | None) -> str:
    return valeur_cecc(champs, "cecc_etat")
