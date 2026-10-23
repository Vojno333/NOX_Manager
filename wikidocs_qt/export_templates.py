from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from openpyxl.styles import Font

from copy import copy
from openpyxl.formula.translate import Translator
from openpyxl.worksheet.cell_range import CellRange

from openpyxl import load_workbook

from .document_rules import REQ_NA, code_matches, doc_has_file, normalize_requirement_code, requirement_state
from .metadata_db import get_uploaded_documents
from .project_manager import get_project_file_path


CE_TEMPLATE_NAME = "Template_BDD_CE_N0X.xlsx"
CECC_TEMPLATE_NAME = "Template_BDD_CECC_N0X.xlsx"
DPE_TEMPLATE_NAME = "Template_BDD_DPE_N0X.xlsx"

def _sanitize_sheet_title(title: str) -> str:
    forbidden = '[]:*?/\\'
    cleaned = "".join("_" if c in forbidden else c for c in str(title).strip())
    cleaned = cleaned[:31]
    return cleaned or "Feuille"

def _set_hyperlink(cell, file_path: Path, display_name: str):
    """
    Ajoute un lien cliquable vers un fichier local.
    """

    if not file_path.exists():
        cell.value = display_name
        return

    cell.value = display_name

    # Excel aime les chemins avec /
    hyperlink_path = file_path.as_posix()

    cell.hyperlink = hyperlink_path
    cell.font = Font(color="0000FF", underline="single")


def _apply_project_identity(ws, template_type: str, project_name: str):
    """
    Met à jour :
    - le grand titre en haut de feuille
    - le nom de l'onglet
    """
    ws["B2"] = f"BASE DE DONNEES {template_type} - {project_name}"
    ws.title = _sanitize_sheet_title(f"BDD {template_type} {project_name}")


def _reset_sheet_view_to_a1(ws):
    """
    Force l'ouverture de la feuille sur A1.
    """
    if ws.sheet_view.selection:
        ws.sheet_view.selection[0].activeCell = "A1"
        ws.sheet_view.selection[0].sqref = "A1"

def _load_project_data(project_dir: Path) -> dict:
    project_file = get_project_file_path(project_dir)
    return json.loads(project_file.read_text(encoding="utf-8"))
def _get_not_applicable_map(project_data: dict) -> dict:
    """
    Retourne la map des exigences non applicables.

    Format attendu dans le .nox :
    {
        "not_applicable_requirements": {
            "CE": {
                "Fournisseur|Reference": ["2006/42/UE"]
            },
            "DPE": {
                "Fournisseur|Reference": ["2011/65/UE"]
            }
        }
    }
    """
    return project_data.get("not_applicable_requirements", {}) or {}


def _normalize_requirement_code(code: str) -> str:
    return normalize_requirement_code(code)


def _code_matches(a: str, b: str) -> bool:
    return code_matches(a, b)


def _is_not_applicable(docs: list[dict], requirement_code: str) -> bool:
    """N/A selon le DERNIER enregistrement mentionnant le code (même règle
    que le dashboard) : une exigence repassée Applicable n'est plus N/A."""
    return requirement_state(docs, requirement_code) == REQ_NA


def _safe_output_name(template_type: str, dossier_number: str) -> str:
    return f"BDD_{template_type}_{dossier_number}.xlsx"


def _group_docs(project_dir: Path):
    docs = get_uploaded_documents(project_dir)

    grouped = defaultdict(list)

    for doc in docs:
        supplier = doc["supplier"]
        reference = doc["reference"]

        source_type = str(doc["source_justification_type"]).upper()
        stored_bdds = doc.get("stored_in_bdds", []) or [source_type]

        for bdd_type in stored_bdds:
            key = (supplier, reference, str(bdd_type).upper())
            grouped[key].append(doc)

    return grouped


def _first_sheet(workbook):
    return workbook[workbook.sheetnames[0]]


def _sorted_docs(docs: list[dict]) -> list[dict]:
    return sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True)





def _first_doc(docs: list[dict]) -> dict | None:
    ordered = _sorted_docs(docs)
    return ordered[0] if ordered else None

def _latest_doc_by_requirement(
    docs: list[dict],
    expected_codes: list[str],
) -> dict[str, dict]:
    """
    Retourne un mapping :
        code attendu export -> document le plus récent couvrant cette exigence

    Permet de matcher :
    - "1907/2006"
    - "1907/2006 — REACh"
    - "1907/2006 | REACh"
    """
    latest: dict[str, dict] = {}

    for doc in _sorted_docs(docs):
        # Un enregistrement « applicabilité seule » n'a pas de fichier à lier.
        if not doc_has_file(doc):
            continue
        doc_codes = doc.get("requirement_codes", []) or []

        for expected_code in expected_codes:
            if expected_code in latest:
                continue

            for doc_code in doc_codes:
                if _code_matches(doc_code, expected_code):
                    latest[expected_code] = doc
                    break

    return latest

def _get_latest_cecc_mpn(docs_cecc: list[dict]) -> str:
    """
    Retourne le Manufacturer Part Number du
    dernier document CECC uploadé.
    """
    if not docs_cecc:
        return ""

    ordered = _sorted_docs(docs_cecc)

    first = ordered[0]

    cecc = first.get("cecc_fields", {}) or {}

    return cecc.get("manufacturer_part_number", "")


def _copy_cell(source_cell, target_cell):
    if source_cell.data_type == "f" and source_cell.value:
        try:
            target_cell.value = Translator(source_cell.value, origin=source_cell.coordinate).translate_formula(
                target_cell.coordinate
            )
        except Exception:
            target_cell.value = source_cell.value
    else:
        target_cell.value = source_cell.value

    if source_cell.has_style:
        target_cell._style = copy(source_cell._style)

    target_cell.font = copy(source_cell.font)
    target_cell.fill = copy(source_cell.fill)
    target_cell.border = copy(source_cell.border)
    target_cell.alignment = copy(source_cell.alignment)
    target_cell.protection = copy(source_cell.protection)
    target_cell.number_format = source_cell.number_format

def _copy_row(ws, source_row: int, target_row: int):
    for col in range(1, ws.max_column + 1):
        _copy_cell(ws.cell(source_row, col), ws.cell(target_row, col))

def _translate_rule_formulas(rule, origin_coord: str, target_coord: str):
    """
    Traduit les formules d'une règle de mise en forme conditionnelle
    quand on la recopie sur une autre zone.
    """
    new_rule = copy(rule)

    formulas = getattr(rule, "formula", None)
    if formulas:
        translated = []
        for formula in formulas:
            if not isinstance(formula, str):
                translated.append(formula)
                continue

            original = formula if formula.startswith("=") else f"={formula}"
            try:
                moved = Translator(original, origin=origin_coord).translate_formula(target_coord)
                if not formula.startswith("=") and moved.startswith("="):
                    moved = moved[1:]
                translated.append(moved)
            except Exception:
                translated.append(formula)

        new_rule.formula = translated

    return new_rule

def _extend_conditional_formatting_to_table_end(
    ws,
    table_start_row: int,
    template_table_end_row: int,
    new_table_end_row: int,
):
    """
    Étend les règles de mise en forme conditionnelle du tableau
    jusqu'à la vraie dernière ligne du tableau, sans toucher
    aux règles hors tableau.
    """
    cf = ws.conditional_formatting

    # On capture d'abord toutes les plages + règles existantes
    captured_blocks = []
    for cf_block in list(cf):
        captured_blocks.append({
            "ranges": list(cf_block.cells.ranges),
            "rules": [copy(rule) for rule in cf[cf_block]],
        })

    # Puis seulement après on vide
    cf._cf_rules.clear()

    # Et on recrée proprement
    for block in captured_blocks:
        rules = block["rules"]

        for sub_range in block["ranges"]:
            min_row = sub_range.min_row
            max_row = sub_range.max_row
            min_col = sub_range.min_col
            max_col = sub_range.max_col

            # Cas 1 : règle totalement dans le tableau template -> on l'étend
            if table_start_row <= min_row <= template_table_end_row and max_row <= template_table_end_row:
                new_min_row = min_row
                new_max_row = new_table_end_row
            else:
                # Cas 2 : règle hors tableau -> on la garde telle quelle
                new_min_row = min_row
                new_max_row = max_row

            if new_max_row < new_min_row:
                continue

            new_sub_range = CellRange(
                min_col=min_col,
                max_col=max_col,
                min_row=new_min_row,
                max_row=new_max_row,
            )

            source_anchor = ws.cell(min_row, min_col).coordinate
            target_anchor = ws.cell(new_min_row, min_col).coordinate

            for rule in rules:
                new_rule = _translate_rule_formulas(rule, source_anchor, target_anchor)
                cf.add(str(new_sub_range), new_rule)

def _copy_bottom_border_row(ws, source_row: int, target_row: int):
    """
    Copie toute la ligne de fin de tableau (style + bordures),
    sans recopier les valeurs.
    """
    for col in range(1, ws.max_column + 1):
        src = ws.cell(source_row, col)
        dst = ws.cell(target_row, col)

        if src.has_style:
            dst._style = copy(src._style)

        dst.font = copy(src.font)
        dst.fill = copy(src.fill)
        dst.border = copy(src.border)
        dst.alignment = copy(src.alignment)
        dst.protection = copy(src.protection)
        dst.number_format = src.number_format
        dst.value = None

def _clear_bottom_border_row(ws, row_idx: int):
    """
    Efface visuellement l'ancienne ligne de fin de tableau.
    """
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row_idx, col)
        cell.value = None
        cell.border = copy(ws.cell(row_idx - 1, col).border)
        cell.fill = copy(ws.cell(row_idx - 1, col).fill)

def _apply_footer_spacing(ws, proved_row: int, estimated_row: int, blank_rows: int = 2):
    """
    Insère des lignes vides avant le footer pour laisser un espace visuel.
    """
    ws.insert_rows(proved_row, blank_rows)
    return proved_row + blank_rows, estimated_row + blank_rows

def _clear_row_values(ws, row_idx: int):
    for col in range(1, ws.max_column + 1):
        ws.cell(row_idx, col).value = None

def _resize_table_area(
    ws,
    required_rows: int,
    start_row: int = 5,
    footer_row_1: int = 235,
    footer_row_2: int = 236,
):
    """
    Adapte la hauteur du tableau :
    - la première ligne de données est start_row
    - la dernière ligne de données template avant la ligne de fin de tableau est footer_row_1 - 2
    - la ligne footer_row_1 - 1 est la ligne de fin de tableau
    - footer_row_1/footer_row_2 contiennent les taux de couverture
    """
    table_end_template_row = footer_row_1 - 1
    template_data_rows = table_end_template_row - start_row
    model_row = start_row

    if required_rows > template_data_rows:
        extra = required_rows - template_data_rows
        insert_at = table_end_template_row
        ws.insert_rows(insert_at, extra)

        for i in range(extra):
            target_row = insert_at + i
            _copy_row(ws, model_row, target_row)


        table_end_row = table_end_template_row + extra
        proved_row = footer_row_1 + extra
        estimated_row = footer_row_2 + extra

    elif required_rows < template_data_rows:
        rows_to_delete = template_data_rows - required_rows
        delete_start = start_row + required_rows
        ws.delete_rows(delete_start, rows_to_delete)

        table_end_row = start_row + required_rows
        proved_row = table_end_row + 1
        estimated_row = table_end_row + 2

    else:
        table_end_row = table_end_template_row
        proved_row = footer_row_1
        estimated_row = footer_row_2

    # Repositionne la ligne de fin de tableau
    if table_end_row != table_end_template_row:
        _copy_bottom_border_row(ws, table_end_template_row, table_end_row)
        _clear_bottom_border_row(ws, table_end_template_row)

    _extend_conditional_formatting_to_table_end(
        ws,
        table_start_row=start_row,
        template_table_end_row=table_end_template_row,
        new_table_end_row=table_end_row - 1,
    )
    return table_end_row, proved_row, estimated_row


def _prepare_data_rows(ws, row_count: int, start_row: int = 5):
    for row in range(start_row, start_row + row_count):
        for col in range(1, ws.max_column + 1):
            ws.cell(row, col).value = None

def _rows_lookup(project_data: dict) -> dict[tuple[str, str], dict]:
    """
    Associe chaque couple (fournisseur, référence) à sa ligne du projet
    (`project.json` → "rows"), qui porte le libellé, le MNP et le n° de
    commande saisis à la création/édition du projet.
    """
    lookup: dict[tuple[str, str], dict] = {}

    for row in project_data.get("rows", []) or []:
        supplier = str(row.get("supplier", "")).strip()
        reference = str(row.get("reference", "")).strip()
        if supplier and reference:
            lookup[(supplier, reference)] = row

    return lookup


def _scan_supplier_reference_pairs(
    project_dir: Path,
    dossier_number: str,
    project_data: dict | None = None,
) -> list[tuple[str, str]]:
    """
    Détermine la liste des couples (fournisseur, référence) à exporter.

    Source de vérité : `project.json` → "rows", exactement comme le tableau
    du dashboard — pour que l'export n'ait ni trou (référence absente parce
    que son dossier a été renommé/supprimé à la main, ou non créé pour la
    première BDD scannée) ni décalage (le nom de dossier passe par
    `_safe_name()` à la création et peut différer du texte saisi, ce qui
    cassait le rattachement du libellé/MNP/n° de commande).

    Le scan des dossiers `Documents/` ne sert plus qu'en repli, pour les
    projets anciens dont le fichier n'aurait pas (ou plus) de "rows".
    """
    rows = (project_data or {}).get("rows") or []
    pairs = [
        (str(r.get("supplier", "")).strip(), str(r.get("reference", "")).strip())
        for r in rows
        if str(r.get("supplier", "")).strip()
    ]
    if pairs:
        return sorted(set(pairs), key=lambda x: (x[0].lower(), x[1].lower()))

    pairs = []
    for bdd_type in ("CE", "CECC", "DPE"):
        docs_dir = project_dir / f"BDD {bdd_type} {dossier_number}" / "Documents"
        if not docs_dir.exists():
            continue

        for supplier_dir in docs_dir.iterdir():
            if not supplier_dir.is_dir():
                continue

            for ref_dir in supplier_dir.iterdir():
                if ref_dir.is_dir():
                    pairs.append((supplier_dir.name, ref_dir.name))

        if pairs:
            break

    return sorted(set(pairs), key=lambda x: (x[0].lower(), x[1].lower()))


def _fill_ce_sheet(ws, pairs, grouped_docs, project_dir, project_data):
    start_row = 5
    rows_lookup = _rows_lookup(project_data)

    ce_column_map = {
        "2006/42/UE": "H",
        "2014/35/UE": "I",
        "2011/65/UE": "J",
        "2015/863": "K",    # alias RoHS : même contenu que J
        "2014/30/UE": "L",
        "2014/68/UE": "M",
        "AUTRES": "N",
    }

    table_end_row, proved_row, estimated_row = _resize_table_area(
        ws, len(pairs), start_row=start_row, footer_row_1=235, footer_row_2=236
    )
    _prepare_data_rows(ws, len(pairs), start_row=start_row)
    proved_row, estimated_row = _apply_footer_spacing(ws, proved_row, estimated_row, blank_rows=2)

    for i, (supplier, reference) in enumerate(pairs, start=start_row):
        row_info = rows_lookup.get((supplier, reference), {})

        docs_cecc = grouped_docs.get((supplier, reference, "CECC"), [])
        mpn = _get_latest_cecc_mpn(docs_cecc) or row_info.get("mnp", "")

        if mpn:
            ws[f"D{i}"] = mpn

        docs = grouped_docs.get((supplier, reference, "CE"), [])
        latest_by_requirement = _latest_doc_by_requirement(
    docs,
    list(ce_column_map.keys())
)

        ws[f"B{i}"] = reference
        ws[f"C{i}"] = row_info.get("label", "")
        ws[f"E{i}"] = supplier
        ws[f"F{i}"] = row_info.get("order_number", "")

        for code, col in ce_column_map.items():
            if _is_not_applicable(docs, code):
                ws[f"{col}{i}"] = "N/A"

        for code, doc in latest_by_requirement.items():
            col = ce_column_map.get(code)
            if not col:
                continue

            if _is_not_applicable(docs, code):
                continue

            filename = doc.get("stored_filename", "")
            relative_path = doc.get("relative_path", "")
            full_path = project_dir / relative_path

            cell = ws[f"{col}{i}"]
            _set_hyperlink(cell, full_path, filename)

    last_data_row = start_row + max(len(pairs), 1) - 1
    _update_ce_footer_formulas(ws, proved_row, estimated_row, last_data_row)


def _fill_dpe_sheet(ws, pairs, grouped_docs, project_dir, project_data):
    start_row = 5
    rows_lookup = _rows_lookup(project_data)

    dpe_column_map = {
        "2011/65/UE": "H",
        "2012/19/UE": "I",
        "2006/66/CE": "J",
        "1907/2006": "K",
        "2019/1021": "L",
        "1005/2009": "M",
        "517/2014": "N",
        "2017/852": "O",
        "528/2012": "P",
        "2013/59/Euratom": "Q",
        "2017/821": "R",
        "2016/1628": "S",
    }

    table_end_row, proved_row, estimated_row = _resize_table_area(
        ws, len(pairs), start_row=start_row, footer_row_1=235, footer_row_2=236
    )
    _prepare_data_rows(ws, len(pairs), start_row=start_row)
    proved_row, estimated_row = _apply_footer_spacing(ws, proved_row, estimated_row, blank_rows=2)

    for i, (supplier, reference) in enumerate(pairs, start=start_row):
        row_info = rows_lookup.get((supplier, reference), {})

        docs_cecc = grouped_docs.get((supplier, reference, "CECC"), [])
        mpn = _get_latest_cecc_mpn(docs_cecc) or row_info.get("mnp", "")

        if mpn:
            ws[f"D{i}"] = mpn

        docs = grouped_docs.get((supplier, reference, "DPE"), [])
        latest_by_requirement = _latest_doc_by_requirement(
    docs,
    list(dpe_column_map.keys())
)

        ws[f"B{i}"] = reference
        ws[f"C{i}"] = row_info.get("label", "")
        ws[f"E{i}"] = supplier
        ws[f"F{i}"] = row_info.get("order_number", "")

        for code, col in dpe_column_map.items():
            if _is_not_applicable(docs, code):
                ws[f"{col}{i}"] = "N/A"

        for code, doc in latest_by_requirement.items():
            col = dpe_column_map.get(code)
            if not col:
                continue

            if _is_not_applicable(docs, code):
                continue

            filename = doc.get("stored_filename", "")
            relative_path = doc.get("relative_path", "")
            full_path = project_dir / relative_path

            cell = ws[f"{col}{i}"]
            _set_hyperlink(cell, full_path, filename)

    last_data_row = start_row + max(len(pairs), 1) - 1
    _update_dpe_footer_formulas(ws, proved_row, estimated_row, last_data_row)


def _fill_cecc_sheet(ws, pairs, grouped_docs, project_dir, project_data):
    start_row = 5
    rows_lookup = _rows_lookup(project_data)

    table_end_row, proved_row, estimated_row = _resize_table_area(
        ws, len(pairs), start_row=start_row, footer_row_1=235, footer_row_2=236
    )
    _prepare_data_rows(ws, len(pairs), start_row=start_row)
    proved_row, estimated_row = _apply_footer_spacing(ws, proved_row, estimated_row, blank_rows=2)

    for i, (supplier, reference) in enumerate(pairs, start=start_row):
        row_info = rows_lookup.get((supplier, reference), {})
        docs = grouped_docs.get((supplier, reference, "CECC"), [])
        first = _first_doc(docs)

        ws[f"B{i}"] = reference
        ws[f"C{i}"] = row_info.get("label", "")
        ws[f"E{i}"] = supplier
        ws[f"F{i}"] = row_info.get("order_number", "")

        mpn = row_info.get("mnp", "")
        if mpn:
            ws[f"D{i}"] = mpn

        if not first:
            continue

        cecc = first.get("cecc_fields", {})

        manufacturer_mpn = cecc.get("manufacturer_part_number", "") or mpn
        if manufacturer_mpn:
            ws[f"D{i}"] = manufacturer_mpn
        ws[f"G{i}"] = cecc.get("manufacturer_doc", "")
        ws[f"H{i}"] = manufacturer_mpn
        ws[f"I{i}"] = cecc.get("status", "")

        # Colonne K = Nom du document CECC + lien cliquable
        display_name = cecc.get("nom_cecc", "") or first.get("stored_filename", "")
        relative_path = first.get("relative_path", "")
        full_path = project_dir / relative_path

        _set_hyperlink(
            ws[f"K{i}"],
            full_path,
            display_name,
        )

        ws[f"L{i}"] = cecc.get("cecc_classement", "")
        ws[f"M{i}"] = cecc.get("categorie_export", "")
        ws[f"N{i}"] = cecc.get("licence", "")
        ws[f"O{i}"] = cecc.get("numero_licence", "")
        ws[f"P{i}"] = cecc.get("pays_origine_4a", "")

    last_data_row = start_row + max(len(pairs), 1) - 1
    _update_cecc_footer_formulas(ws, proved_row, estimated_row, last_data_row)


OLD_EXPORTS_DIRNAME = "OLD"


def _locked_message(output: Path) -> str:
    return (
        f"Impossible d'archiver l'ancien export :\n{output}\n\n"
        f"Le fichier est probablement ouvert dans Excel : fermez-le puis relancez l'export."
    )


def _ensure_not_locked(output: Path) -> None:
    if not output.exists():
        return
    try:
        with output.open("r+b"):
            pass
    except PermissionError as e:
        raise PermissionError(_locked_message(output)) from e


def _archive_previous_export(output: Path) -> Path | None:
    """Déplace l'export existant dans `<dossier>/OLD/<nom>_V_<date de dernière
    modification>.xlsx` avant qu'il soit remplacé. Retourne le chemin archivé,
    ou None s'il n'y avait pas d'ancienne version."""
    if not output.exists():
        return None

    old_dir = output.parent / OLD_EXPORTS_DIRNAME
    old_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.fromtimestamp(output.stat().st_mtime).strftime("%Y-%m-%d_%Hh%M")
    target = old_dir / f"{output.stem}_V_{stamp}{output.suffix}"
    i = 2
    while target.exists():
        target = old_dir / f"{output.stem}_V_{stamp} ({i}){output.suffix}"
        i += 1

    try:
        shutil.move(str(output), str(target))
    except PermissionError as e:
        raise PermissionError(_locked_message(output)) from e
    return target


def _save_versioned(workbook, output: Path) -> Path | None:
    """Archive l'éventuelle version précédente puis enregistre le classeur."""
    output.parent.mkdir(parents=True, exist_ok=True)
    archived = _archive_previous_export(output)
    workbook.save(output)
    return archived


def export_project_templates(project_dir: Path) -> list[tuple[Path, Path | None]]:
    """Remplit les templates des BDD activées.

    Retourne, pour chaque export, (fichier créé, ancienne version archivée
    dans OLD ou None).
    """
    project_data = _load_project_data(project_dir)
    dossier_number = project_data["dossier_number"]
    project_name = project_data.get("project_name", dossier_number)
    enabled_bdds = project_data.get("enabled_bdds", ["CE", "CECC", "DPE"])

    grouped_docs = _group_docs(project_dir)
    pairs = _scan_supplier_reference_pairs(project_dir, dossier_number, project_data)

    base_dir = Path(__file__).resolve().parent.parent

    ce_template = base_dir / CE_TEMPLATE_NAME
    cecc_template = base_dir / CECC_TEMPLATE_NAME
    dpe_template = base_dir / DPE_TEMPLATE_NAME

    if not ce_template.exists():
        raise FileNotFoundError(f"Template introuvable : {ce_template.name}")
    if not cecc_template.exists():
        raise FileNotFoundError(f"Template introuvable : {cecc_template.name}")
    if not dpe_template.exists():
        raise FileNotFoundError(f"Template introuvable : {dpe_template.name}")

    # Vérifie AVANT d'écrire quoi que ce soit qu'aucun export existant n'est
    # ouvert (Excel le verrouille) : évite un export à moitié fait.
    for t in ("CE", "CECC", "DPE"):
        if t in enabled_bdds:
            _ensure_not_locked(project_dir / f"BDD {t} {dossier_number}" / _safe_output_name(t, dossier_number))

    exports = []

    if "CE" in enabled_bdds:
        ce_output = project_dir / f"BDD CE {dossier_number}" / _safe_output_name("CE", dossier_number)

        wb_ce = load_workbook(ce_template)
        ws_ce = _first_sheet(wb_ce)
        _apply_project_identity(ws_ce, "CE", project_name)
        _fill_ce_sheet(ws_ce, pairs, grouped_docs, project_dir, project_data)
        _reset_sheet_view_to_a1(ws_ce)
        exports.append((ce_output, _save_versioned(wb_ce, ce_output)))

    if "CECC" in enabled_bdds:
        cecc_output = project_dir / f"BDD CECC {dossier_number}" / _safe_output_name("CECC", dossier_number)

        wb_cecc = load_workbook(cecc_template)
        ws_cecc = _first_sheet(wb_cecc)
        _apply_project_identity(ws_cecc, "CECC", project_name)
        _fill_cecc_sheet(ws_cecc, pairs, grouped_docs, project_dir, project_data)
        _reset_sheet_view_to_a1(ws_cecc)
        exports.append((cecc_output, _save_versioned(wb_cecc, cecc_output)))

    if "DPE" in enabled_bdds:
        dpe_output = project_dir / f"BDD DPE {dossier_number}" / _safe_output_name("DPE", dossier_number)

        wb_dpe = load_workbook(dpe_template)
        ws_dpe = _first_sheet(wb_dpe)
        _apply_project_identity(ws_dpe, "DPE", project_name)
        _fill_dpe_sheet(ws_dpe, pairs, grouped_docs, project_dir, project_data)
        _reset_sheet_view_to_a1(ws_dpe)
        exports.append((dpe_output, _save_versioned(wb_dpe, dpe_output)))

    return exports

def _update_ce_footer_formulas(ws, proved_row: int, estimated_row: int, last_data_row: int):
    requirement_cols = ["H", "I", "J", "K", "L", "M"]

    ws[f"C{proved_row}"] = f'=AVERAGE({requirement_cols[0]}{proved_row}:{requirement_cols[-1]}{proved_row})'
    ws[f"C{estimated_row}"] = f'=AVERAGE({requirement_cols[0]}{estimated_row}:{requirement_cols[-1]}{estimated_row})'

    for col in requirement_cols:
        ws[f"{col}{proved_row}"] = f'=IFERROR((COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"*estimation*")-COUNTIF({col}5:{col}{last_data_row},"N/A"))/(COUNTBLANK({col}5:{col}{last_data_row})+COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"N/A")),0)'
        ws[f"{col}{estimated_row}"] = f'=IFERROR((COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"N/A"))/(COUNTBLANK({col}5:{col}{last_data_row})+COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"N/A")),0)'

def _update_dpe_footer_formulas(ws, proved_row: int, estimated_row: int, last_data_row: int):
    requirement_cols = ["H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]

    ws[f"C{proved_row}"] = f'=AVERAGE({requirement_cols[0]}{proved_row}:{requirement_cols[-1]}{proved_row})'
    ws[f"C{estimated_row}"] = f'=AVERAGE({requirement_cols[0]}{estimated_row}:{requirement_cols[-1]}{estimated_row})'

    for col in requirement_cols:
        ws[f"{col}{proved_row}"] = f'=IFERROR((COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"*estimation*")-COUNTIF({col}5:{col}{last_data_row},"N/A"))/(COUNTBLANK({col}5:{col}{last_data_row})+COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"N/A")),0)'
        ws[f"{col}{estimated_row}"] = f'=IFERROR((COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"N/A"))/(COUNTBLANK({col}5:{col}{last_data_row})+COUNTA({col}5:{col}{last_data_row})-COUNTIF({col}5:{col}{last_data_row},"N/A")),0)'
    
def _update_cecc_footer_formulas(ws, proved_row: int, estimated_row: int, last_data_row: int):
    status_range = f"$I$5:$I${last_data_row}"
    denominator = f'(COUNTIF({status_range},"Validé")+COUNTIF({status_range},"Relancé")+COUNTIF({status_range},"Non conforme")+COUNTIF({status_range},"Estimation"))'

    ws[f"C{proved_row}"] = f'=IFERROR(COUNTIF({status_range},"Validé")/{denominator},0)'
    ws[f"C{estimated_row}"] = f'=IFERROR((COUNTIF({status_range},"Validé")+COUNTIF({status_range},"Estimation"))/{denominator},0)'

