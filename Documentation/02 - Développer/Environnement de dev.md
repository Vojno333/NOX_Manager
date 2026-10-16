---
tags: [nox, dev, setup]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Environnement de développement

## Prérequis

- **Windows 10/11** (le code a des branches `sys.platform.startswith("win")`, et les chemins/l'AppUserModelID sont pensés Windows).
- **Python 3.14** côté build d'origine (le chemin de `pyinstaller.exe` dans `Compilation de l'exe.txt` est `…\Python\Python314\Scripts`). La version minimale réellement requise n'est pas testée : le code utilise `X | None` et `list[str]`, donc **≥ 3.10**.
- Attention : sur ce poste, la commande `python` peut renvoyer « Python was not found » (alias du Microsoft Store). Utiliser le lanceur `py` ou le chemin complet de l'interpréteur, et désactiver l'alias dans *Paramètres → Applications → Paramètres avancés → Alias d'exécution*.

## Installation

Il n'y a pas de `requirements.txt` (NOX-001 dans [[Backlog]]). Dépendances déduites des imports :

| Paquet | Utilisé pour |
|---|---|
| `PySide6` | Interface |
| `openpyxl` | Export Excel |
| `python-docx` | Import de `docx` dans `utils.py` (chargé au démarrage, voir [[Dette technique#DT-005]]) |
| `pyinstaller` | Build |

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install PySide6 openpyxl python-docx pyinstaller
py -m pip freeze > requirements.txt   # à faire une fois, puis commiter
```

`.venv/` n'est pas dans `.gitignore` : l'ajouter avant de commiter, ou créer l'environnement hors du dépôt.

## Lancer

```powershell
py qt_main.py
```

Les données de test : créer un projet dans un dossier jetable (par ex. `C:\Temp\NOX_Test\`) plutôt que dans le dépôt. `Projects/` et `Documents/` sont ignorés par git par sécurité.

## Débogage

- L'application compilée n'affiche pas de console ; en dev, lancer depuis un terminal pour voir les traces Python.
- Les `except Exception: pass` masquent certaines erreurs ([[Dette technique#DT-004]]) : en cas de comportement muet, chercher d'abord là (lecture de `project.json`, état applicatif).
- Inspecter la base d'un projet : ouvrir `<projet>/.nox/nox_metadata.db` avec *DB Browser for SQLite* ou

```powershell
py -c "import sqlite3,sys; c=sqlite3.connect(r'C:\Temp\NOX_Test\MonProjet\.nox\nox_metadata.db'); [print(r) for r in c.execute('select id,supplier,reference,source_justification_type,uploaded_at,stored_filename from uploaded_documents order by id desc limit 20')]"
```

- Repartir de zéro côté utilisateur : supprimer `%USERPROFILE%\.nox_manager\` (efface uniquement la liste des projets récents).
- Pour tester l'affichage d'un widget isolément, `Test_interface.py` montre le principe (maquette autonome, pas de lien avec `wikidocs_qt`).

## Éditeur

Le dépôt ignore `.vscode/` et `.idea/`. Aucune configuration de formateur ou de linter n'est fournie ([[Conventions de code]]).

## Ouvrir la documentation

`Documentation/` est prévu pour Obsidian (liens `[[…]]`). Ouvrir ce dossier comme coffre. Voir [[Dette technique#DT-008]] pour les règles `.gitignore` associées.
