"""Un projet de la liste des récents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjetRecent:
    nom: str
    numero_dossier: str
    chemin: str
    ouvert_le: str = ""

    @classmethod
    def depuis_dict(cls, d: dict) -> ProjetRecent:
        return cls(
            nom=str(d.get("name", "")),
            numero_dossier=str(d.get("dossier_number", "")),
            chemin=str(d.get("path", "")),
            ouvert_le=str(d.get("last_opened", "")),
        )
