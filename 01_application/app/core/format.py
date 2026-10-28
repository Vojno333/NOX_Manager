"""Mise en forme de valeurs pour l'affichage.

Repris de `00_ancien/wikidocs_qt/utils.py` (`human_size`) et `home_window.py`
(`_format_datetime`).
"""

from __future__ import annotations

from datetime import datetime


def taille_lisible(n: int) -> str:
    """Taille en o, Ko, Mo, Go ou To."""
    taille = float(n or 0)
    for unite in ["o", "Ko", "Mo", "Go", "To"]:
        if taille < 1024 or unite == "To":
            return f"{int(taille)} {unite}" if unite == "o" else f"{taille:.1f} {unite}"
        taille /= 1024.0
    return ""


def date_lisible(iso: str) -> str:
    """Date ISO → « JJ/MM/AAAA HH:MM » ; vide → « — » ; illisible → telle quelle."""
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso
