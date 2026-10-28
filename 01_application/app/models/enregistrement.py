"""Enregistrement : un événement daté de la table `uploaded_documents`.

Un dépôt de document, ou un réglage d'applicabilité seul (sans fichier).
Repris de `v1-avant-refonte:wikidocs_qt/metadata_db.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Enregistrement:
    fournisseur: str
    reference: str
    livrable_source: str  # livrable depuis lequel le dépôt a été fait
    livrables_rangement: list[str] = field(default_factory=list)  # où le fichier a été copié
    codes_couverts: list[str] = field(default_factory=list)  # exigences justifiées par le fichier
    libelles_couverts: list[str] = field(default_factory=list)
    champs_cecc: dict = field(default_factory=dict)
    nom_original: str = ""
    nom_stocke: str = ""
    chemin_relatif: str = ""  # séparateur « / », relatif au dossier du projet
    depose_le: str = ""  # date ISO, sert à l'ordre des événements
    codes_na: list[str] = field(default_factory=list)
    libelles_na: list[str] = field(default_factory=list)
    codes_applicables: list[str] = field(default_factory=list)
    # E1 : ligne de l'article ; vide = première ligne du couple (décision 0005).
    id_ligne: str = ""
    id: int | None = None

    @property
    def a_un_fichier(self) -> bool:
        """Faux pour un enregistrement « applicabilité seule »."""
        return bool(str(self.chemin_relatif or "").strip())

    @classmethod
    def depuis_dict(cls, d: dict) -> Enregistrement:
        """Depuis un dictionnaire aux noms de l'ancienne application."""
        return cls(
            fournisseur=d["supplier"],
            reference=d["reference"],
            livrable_source=d["source_justification_type"],
            livrables_rangement=list(d.get("stored_in_bdds") or []),
            codes_couverts=list(d.get("requirement_codes") or []),
            libelles_couverts=list(d.get("requirement_labels") or []),
            champs_cecc=dict(d.get("cecc_fields") or {}),
            nom_original=d.get("original_filename", ""),
            nom_stocke=d.get("stored_filename", ""),
            chemin_relatif=d.get("relative_path", ""),
            depose_le=d.get("uploaded_at", ""),
            codes_na=list(d.get("not_applicable_codes") or []),
            libelles_na=list(d.get("not_applicable_labels") or []),
            codes_applicables=list(d.get("applicable_codes") or []),
            id_ligne=str(d.get("line_id", "") or ""),
            id=d.get("id"),
        )
