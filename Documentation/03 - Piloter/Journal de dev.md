---
tags: [nox, journal]
maj: 2026-10-16
---

↑ [[00 - Index]]

# Journal de dev

Plus récent en haut. **Une entrée par session de travail**, courte : ce qui a été fait, ce qui a été décidé, ce qui reste. Les commits n'y sont pas recopiés (voir `git log`), on y met le *pourquoi*.

Modèle d'entrée : [[Modèle - Entrée de journal]].


---

## 2026-10-16 : alignement export ↔ interface
**Objectif** : corriger des signalements utilisateur — import en masse décalé, dossier « chapo » en trop à la création de projet, numéro affiché en trop d'endroits, export Excel avec des colonnes vides.
**Fait** :
- Import en masse (`new_project_dialog.py`) : `_lines()` supprimait les lignes vides colonne par colonne, décalant les colonnes entre elles dès qu'une ligne était vide dans une seule d'entre elles. Remplacé par `_split_bulk_column` (conserve la position de chaque ligne) ; le filtrage des lignes totalement vides se fait après coup, dans `_import_bulk_rows`.
- Création de projet : `project_dir` était `emplacement / numéro d'affaire`. C'est maintenant directement `emplacement` : plus de dossier « chapo », `.nox` et `BDD …` se créent à la racine choisie.
- Accueil et dashboard affichaient le numéro de l'affaire (`project_name`) ; ils affichent maintenant `dossier_number` (ajouté à `nox_state.json` via `ProjectManager.add_recent_project`), avec repli sur le nom si absent (anciens projets).
- Export Excel (`export_templates.py`) : colonnes Libellé (C), MPN (D), N° de commande (F) jamais remplies. Cause racine : `_fill_*_sheet` ne lisait jamais `project.json → rows` (seulement B/E depuis le scan des dossiers, D depuis un éventuel document CECC uploadé). Ajout de `_rows_lookup` pour relire label/mnp/order_number par (fournisseur, référence).
- En testant ce correctif, un deuxième problème, plus profond, est apparu : l'export construisait sa liste de références par **scan des dossiers** (`_scan_supplier_reference_pairs`, propre à `export_templates.py`), alors que le dashboard part de `rows` en priorité (c'était l'ex-BUG-004, retiré de [[Bugs connus]]). Les noms de dossiers passent par `_safe_name()` à la création (espaces normalisés, caractères interdits remplacés) : les clés ne correspondaient plus à celles de `_rows_lookup`, et une référence dont le dossier avait été renommé/supprimé à la main disparaissait silencieusement de l'export sans disparaître du dashboard. Alignée sur l'implémentation du dashboard : `rows` en priorité, scan des dossiers seulement en repli (projets anciens sans `rows`).
**Décidé** : ne pas fusionner les deux implémentations de `_scan_supplier_reference_pairs` (dashboard / export) dans ce passage — elles se comportent maintenant pareil mais restent dupliquées (voir [[Dette technique#DT-001]]).
**Reste / prochain pas** : envisager le module `compliance.py` sans Qt de [[Dette technique#DT-001]] pour porter cette logique une seule fois ; vérifier BUG-006 (MPN dupliqué en D et H dans l'export CECC) si l'occasion se présente.

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
