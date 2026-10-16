---
tags: [nox, flux]
maj: 2026-10-16
---

↑ [[00 - Index]] · Vocabulaire : [[Glossaire]]

# Flux fonctionnels

Séquences de bout en bout, avec les fonctions concernées. Voir [[Modèle de données]] pour les structures et [[Règles métier]] pour les calculs.

## 1. Création d'un projet

`HomeWindow._create_new_project` → `NewProjectDialog`

1. L'utilisateur saisit nom, n° de dossier, code date, emplacement, BDD à activer, et les références (une par une, en CSV « Fournisseur;Reference;Libelle;MNP;N_commande », ou en colonnes collées).
2. `ProjectManager.create_project_file` écrit `.nox/project.json` (lignes normalisées, BDD ordonnées), supprime l'éventuel `.nox_project.json`, ajoute le projet et l'emplacement aux récents.
3. Pour chaque BDD activée : création de `BDD <type> <n°>/Documents/`, d'un `.xlsx` vide (`touch`) et des dossiers `Fournisseur/Référence` (`create_folders_and_subfolders`).

**Édition d'un projet existant** (même dialogue, `NewProjectDialog` réutilisé depuis le dashboard) : les lignes retirées entraînent la suppression de leurs dossiers vides côté disque et de leurs lignes en base (`delete_uploaded_documents_for_rows`). Vérifier ce comportement avant toute modification ([[Plan de test#Édition de projet]]).

## 2. Ouverture d'un projet

`HomeWindow._open_selected_recent_project` / `_open_existing_project` → `ProjectManager.load_project` → `ProjectDashboardWindow(project_data)`.

- `init_metadata_db` est appelé à l'ouverture du dashboard : les migrations SQLite s'appliquent donc à l'ouverture, pas à l'export.
- Projet introuvable ou illisible : `load_project` renvoie `None` (les erreurs de lecture sont avalées, voir [[Dette technique#DT-004]]).

## 3. Import d'un justificatif

Dashboard → sélection de lignes → « Importer » → `_open_upload_from_selection("import")` → `UploadDocumentDialog(mode="import", batch_targets=…)`.

Contraintes vérifiées avant ouverture : au moins une ligne sélectionnée, **un seul type de BDD** dans la sélection.

Dans le dialogue :
1. Choix du fichier (PDF/DOCX/XLSX, glisser-déposer via `DropZone`).
2. CE/DPE : régler le tri-état de chaque exigence ; cocher celles que **ce document couvre**. CECC : renseigner au minimum *Fournisseur Doc*, *Manufacturer Part Number*, *Nom : CECC*.
3. `_validate()` bloque si des exigences sont « Non défini », si le fichier manque, ou si la BDD n'est pas activée.
4. `_save_document()` : pour chaque cible du lot et chaque dossier de destination (`_target_folders_for`) → copie du fichier + `insert_uploaded_document`. Émet `documentSaved` ; le dashboard recharge.

Cas particulier : si aucune exigence n'est cochée en import CE/DPE, **aucun fichier n'est copié**, et l'état d'applicabilité est enregistré comme en mode 4 (`applicability_only`).

## 4. Applicabilité seule

Bouton « Gérer l'applicabilité » → même dialogue en `mode="applicability"`. Aucun fichier ; une ligne SQLite est insérée par cible avec `stored_filename=""`. Indisponible pour CECC.

## 5. Suivi

`ProjectDashboardWindow._load_table` : `_build_table_rows` produit une ligne par (référence × BDD activée), avec compteur de fichiers présents sur disque (`documents`) et nombre d'événements en base (`documents_db`). Filtres par colonne (`FilterableHeader` + `FilterPopup`) et « chips » de filtres actifs. `DetailPanel` affiche les exigences et documents de la ligne sélectionnée ; un clic sur un document l'ouvre avec l'application par défaut (`_open_file`).

## 6. Export

Bouton d'export → `export_project_templates(project_dir)`.

1. Lecture de `project.json`, regroupement des documents par (fournisseur, référence, BDD) (`_group_docs`).
2. Liste des couples (fournisseur, référence) à partir de **`project.json` → `rows`** (même source que le dashboard) ; repli sur un **scan des dossiers** seulement si `rows` est vide (`_scan_supplier_reference_pairs`). Le libellé, le MNP et le n° de commande de chaque ligne sont relus depuis `rows` pour remplir les colonnes C/D/F des templates (`_rows_lookup`).
3. Pour chaque BDD activée : chargement du template, en-tête projet, remplissage, redimensionnement du tableau et du pied (`_resize_table_area`), extension de la mise en forme conditionnelle, écriture de `BDD <type> <n°>/BDD_<type>_<n°>.xlsx`.
4. Message listant les fichiers, ou message d'erreur (`FileNotFoundError` si un template manque).

L'export **écrase** le fichier du même nom sans confirmation ; ne pas y saisir de données à la main.

## 7. Suppression

| Action | Portée | Réversible |
|---|---|---|
| Accueil → « Retirer des projets récents » | Entrée dans `nox_state.json` | Oui (rouvrir le projet) |
| Accueil → « Supprimer définitivement » | `shutil.rmtree` du **dossier projet entier**, après une confirmation supplémentaire | **Non** |
| Dashboard → supprimer une référence | Lignes SQLite de (fournisseur, référence) **uniquement** ; les fichiers restent sur disque | Non pour la base ; fichiers conservés (voir [[Bugs connus#BUG-005]]) |
