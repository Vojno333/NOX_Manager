"""Dimensionnement et centrage commun à toutes les fenêtres et dialogues.

Repris de `v1-avant-refonte:wikidocs_qt/window_geometry.py` (`fit_and_center`).
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


def _ecran(widget: QtWidgets.QWidget) -> QtGui.QScreen | None:
    """Écran de la fenêtre parente visible, sinon celui du curseur, sinon le principal."""
    parent = widget.parentWidget()
    ecran = parent.screen() if parent is not None and parent.isVisible() else None
    return (
        ecran
        or QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos())
        or widget.screen()
        or QtGui.QGuiApplication.primaryScreen()
    )


def ajuster_et_centrer(
    widget: QtWidgets.QWidget,
    largeur: int,
    hauteur: int,
    largeur_min: int | None = None,
    hauteur_min: int | None = None,
    marge: float = 0.92,
) -> None:
    """Donne à *widget* la taille voulue, réduite si l'écran est plus petit
    (barre des tâches déduite), puis le centre sur sa fenêtre parente, ou sur
    l'écran à défaut. La fenêtre reste redimensionnable jusqu'à un plancher
    raisonnable, pour que chaque contrôle reste accessible sur un petit écran.
    """
    ecran = _ecran(widget)
    dispo = ecran.availableGeometry() if ecran else QtCore.QRect(0, 0, largeur, hauteur)

    w = min(largeur, int(dispo.width() * marge))
    h = min(hauteur, int(dispo.height() * marge))
    widget.setMinimumSize(min(largeur_min or largeur, w), min(hauteur_min or hauteur, h))
    widget.resize(w, h)

    parent = widget.parentWidget()
    ref = parent.frameGeometry() if parent is not None and parent.isVisible() else dispo
    x = ref.x() + (ref.width() - w) // 2
    y = ref.y() + (ref.height() - h) // 2
    x = max(dispo.x(), min(x, dispo.x() + dispo.width() - w))
    y = max(dispo.y(), min(y, dispo.y() + dispo.height() - h))
    widget.move(x, y)
