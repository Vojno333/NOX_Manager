#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from PySide6 import QtWidgets, QtGui

from wikidocs_qt.home_window import HomeWindow
from wikidocs_qt.theme import get_app_stylesheet

try:
    import pyi_splash
except Exception:
    pyi_splash = None


def _base_dir() -> Path:
    """Dossier de base des ressources, valable en dev ET une fois compilé.
    En onefile PyInstaller, __file__ pointe vers le dossier temporaire
    d'extraction (sys._MEIPASS) et NON vers le dossier du script source :
    il faut donc utiliser _MEIPASS en priorité quand il existe."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _set_windows_app_id():
    """Force un AppUserModelID dédié pour que Windows n'affiche pas
    l'icône générique de python/pyinstaller et regroupe correctement
    l'application dans la barre des tâches."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "NOX_Manager.WikidocsQt.1"
        )
    except Exception:
        pass


def run():
    _set_windows_app_id()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#f5f6f8"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#111827"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#f9fafb"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#111827"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#111827"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#2563eb"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(get_app_stylesheet())

    icon_path = _base_dir() / "LOGO_Nox.ico"
    app_icon = QtGui.QIcon(str(icon_path)) if icon_path.exists() else QtGui.QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    if sys.platform.startswith("win"):
        QtWidgets.QApplication.setFont(QtGui.QFont("Segoe UI", 10))

    window = HomeWindow()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.showMaximized()

    app.processEvents()

    if pyi_splash and pyi_splash.is_alive():
        pyi_splash.close()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())