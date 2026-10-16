---
tags: [nox, architecture]
maj: 2026-09-21
---

↑ [[00 - Index]] · Vocabulaire : [[Glossaire]]

# Architecture

## Vue d'ensemble

Application de bureau **monoprocessus, sans serveur** : PySide6 pour l'interface, SQLite + JSON pour les données, openpyxl pour l'export Excel. Tout est stocké dans le dossier du projet choisi par l'utilisateur, sauf un petit état par utilisateur dans `~/.nox_manager/`.

```
qt_main.py                     ← point d'entrée (QApplication, thème, splash)
└── HomeWindow                 ← accueil, projets récents
    ├── NewProjectDialog       ← création / édition d'un projet
    └── ProjectDashboardWindow ← tableau de suivi d'un projet
        ├── UploadDocumentDialog   ← import d'un justificatif / applicabilité
        ├── ProjectSettingsDialog  ← BDD activées…
        ├── FilterPopup            ← filtre de colonne
        └── export_project_templates() → 3 fichiers Excel
```

## Dépendances entre modules

```
document_rules   ← (constantes, aucune dépendance)
project_manager  → document_rules
metadata_db      → project_manager (get_project_hidden_dir)
project_structure (autonome)
window_geometry   (autonome, Qt)
utils             (autonome ; importe python-docx)
theme             (autonome)
export_templates → metadata_db, project_manager
new_project_dialog → project_manager, project_structure, document_rules, metadata_db, window_geometry
upload_document_dialog → document_rules, project_manager, metadata_db, window_geometry
project_dashboard_window → filter_popup, metadata_db, upload_document_dialog, export_templates,
                           document_rules, project_manager, project_structure, new_project_dialog, window_geometry
home_window → project_manager, new_project_dialog, project_dashboard_window, window_geometry, utils
```

Aucune dépendance circulaire. `document_rules` et `metadata_db` sont les modules « bas niveau » ; les trois gros fichiers d'UI (`upload_document_dialog` ~1900 lignes, `project_dashboard_window` ~1650, `new_project_dialog` ~1480) concentrent l'essentiel de la logique.

## Responsabilités

| Couche | Fichiers | Rôle |
|---|---|---|
| Présentation | `home_window`, `project_dashboard_window`, `new_project_dialog`, `upload_document_dialog`, `project_settings_dialog`, `filter_popup`, `theme`, `window_geometry` | Widgets Qt, styles, positionnement |
| Persistance | `project_manager`, `metadata_db`, `project_structure` | JSON, SQLite, création de dossiers |
| Export | `export_templates` | Remplissage des templates Excel |
| Domaine | `document_rules` | Exigences, champs, statuts |
| Utilitaires | `utils` | Normalisation de texte, formats |

**Attention** : la logique métier (calcul de complétion, interprétation du N/A, correspondance des codes d'exigence) vit **dans les classes d'UI** (`ProjectDashboardWindow._is_not_applicable`, `_compute_*`, `_doc_applies_to_type`) et est **dupliquée** dans `export_templates`. C'est la source du [[Bugs connus#BUG-002]] et la première cible de [[Dette technique#DT-001]].

## Cycle de vie et navigation

1. `qt_main.run()` crée `HomeWindow` (maximisée) et ferme le splash PyInstaller.
2. `HomeWindow` liste les projets récents (`ProjectManager.get_recent_projects`), calcule des statistiques (`_compute_project_stats`) et ouvre un `ProjectDashboardWindow` via `_open_project_from_data`.
3. Le dashboard recharge tout depuis le disque à chaque `_load_table()` : pas de modèle en mémoire partagé, pas de cache persistant (un cache `by_sup_ref` est reconstruit à chaque rechargement).
4. Les dialogues sont modaux (`exec()`) ; `UploadDocumentDialog` émet `documentSaved`, que le dashboard écoute pour recharger.

## Points structurants

- **Tableau du dashboard** : une ligne = un couple (fournisseur, référence) × un type de BDD activé (`enabled_bdds`). `MainTab` + `FilterableHeader` (icône de filtre dans l'en-tête) + `DetailPanel` (panneau de détail à droite).
- **Import** : `UploadDocumentDialog` a deux modes (`mode="import"` et `mode="applicability"`) et trois pages (`CEPage`, `DPEPage`, `CECCPage`). Il gère l'import en lot via `batch_targets`.
- **Partage RoHS CE/DPE** : la directive `2011/65/UE` (RoHS) est commune ; un document CE ou DPE qui la couvre est copié dans les deux dossiers BDD (`_storage_types`).
- **Fenêtres** : toute fenêtre passe par `fit_and_center()` (écran de la fenêtre parente, taille bornée à 92 % de la zone disponible).
- **Icônes** : `dpe_icon.svg` / `eu_icon.svg` chargés depuis `Path(__file__).parent` (`ICONS_DIR`), donc dans `wikidocs_qt/` en dev comme en build.

## Chemins de ressources (dev vs build)

| Ressource | Comment elle est retrouvée | Piège |
|---|---|---|
| `LOGO_Nox.ico` | `qt_main._base_dir()` (`sys._MEIPASS` sinon dossier du script) | À déclarer dans `datas` du build |
| `Template_BDD_*_N0X.xlsx` | `Path(__file__).parent.parent` depuis `export_templates.py` | Doivent être à la racine des données, à côté de `wikidocs_qt/` |
| `*.svg` | `Path(__file__).parent` | Couverts par `('wikidocs_qt', 'wikidocs_qt')` |

Voir [[Build et livraison]].

## Nom historique

Le package s'appelle `wikidocs_qt` et l'AppUserModelID `NOX_Manager.WikidocsQt.1` : reliquat d'un ancien nom. Ne pas changer l'AppUserModelID sans raison (regroupement dans la barre des tâches Windows).
