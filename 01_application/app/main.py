"""Point d'entrée de NOX Manager.

Socle de la reconstruction : les fenêtres arrivent tâche par tâche
(`docs/travaux.md`), en reprenant `00_ancien/qt_main.py`.
"""

from __future__ import annotations

import sys

from PySide6 import QtWidgets

from app.core.config import reglages


def run() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    fenetre = QtWidgets.QMainWindow()
    fenetre.setWindowTitle(reglages()["nom"])
    fenetre.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
