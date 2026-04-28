from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .project_manager import get_project_hidden_dir


DB_FILENAME = "nox_metadata.db"


def get_metadata_db_path(project_dir: Path) -> Path:
    db_dir = get_project_hidden_dir(project_dir)
    return db_dir / DB_FILENAME


def connect_metadata_db(project_dir: Path) -> sqlite3.Connection:
    db_path = get_metadata_db_path(project_dir)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_metadata_db(project_dir: Path) -> None:
    conn = connect_metadata_db(project_dir)
    try:
        conn.execute("""
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
                not_applicable_labels_json TEXT NOT NULL DEFAULT '[]'
            )
        """)

        # Migration pour les anciennes bases déjà créées
        for column_name in (
            "not_applicable_codes_json",
            "not_applicable_labels_json",
        ):
            try:
                conn.execute(
                    f"ALTER TABLE uploaded_documents "
                    f"ADD COLUMN {column_name} TEXT NOT NULL DEFAULT '[]'"
                )
            except sqlite3.OperationalError:
                pass

        conn.commit()
    finally:
        conn.close()


def insert_uploaded_document(
    project_dir: Path,
    supplier: str,
    reference: str,
    source_justification_type: str,
    stored_in_bdds: list[str],
    requirement_codes: list[str],
    requirement_labels: list[str],
    cecc_fields: dict[str, str],
    original_filename: str,
    stored_filename: str,
    relative_path: str,
    uploaded_at: str,
    not_applicable_codes: list[str] | None = None,
    not_applicable_labels: list[str] | None = None,
) -> None:
    conn = connect_metadata_db(project_dir)
    try:
        conn.execute("""
            INSERT INTO uploaded_documents (
                supplier,
                reference,
                source_justification_type,
                stored_in_bdds_json,
                requirement_codes_json,
                requirement_labels_json,
                cecc_fields_json,
                original_filename,
                stored_filename,
                relative_path,
                uploaded_at,
                not_applicable_codes_json,
                not_applicable_labels_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            supplier,
            reference,
            source_justification_type,
            json.dumps(stored_in_bdds, ensure_ascii=False),
            json.dumps(requirement_codes, ensure_ascii=False),
            json.dumps(requirement_labels, ensure_ascii=False),
            json.dumps(cecc_fields, ensure_ascii=False),
            original_filename,
            stored_filename,
            relative_path,
            uploaded_at,
            json.dumps(not_applicable_codes or [], ensure_ascii=False),
            json.dumps(not_applicable_labels or [], ensure_ascii=False),
        ))
        conn.commit()
    finally:
        conn.close()


def get_uploaded_documents(project_dir: Path) -> list[dict[str, Any]]:
    conn = connect_metadata_db(project_dir)
    try:
        cur = conn.execute("""
            SELECT
                id,
                supplier,
                reference,
                source_justification_type,
                stored_in_bdds_json,
                requirement_codes_json,
                requirement_labels_json,
                cecc_fields_json,
                original_filename,
                stored_filename,
                relative_path,
                uploaded_at,
                not_applicable_codes_json,
                not_applicable_labels_json
            FROM uploaded_documents
            ORDER BY supplier, reference, uploaded_at DESC
        """)

        rows = []
        for row in cur.fetchall():
            rows.append({
                "id": row[0],
                "supplier": row[1],
                "reference": row[2],
                "source_justification_type": row[3],
                "stored_in_bdds": json.loads(row[4] or "[]"),
                "requirement_codes": json.loads(row[5] or "[]"),
                "requirement_labels": json.loads(row[6] or "[]"),
                "cecc_fields": json.loads(row[7] or "{}"),
                "original_filename": row[8],
                "stored_filename": row[9],
                "relative_path": row[10],
                "uploaded_at": row[11],
                "not_applicable_codes": json.loads(row[12] or "[]"),
                "not_applicable_labels": json.loads(row[13] or "[]"),
            })

        return rows
    finally:
        conn.close()


def get_latest_uploaded_documents(
    project_dir: Path,
    supplier: str | None = None,
    reference: str | None = None,
    source_justification_type: str | None = None,
) -> list[dict[str, Any]]:
    docs = get_uploaded_documents(project_dir)

    if supplier is not None:
        docs = [d for d in docs if d["supplier"] == supplier]

    if reference is not None:
        docs = [d for d in docs if d["reference"] == reference]

    if source_justification_type is not None:
        docs = [
            d for d in docs
            if str(d["source_justification_type"]).upper()
            == str(source_justification_type).upper()
        ]

    docs.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
    return docs


def get_latest_cecc_fields(
    project_dir: Path,
    supplier: str,
    reference: str,
) -> dict[str, str]:
    docs = get_latest_uploaded_documents(
        project_dir=project_dir,
        supplier=supplier,
        reference=reference,
        source_justification_type="CECC",
    )

    for doc in docs:
        cecc_fields = doc.get("cecc_fields", {}) or {}
        if cecc_fields:
            return cecc_fields

    return {}


def delete_uploaded_documents_for_rows(project_dir: Path, rows: list[dict]) -> None:
    if not rows:
        return

    conn = connect_metadata_db(project_dir)
    try:
        for row in rows:
            supplier = str(row.get("supplier", "")).strip()
            reference = str(row.get("reference", "")).strip()

            if not supplier or not reference:
                continue

            conn.execute(
                """
                DELETE FROM uploaded_documents
                WHERE supplier = ? AND reference = ?
                """,
                (supplier, reference),
            )

        conn.commit()
    finally:
        conn.close()