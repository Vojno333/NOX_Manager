"""Dépôt d'un justificatif ou réglage de l'applicabilité seule (R7 à R14).

Repris de `v1-avant-refonte:wikidocs_qt/upload_document_dialog.py` (`_validate`,
`_save_document`, `_storage_types`, `_has_rohs`, `_selected_requirements`,
`_auto_name`, `_build_final_filename`, `_cecc_fields_data`,
`_prefill_existing_cecc_fields`, `_prefill_existing_applicability`).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.dataaccess import arborescence, base_projet, projet_fichier
from app.models.depot import APPLICABILITE, IMPORT, SaisieDepot
from app.models.enregistrement import Enregistrement
from app.models.referentiel import EXTENSIONS_DEPOT, FORMATS_DEPOT
from app.services import applicabilite as ap

CHAMPS_CECC_OBLIGATOIRES = ("manufacturer_doc", "manufacturer_part_number", "nom_cecc")


def format_accepte(fichier: Path) -> bool:
    """Extension dans la liste fermée des formats acceptés (E2)."""
    return fichier.suffix.lower() in EXTENSIONS_DEPOT


# ── Exigences saisies ──
def _codes(saisie: SaisieDepot, etat: int) -> list[str]:
    if saisie.livrable not in ("CE", "DPE"):
        return []
    return [code for code, e in saisie.etats.items() if e == etat]


def codes_applicables(saisie: SaisieDepot) -> list[str]:
    return _codes(saisie, ap.APPLICABLE)


def codes_na(saisie: SaisieDepot) -> list[str]:
    return _codes(saisie, ap.NA)


def codes_couverts(saisie: SaisieDepot) -> list[str]:
    """Exigences justifiées par le document : applicables et cochées (import),
    ou toutes les applicables (applicabilité seule)."""
    applicables = codes_applicables(saisie)
    if saisie.mode == APPLICABILITE:
        return applicables
    return [c for c in applicables if c in saisie.coches]


def _rohs_present(saisie: SaisieDepot, avec_applicabilite: bool) -> bool:
    codes = codes_couverts(saisie)
    if avec_applicabilite:
        codes = codes + codes_applicables(saisie) + codes_na(saisie)
    return any(ap.est_rohs(c) for c in codes)


def livrables_concernes(
    saisie: SaisieDepot, livrables_suivis: list[str], avec_applicabilite: bool = False
) -> list[str]:
    """Livrables où ranger le fichier : RoHS couverte → CE et DPE (R14).

    Avec `avec_applicabilite`, livrables où l'enregistrement s'applique :
    RoHS simplement réglée suffit pour que l'autre livrable reprenne son état.
    """
    suivis = {str(v).strip().upper() for v in livrables_suivis}
    if saisie.livrable == "CE" and _rohs_present(saisie, avec_applicabilite):
        return [t for t in ("CE", "DPE") if t in suivis]
    if saisie.livrable == "DPE" and _rohs_present(saisie, avec_applicabilite):
        return [t for t in ("DPE", "CE") if t in suivis]
    return [saisie.livrable] if saisie.livrable in suivis else []


def applicabilite_seule(saisie: SaisieDepot) -> bool:
    """Aucun document à conserver : mode applicabilité, ou import CE / DPE sans
    exigence cochée (R11)."""
    if saisie.mode == APPLICABILITE:
        return True
    return saisie.livrable in ("CE", "DPE") and not codes_couverts(saisie)


# ── Fiche CECC (R12) ──
def champs_cecc_finals(saisie: SaisieDepot) -> dict[str, str]:
    """Champs saisis ; un nom CECC vide prend le nom du fichier (constat C7)."""
    champs = dict(saisie.champs_cecc)
    if saisie.fichier:
        champs["nom_cecc"] = champs.get("nom_cecc") or saisie.fichier.name
    return champs


def fiche_cecc_initiale(dossier: Path, fournisseur: str, reference: str) -> dict:
    """Pré-remplissage de la fiche CECC : la dernière fiche de l'article (R12) ;
    à défaut, le fournisseur et le MNP de l'article (E4)."""
    fiche = base_projet.derniere_fiche_cecc(dossier, fournisseur, reference)
    if fiche:
        return fiche
    projet = projet_fichier.lire_projet(dossier)
    article = projet.article(fournisseur, reference) if projet else None
    return {
        "manufacturer_doc": fournisseur,
        "manufacturer_part_number": article.mnp if article else "",
    }


def etats_existants(
    dossier: Path, fournisseur: str, reference: str, livrable: str, codes: list[str]
) -> dict[str, int] | None:
    """État déjà enregistré de chaque exigence, ou None si rien n'est enregistré
    pour l'article dans ce livrable."""
    enrs = [
        e
        for e in base_projet.lire_tous(dossier)
        if str(e.fournisseur) == str(fournisseur)
        and str(e.reference) == str(reference)
        and (
            str(e.livrable_source).upper() == livrable
            or livrable in [str(b).upper() for b in e.livrables_rangement]
        )
    ]
    if not enrs:
        return None
    return {code: ap.etat_exigence(enrs, code) for code in codes}


# ── Nom du fichier (R13) ──
def nom_automatique(livrable: str, fournisseur: str, reference: str) -> str:
    morceaux = [
        livrable,
        arborescence.nom_sur_partie(fournisseur),
        arborescence.nom_sur_partie(reference),
    ]
    return "_".join(m for m in morceaux if m)


def nom_final(saisie: SaisieDepot, fournisseur: str, reference: str) -> str:
    """Nom saisi, sinon nom automatique ; l'extension du fichier d'origine est
    toujours gardée (E3), sans être doublée si le nom saisi la porte déjà."""
    if not saisie.fichier:
        return "—"
    extension = saisie.fichier.suffix
    saisi = saisie.nom_saisi.strip()
    if saisi:
        return saisi if saisi.lower().endswith(extension.lower()) else saisi + extension
    return nom_automatique(saisie.livrable, fournisseur, reference) + extension


# ── Contrôles (R7 à R12) ──
def verifier(saisie: SaisieDepot, livrables_suivis: list[str]) -> str | None:
    """Message de refus, ou None si l'enregistrement peut se faire."""
    livrable = saisie.livrable
    if livrable not in [str(v).strip().upper() for v in livrables_suivis]:
        return f"Le livrable {livrable} n'est pas activé sur ce projet."
    if saisie.fichier and not format_accepte(saisie.fichier):
        return "Format de fichier non accepté. Formats acceptés : " + ", ".join(FORMATS_DEPOT) + "."
    if livrable in ("CE", "DPE"):
        if saisie.mode == APPLICABILITE:
            return None
        couverts = codes_couverts(saisie)
        if couverts and not saisie.fichier:
            return "Un document doit être fourni : au moins une exigence applicable est cochée."
        if saisie.fichier and not couverts:
            return (
                "Un fichier a été sélectionné mais aucune exigence n'est cochée. "
                "Coche au moins une exigence «Applicable» pour l'associer à ce "
                "document, ou retire le fichier pour n'enregistrer que "
                "l'applicabilité."
            )
        if saisie.fichier and couverts:
            non_definies = sum(1 for e in saisie.etats.values() if e == ap.NON_DEFINI)
            if non_definies:
                return (
                    f"{non_definies} exigence(s) sont encore «Non défini(es)». "
                    f"Veuillez indiquer «Applicable» ou «N/A» pour chacune avant "
                    f"d'importer ce document."
                )
    elif livrable == "CECC":
        if saisie.mode == APPLICABILITE:
            return "La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC."
        if not saisie.fichier or not saisie.fichier.exists():
            return "Merci de choisir un fichier."
        champs = champs_cecc_finals(saisie)
        if any(not champs.get(k) for k in CHAMPS_CECC_OBLIGATOIRES):
            return (
                "Pour un justificatif CECC, renseignez au minimum "
                "Fournisseur Doc, Manufacturer Part Number et Nom : CECC."
            )
    return None


# ── Enregistrement ──
def enregistrer(saisie: SaisieDepot) -> int:
    """Enregistre le dépôt pour chaque article ciblé ; retourne le nombre d'articles.

    Un fichier est copié dans chaque livrable de rangement, avec un
    enregistrement par copie (R14). Le contrôle `verifier` doit être passé.
    """
    projet = projet_fichier.lire_projet(saisie.dossier)
    suivis = projet.livrables
    rangement = livrables_concernes(saisie, suivis, avec_applicabilite=True)
    cecc = champs_cecc_finals(saisie) if saisie.livrable == "CECC" else {}
    seule = applicabilite_seule(saisie)
    couverts = [] if seule else codes_couverts(saisie)
    na = codes_na(saisie)
    applicables = codes_applicables(saisie)

    def _enregistrement(f, r, nom_original="", nom_stocke="", chemin="") -> Enregistrement:
        return Enregistrement(
            fournisseur=f,
            reference=r,
            livrable_source=saisie.livrable,
            livrables_rangement=list(rangement),
            codes_couverts=list(couverts),
            libelles_couverts=list(couverts),
            champs_cecc=dict(cecc),
            nom_original=nom_original,
            nom_stocke=nom_stocke,
            chemin_relatif=chemin,
            depose_le=datetime.now().isoformat(),
            codes_na=list(na),
            libelles_na=list(na),
            codes_applicables=list(applicables),
        )

    for f, r in saisie.cibles:
        f, r = str(f), str(r)
        if seule:
            base_projet.ajouter(saisie.dossier, _enregistrement(f, r))
            continue
        nom = nom_final(saisie, f, r)
        for livrable in livrables_concernes(saisie, suivis):
            dossier = arborescence.dossier_documents(
                saisie.dossier, livrable, projet.numero_dossier, f, r
            )
            copie = arborescence.copier_document(saisie.fichier, dossier, nom)
            chemin = arborescence.chemin_relatif(saisie.dossier, copie)
            base_projet.ajouter(
                saisie.dossier, _enregistrement(f, r, saisie.fichier.name, copie.name, chemin)
            )
    return len(saisie.cibles)


def message_de_fin(saisie: SaisieDepot, nombre: int) -> tuple[str, str]:
    if applicabilite_seule(saisie):
        return (
            "Applicabilité enregistrée",
            f"L'applicabilité a été mise à jour pour {nombre} ligne(s).",
        )
    return "Import terminé", f"Les modifications ont été appliquées à {nombre} ligne(s)."


def verifier_selection(livrables: list[str], mode: str = IMPORT) -> tuple[str, str] | None:
    """Avant d'ouvrir le dialogue : (titre, message) de refus, ou None.

    Un dépôt groupé ne concerne qu'un seul livrable (R8) ; pas d'applicabilité
    seule en CECC.
    """
    types = {str(t).upper() for t in livrables}
    if len(types) > 1:
        return (
            "Import multiple impossible",
            "La sélection multiple doit contenir un seul type de justificatif.",
        )
    if mode == APPLICABILITE and "CECC" in types:
        return (
            "Applicabilité",
            "La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC. "
            "Utilise «Importer un document» pour ce type.",
        )
    return None
