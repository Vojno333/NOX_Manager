---
tags: [nox, journal]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Journal de dev

Plus récent en haut. **Une entrée par session de travail**, courte : ce qui a été fait, ce qui a été décidé, ce qui reste. Les commits n'y sont pas recopiés (voir `git log`), on y met le *pourquoi*.

Modèle d'entrée : [[Modèle - Entrée de journal]].


---

## 2026-09-21 : réorganisation de la documentation
**Objectif** : supprimer les liens cassés, éviter les doublons et donner un point d'entrée unique.
**Fait** : notes rangées en `01 - Comprendre`, `02 - Développer`, `03 - Piloter`, `04 - Utilisateurs` ; [[00 - Index]] créé (remplace `Accueil`) ; 3 modèles dans `_Modèles/` ; titres de [[Dette technique]] passés à `DT-00x` seul et ancres `Backlog#NOX-…` remplacées par `NOX-… dans [[Backlog]]` ; lien « ↑ Index » en tête de chaque note ; listes de clés CECC dédoublonnées (source : [[Bugs connus#BUG-001]]) ; `CLAUDE.md` pointe vers l'index.
**Décidé** : la correspondance DT ↔ NOX est portée par la colonne « Source » du [[Backlog]] (la colonne « Backlog » de [[Dette technique]] est retirée) ; un fait = une note, ailleurs un lien.
**Reste / prochain pas** : règles `.gitignore` pour `Documentation/.obsidian/` (non modifié, en attente d'accord) ; suivre la doc dans git quand le travail en cours sera commité.

## 2026-09-21 : mise en place de la documentation et audit de lecture
**Objectif** : disposer d'un `CLAUDE.md` et d'un dossier `Documentation/` pour reprendre le projet sans dépendre de la mémoire de quelqu'un.
**Fait** : rédaction de [[Architecture]], [[Modèle de données]], [[Règles métier]], [[Flux fonctionnels]], [[Build et livraison]], [[Environnement de dev]], [[Conventions de code]], [[Plan de test]], [[Guide utilisateur]], [[Glossaire]], [[Backlog]], [[Bugs connus]], [[Dette technique]], [[Décisions (ADR)]], [[Changelog]].
**Constaté** : incohérences de clés CECC ([[Bugs connus#BUG-001]]), règle de N/A différente entre export et dashboard ([[Bugs connus#BUG-002]]), `.spec` non versionné, pas de `requirements.txt`. Aucun de ces points n'a été reproduit : tout vient de la lecture du code.
**Reste / prochain pas** : reproduire BUG-001 et BUG-002 avec un projet jouet ; arbitrer les priorités du [[Backlog]] ; commiter le travail en cours (NOX-007).

## État du dépôt au 2026-09-21 (travail non commité)
Modifications en cours par rapport à `f7cd469` (10 fichiers, +695 / −219) :

| Fichier | Nature (lecture du diff, à compléter par l'auteur) |
|---|---|
| `wikidocs_qt/project_dashboard_window.py` | Le plus gros changement (~326 lignes) |
| `wikidocs_qt/upload_document_dialog.py` | ~380 lignes |
| `wikidocs_qt/new_project_dialog.py` | ~56 lignes |
| `wikidocs_qt/home_window.py` | ~51 lignes |
| `wikidocs_qt/project_settings_dialog.py` | ~48 lignes : colonne **MNP** dans le tableau des références, champ de saisie en masse des MNP |
| `qt_main.py` | ~37 lignes : AppUserModelID Windows, `_base_dir()` (ressources compatibles PyInstaller), icône appliquée aussi à la fenêtre d'accueil |
| `wikidocs_qt/filter_popup.py`, `document_rules.py` | Mineurs (`AUTRES` retiré de `CE_REQUIREMENTS`) |
| `flash.png` | Image du splash allégée : 1,43 Mo → 58 Ko |
| `.gitignore` | +11 lignes |

Nouveaux fichiers non suivis : `wikidocs_qt/window_geometry.py` (`fit_and_center`), `wikidocs_qt/dpe_icon.svg`, `wikidocs_qt/eu_icon.svg`, `wikidocs_qt/new_project_dialog2.py` (variante sans MNP), `Documentation/`.

Le `.spec` (modifié le 2026-07-21) n'est pas versionné à cause de `*.spec` dans `.gitignore`.

---

## 2026-04-30 : améliorations du dashboard
Deux commits le même jour :
- `8e0b8a1` *Amélioration UI : optimisation affichage dashboard et corrections visuelles* : refonte de `project_dashboard_window.py` (~2 250 lignes touchées) ; ajout de `Test_interface.py` (maquette d'accueil).
- `f7cd469` *amélioration tableau* : ajustements du tableau du dashboard ; `upload_document_dialog.py` allégé (~107 lignes retirées).

## 2026-04-29 : applicabilité tri-état
`12f8997` *Ajout du système d'applicabilité tri-état* : introduction de `ThreeStateToggle` (N/A / Non défini / Applicable), du mode « applicabilité » du dialogue d'import, des colonnes `not_applicable_*_json` en base, de la résolution du N/A dans le dashboard. Migration `ALTER TABLE` ajoutée pour les bases existantes.

## 2026-04-28 : première version
`aacc17c` *Initial commit : NOX_Manager v1*. Structure `wikidocs_qt/`, création de projet, dashboard, import, export Excel, build PyInstaller.

## Repères (dates de fichiers, hors git)
- 2026-04-07 : templates `Template_BDD_CE/CECC/DPE_N0X.xlsx`.
- 2026-04-13 : notes de compilation (`Compilation de l'exe.txt`).
- 2026-04-29 : `Test_interface.py`.
- 2026-07-21 : `NOX_Manager.spec`, `qt_main.py`.
