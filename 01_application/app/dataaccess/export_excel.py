"""Écriture des exports Excel dans les modèles `Template_BDD_*_N0X.xlsx`.

Mécanique du classeur seulement : le contenu des cellules est décidé par
`services/export.py`. Repris de `00_ancien/wikidocs_qt/export_templates.py`.
"""

from __future__ import annotations

import shutil
from copy import copy
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.formula.translate import Translator
from openpyxl.styles import Font
from openpyxl.worksheet.cell_range import CellRange

from app.core.config import ressource
from app.models.export import ContenuExport

DOSSIER_ARCHIVES = "OLD"
PREMIERE_LIGNE = 5
PIED_1, PIED_2 = 235, 236  # lignes des taux de couverture dans les modèles

_COLONNES_PIED = {
    "CE": ["H", "I", "J", "K", "L", "M"],
    "DPE": ["H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"],
}


def nom_modele(livrable: str) -> str:
    return f"Template_BDD_{livrable}_N0X.xlsx"


# ── Fichier ouvert, archivage ──
def message_verrou(sortie: Path) -> str:
    return (
        f"Impossible d'archiver l'ancien export :\n{sortie}\n\n"
        f"Le fichier est probablement ouvert dans Excel : fermez-le puis relancez l'export."
    )


def verifier_non_verrouille(sortie: Path) -> None:
    """PermissionError si l'export existant est ouvert (Excel le verrouille)."""
    if not sortie.exists():
        return
    try:
        with sortie.open("r+b"):
            pass
    except PermissionError as e:
        raise PermissionError(message_verrou(sortie)) from e


def archiver(sortie: Path) -> Path | None:
    """Déplace l'export existant dans `OLD/<nom>_V_<date de modification>.xlsx`."""
    if not sortie.exists():
        return None
    archives = sortie.parent / DOSSIER_ARCHIVES
    archives.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.fromtimestamp(sortie.stat().st_mtime).strftime("%Y-%m-%d_%Hh%M")
    cible = archives / f"{sortie.stem}_V_{horodatage}{sortie.suffix}"
    i = 2
    while cible.exists():
        cible = archives / f"{sortie.stem}_V_{horodatage} ({i}){sortie.suffix}"
        i += 1
    try:
        shutil.move(str(sortie), str(cible))
    except PermissionError as e:
        raise PermissionError(message_verrou(sortie)) from e
    return cible


# ── Copie de lignes et de styles ──
def _copier_style(source, cible) -> None:
    if source.has_style:
        cible._style = copy(source._style)
    cible.font = copy(source.font)
    cible.fill = copy(source.fill)
    cible.border = copy(source.border)
    cible.alignment = copy(source.alignment)
    cible.protection = copy(source.protection)
    cible.number_format = source.number_format


def _copier_cellule(source, cible) -> None:
    if source.data_type == "f" and source.value:
        try:
            cible.value = Translator(source.value, origin=source.coordinate).translate_formula(
                cible.coordinate
            )
        except Exception:  # formule non traduisible : recopiée telle quelle
            cible.value = source.value
    else:
        cible.value = source.value
    _copier_style(source, cible)


def _copier_ligne(ws, source: int, cible: int) -> None:
    for col in range(1, ws.max_column + 1):
        _copier_cellule(ws.cell(source, col), ws.cell(cible, col))


def _traduire_regle(regle, origine: str, cible: str):
    nouvelle = copy(regle)
    formules = getattr(regle, "formula", None)
    if formules:
        traduites = []
        for formule in formules:
            if not isinstance(formule, str):
                traduites.append(formule)
                continue
            texte = formule if formule.startswith("=") else f"={formule}"
            try:
                deplacee = Translator(texte, origin=origine).translate_formula(cible)
                if not formule.startswith("=") and deplacee.startswith("="):
                    deplacee = deplacee[1:]
                traduites.append(deplacee)
            except Exception:  # formule non traduisible : gardée telle quelle
                traduites.append(formule)
        nouvelle.formula = traduites
    return nouvelle


def _etendre_mise_en_forme(ws, debut: int, fin_modele: int, nouvelle_fin: int) -> None:
    """Étend jusqu'à la dernière ligne du tableau les règles de mise en forme
    conditionnelle du tableau, sans toucher à celles qui sont hors tableau."""
    mef = ws.conditional_formatting
    blocs = [
        {"plages": list(bloc.cells.ranges), "regles": [copy(r) for r in mef[bloc]]}
        for bloc in list(mef)
    ]
    mef._cf_rules.clear()
    for bloc in blocs:
        for plage in bloc["plages"]:
            dans_tableau = debut <= plage.min_row <= fin_modele and plage.max_row <= fin_modele
            max_row = nouvelle_fin if dans_tableau else plage.max_row
            if max_row < plage.min_row:
                continue
            nouvelle = CellRange(
                min_col=plage.min_col, max_col=plage.max_col, min_row=plage.min_row, max_row=max_row
            )
            ancre = ws.cell(plage.min_row, plage.min_col).coordinate
            for regle in bloc["regles"]:
                mef.add(str(nouvelle), _traduire_regle(regle, ancre, ancre))


def _copier_ligne_de_fin(ws, source: int, cible: int) -> None:
    for col in range(1, ws.max_column + 1):
        dst = ws.cell(cible, col)
        _copier_style(ws.cell(source, col), dst)
        dst.value = None


def _effacer_ligne_de_fin(ws, ligne: int) -> None:
    for col in range(1, ws.max_column + 1):
        cellule = ws.cell(ligne, col)
        cellule.value = None
        cellule.border = copy(ws.cell(ligne - 1, col).border)
        cellule.fill = copy(ws.cell(ligne - 1, col).fill)


def _ajuster_tableau(ws, nb_lignes: int) -> tuple[int, int]:
    """Adapte la hauteur du tableau du modèle à `nb_lignes` ; retourne les
    lignes des deux taux de couverture."""
    fin_modele = PIED_1 - 1  # ligne de fin de tableau du modèle
    lignes_modele = fin_modele - PREMIERE_LIGNE
    if nb_lignes > lignes_modele:
        extra = nb_lignes - lignes_modele
        ws.insert_rows(fin_modele, extra)
        for i in range(extra):
            _copier_ligne(ws, PREMIERE_LIGNE, fin_modele + i)
        fin, pied_1, pied_2 = fin_modele + extra, PIED_1 + extra, PIED_2 + extra
    elif nb_lignes < lignes_modele:
        ws.delete_rows(PREMIERE_LIGNE + nb_lignes, lignes_modele - nb_lignes)
        fin = PREMIERE_LIGNE + nb_lignes
        pied_1, pied_2 = fin + 1, fin + 2
    else:
        fin, pied_1, pied_2 = fin_modele, PIED_1, PIED_2
    if fin != fin_modele:
        _copier_ligne_de_fin(ws, fin_modele, fin)
        _effacer_ligne_de_fin(ws, fin_modele)
    _etendre_mise_en_forme(ws, PREMIERE_LIGNE, fin_modele, fin - 1)
    return pied_1, pied_2


def _vider_lignes(ws, nb_lignes: int) -> None:
    for ligne in range(PREMIERE_LIGNE, PREMIERE_LIGNE + nb_lignes):
        for col in range(1, ws.max_column + 1):
            ws.cell(ligne, col).value = None


# ── Pied de tableau (R26) ──
def _formules_ce_dpe(ws, colonnes: list[str], pied_1: int, pied_2: int, derniere: int) -> None:
    ws[f"C{pied_1}"] = f"=AVERAGE({colonnes[0]}{pied_1}:{colonnes[-1]}{pied_1})"
    ws[f"C{pied_2}"] = f"=AVERAGE({colonnes[0]}{pied_2}:{colonnes[-1]}{pied_2})"
    for c in colonnes:
        p = f"{c}5:{c}{derniere}"
        base = f'(COUNTBLANK({p})+COUNTA({p})-COUNTIF({p},"N/A"))'
        ws[f"{c}{pied_1}"] = (
            f'=IFERROR((COUNTA({p})-COUNTIF({p},"*estimation*")-COUNTIF({p},"N/A"))/{base},0)'
        )
        ws[f"{c}{pied_2}"] = f'=IFERROR((COUNTA({p})-COUNTIF({p},"N/A"))/{base},0)'


def _formules_cecc(ws, pied_1: int, pied_2: int, derniere: int) -> None:
    p = f"$I$5:$I${derniere}"
    total = (
        f'(COUNTIF({p},"Validé")+COUNTIF({p},"Relancé")'
        f'+COUNTIF({p},"Non conforme")+COUNTIF({p},"Estimation"))'
    )
    ws[f"C{pied_1}"] = f'=IFERROR(COUNTIF({p},"Validé")/{total},0)'
    ws[f"C{pied_2}"] = f'=IFERROR((COUNTIF({p},"Validé")+COUNTIF({p},"Estimation"))/{total},0)'


# ── Écriture ──
def _titre_d_onglet(titre: str) -> str:
    nettoye = "".join("_" if c in "[]:*?/\\" else c for c in str(titre).strip())[:31]
    return nettoye or "Feuille"


def _ecrire_cellule(ws, coordonnee: str, valeur, lien: Path | None) -> None:
    cellule = ws[coordonnee]
    cellule.value = valeur
    if lien is not None:
        cellule.hyperlink = lien.as_posix()
        cellule.font = Font(color="0000FF", underline="single")


def ecrire(contenu: ContenuExport) -> Path | None:
    """Remplit le modèle, archive l'export précédent puis enregistre.

    Retourne le chemin de l'ancienne version archivée, ou None.
    """
    classeur = load_workbook(ressource(nom_modele(contenu.livrable)))
    ws = classeur[classeur.sheetnames[0]]
    ws["B2"] = contenu.titre
    ws.title = _titre_d_onglet(contenu.onglet)

    nb = len(contenu.lignes)
    pied_1, pied_2 = _ajuster_tableau(ws, nb)
    _vider_lignes(ws, nb)
    ws.insert_rows(pied_1, 2)  # deux lignes vides avant le pied de tableau
    pied_1, pied_2 = pied_1 + 2, pied_2 + 2

    for i, cellules in enumerate(contenu.lignes, start=PREMIERE_LIGNE):
        for colonne, cellule in cellules:
            _ecrire_cellule(ws, f"{colonne}{i}", cellule.valeur, cellule.lien)

    derniere = PREMIERE_LIGNE + max(nb, 1) - 1
    if contenu.livrable == "CECC":
        _formules_cecc(ws, pied_1, pied_2, derniere)
    else:
        _formules_ce_dpe(ws, _COLONNES_PIED[contenu.livrable], pied_1, pied_2, derniere)

    if ws.sheet_view.selection:
        ws.sheet_view.selection[0].activeCell = "A1"
        ws.sheet_view.selection[0].sqref = "A1"

    contenu.sortie.parent.mkdir(parents=True, exist_ok=True)
    archive = archiver(contenu.sortie)
    classeur.save(contenu.sortie)
    return archive
