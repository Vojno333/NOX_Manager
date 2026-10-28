"""Contenu des exports Excel CE, CECC et DPE, et lancement de l'export.

Repris de `v1-avant-refonte:wikidocs_qt/export_templates.py` (`_fill_ce_sheet`,
`_fill_dpe_sheet`, `_fill_cecc_sheet`, `_group_docs`, `_rows_lookup`,
`_scan_supplier_reference_pairs`, `_latest_doc_by_requirement`,
`export_project_templates`) et `project_dashboard_window.py` (`_export_templates`).

Comme l'ancienne application, l'export lit les lignes du projet telles
qu'écrites dans le fichier (constat C6) et met des liens absolus (C10).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.dataaccess import arborescence, base_projet, export_excel, projet_fichier
from app.models.enregistrement import Enregistrement
from app.models.export import Cellule, ContenuExport
from app.models.projet import Projet
from app.models.referentiel import CHAMPS_CECC, COLONNES_CE, COLONNES_DPE, LIVRABLES
from app.services import applicabilite as ap

_COLONNES = {"CE": COLONNES_CE, "DPE": COLONNES_DPE}


def _regrouper(enrs: list[Enregistrement]) -> dict[tuple[str, str, str], list[Enregistrement]]:
    """Enregistrements par (fournisseur, référence, livrable de rangement)."""
    groupes: dict[tuple[str, str, str], list[Enregistrement]] = defaultdict(list)
    for e in enrs:
        for livrable in e.livrables_rangement or [str(e.livrable_source).upper()]:
            groupes[(e.fournisseur, e.reference, str(livrable).upper())].append(e)
    return groupes


def _infos_lignes(projet: Projet) -> dict[tuple[str, str], dict]:
    """Ligne brute du projet par article ; en cas de doublon, la dernière gagne (C6)."""
    infos = {}
    for ligne in projet.lignes_brutes:
        f = str(ligne.get("supplier", "")).strip()
        r = str(ligne.get("reference", "")).strip()
        if f and r:
            infos[(f, r)] = ligne
    return infos


def couples_a_exporter(projet: Projet) -> list[tuple[str, str]]:
    couples = [
        (str(ligne.get("supplier", "")).strip(), str(ligne.get("reference", "")).strip())
        for ligne in projet.lignes_brutes
        if str(ligne.get("supplier", "")).strip()
    ]
    if not couples:
        couples = arborescence.couples_des_dossiers(
            projet.dossier, projet.numero_dossier, LIVRABLES
        )
    return sorted(set(couples), key=lambda x: (x[0].lower(), x[1].lower()))


def _plus_recent(enrs: list[Enregistrement]) -> Enregistrement | None:
    ordonnes = ap.plus_recents_d_abord(enrs)
    return ordonnes[0] if ordonnes else None


def _dernier_par_exigence(enrs: list[Enregistrement], codes: list[str]) -> dict:
    """Code → document le plus récent (avec fichier) qui le couvre."""
    derniers: dict[str, Enregistrement] = {}
    for e in ap.plus_recents_d_abord(enrs):
        if not e.a_un_fichier:
            continue
        for code in codes:
            if code not in derniers and ap.couvre(e, code):
                derniers[code] = e
    return derniers


def _cellule_document(dossier: Path, chemin_relatif: str, texte: str) -> Cellule:
    """Texte du document, avec un lien s'il est présent sur le disque (R25, R25 quater)."""
    chemin = dossier / chemin_relatif
    return Cellule(texte, chemin if arborescence.existe(chemin) else None)


def _lignes_ce_dpe(projet, livrable, couples, groupes, infos) -> list:
    colonnes = _COLONNES[livrable]
    lignes = []
    for f, r in couples:
        info = infos.get((f, r), {})
        cellules = []
        fiche = _plus_recent(groupes.get((f, r, "CECC"), []))
        mpn = (fiche.champs_cecc.get("manufacturer_part_number", "") if fiche else "") or info.get(
            "mnp", ""
        )
        if mpn:
            cellules.append(("D", Cellule(mpn)))
        docs = groupes.get((f, r, livrable), [])
        derniers = _dernier_par_exigence(docs, list(colonnes))
        cellules += [
            ("B", Cellule(r)),
            ("C", Cellule(info.get("label", ""))),
            ("E", Cellule(f)),
            ("F", Cellule(info.get("order_number", ""))),
        ]
        na = {code for code in colonnes if ap.etat_exigence(docs, code) == ap.NA}
        cellules += [(colonnes[code], Cellule("N/A")) for code in colonnes if code in na]
        for code, doc in derniers.items():
            if code not in na:
                cellule = _cellule_document(projet.dossier, doc.chemin_relatif, doc.nom_stocke)
                cellules.append((colonnes[code], cellule))
        lignes.append(cellules)
    return lignes


def _lignes_cecc(projet, couples, groupes, infos) -> list:
    lignes = []
    for f, r in couples:
        info = infos.get((f, r), {})
        fiche = _plus_recent(groupes.get((f, r, "CECC"), []))
        cellules = [
            ("B", Cellule(r)),
            ("C", Cellule(info.get("label", ""))),
            ("E", Cellule(f)),
            ("F", Cellule(info.get("order_number", ""))),
        ]
        # E8 : D = MNP saisi pour l'article, H = MPN de la fiche (vide sans fiche).
        mnp = info.get("mnp", "")
        if mnp:
            cellules.append(("D", Cellule(mnp)))
        if fiche:
            champs = fiche.champs_cecc
            cellules += [
                ("G", Cellule(champs.get("manufacturer_doc", ""))),
                ("H", Cellule(champs.get("manufacturer_part_number", ""))),
                ("I", Cellule(ap.statut_cecc(champs))),
            ]
            nom = champs.get("nom_cecc", "") or fiche.nom_stocke
            cellules.append(("K", _cellule_document(projet.dossier, fiche.chemin_relatif, nom)))
            cellules += [
                (col, Cellule(ap.valeur_cecc(champs, cle)))
                for cle, _, col in CHAMPS_CECC
                if col not in ("G", "H", "I", "K")
            ]
        lignes.append(cellules)
    return lignes


def contenus(projet: Projet, enrs: list[Enregistrement] | None = None) -> list[ContenuExport]:
    """Contenu de chaque export des livrables suivis, dans l'ordre CE, CECC, DPE."""
    if enrs is None:
        enrs = base_projet.lire_tous(projet.dossier)
    groupes = _regrouper(enrs)
    infos = _infos_lignes(projet)
    couples = couples_a_exporter(projet)
    numero = projet.numero_dossier
    affaire = str(projet.donnees.get("project_name", numero))
    resultat = []
    for livrable in LIVRABLES:
        if livrable not in projet.livrables:
            continue
        if livrable == "CECC":
            lignes = _lignes_cecc(projet, couples, groupes, infos)
        else:
            lignes = _lignes_ce_dpe(projet, livrable, couples, groupes, infos)
        resultat.append(
            ContenuExport(
                livrable=livrable,
                sortie=chemin_export(projet, livrable),
                titre=f"BASE DE DONNEES {livrable} - {affaire}",
                onglet=f"BDD {livrable} {affaire}",
                lignes=lignes,
            )
        )
    return resultat


def chemin_export(projet: Projet, livrable: str) -> Path:
    racine = arborescence.dossier_livrable(projet.dossier, livrable, projet.numero_dossier)
    return racine / arborescence.nom_export(livrable, projet.numero_dossier)


def exporter(dossier: Path) -> list[tuple[Path, Path | None]]:
    """Exporte les livrables suivis ; retourne (fichier créé, ancienne version archivée).

    Aucun fichier n'est écrit si l'un des exports existants est ouvert (R27).
    """
    projet = projet_fichier.lire_projet(dossier)
    if projet is None:
        raise FileNotFoundError(f"Fichier projet introuvable dans {dossier}")
    a_ecrire = contenus(projet)
    for contenu in a_ecrire:
        export_excel.verifier_non_verrouille(contenu.sortie)
    return [(c.sortie, export_excel.ecrire(c)) for c in a_ecrire]


def message_de_fin(resultats: list[tuple[Path, Path | None]]) -> str:
    message = "Fichiers exportés :\n\n" + "\n".join(str(p) for p, _ in resultats)
    archives = [a for _, a in resultats if a]
    if archives:
        message += "\n\nAnciennes versions déplacées dans OLD :\n\n" + "\n".join(
            a.name for a in archives
        )
    return message
