"""Préférences de l'utilisateur : `~/.nox_manager/nox_state.json`.

Projets récents, emplacements récents, emplacement par défaut. Un fichier
absent ou illisible donne les valeurs par défaut, sans message.
Repris de `00_ancien/wikidocs_qt/project_manager.py` (partie état).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.config import reglages
from app.models.projet_recent import ProjetRecent


def _defaut() -> dict:
    return {"recent_projects": [], "recent_locations": [], "default_location": ""}


class EtatUtilisateur:
    def __init__(self, fichier: Path | None = None) -> None:
        self.fichier = fichier or Path(reglages()["etat_utilisateur"]).expanduser()
        self.maximum = int(reglages()["projets_recents_max"])

    def _lire(self) -> dict:
        etat = _defaut()
        try:
            lu = json.loads(self.fichier.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return etat
        if isinstance(lu, dict):
            etat.update(lu)
        return etat

    def _ecrire(self, etat: dict) -> None:
        self.fichier.parent.mkdir(parents=True, exist_ok=True)
        self.fichier.write_text(json.dumps(etat, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Projets récents ──
    def projets_recents(self) -> list[ProjetRecent]:
        return [ProjetRecent.depuis_dict(p) for p in self._lire()["recent_projects"]]

    def ajouter_projet_recent(self, nom: str, dossier: Path, numero_dossier: str = "") -> None:
        etat = self._lire()
        chemin = str(dossier.resolve())
        projets = [p for p in etat["recent_projects"] if p.get("path") != chemin]
        projets.insert(
            0,
            {
                "name": nom,
                "dossier_number": numero_dossier,
                "path": chemin,
                "last_opened": datetime.now().isoformat(),
            },
        )
        etat["recent_projects"] = projets[: self.maximum]
        self._ecrire(etat)

    def retirer_projet_recent(self, dossier: str | Path) -> None:
        etat = self._lire()
        chemin = str(Path(dossier).resolve())
        etat["recent_projects"] = [
            p for p in etat["recent_projects"] if str(Path(p.get("path", "")).resolve()) != chemin
        ]
        self._ecrire(etat)

    # ── Emplacements ──
    def emplacements_recents(self) -> list[str]:
        return list(self._lire()["recent_locations"])

    def ajouter_emplacement_recent(self, dossier: Path) -> None:
        """Ajoute l'emplacement en tête des récents et en fait l'emplacement par défaut."""
        etat = self._lire()
        chemin = str(dossier.resolve())
        emplacements = [p for p in etat["recent_locations"] if p != chemin]
        emplacements.insert(0, chemin)
        etat["recent_locations"] = emplacements[: self.maximum]
        etat["default_location"] = chemin
        self._ecrire(etat)

    def emplacement_par_defaut(self) -> str:
        return str(self._lire()["default_location"] or "")
