"""Corrections : retirer ou remplacer le justificatif d'une exigence, vider un
article pour un livrable (R21, R22, R23).

Repris de `v1-avant-refonte:wikidocs_qt/project_dashboard_window.py` (`_on_delete_row`,
`_keep_only_rohs`, `_justif_docs_for_code`, `_remove_justif_for_codes`,
`_detach_and_delete_file`, `_on_delete_justif`, `_on_replace_justif`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from app.dataaccess import arborescence, base_projet
from app.models.enregistrement import Enregistrement
from app.models.referentiel import CODE_ROHS
from app.services import applicabilite as ap


def _de_l_article(dossier: Path, fournisseur: str, reference: str) -> list[Enregistrement]:
    return [
        e
        for e in base_projet.lire_tous(dossier)
        if e.fournisseur == fournisseur and e.reference == reference
    ]


def _chemins_utilises(dossier: Path) -> list[str]:
    return [e.chemin_relatif for e in base_projet.lire_tous(dossier)]


def detacher_et_supprimer(dossier: Path, enr: Enregistrement) -> tuple[str | None, str | None]:
    """L'enregistrement perd son fichier (il garde son applicabilité) ; le fichier
    est supprimé s'il n'est plus utilisé. Retourne (nom supprimé, erreur)."""
    base_projet.detacher_fichier(dossier, enr.id)
    chemin = enr.chemin_relatif
    if chemin in _chemins_utilises(dossier):
        return None, None
    try:
        arborescence.supprimer_fichier(dossier / chemin)
    except OSError as e:
        return None, f"Impossible de supprimer le fichier :\n\n{dossier / chemin}\n\n{e}"
    return enr.nom_stocke or Path(chemin).name, None


# ── Justificatif d'une exigence (R21, E6) ──
def documents_justifiant(
    dossier: Path,
    fournisseur: str,
    reference: str,
    livrable: str,
    code: str,
    avant: str | None = None,
) -> list[Enregistrement]:
    """Enregistrements avec fichier de l'article, valant pour le livrable, qui
    couvrent l'exigence ; avec `avant`, seulement ceux déposés avant cette date."""
    return [
        e
        for e in _de_l_article(dossier, fournisseur, reference)
        if ap.vaut_pour_livrable(e, livrable)
        and e.a_un_fichier
        and ap.couvre(e, code)
        and (avant is None or (e.depose_le or "") < avant)
    ]


def message_retrait(fournisseur: str, reference: str, code: str, docs) -> str:
    noms = sorted({e.nom_stocke for e in docs})
    message = (
        f"Retirer le justificatif de l'exigence {code} pour {fournisseur} / {reference} ?\n\n"
        + "\n".join(f"• {n}" for n in noms)
        + "\n\nL'exigence reste «Applicable», sans document. Un fichier qui "
        "ne justifie plus aucune exigence est supprimé du dossier projet."
    )
    if ap.est_rohs(code):
        message += "\n\nRoHS est commun au CE et au DPE : le retrait s'applique aux deux."
    return message


def retirer_exigences(
    dossier: Path, docs: list[Enregistrement], codes: list[str]
) -> tuple[list[str], list[str]]:
    """Retire `codes` des exigences couvertes par `docs`. Un enregistrement qui ne
    couvre plus rien garde son applicabilité mais perd son fichier, supprimé s'il
    n'est plus utilisé. Retourne (fichiers supprimés, erreurs)."""
    supprimes, erreurs = [], []
    for enr in docs:
        gardes = [
            i
            for i, c in enumerate(enr.codes_couverts)
            if not any(ap.codes_egaux(c, r) for r in codes)
        ]
        if len(gardes) == len(enr.codes_couverts):
            continue
        nouveaux = [enr.codes_couverts[i] for i in gardes]
        libelles = [enr.libelles_couverts[i] for i in gardes if i < len(enr.libelles_couverts)]
        base_projet.modifier_listes_de_codes(
            dossier, enr.id, {"codes_couverts": nouveaux, "libelles_couverts": libelles}
        )
        if not nouveaux:
            nom, erreur = detacher_et_supprimer(dossier, enr)
            if nom:
                supprimes.append(nom)
            if erreur:
                erreurs.append(erreur)
    return supprimes, erreurs


def message_remplacement(codes: list[str]) -> str | None:
    """Alerte quand le remplacement porte sur plusieurs exigences (E6)."""
    if len(codes) < 2:
        return None
    return (
        f"Le nouveau document remplacera l'ancien pour les {len(codes)} exigences "
        "sélectionnées :\n\n" + "\n".join(f"• {c}" for c in codes) + "\n\nContinuer ?"
    )


def remplacer_apres_depot(
    dossier: Path, fournisseur: str, reference: str, debut: str, selection: list[str]
) -> tuple[list[str], list[str]]:
    """Après un dépôt de remplacement commencé à `debut` : les anciens documents ne
    justifient plus les exigences sélectionnées que le nouveau couvre (E6).

    Les autres exigences de l'ancien document restent justifiées par lui.
    """
    avec_fichier = [e for e in _de_l_article(dossier, fournisseur, reference) if e.a_un_fichier]
    nouveaux = [e for e in avec_fichier if (e.depose_le or "") >= debut]
    codes = [code for code in selection if any(ap.couvre(e, code) for e in nouveaux)]
    livrables = {str(e.livrable_source).upper() for e in nouveaux}
    anciens = [
        e
        for e in avec_fichier
        if (e.depose_le or "") < debut and any(ap.vaut_pour_livrable(e, t) for t in livrables)
    ]
    if not codes:
        return [], []
    return retirer_exigences(dossier, anciens, codes)


# ── Vider un article pour un livrable (R23, E7) ──
@dataclass
class Vidage:
    fournisseur: str
    reference: str
    livrable: str
    dossier_livrable: str
    a_supprimer: list[Enregistrement] = field(default_factory=list)
    a_reduire: list[Enregistrement] = field(default_factory=list)  # copies RoHS d'un autre livrable
    fichiers: set[Path] = field(default_factory=set)
    # E7 : justificatifs RoHS de l'article rangés dans l'autre livrable (CE ↔ DPE).
    dossier_autre: str = ""
    rohs_autre: list[Enregistrement] = field(default_factory=list)

    @property
    def vide(self) -> bool:
        return not self.a_supprimer and not self.fichiers and not self.rohs_autre

    def message_rien(self) -> str:
        return (
            f"Aucune information ni aucun document {self.livrable} "
            f"pour {self.fournisseur} / {self.reference}."
        )

    def message_confirmation(self) -> str:
        noms = sorted(f.name for f in self.fichiers)
        liste = "\n".join(f"• {n}" for n in noms[:15])
        if len(noms) > 15:
            liste += f"\n• … et {len(noms) - 15} autre(s)"
        t = self.livrable
        message = (
            f"Supprimer les informations {t} de {self.fournisseur} / {self.reference} ?\n\n"
            f"• {len(self.a_supprimer)} enregistrement(s) {t} (exigences, applicabilité"
            f"{', champs CECC' if t == 'CECC' else ''})\n"
            f"• {len(self.fichiers)} fichier(s) du dossier « {self.dossier_livrable} »"
            + (f" :\n{liste}" if liste else "")
            + "\n\nLes autres BDD ne sont pas touchées. Cette action est irréversible."
        )
        if self.rohs_autre:
            noms = sorted({e.nom_stocke for e in self.rohs_autre})
            message += (
                "\n\nRoHS est commun au CE et au DPE : son justificatif rangé dans "
                f"« {self.dossier_autre} » est aussi retiré :\n"
                + "\n".join(f"• {n}" for n in noms)
                + "\nL'applicabilité de l'autre BDD est conservée."
            )
        return message


def preparer_vidage(
    dossier: Path, numero_dossier: str, fournisseur: str, reference: str, livrable: str
) -> Vidage:
    """Ce que vider l'article pour ce livrable supprimerait.

    Enregistrements supprimés : ceux dont le fichier est rangé dans le dossier
    du livrable, et ceux d'applicabilité seule saisis depuis lui. Une copie
    rangée ailleurs mais saisie depuis ce livrable est réduite à RoHS.
    """
    livrable = livrable.upper()
    nom_dossier = f"BDD {livrable} {numero_dossier}"
    plan = Vidage(fournisseur, reference, livrable, nom_dossier)
    for e in _de_l_article(dossier, fournisseur, reference):
        depuis_ce_livrable = str(e.livrable_source).upper() == livrable
        if e.a_un_fichier and PurePosixPath(e.chemin_relatif).parts[0] == nom_dossier:
            plan.a_supprimer.append(e)
        elif depuis_ce_livrable and not e.a_un_fichier:
            plan.a_supprimer.append(e)
        elif depuis_ce_livrable:
            plan.a_reduire.append(e)
    fichiers = {dossier / e.chemin_relatif for e in plan.a_supprimer if e.a_un_fichier}
    dossier_article = arborescence.dossier_documents(
        dossier, livrable, numero_dossier, fournisseur, reference
    )
    fichiers |= set(arborescence.fichiers_du_dossier(dossier_article))
    plan.fichiers = {f for f in fichiers if arborescence.existe(f)}
    autre = {"CE": "DPE", "DPE": "CE"}.get(livrable)
    if autre:
        plan.dossier_autre = f"BDD {autre} {numero_dossier}"
        plan.rohs_autre = _rohs_dans(dossier, fournisseur, reference, plan.dossier_autre)
    return plan


def _rohs_dans(dossier: Path, fournisseur: str, reference: str, nom_dossier: str):
    """Enregistrements de l'article dont le fichier, rangé dans `nom_dossier`, couvre RoHS."""
    return [
        e
        for e in _de_l_article(dossier, fournisseur, reference)
        if e.a_un_fichier
        and PurePosixPath(e.chemin_relatif).parts[0] == nom_dossier
        and any(ap.est_rohs(c) for c in e.codes_couverts)
    ]


def _garder_rohs(dossier: Path, enr: Enregistrement) -> list[str]:
    """Réduit l'enregistrement à RoHS (libellés gardés alignés) ; retourne les erreurs."""

    def paires(codes, libelles):
        gardes = [i for i, c in enumerate(codes) if ap.est_rohs(c)]
        return [codes[i] for i in gardes], [libelles[i] for i in gardes if i < len(libelles)]

    couverts, libelles = paires(enr.codes_couverts, enr.libelles_couverts)
    na, libelles_na = paires(enr.codes_na, enr.libelles_na)
    base_projet.modifier_listes_de_codes(
        dossier,
        enr.id,
        {
            "codes_couverts": couverts,
            "libelles_couverts": libelles,
            "codes_applicables": paires(enr.codes_applicables, [])[0],
            "codes_na": na,
            "libelles_na": libelles_na,
        },
    )
    if not couverts and enr.a_un_fichier:
        _, erreur = detacher_et_supprimer(dossier, enr)
        return [erreur] if erreur else []
    return []


def vider(dossier: Path, plan: Vidage) -> list[str]:
    """Applique le vidage ; retourne les fichiers qui n'ont pas pu être supprimés."""
    base_projet.supprimer(dossier, [e.id for e in plan.a_supprimer])
    echecs = []
    for e in plan.a_reduire:
        echecs += _garder_rohs(dossier, e)
    if plan.dossier_autre:
        rohs = _rohs_dans(dossier, plan.fournisseur, plan.reference, plan.dossier_autre)
        _, erreurs = retirer_exigences(dossier, rohs, [CODE_ROHS])
        echecs += erreurs
    utilises = {
        (dossier / e.chemin_relatif).resolve()
        for e in base_projet.lire_tous(dossier)
        if e.a_un_fichier
    }
    for f in plan.fichiers:
        if f.resolve() in utilises:
            continue
        try:
            arborescence.supprimer_fichier(f)
        except OSError as e:
            echecs.append(f"{f.name} : {e}")
    return echecs


def message_echecs_vidage(echecs: list[str]) -> str:
    return "Certains fichiers n'ont pas pu être supprimés (ouverts ailleurs ?) :\n\n" + "\n".join(
        echecs
    )
