---
tags: [nox, dette]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Dette technique

Constats de structure, sans bug immédiat. Les défauts fonctionnels sont dans [[Bugs connus]] ; la priorité et le statut de chaque entrée sont dans [[Backlog]] (colonne « Source »). Taille : S < 1 h, M < 1 jour, L > 1 jour (estimations à affiner).

| ID | Sujet | Taille |
|---|---|---|
| DT-001 | Logique métier dans l'UI et dupliquée | L |
| DT-002 | Constantes d'exigences dupliquées | S |
| DT-003 | Très gros fichiers d'UI | L |
| DT-004 | Erreurs avalées, aucun journal d'exécution | M |
| DT-005 | Code mort | S |
| DT-006 | Convention « estimation » implicite | M |
| DT-007 | `new_project_dialog2.py` : copie divergente | S |
| DT-008 | Règles `.gitignore` incohérentes | S |
| DT-009 | Aucun test automatisé | L |
| DT-010 | SQLite en WAL et dossiers potentiellement réseau | M |

## DT-001
**Logique métier dans l'UI et dupliquée.**
`_is_not_applicable`, `_code_matches`, `_normalize_requirement_code`, `_compute_*` existent dans `ProjectDashboardWindow` **et** (sauf le calcul) dans `export_templates`. Les deux versions ont déjà divergé ([[Bugs connus#BUG-002]]). Cible : un module `compliance.py` (sans Qt) contenant résolution du N/A, correspondance des codes et complétion, appelé par le dashboard et l'export, et testable seul.

## DT-002
**Constantes dupliquées.**
`_build_table_rows` redéfinit `CE_CODES` / `DPE_CODES` alors que `document_rules` fournit `CE_REQUIREMENTS` / `DPE_REQUIREMENTS` ; `export_templates` porte ses propres tables code→colonne ; la liste de pays (`DZ-Algérie`…) est codée en dur dans `upload_document_dialog.py`. Ajouter une exigence oblige aujourd'hui à modifier 4 endroits. Cible : `document_rules` comme source unique, avec le mapping de colonnes Excel à côté.

## DT-003
**Gros fichiers.**
`upload_document_dialog.py` (~1930 l.), `project_dashboard_window.py` (~1660 l.), `new_project_dialog.py` (~1480 l.). Découpage naturel : un module par page (`CEPage`, `DPEPage`, `CECCPage`), les widgets réutilisables (`ThreeStateToggle`, `DropZone`, `KpiCard`, `FilterChip`, `FilterableHeader`) dans `widgets/`.

## DT-004
**Erreurs avalées.**
`load_project`, `_load_state`, `create_project_file` (suppression du legacy) et l'AppUserModelID font `except Exception: pass/continue`. L'application est compilée sans console (`console=False`) : en cas de problème, l'utilisateur ne voit rien et nous n'avons aucune trace. Cible : `logging` vers `~/.nox_manager/logs/nox.log` (rotation), et message d'erreur explicite quand un `project.json` est illisible.

## DT-005
**Code mort.**
- `export_templates._get_not_applicable_map` (jamais appelée ; clé `not_applicable_requirements` inexistante dans le format).
- `utils.py` : seule `human_size` est utilisée ; `search_rects_with_words` (attend un objet page PDF), `norm_text`, `norm_no_diacritics`, `norm_rel`, `fmt_dt` et l'import de `python-docx` ne servent à rien aujourd'hui, mais **imposent `python-docx` au démarrage** (`from docx import Document` au niveau module).
- `CECC_STATUSES` importé dans `upload_document_dialog.py` sans être utilisé.
- `_scan_supplier_reference_pairs` : deux implémentations divergentes (dashboard et export).

## DT-006
**Convention « estimation ».**
Une estimation est reconnue par la présence du mot dans le **nom de fichier** ([[Règles métier#Convention « estimation »]]). Renommer un fichier change la complétion. Cible : une case « Estimation » à l'import, stockée en base.

## DT-007
**`new_project_dialog2.py`.**
Copie de `new_project_dialog.py` sans le champ MNP, non importée. Deux copies de 1 400 lignes qui divergent. Trancher : fusionner (MNP optionnel) ou supprimer.

## DT-008
**`.gitignore`.**
- `*.spec` exclut `NOX_Manager.spec` : le build n'est pas reproductible depuis le dépôt.
- Les règles `docs/.obsidian/…` visent un dossier `docs/` qui n'existe pas : le dossier est `Documentation/`. Si tu ouvres `Documentation/` dans Obsidian, ajouter `Documentation/.obsidian/workspace*.json`, `Documentation/.obsidian/cache`, `Documentation/.trash/`.
- `Documents/`, `Projects/` : ignorés à tout niveau ; attention si un jour un dossier de code porte ce nom.

## DT-009
**Pas de tests.**
Aucune suite automatisée. Modules facilement testables sans Qt : `project_manager`, `metadata_db`, `project_structure`, et l'export (avec un projet jouet et les templates). Voir NOX-030 dans [[Backlog]] et [[Plan de test]].

## DT-010
**SQLite WAL et réseau.**
`connect_metadata_db` active `journal_mode=WAL`. Si des projets vivent sur un **partage réseau** ou un OneDrive synchronisé, WAL est déconseillé (mémoire partagée non supportée, fichiers `-wal`/`-shm` synchronisés au mauvais moment). **À valider** : où les utilisateurs stockent-ils leurs projets, et à plusieurs sur le même projet ?
