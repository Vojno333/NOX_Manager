"""Construit le projet d'essai et enregistre les résultats de référence.

Étape R4 de la reprise : on fait produire par l'application ACTUELLE les
résultats observables (pourcentages du tableau de suivi, contenu des exports
Excel, arborescence) sur un projet d'essai au format réel. La nouvelle
application devra produire les mêmes résultats sur le même projet (R31).

Usage :
    py tests/reference/construire_reference.py [racine_de_l_ancien_code]

La racine par défaut est la racine du dépôt ; après le gel (R5), passer
`00_ancien`.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEPOT = ICI.parent.parent
PROJET = ICI / "projet_essai"
ATTENDU = ICI / "attendu"

DOSSIER = "N999"
AFFAIRE = "AFF-ESSAI"

# ── Articles du projet ────────────────────────────────────────────────────────
# La 2e ligne ACME / REF-001 est un doublon (autre n° de commande) : l'appli
# actuelle ne garde que la première (R3). Elle servira aussi à tester E1.
ROWS = [
    {
        "supplier": "ACME",
        "reference": "REF-001",
        "label": "Vis inox M6",
        "mnp": "MNP-001",
        "order_number": "CMD-1",
    },
    {
        "supplier": "ACME",
        "reference": "REF-001",
        "label": "Vis inox M6",
        "mnp": "MNP-001",
        "order_number": "CMD-1B",
    },
    {
        "supplier": "ACME",
        "reference": "REF-002",
        "label": "Écrou frein",
        "mnp": "MNP-002",
        "order_number": "CMD-2",
    },
    {
        "supplier": "BETA",
        "reference": "REF-010",
        "label": "Moteur 24V",
        "mnp": "MNP-010",
        "order_number": "CMD-10",
    },
    {
        "supplier": "DELTA",
        "reference": "REF-030",
        "label": "Câble",
        "mnp": "MNP-030",
        "order_number": "CMD-30",
    },
    {"supplier": "EPS", "reference": "REF-040", "label": "Capot", "mnp": "", "order_number": ""},
    {
        "supplier": "GAMMA",
        "reference": "REF-020",
        "label": "Carte E/S",
        "mnp": "MNP-020",
        "order_number": "CMD-20",
    },
]

CE_ALL = ["2006/42/UE", "2014/35/UE", "2011/65/UE", "2015/863", "2014/30/UE", "2014/68/UE"]
DPE_ALL = [
    "2011/65/UE",
    "2012/19/UE",
    "2006/66/CE",
    "1907/2006",
    "2019/1021",
    "1005/2009",
    "517/2014",
    "2017/852",
    "528/2012",
    "2013/59/Euratom",
    "2017/821",
    "2016/1628",
]


def _bdd_dir(t: str) -> str:
    return f"BDD {t} {DOSSIER}"


def _doc_path(t: str, sup: str, ref: str, name: str) -> str:
    return f"{_bdd_dir(t)}/Documents/{sup}/{ref}/{name}"


def _rec(sup, ref, src, stored, req=(), app=(), na=(), cecc=None, name="", path="", at=""):
    return dict(
        supplier=sup,
        reference=ref,
        source_justification_type=src,
        stored_in_bdds=list(stored),
        requirement_codes=list(req),
        requirement_labels=list(req),
        cecc_fields=cecc or {},
        original_filename=name,
        stored_filename=name,
        relative_path=path,
        uploaded_at=at,
        not_applicable_codes=list(na),
        not_applicable_labels=list(na),
        applicable_codes=list(app),
    )


def _records() -> list[dict]:
    """Chaque bloc illustre une ou plusieurs règles de docs/besoin/besoin.md."""
    r = []
    # ACME / REF-001, CE — R15, R17 : 3 applicables (Machine, RoHS, CEM),
    # Machine et CEM couvertes, RoHS sans document → 2/3.
    n = "CE_ACME_REF-001.pdf"
    r.append(
        _rec(
            "ACME",
            "REF-001",
            "CE",
            ["CE"],
            req=["2006/42/UE", "2014/30/UE"],
            app=["2006/42/UE", "2011/65/UE", "2015/863", "2014/30/UE"],
            na=["2014/35/UE", "2014/68/UE"],
            name=n,
            path=_doc_path("CE", "ACME", "REF-001", n),
            at="2026-01-10T09:00:00",
        )
    )

    # ACME / REF-002, CE — R17/R18 : Machine couverte par un document normal
    # et une estimation (½). R15 : Basse tension N/A puis repassée Applicable
    # sans document (applicabilité seule) → (0,5 + 0) / 2.
    r.append(
        _rec(
            "ACME",
            "REF-002",
            "CE",
            ["CE"],
            app=["2006/42/UE"],
            na=["2014/35/UE", "2011/65/UE", "2015/863", "2014/30/UE", "2014/68/UE"],
            at="2026-01-11T09:00:00",
        )
    )
    n = "CE_ACME_REF-002.pdf"
    r.append(
        _rec(
            "ACME",
            "REF-002",
            "CE",
            ["CE"],
            req=["2006/42/UE"],
            app=["2006/42/UE"],
            na=["2014/35/UE", "2011/65/UE", "2015/863", "2014/30/UE", "2014/68/UE"],
            name=n,
            path=_doc_path("CE", "ACME", "REF-002", n),
            at="2026-01-12T09:00:00",
        )
    )
    n = "CE_ACME_REF-002_estimation.pdf"
    r.append(
        _rec(
            "ACME",
            "REF-002",
            "CE",
            ["CE"],
            req=["2006/42/UE"],
            app=["2006/42/UE"],
            na=["2014/35/UE", "2011/65/UE", "2015/863", "2014/30/UE", "2014/68/UE"],
            name=n,
            path=_doc_path("CE", "ACME", "REF-002", n),
            at="2026-01-13T09:00:00",
        )
    )
    r.append(_rec("ACME", "REF-002", "CE", ["CE"], app=["2014/35/UE"], at="2026-01-14T09:00:00"))

    # BETA / REF-010 — R14, R16 : document RoHS déposé depuis le DPE, code
    # écrit avec son libellé, rangé dans DPE et CE. DPE : RoHS + REACh
    # applicables → 1/2. CE : RoHS couverte, le reste « non défini » → 1/5.
    # Comme l'appli actuelle : une copie et un enregistrement par dossier
    # (DPE puis CE), tous deux marqués rangés dans DPE et CE.
    n = "DPE_BETA_REF-010.pdf"
    for t, at in (("DPE", "2026-02-01T09:00:00"), ("CE", "2026-02-01T09:00:01")):
        r.append(
            _rec(
                "BETA",
                "REF-010",
                "DPE",
                ["DPE", "CE"],
                req=["2011/65/UE — RoHS"],
                app=["2011/65/UE — RoHS", "1907/2006 | REACh"],
                na=[c for c in DPE_ALL if c not in ("2011/65/UE", "1907/2006")],
                name=n,
                path=_doc_path(t, "BETA", "REF-010", n),
                at=at,
            )
        )
    # BETA / REF-010, CECC — R19 : Validé puis Relancé → dernier = Relancé → 0 %.
    for at, status, n in (
        ("2026-02-02T09:00:00", "Validé", "CECC_BETA_REF-010.pdf"),
        ("2026-02-03T09:00:00", "Relancé", "CECC_BETA_REF-010 (1).pdf"),
    ):
        r.append(
            _rec(
                "BETA",
                "REF-010",
                "CECC",
                ["CECC"],
                cecc={
                    "manufacturer_doc": "BETA",
                    "manufacturer_part_number": "MPN-BETA",
                    "cecc_etat": status,
                    "nom_cecc": "CECC BETA",
                    "pays_origine": "FR-France",
                },
                name=n,
                path=_doc_path("CECC", "BETA", "REF-010", n),
                at=at,
            )
        )

    # GAMMA / REF-020, CECC — R19, R25 bis : Relancé puis Validé → 100 % ;
    # MPN de la fiche dans D et H (et en D des exports CE / DPE).
    for at, status, n in (
        ("2026-03-01T09:00:00", "Relancé", "CECC_GAMMA_REF-020.pdf"),
        ("2026-03-02T09:00:00", "Validé", "CECC_GAMMA_REF-020 (1).pdf"),
    ):
        r.append(
            _rec(
                "GAMMA",
                "REF-020",
                "CECC",
                ["CECC"],
                cecc={
                    "manufacturer_doc": "GAMMA Inc",
                    "manufacturer_part_number": "MPN-GAMMA",
                    "cecc_etat": status,
                    "cecc_date": "02/03/2026",
                    "nom_cecc": "Déclaration GAMMA",
                    "cecc_classement": "DU",
                    "categorie": "5A992",
                    "licence_yn": "Non",
                    "pays_origine": "US-États-Unis",
                    "eccn_value": "120",
                },
                name=n,
                path=_doc_path("CECC", "GAMMA", "REF-020", n),
                at=at,
            )
        )

    # DELTA / REF-030, DPE — document en base dont le fichier a disparu :
    # compté dans la complétion, affiché sans lien dans l'export.
    n = "DPE_DELTA_REF-030.pdf"
    r.append(
        _rec(
            "DELTA",
            "REF-030",
            "DPE",
            ["DPE"],
            req=["1907/2006"],
            app=["1907/2006"],
            na=[c for c in DPE_ALL if c != "1907/2006"],
            name=n,
            path=_doc_path("DPE", "DELTA", "REF-030", n),
            at="2026-04-01T09:00:00",
        )
    )

    # EPS / REF-040 — CE tout N/A → 100 % (R17). CECC : ancienne clé
    # « status » = « Estimation » → lue, mais ≠ Validé → 0 % (R19, avant E5).
    r.append(_rec("EPS", "REF-040", "CE", ["CE"], na=CE_ALL, at="2026-05-01T09:00:00"))
    n = "CECC_EPS_REF-040.pdf"
    r.append(
        _rec(
            "EPS",
            "REF-040",
            "CECC",
            ["CECC"],
            cecc={
                "manufacturer_doc": "EPS",
                "manufacturer_part_number": "MPN-EPS",
                "status": "Estimation",
                "nom_cecc": "CECC EPS",
            },
            name=n,
            path=_doc_path("CECC", "EPS", "REF-040", n),
            at="2026-05-02T09:00:00",
        )
    )
    return r


MISSING_FILES = {"DPE_DELTA_REF-030.pdf"}


def construire_projet(ancien: Path) -> None:
    sys.path.insert(0, str(ancien))
    from wikidocs_qt.metadata_db import init_metadata_db, insert_uploaded_document  # noqa: E402

    if PROJET.exists():
        shutil.rmtree(PROJET)
    (PROJET / ".nox").mkdir(parents=True)
    data = {
        "project_name": AFFAIRE,
        "project_path": str(PROJET),
        "dossier_number": DOSSIER,
        "date_code": "28/10/2026",
        "created_at": "2026-01-01T08:00:00",
        "updated_at": "2026-01-01T08:00:00",
        "project_meta_dir": ".nox",
        "project_file_version": 3,
        "rows": ROWS,
        "enabled_bdds": ["CE", "CECC", "DPE"],
    }
    (PROJET / ".nox" / "project.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for t in ("CE", "CECC", "DPE"):
        for row in ROWS:
            (PROJET / _bdd_dir(t) / "Documents" / row["supplier"] / row["reference"]).mkdir(
                parents=True, exist_ok=True
            )

    init_metadata_db(PROJET)
    for rec in _records():
        insert_uploaded_document(PROJET, **rec)
        if rec["relative_path"] and rec["stored_filename"] not in MISSING_FILES:
            f = PROJET / rec["relative_path"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"%PDF-1.4\n% document d'essai NOX\n")


def relever_tableau_de_suivi(ancien: Path) -> dict:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6 import QtWidgets  # noqa: E402
    from wikidocs_qt.project_dashboard_window import ProjectDashboardWindow  # noqa: E402

    # Gardée en vie le temps du relevé : Qt exige une application pour créer la fenêtre.
    _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])  # noqa: F841
    data = json.loads((PROJET / ".nox" / "project.json").read_text(encoding="utf-8"))
    win = ProjectDashboardWindow(data)
    lignes = [
        {
            k: r[k]
            for k in ("supplier", "reference", "label", "mnp", "order_number", "type", "completion")
        }
        for r in win._all_rows_cache
    ]
    # Indicateurs : même formule que _update_kpis (moyenne arrondie, sans filtre).
    kpi = {}
    for t in ("CE", "CECC", "DPE"):
        vals = [r["completion_value"] for r in win._all_rows_cache if r["type"] == t]
        kpi[t] = f"{round(sum(vals) / len(vals) * 100)} %" if vals else "0 %"
    win.close()
    return {"lignes": lignes, "indicateurs": kpi}


def relever_exports(ancien: Path) -> dict:
    from openpyxl import load_workbook  # noqa: E402
    from wikidocs_qt.export_templates import export_project_templates  # noqa: E402

    resultats = export_project_templates(PROJET)
    out = {}
    for chemin, _archive in resultats:
        wb = load_workbook(chemin)
        ws = wb.worksheets[0]
        cellules = {}
        for row in ws.iter_rows():
            for c in row:
                if c.value is None and not c.hyperlink:
                    continue
                v = {"valeur": c.value}
                if c.hyperlink:
                    cible = c.hyperlink.target or ""
                    racine = PROJET.as_posix()
                    v["lien"] = cible.replace(racine, "<PROJET>")
                cellules[c.coordinate] = v
        out[chemin.name] = {"onglet": ws.title, "cellules": cellules}
    return out


def relever_arborescence() -> list[str]:
    return sorted(
        p.relative_to(PROJET).as_posix() + ("/" if p.is_dir() else "")
        for p in PROJET.rglob("*")
        if ".nox" not in p.parts
    )


def main() -> None:
    ancien = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEPOT
    construire_projet(ancien)
    ATTENDU.mkdir(exist_ok=True)
    suivi = relever_tableau_de_suivi(ancien)
    exports = relever_exports(ancien)
    arbo = relever_arborescence()
    for nom, contenu in (
        ("tableau_de_suivi.json", suivi),
        ("exports.json", exports),
        ("arborescence.json", arbo),
    ):
        (ATTENDU / nom).write_text(
            json.dumps(contenu, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(json.dumps(suivi, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
