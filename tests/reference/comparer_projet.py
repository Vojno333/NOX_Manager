"""
**Outil de la reprise, gelé** : il exécute l'ancienne application, qui n'est plus
dans le dossier. Pour le rejouer : `git worktree add ../nox-ancien v1-avant-refonte`,
puis passer ce dossier comme racine de l'ancien code.
Compare l'ancienne et la nouvelle application sur un vrai projet (recette, tâche 22).

Usage (depuis la racine du dépôt) :
    uv run python tests/reference/comparer_projet.py "<projet>" "<racine de l'ancien code>"

Confidentialité : le script n'affiche AUCUN contenu du projet (ni article, ni
nom de fichier, ni valeur) : seulement des nombres et un verdict.

Le projet d'origine est seulement lu. Le script en fait deux copies
temporaires, une pour chaque application : `.nox` complet, mêmes dossiers, et
les documents remplacés par des fichiers vides du même nom (seule leur
présence compte pour l'export). Les copies sont effacées à la fin.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Racine de l'ancien code : 2e argument (worktree de `v1-avant-refonte`).
sys.path.insert(0, str(Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEPOT / "00_ancien"))
sys.path.insert(0, str(DEPOT / "01_application"))


def copier(source: Path, cible: Path) -> Path:
    for dossier, sous_dossiers, fichiers in os.walk(source):
        rel = Path(dossier).relative_to(source)
        if rel.parts and rel.parts[-1] == "OLD":
            sous_dossiers.clear()
            continue
        (cible / rel).mkdir(parents=True, exist_ok=True)
        for nom in fichiers:
            if rel.parts and rel.parts[0] == ".nox":
                shutil.copy2(Path(dossier) / nom, cible / rel / nom)
            elif not (len(rel.parts) == 1 and nom.startswith("BDD_") and nom.endswith(".xlsx")):
                (cible / rel / nom).touch()
    fichier = cible / ".nox" / "project.json"
    if fichier.exists():
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
        donnees["project_path"] = str(cible)  # l'ancienne application suit ce chemin
        fichier.write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")
    return cible


def relever_export(chemin: Path, racine: Path) -> dict:
    from openpyxl import load_workbook

    ws = load_workbook(chemin).worksheets[0]
    cellules = {}
    for row in ws.iter_rows():
        for c in row:
            if c.value is None and not c.hyperlink:
                continue
            lien = (
                (c.hyperlink.target or "").replace(racine.as_posix(), "<P>")
                if c.hyperlink
                else None
            )
            cellules[c.coordinate] = (c.value, lien)
    return {"onglet": ws.title, "cellules": cellules}


def ancienne(projet: Path) -> tuple[list, dict, dict]:
    from PySide6 import QtWidgets
    from wikidocs_qt.export_templates import export_project_templates
    from wikidocs_qt.project_dashboard_window import ProjectDashboardWindow
    from wikidocs_qt.project_manager import ProjectManager

    _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])  # noqa: F841
    fenetre = ProjectDashboardWindow(ProjectManager().load_project(projet))
    cles = ("supplier", "reference", "label", "mnp", "order_number", "type", "completion")
    lignes = [tuple(r[k] for k in cles) for r in fenetre._all_rows_cache]
    kpi = {}
    for t in ("CE", "CECC", "DPE"):
        v = [r["completion_value"] for r in fenetre._all_rows_cache if r["type"] == t]
        kpi[t] = round(sum(v) / len(v) * 100) if v else 0
    fenetre.close()
    exports = {p.name: relever_export(p, projet) for p, _ in export_project_templates(projet)}
    return lignes, kpi, exports


def nouvelle(projet: Path) -> tuple[list, dict, dict]:
    from app.dataaccess import projet_fichier
    from app.services import completion, export

    suivi = completion.lignes_de_suivi(projet_fichier.lire_projet(projet))
    lignes = [
        (
            lg.fournisseur,
            lg.reference,
            lg.libelle,
            lg.mnp,
            lg.n_commande,
            lg.livrable,
            lg.completion_texte,
        )
        for lg in suivi
    ]
    exports = {p.name: relever_export(p, projet) for p, _ in export.exporter(projet)}
    return lignes, completion.indicateurs(suivi), exports


def main() -> None:
    source = Path(sys.argv[1]).resolve()
    if not (source / ".nox" / "project.json").exists():
        sys.exit("Ce dossier ne contient pas de .nox/project.json.")
    tmp = Path(tempfile.mkdtemp(prefix="nox_recette_"))
    try:
        a = ancienne(copier(source, tmp / "ancienne"))
        n = nouvelle(copier(source, tmp / "nouvelle"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ecarts = 0
    lignes_diff = sum(1 for x, y in zip(a[0], n[0], strict=False) if x != y)
    lignes_diff += abs(len(a[0]) - len(n[0]))
    ecarts += lignes_diff
    print(
        f"Tableau de suivi : {len(a[0])} lignes (ancienne), {len(n[0])} (nouvelle), "
        f"{lignes_diff} ligne(s) différente(s)"
    )
    kpi_diff = [t for t in ("CE", "CECC", "DPE") if a[1][t] != n[1][t]]
    ecarts += len(kpi_diff)
    etat_kpi = "identiques" if not kpi_diff else "différents pour " + ", ".join(kpi_diff)
    print(f"Indicateurs : {etat_kpi}")
    for nom in sorted(set(a[2]) | set(n[2])):
        ea, en = a[2].get(nom), n[2].get(nom)
        livrable = nom.split("_")[1] if "_" in nom else "?"
        if ea is None or en is None:
            ecarts += 1
            print(f"Export {livrable} : produit par une seule des deux applications")
            continue
        coords = set(ea["cellules"]) | set(en["cellules"])
        diff = sum(1 for c in coords if ea["cellules"].get(c) != en["cellules"].get(c))
        diff += ea["onglet"] != en["onglet"]
        ecarts += diff
        print(f"Export {livrable} : {len(coords)} cellules, {diff} différente(s)")
    print("\nVERDICT : " + ("CONFORME" if ecarts == 0 else f"{ecarts} ÉCART(S) — à analyser"))


if __name__ == "__main__":
    main()
