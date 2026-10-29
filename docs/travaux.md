# Travaux — NOX Manager

*Établi le 2026-10-28 (étape R7 de la reprise). Suivi interne : l'identifiant d'une branche est le numéro de la tâche (`dev/task/<n°>`, depuis `develop`, vers `develop`).*

*Règles de lecture :*
- *« Source » cite les fichiers de `00_ancien/` à ouvrir ; on y reprend les règles, les calculs et les libellés, sans les réécrire de mémoire.*
- *Les tâches d'une même vague peuvent avancer en parallèle : elles ne touchent pas les mêmes fichiers. Une vague attend la précédente.*
- *Chemins du nouveau code relatifs à `01_application/app/`.*

## Partie 1 — Reconstruction à l'identique (R1–R31)

### Vague 1 — Socle

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 1 | **Ressources et référentiels.** Copier les 3 modèles Excel, `LOGO_Nox.ico`, `flash.png`, `eu_icon.svg` et `dpe_icon.svg` dans `ressources/` (racine du dépôt). `core/config.py` les retrouve, en développement comme dans l'exécutable. `models/referentiel.py` contient les exigences CE / DPE, l'alias RoHS, les champs et statuts CECC, les anciennes clés CECC, la correspondance exigence → colonne Excel, la liste des pays et le classement CECC. | — | R14, R19, R25 | ☑ |
| 2 | **Thème et géométrie des fenêtres.** `ui/theme.py` (Fusion, palette claire, feuille de style, Segoe UI 10) et `ui/geometrie.py` (dimensionner et centrer sur le bon écran). | — | technique (AGENTS §4) | ☑ |
| 3 | **Contrôles automatiques sur GitHub.** `.github/workflows/` lance `ruff`, les tests et le contrôle des couches à chaque envoi. | — | technique (décision 0002) | ☑ |

Sources : 1 ← `document_rules.py`, `export_templates.py` (dictionnaires de colonnes), `upload_document_dialog.py` (`COUNTRY_ORIGIN_4A`, listes des menus CECC). 2 ← `theme.py`, `window_geometry.py`, `qt_main.py` (palette).
Tests : 1 — chaque exigence a sa colonne, `2015/863` est un alias de `2011/65/UE`, les 5 statuts officiels. 3 — le workflow échoue sur une couche violée.

### Vague 2 — Accès aux données

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 4 | **Fichier projet.** `models/projet.py` (Projet, Article) et `dataaccess/projet_fichier.py` : lire et écrire `.nox/project.json` v3, lire l'ancien `.nox_project.json` en repli, normaliser les articles (sans fournisseur ou sans référence → retirés ; doublon → le premier gagne), ordonner les livrables. | 1 | R3, R31 | ☑ |
| 5 | **Base des enregistrements.** `models/enregistrement.py` et `dataaccess/base_projet.py` : création et migrations tolérantes, WAL, ajout, lecture, mise à jour des listes de codes, détachement du fichier, suppression par identifiant et par article, dernière fiche CECC. | 1 | R31 | ☑ |
| 6 | **Préférences de l'utilisateur.** `dataaccess/etat_utilisateur.py` : 10 projets et 10 emplacements récents, emplacement par défaut, fichier corrompu → valeurs par défaut sans message. | 1 | R28 | ☑ |
| 7 | **Dossiers et fichiers du projet.** `dataaccess/arborescence.py` : nettoyage des noms (`<>:"/\|?*` → `_`), création de `BDD <type> <n°>/Documents/<F>/<R>/` et du `.xlsx` vide, copie avec suffixe ` (1)`, ` (2)`…, suppression, contenu d'un dossier d'article, présence d'un fichier. | 1 | R5, R13, R30 | ☑ |

Sources : 4 ← `project_manager.py` (`_normalize_rows`, `_normalize_enabled_bdds`, `load_project`, `save_project`, `create_project_file`). 5 ← `metadata_db.py`. 6 ← `project_manager.py` (partie état). 7 ← `project_structure.py`, `upload_document_dialog.py` (`_safe_name_part`, `_unique_target_path`), `new_project_dialog.py` (`_create_project`, création des dossiers).
Tests : 4 et 5 — lecture de `tests/reference/projet_essai` (ACME / REF-001 avec CMD-1, 14 enregistrements). 6 — onzième projet → le plus ancien sort. 7 — S3, collision de noms.

### Vague 3 — Règles d'applicabilité et projets

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 8 | **Applicabilité.** `services/applicabilite.py` : normalisation et correspondance des codes, alias RoHS, état d'une exigence d'après le dernier enregistrement, enregistrement « avec fichier », document valant pour un livrable (RoHS commun), estimation repérée au nom du fichier. | 4, 5 | R14, R15, R16, R18 | ☑ |
| 9 | **Créer, modifier, supprimer un projet.** `services/projets.py` : contrôles et messages, découpage de l'import en masse, modèle CSV, création de la structure, retrait d'articles avec suppression ou conservation des dossiers et données, retrait des récents, suppression définitive. | 4, 5, 6, 7 | R1, R2, R4, R5, R6, R29 | ☑ |

Sources : 8 ← `document_rules.py`, `project_dashboard_window.py` (`_doc_applies_to_type`, `_compute_requirement_score`). 9 ← `new_project_dialog.py` (`_validate`, `_parse_bulk_lines`, `_split_bulk_column`, `_import_bulk_rows`, `_download_bulk_template`, `_create_project`, `_update_project`), `home_window.py` (`_delete_selected_project`).
Tests : 8 — N/A puis Applicable → Applicable ; « 1907/2006 \| REACh » = « 1907/2006 ». 9 — S1, S2, S4, S5 ; chaque message refusé à l'identique.

### Vague 4 — Calculs, export, dépôt, corrections, premiers écrans

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 10 | **Complétion et indicateurs.** `services/completion.py` : lignes article × livrable (liste du projet, repli sur les dossiers), complétion CE / DPE et CECC, indicateurs. | 4, 5, 8 | R17, R19, R20 | ☑ |
| 11 | **Export Excel.** `dataaccess/export_excel.py` (modèles, copie de lignes et de styles, mise en forme conditionnelle, formules du bas, liens) et `services/export.py` (contenu des cellules, archivage dans `OLD/`, contrôle du fichier ouvert). | 4, 5, 7, 8 | R24, R25, R25 bis, R25 ter, R25 quater, R26, R27 | ☑ |
| 12 | **Dépôt d'un justificatif.** `services/depot.py` : contrôles, nommage automatique, livrables de rangement (RoHS), un enregistrement par dossier, applicabilité seule, pré-remplissage CECC, nom CECC repris du fichier (C7). | 5, 7, 8 | R7–R14 | ☑ |
| 13 | **Corrections.** `services/corrections.py` : retirer le justificatif d'une exigence, remplacer, vider un article pour un livrable (copie RoHS réduite à RoHS). | 5, 7, 8 | R14, R21, R22, R23 | ☑ |
| 14 | **Écran d'accueil.** `ui/accueil.py` et `main.py` : projets récents, recherche, ouvrir, créer, supprimer, statistiques disque calculées hors du fil de l'interface. | 2, 6, 9 | R28, R29 | ☑ |
| 15 | **Dialogue de projet.** `ui/dialogue_projet.py` : saisie manuelle, onglet d'import en masse, modèle CSV, mode modification. | 2, 9 | R1–R6 | ☑ |

Sources : 10 ← `project_dashboard_window.py` (`_build_table_rows`, `_compute_ce_dpe_completion`, `_compute_cecc_completion`, `_update_kpis`, `_scan_supplier_reference_pairs`). 11 ← `export_templates.py`. 12 ← `upload_document_dialog.py` (`_validate`, `_save_document`, `_storage_types`, `_auto_name`, `_build_final_filename`, `_cecc_fields_data`, `_prefill_existing_cecc_fields`). 13 ← `project_dashboard_window.py` (`_on_delete_row`, `_keep_only_rohs`, `_remove_justif_for_codes`, `_detach_and_delete_file`, `_on_delete_justif`, `_on_replace_justif`). 14 ← `home_window.py`, `qt_main.py`. 15 ← `new_project_dialog.py` (**pas** `new_project_dialog2.py`).
Tests : 10 — `attendu/tableau_de_suivi.json` identique. 11 — `attendu/exports.json` identique, S22, S23. 12 — S9 à S15. 13 — S17 à S21. 14 et 15 — S1, S6, S24 à S26 à l'écran.

### Vague 5 — Écrans du suivi et référence automatisée

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 16 | **Référence automatisée.** `tests/test_reference.py` : sur une copie de `projet_essai`, le nouveau code produit exactement `attendu/` (tableau, exports, arborescence). | 10, 11 | R31 | ☑ |
| 17 | **Composants du dépôt.** `ui/composants_depot.py` : bascule à trois états, zone de glisser-déposer, pages d'exigences CE et DPE (RoHS synchronisé, compteurs, aperçu du nom). | 2, 1 | R10, R14 | ☑ |
| 18 | **Tableau de suivi.** `ui/tableau_de_suivi.py` et `ui/filtre.py` : onglets Tous / par livrable, indicateurs, filtres par colonne et pastilles, bouton d'export et message de fin. | 2, 10, 11 | R20, R24, R27 | ☑ |

Sources : 17 ← `upload_document_dialog.py` (`ThreeStateToggle`, `DropZone`, `CEPage`, `DPEPage`, `_link_rohs_rows`). 18 ← `project_dashboard_window.py` (`MainTab`, `FilterableHeader`, KPI, `_load_table`, `_export_templates`), `filter_popup.py`.
Tests : 18 — un filtre change les indicateurs (R20).

### Vague 6 — Dialogue de dépôt et détail d'un article

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 19 | **Dialogue de dépôt.** `ui/dialogue_depot.py` : page CECC (menus, aides), assemblage des pages, modes import / applicabilité, lot de cibles, messages de refus. | 12, 17 | R7–R13 | ☑ |
| 20 | **Panneau de détail.** `ui/panneau_detail.py` : exigences et documents d'un article, ouverture d'un document, clic droit Ouvrir / Remplacer / Supprimer, boutons Modifier et Supprimer la référence. | 13, 18 | R21, R22, R23 | ☑ |

Sources : 19 ← `upload_document_dialog.py` (`CECCPage`, `UploadDocumentDialog`, `CECC_FIELD_HELP`). 20 ← `project_dashboard_window.py` (`DetailPanel`, `_on_doc_context_menu`, `_open_file`).

### Vague 7 à 10 — Assemblage, recette, fin de la reconstruction

| # | Tâche | Dépend de | Règles | Fait |
|---|---|---|---|---|
| 21 | **Assemblage et fabrication.** Relier accueil → tableau de suivi → dialogues ; `NOX_Manager.spec` versionné (ressources, icône, écran de démarrage, fermeture du splash) ; `uv run build` ; liste de vérification de la livraison. | 14, 15, 18, 19, 20 | technique (décision 0002) | ☑ |
| 22 | **Recette.** Jouer S1 à S27 sur l'exécutable fabriqué, sur une copie de `projet_essai` et sur une copie d'un vrai projet du partage. Consigner les écarts. | 16, 21 | R1–R31 | ☑ |
| 23 | **Supprimer `00_ancien/`.** Possible seulement si la tâche 22 est sans écart et si la référence automatisée passe. | 22 | — | ☑ |

Sources : 21 ← `00_ancien/NOX_Manager.spec`, `qt_main.py`, `Documentation/02 - Développer/Build et livraison.md`.

## Partie 2 — Évolutions (après la tâche 23)

*Chaque évolution change volontairement un résultat : elle met à jour `tests/reference/attendu/` ou les scénarios dans la même tâche, en le disant dans le commit.*

| Vague | # | Évolution | Dépend de | Fichiers principaux | Fait |
|---|---|---|---|---|---|
| 11 | 24 | **E14** Protection contre les enregistrements simultanés (modalité à préciser d'abord) | 23 | `dataaccess/verrou.py`, `ui/accueil.py`, `ui/tableau_de_suivi.py` | ☑ |
| 11 | 25 | **E5** Une estimation vaut un validé dans l'outil | 23 | `services/completion.py` | ☑ |
| 11 | 26 | **E8** Colonnes D et H de l'export CECC distinctes | 23 | `services/export.py` | ☑ |
| 11 | 27 | **E2** Formats de fichiers étendus | 23 | `services/depot.py`, `ui/dialogue_depot.py` | ☑ |
| 11 | 28 | **E6** Remplacement limité aux exigences sélectionnées | 23 | `services/corrections.py`, `ui/panneau_detail.py` | ☑ |
| 12 | 29 | **E9** Titre et onglet des exports au n° de dossier | 26 | `services/export.py` | ☑ |
| 12 | 30 | **E3** Extension toujours conservée | 27 | `services/depot.py` | ☑ |
| 12 | 31 | **E7** Vider un article vide aussi le RoHS de l'autre livrable | 28 | `services/corrections.py` | ☑ |
| 12 | 32 | **E12** Fichier disparu signalé | 24, 25 | `services/completion.py`, `ui/tableau_de_suivi.py` | ☑ |
| 13 | 33 | **E11** Chaque export pointe vers son propre dossier | 29 | `services/export.py` | ☑ |
| 13 | 34 | **E4** Premier remplissage de la fiche CECC | 30 | `services/depot.py` | ☑ |
| 14 | 35 | **E13** Liens relatifs dans les exports | 33 | `dataaccess/export_excel.py`, `services/export.py` | ☑ |
| 14 | 36 | **E10** Nom CECC vraiment obligatoire | 34 | `services/depot.py`, `ui/dialogue_depot.py` | ☑ |
| 15 | 37 | **E1 (1/2)** Lignes multiples d'un même article : identifiant de ligne, rangement en sous-dossiers, enregistrements rattachés à la ligne | 23, décision à écrire | `models/`, `dataaccess/`, `services/projets.py` | ☑ |
| 16 | 38 | **E1 (2/2)** Lignes multiples : tableau de suivi, dépôt, corrections, export | 37 | `services/`, `ui/` | ☑ |
| — | 39 | *Défaut de recette V4* : E6, le clic droit « Remplacer » ne s'ouvrait que sur la colonne du document ; Ctrl + clic sur un document l'ouvrait au lieu de le sélectionner | 28 | `ui/panneau_detail.py` | ☑ |
| — | 40 | *Livraison v2.0* : E1 livrée activée (décision 0005, avenant), tests indépendants du réglage livré, ménage du dépôt, étiquette `v2.0` | 38, 39 | `config.json`, `tests/conftest.py`, `docs/` | ☑ |

## Couverture des règles

Toutes les règles R1–R31 et les évolutions E1–E14 figurent dans au moins une tâche. Fonctions de consultation : recherche de projet (14), filtres (18), ouverture d'un document (20).
