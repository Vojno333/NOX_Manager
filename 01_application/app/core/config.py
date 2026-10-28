"""Paramétrage et emplacement des ressources.

`config.json` contient les réglages ordinaires, lisibles et modifiables à la
main. Il n'y a aucun secret dans cette application, donc pas de `.env`.

En exécutable fabriqué par PyInstaller, les ressources sont dans
`sys._MEIPASS` ; en développement, à la racine du dépôt.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

RACINE_DEPOT = Path(__file__).resolve().parents[3]


def racine_ressources() -> Path:
    """Dossier où se trouvent `config.json` et les ressources livrées."""
    return Path(getattr(sys, "_MEIPASS", RACINE_DEPOT))


@lru_cache
def reglages() -> dict:
    return json.loads((racine_ressources() / "config.json").read_text("utf-8"))
