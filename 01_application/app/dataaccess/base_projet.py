"""Base SQLite d'un projet : `.nox/nox_metadata.db`, table `uploaded_documents`.

Repris de `v1-avant-refonte:wikidocs_qt/metadata_db.py`. Les colonnes `*_json`
contiennent des listes ou dictionnaires JSON (`ensure_ascii=False`).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.models.enregistrement import Enregistrement

FICHIER_BASE = "nox_metadata.db"

_CREATION = """
    CREATE TABLE IF NOT EXISTS uploaded_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier TEXT NOT NULL,
        reference TEXT NOT NULL,
        source_justification_type TEXT NOT NULL,
        stored_in_bdds_json TEXT NOT NULL,
        requirement_codes_json TEXT NOT NULL,
        requirement_labels_json TEXT NOT NULL,
        cecc_fields_json TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        stored_filename TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        not_applicable_codes_json TEXT NOT NULL DEFAULT '[]',
        not_applicable_labels_json TEXT NOT NULL DEFAULT '[]',
        applicable_codes_json TEXT NOT NULL DEFAULT '[]',
        line_id TEXT NOT NULL DEFAULT ''
    )
"""

# Colonnes ajoutées après coup : migration tolérante des anciennes bases.
_COLONNES_AJOUTEES = {
    "not_applicable_codes_json": "'[]'",
    "not_applicable_labels_json": "'[]'",
    "applicable_codes_json": "'[]'",
    "line_id": "''",  # E1, décision 0005
}

# Attribut de l'enregistrement → colonne. Liste fermée : seuls ces noms
# entrent dans une requête.
_COLONNES = {
    "fournisseur": "supplier",
    "reference": "reference",
    "livrable_source": "source_justification_type",
    "livrables_rangement": "stored_in_bdds_json",
    "codes_couverts": "requirement_codes_json",
    "libelles_couverts": "requirement_labels_json",
    "champs_cecc": "cecc_fields_json",
    "nom_original": "original_filename",
    "nom_stocke": "stored_filename",
    "chemin_relatif": "relative_path",
    "depose_le": "uploaded_at",
    "codes_na": "not_applicable_codes_json",
    "libelles_na": "not_applicable_labels_json",
    "codes_applicables": "applicable_codes_json",
    "id_ligne": "line_id",
}
LISTES_DE_CODES = (
    "codes_couverts",
    "libelles_couverts",
    "codes_applicables",
    "codes_na",
    "libelles_na",
)

_initialisees: set[Path] = set()


def chemin_base(dossier: Path) -> Path:
    return dossier / ".nox" / FICHIER_BASE


def _ouvrir(dossier: Path) -> sqlite3.Connection:
    fichier = chemin_base(dossier)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(fichier))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def initialiser(dossier: Path) -> None:
    """Crée la table si besoin et ajoute les colonnes manquantes."""
    conn = _ouvrir(dossier)
    try:
        conn.execute(_CREATION)
        for colonne, defaut in _COLONNES_AJOUTEES.items():
            try:
                conn.execute(
                    f"ALTER TABLE uploaded_documents ADD COLUMN {colonne} "  # noqa: S608 — nom fixe
                    f"TEXT NOT NULL DEFAULT {defaut}"
                )
            except sqlite3.OperationalError:
                pass
        conn.commit()
    finally:
        conn.close()
    _initialisees.add(chemin_base(dossier).resolve())


def _connecter(dossier: Path) -> sqlite3.Connection:
    fichier = chemin_base(dossier)
    if not fichier.exists() or fichier.resolve() not in _initialisees:
        initialiser(dossier)
    return _ouvrir(dossier)


def _en_colonne(attribut: str, valeur) -> object:
    if _COLONNES[attribut].endswith("_json"):
        return json.dumps(valeur, ensure_ascii=False)
    return valeur


def ajouter(dossier: Path, enr: Enregistrement) -> int:
    """Ajoute un enregistrement et retourne son identifiant."""
    attributs = list(_COLONNES)
    colonnes = ", ".join(_COLONNES[a] for a in attributs)
    marques = ", ".join("?" for _ in attributs)
    conn = _connecter(dossier)
    try:
        cur = conn.execute(
            f"INSERT INTO uploaded_documents ({colonnes}) VALUES ({marques})",  # noqa: S608
            [_en_colonne(a, getattr(enr, a)) for a in attributs],
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def lire_tous(dossier: Path) -> list[Enregistrement]:
    """Tous les enregistrements, par fournisseur, référence, puis du plus récent au plus ancien."""
    attributs = list(_COLONNES)
    colonnes = ", ".join(_COLONNES[a] for a in attributs)
    conn = _connecter(dossier)
    try:
        lignes = conn.execute(
            f"SELECT id, {colonnes} FROM uploaded_documents "  # noqa: S608
            "ORDER BY supplier, reference, uploaded_at DESC"
        ).fetchall()
    finally:
        conn.close()
    resultat = []
    for ligne in lignes:
        valeurs = {}
        for attribut, valeur in zip(attributs, ligne[1:], strict=True):
            if _COLONNES[attribut].endswith("_json"):
                vide = "{}" if attribut == "champs_cecc" else "[]"
                valeur = json.loads(valeur or vide)
            valeurs[attribut] = valeur
        resultat.append(Enregistrement(id=ligne[0], **valeurs))
    return resultat


def lire_derniers(
    dossier: Path,
    fournisseur: str | None = None,
    reference: str | None = None,
    livrable_source: str | None = None,
) -> list[Enregistrement]:
    """Enregistrements filtrés, du plus récent au plus ancien."""
    enrs = lire_tous(dossier)
    if fournisseur is not None:
        enrs = [e for e in enrs if e.fournisseur == fournisseur]
    if reference is not None:
        enrs = [e for e in enrs if e.reference == reference]
    if livrable_source is not None:
        enrs = [e for e in enrs if str(e.livrable_source).upper() == livrable_source.upper()]
    enrs.sort(key=lambda e: e.depose_le or "", reverse=True)
    return enrs


def derniere_fiche_cecc(dossier: Path, fournisseur: str, reference: str) -> dict:
    """Champs de la fiche CECC la plus récente non vide de l'article, ou {}."""
    for enr in lire_derniers(dossier, fournisseur, reference, "CECC"):
        if enr.champs_cecc:
            return enr.champs_cecc
    return {}


def modifier_listes_de_codes(dossier: Path, id_enr: int, listes: dict[str, list[str]]) -> None:
    """Réécrit les listes indiquées (clés parmi `LISTES_DE_CODES`)."""
    attributs = [a for a in listes if a in LISTES_DE_CODES]
    if not attributs:
        return
    affectations = ", ".join(f"{_COLONNES[a]} = ?" for a in attributs)
    conn = _connecter(dossier)
    try:
        conn.execute(
            f"UPDATE uploaded_documents SET {affectations} WHERE id = ?",  # noqa: S608
            [json.dumps(listes[a], ensure_ascii=False) for a in attributs] + [id_enr],
        )
        conn.commit()
    finally:
        conn.close()


def detacher_fichier(dossier: Path, id_enr: int) -> None:
    """L'enregistrement garde son applicabilité mais ne référence plus aucun fichier."""
    conn = _connecter(dossier)
    try:
        conn.execute(
            "UPDATE uploaded_documents "
            "SET original_filename = '', stored_filename = '', relative_path = '' WHERE id = ?",
            (id_enr,),
        )
        conn.commit()
    finally:
        conn.close()


def supprimer(dossier: Path, ids: list[int]) -> None:
    if not ids:
        return
    conn = _connecter(dossier)
    try:
        conn.executemany("DELETE FROM uploaded_documents WHERE id = ?", [(i,) for i in ids])
        conn.commit()
    finally:
        conn.close()


def supprimer_pour_articles(dossier: Path, cles: list[tuple[str, str]]) -> None:
    """Supprime tous les enregistrements des articles (fournisseur, référence) donnés."""
    cles = [(f.strip(), r.strip()) for f, r in cles if f.strip() and r.strip()]
    if not cles:
        return
    conn = _connecter(dossier)
    try:
        conn.executemany(
            "DELETE FROM uploaded_documents WHERE supplier = ? AND reference = ?", cles
        )
        conn.commit()
    finally:
        conn.close()
