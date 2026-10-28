from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


def fit_and_center(
    widget: QtWidgets.QWidget,
    desired_w: int,
    desired_h: int,
    min_w: int | None = None,
    min_h: int | None = None,
    margin: float = 0.92,
) -> None:
    """Size *widget* to desired_w x desired_h, shrinking it to fit the
    available screen (taskbar-aware) when the screen is smaller, then
    center it over its parent (or over the screen if there is no visible
    parent). Keeps the window user-resizable down to a sane floor so every
    control stays reachable on small or scaled displays.

    L'écran choisi est, dans l'ordre : celui de la fenêtre parente (si
    visible), pour que chaque nouvelle fenêtre/dialogue s'ouvre sur le
    même écran que la fenêtre qui l'a ouverte ; sinon l'écran sous le
    curseur ; sinon l'écran principal."""
    parent = widget.parentWidget()

    screen = None
    if parent is not None and parent.isVisible():
        screen = parent.screen()
    if screen is None:
        screen = QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos())
    if screen is None:
        screen = widget.screen()
    if screen is None:
        screen = QtGui.QGuiApplication.primaryScreen()

    avail = screen.availableGeometry() if screen else QtCore.QRect(0, 0, desired_w, desired_h)

    w = min(desired_w, int(avail.width() * margin))
    h = min(desired_h, int(avail.height() * margin))

    floor_w = min(min_w or desired_w, w)
    floor_h = min(min_h or desired_h, h)
    widget.setMinimumSize(floor_w, floor_h)
    widget.resize(w, h)

    ref = parent.frameGeometry() if (parent is not None and parent.isVisible()) else avail

    x = ref.x() + (ref.width() - w) // 2
    y = ref.y() + (ref.height() - h) // 2
    x = max(avail.x(), min(x, avail.x() + avail.width() - w))
    y = max(avail.y(), min(y, avail.y() + avail.height() - h))
    widget.move(x, y)