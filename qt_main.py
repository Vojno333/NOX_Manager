#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from PySide6 import QtWidgets, QtGui

from wikidocs_qt.home_window import HomeWindow
from wikidocs_qt.theme import get_app_stylesheet
from PySide6 import QtWidgets, QtGui

try:
    import pyi_splash
except Exception:
    pyi_splash = None


def run():
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

    icon_path = Path(__file__).resolve().parent / "LOGO_Nox.ico"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    if sys.platform.startswith("win"):
        QtWidgets.QApplication.setFont(QtGui.QFont("Segoe UI", 10))

    window = HomeWindow()
    window.showMaximized()

    app.processEvents()

    if pyi_splash and pyi_splash.is_alive():
        pyi_splash.close()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())