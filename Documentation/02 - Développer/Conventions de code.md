---
tags: [nox, dev, conventions]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Conventions de code

Relevées dans le code existant (2026-09-21). Règle d'or : **imiter le voisinage**. Voir aussi [[Architecture]].

## Python

- `from __future__ import annotations` en tête de module ; annotations modernes (`list[str]`, `str | None`, `dict[str, Any]`).
- `pathlib.Path` partout ; jamais de concaténation de chaînes pour un chemin. Les chemins **stockés en base** sont relatifs au projet avec `/` (`str(p.relative_to(project_dir)).replace("\\", "/")`).
- Imports relatifs dans le package : `from .metadata_db import …`.
- Fonctions et helpers privés préfixés `_`. Constantes en `MAJUSCULES` (`JUSTIFICATION_TYPES`, `DB_FILENAME`).
- JSON : `encoding="utf-8"`, `indent=2`, `ensure_ascii=False`. SQLite : toujours `try/finally: conn.close()`.
- Pas de `print` : pour l'instant pas de `logging` non plus (NOX-023 dans [[Backlog]]).
- Les modules de persistance et de calcul **ne doivent pas importer Qt** ; c'est la règle à faire respecter à l'avenir ([[Décisions (ADR)#ADR-009 : Extraire la logique de conformité hors de l'UI]]).

## Langue

- **Tout texte visible est en français**, avec accents (« Applicabilité », « Référence »). Guillemets français « … » pour les messages.
- Docstrings et commentaires : français ou anglais selon le fichier ; garder la langue du fichier.
- Identifiants : anglais (`supplier`, `reference`, `stored_filename`). Clés techniques du domaine en snake_case anglais/français mêlé (`nom_cecc`, `pays_origine`) : ne pas renommer sans migration ([[Bugs connus#BUG-001]]).

## Qt / PySide6

- `from PySide6 import QtCore, QtGui, QtWidgets` ; `Qt` importé depuis `PySide6.QtCore` quand utile.
- Un widget = une classe (`KpiCard`, `ThreeStateToggle`, `DropZone`…). Signaux déclarés en attribut de classe (`documentSaved = QtCore.Signal()`), connectés par l'appelant.
- **Toute nouvelle fenêtre ou dialogue** : `fit_and_center(self, largeur, hauteur, min_w, min_h)` de `window_geometry.py`. Ne pas coder de `resize` / `move` bruts.
- Style : feuille de style globale `theme.get_app_stylesheet()` + styles locaux en f-strings dans les fichiers d'UI. Palette de référence : bleu `#2563EB`, texte `#111827` / `#0F172A`, fond `#F5F6F8` / `#F8FAFC`, rouge `#EF4444`, gris `#9CA3AF`. Police *Segoe UI* 10.
- Opérations longues : `QApplication.setOverrideCursor(Qt.WaitCursor)` avec `restoreOverrideCursor` en `finally` (voir `_reload_after_import`).
- Messages à l'utilisateur : `QMessageBox` (information / warning / question / critical) avec titre court et texte actionnable. Confirmation obligatoire avant toute suppression.
- Toute liste affichée est **rechargée depuis le disque** (`_load_table`) ; ne pas maintenir un état parallèle en mémoire.

## Données

- Toute saisie utilisateur utilisée comme nom de dossier ou de fichier passe par `project_structure._safe_name`.
- Toute nouvelle colonne SQLite : ajout dans `CREATE TABLE` **et** dans la boucle de migration de `init_metadata_db` ([[Modèle de données#Migrations]]).
- Toute nouvelle clé dans `project.json` : lecture avec valeur par défaut dans `ProjectManager.load_project` (les anciens projets n'auront pas la clé).
- Tout nouveau champ CECC : ajouter à `CECC_FREE_FIELDS` et gérer import, dashboard **et** export d'un coup.

## Ressources et build

- Lire une ressource embarquée via `_base_dir()` (`qt_main.py`) ou `Path(__file__).parent`, jamais via le répertoire courant.
- Tout nouveau fichier de données → `datas` du `.spec` ([[Build et livraison]]).

## Git

- Branche `main` unique aujourd'hui. Messages de commit en français, à l'impératif ou au passé descriptif (« Ajout du système d'applicabilité tri-état »), un sujet par commit.
- Ne jamais commiter de projet réel, de base `.db`, ni d'export (`.gitignore` protège `*.db`, `Projects/`, `Documents/`, `exports/`).
- Les fichiers `.py` sont en LF dans le dépôt ; Git avertit d'une conversion CRLF (Windows) : configurer `core.autocrlf` une fois pour toutes pour éviter du bruit dans les diffs.

## Checklist avant de commiter

- [ ] L'application démarre (`py qt_main.py`) et le scénario touché est joué ([[Plan de test]]).
- [ ] Texte UI en français, accentué.
- [ ] Aucune donnée de projet ni chemin personnel en dur.
- [ ] Nouvelle ressource → `.spec` mis à jour.
- [ ] Modèle de données modifié → migration + [[Modèle de données]] à jour.
- [ ] Comportement visible modifié → [[Changelog]] et [[Journal de dev]].
- [ ] Bug corrigé → retiré de [[Bugs connus]].
