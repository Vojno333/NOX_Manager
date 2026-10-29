# Index de l'existant — NOX Manager

*Établi le 2026-10-28, au démarrage de la reprise (étape R1). Hors `.git/`, `build/`, `dist/`, `__pycache__/`.*

## Points d'entrée

| Point d'entrée | Ce qu'il lance |
|---|---|
| `qt_main.py` → `run()` | l'application (accueil `HomeWindow` en plein écran) |
| `NOX_Manager.spec` / `Compilation de l'exe.txt` | la fabrication de l'exécutable Windows (PyInstaller) |

Chaîne d'appel : `qt_main` → `home_window` → `new_project_dialog`, `project_dashboard_window` → `upload_document_dialog`, `filter_popup`, `export_templates` → `metadata_db`, `project_manager`, `project_structure`, `document_rules`, `window_geometry`, `theme`, `utils`.

## Code atteignable

| Fichier | Lignes | Octets | Rôle |
|---|---:|---:|---|
| `qt_main.py` | 83 | 2 711 | Démarrage : style, icône, fermeture du splash, ouverture de l'accueil |
| `wikidocs_qt/__init__.py` | 3 | 62 | Marqueur de package |
| `wikidocs_qt/home_window.py` | 996 | 37 032 | Accueil : projets récents, emplacements, création / ouverture de projet |
| `wikidocs_qt/new_project_dialog.py` | 1 504 | 55 693 | Création / modification d'un projet : lignes fournisseur / référence / libellé / MNP / n° de commande, import en masse |
| `wikidocs_qt/project_dashboard_window.py` | 1 951 | 84 857 | Tableau de suivi du projet : KPI, filtres, panneau de détail, suppression / détachement de documents, lancement de l'export |
| `wikidocs_qt/upload_document_dialog.py` | 1 986 | 75 734 | Dépôt d'un justificatif : pages CE / DPE / CECC, bascule tri-état, zone de glisser-déposer |
| `wikidocs_qt/filter_popup.py` | 98 | 3 887 | Fenêtre de filtre des en-têtes du tableau |
| `wikidocs_qt/export_templates.py` | 806 | 29 483 | Remplissage des trois modèles Excel, archivage de l'export précédent |
| `wikidocs_qt/metadata_db.py` | 325 | 10 374 | Base SQLite par projet (documents déposés), migrations tolérantes |
| `wikidocs_qt/project_manager.py` | 238 | 7 835 | État applicatif, lecture / écriture de `project.json` et de l'état utilisateur |
| `wikidocs_qt/project_structure.py` | 48 | 1 386 | Création de l'arborescence de dossiers d'un projet |
| `wikidocs_qt/document_rules.py` | 135 | 5 205 | Règles métier : types de BDD, exigences CE / DPE, champs et statuts CECC, tri-état |
| `wikidocs_qt/window_geometry.py` | 52 | 1 918 | Dimensionnement et centrage des fenêtres |
| `wikidocs_qt/theme.py` | 197 | 4 198 | Feuille de style de l'application |
| `wikidocs_qt/utils.py` | 97 | 3 294 | Utilitaires ; **seul `human_size` est utilisé** |

## Données et ressources atteignables

| Fichier | Octets | Rôle |
|---|---:|---|
| `Template_BDD_CE_N0X.xlsx` | 48 909 | Modèle d'export CE |
| `Template_BDD_DPE_N0X.xlsx` | 50 043 | Modèle d'export DPE |
| `Template_BDD_CECC_N0X.xlsx` | 33 748 | Modèle d'export CECC |
| `wikidocs_qt/eu_icon.svg` | 1 118 | Icône du KPI CE |
| `wikidocs_qt/dpe_icon.svg` | 32 225 | Icône du KPI DPE |
| `LOGO_Nox.ico` | 22 853 | Icône de l'application |
| `flash.png` | 58 417 | Écran de démarrage de l'exécutable |

## Atteignable depuis aucun point d'entrée

| Élément | Taille | Constat |
|---|---:|---|
| `wikidocs_qt/project_settings_dialog.py` | 280 l. | Dialogue de réglages de projet ; **importé nulle part** |
| `wikidocs_qt/new_project_dialog2.py` | 1 471 l. | Variante sans champ MNP, non suivie par git ; importée nulle part |
| `Test_interface.py` | 643 l. | Maquette autonome de l'accueil |
| `utils.py` : `norm_text`, `norm_rel`, `fmt_dt`, `norm_no_diacritics`, `search_rects_with_words` | — | Jamais appelées ; `search_rects_with_words` impose pourtant `python-docx` au démarrage |
| `export_templates.py` : `_get_not_applicable_map`, `_clear_row_values` | — | Jamais appelées |
| `document_rules.py` : `REQ_UNDEFINED`, `ROHS_CODE` | — | Non référencés hors du module (peuvent servir en interne) |

Soit environ **2 400 lignes sur 10 300** hors périmètre de reprise.

## Doublons repérés

- `_normalize_requirement_code`, `_code_matches`, `_is_not_applicable` existent à la fois dans `export_templates.py` et comme méthodes de `project_dashboard_window.py`, en plus des versions de `document_rules.py`. La même règle (tri-état, correspondance des codes) est donc écrite à trois endroits.

## Hors code

| Élément | Rôle |
|---|---|
| `CLAUDE.md` | Consignes de travail sur le dépôt |
| `Documentation/` | Coffre Obsidian : architecture, règles métier, modèle de données, plan de test, backlog, bugs connus, journal, changelog, guide utilisateur. Source précieuse pour R3 et R4 |
| `.gitignore` | Exclut `*.spec`, `build/`, `dist/` |
