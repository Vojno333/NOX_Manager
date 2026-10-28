"""Les commandes du projet.

uv run dev      lance l'application sur le poste
uv run test     joue les tests
uv run lint     met en forme et vérifie le code
uv run couches  vérifie que les dépendances entre couches descendent
uv run build    fabrique l'exécutable (dist/NOX_Manager/)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
APP = RACINE / "01_application" / "app"

# couche → (motif d'import interdit, raison)
_INTERDITS = {
    "services": (
        r"PySide6|sqlite3|openpyxl|app\.ui",
        "un service ne connaît ni Qt, ni la base, ni les fichiers Excel, ni l'interface",
    ),
    "dataaccess": (r"PySide6|app\.ui|app\.services", "ni Qt, ni l'interface, ni les services"),
    "models": (
        r"PySide6|sqlite3|openpyxl|app\.(ui|services|dataaccess)",
        "un objet métier ne dépend de rien",
    ),
    "core": (r"app\.(ui|services|dataaccess|models)", "core est transverse"),
}


def _lancer(*commande: str) -> None:
    # Commandes fixes, écrites dans ce fichier : aucune entrée extérieure.
    sys.exit(subprocess.call(commande, cwd=RACINE))  # noqa: S603


def dev() -> None:
    _lancer(sys.executable, "-m", "app.main")


def test() -> None:
    _lancer(sys.executable, "-m", "pytest", "-q")


def lint() -> None:
    code = subprocess.call([sys.executable, "-m", "ruff", "format", "."], cwd=RACINE)
    code |= subprocess.call([sys.executable, "-m", "ruff", "check", "--fix", "."], cwd=RACINE)
    sys.exit(code)


def verifier_couches() -> list[str]:
    erreurs = []
    for couche, (motif, raison) in _INTERDITS.items():
        regle = re.compile(rf"^\s*(from|import)\s+({motif})", re.MULTILINE)
        for fichier in (APP / couche).rglob("*.py"):
            texte = fichier.read_text("utf-8")
            for m in regle.finditer(texte):
                ligne = texte[: m.start()].count("\n") + 1
                erreurs.append(f"{fichier.relative_to(RACINE)}:{ligne} — {raison}")
    return erreurs


def couches() -> None:
    erreurs = verifier_couches()
    for e in erreurs:
        print(e)
    print("Couches conformes." if not erreurs else f"{len(erreurs)} dépendance(s) interdite(s).")
    sys.exit(1 if erreurs else 0)


def build() -> None:
    spec = RACINE / "NOX_Manager.spec"
    if not spec.exists():
        print("NOX_Manager.spec absent : il est créé par la tâche de livraison (docs/travaux.md).")
        sys.exit(1)
    _lancer(sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec))
