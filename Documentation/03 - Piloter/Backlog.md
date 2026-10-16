---
tags: [nox, backlog]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Backlog

> Proposition initiale issue de l'audit de lecture du 2026-09-21. **Les priorités sont à arbitrer par toi** : elles reflètent le risque technique, pas les besoins des utilisateurs.

Priorités : **P0** bloque la fiabilité des données · **P1** à faire bientôt · **P2** confort / qualité · **P3** plus tard.
Statuts : `À faire` · `En cours` · `Fait` · `Abandonné`.

## Comment l'utiliser

- Une ligne = une tâche livrable seule. Ajouter la source (bug, dette, demande utilisateur).
- Quand une tâche démarre : statut `En cours` + entrée dans [[Journal de dev]]. Quand elle est finie : `Fait` + ligne dans [[Changelog]].
- Numéroter à la suite (NOX-0xx), ne jamais réutiliser un numéro.

## Fiabilité des données

| ID | Prio | Tâche | Source | Statut |
|---|---|---|---|---|
| NOX-010 | P0 | Unifier les clés de `cecc_fields` (import ↔ dashboard ↔ export) autour de `CECC_FREE_FIELDS`, avec lecture rétro-compatible des anciennes clés | [[Bugs connus#BUG-001]] | À faire |
| NOX-012 | P0 | Aligner la résolution du N/A de l'export sur celle du dashboard (dernier événement gagnant) | [[Bugs connus#BUG-002]] | À faire |
| NOX-011 | P1 | Définir la liste officielle des statuts CECC (avec le métier) et l'utiliser partout | [[Bugs connus#BUG-003]] | À faire |
| NOX-013 | P1 | Faire partir l'export de la même liste de références que le dashboard (`project.json`) | [[Bugs connus#BUG-004]] | À faire |
| NOX-014 | P1 | Suppression d'une référence : supprimer aussi les fichiers (avec confirmation) ou corriger le libellé | [[Bugs connus#BUG-005]] | À faire |
| NOX-015 | P2 | Vérifier le double export du MPN (colonnes D et H du template CECC) | [[Bugs connus#BUG-006]] | À faire |

## Livraison et outillage

| ID | Prio | Tâche | Source | Statut |
|---|---|---|---|---|
| NOX-001 | P1 | Créer `requirements.txt` (PySide6, openpyxl, python-docx, pyinstaller) avec versions figées | [[Environnement de dev]] | À faire |
| NOX-002 | P1 | Versionner `NOX_Manager.spec` (`!NOX_Manager.spec` dans `.gitignore`) et en faire l'unique procédure de build | [[Build et livraison]] | À faire |
| NOX-003 | P2 | Corriger le `.gitignore` (règles Obsidian pour `Documentation/`) | [[Dette technique#DT-008]] | À faire |
| NOX-004 | P2 | Ajouter un numéro de version affiché dans l'application (accueil / « À propos ») et lu depuis un seul endroit | [[Build et livraison]] | À faire |
| NOX-005 | P1 | Trancher `new_project_dialog2.py` : fusionner (MNP optionnel) ou supprimer | [[Dette technique#DT-007]] | À faire |
| NOX-006 | P2 | Script `build.ps1` : nettoyage `build/` `dist/`, PyInstaller, vérification des ressources embarquées | [[Build et livraison]] | À faire |
| NOX-007 | P2 | Commiter le travail en cours (icônes SVG, `window_geometry.py`, réglages, dashboard) en commits lisibles | [[Journal de dev]] | À faire |

## Qualité et maintenabilité

| ID | Prio | Tâche | Source | Statut |
|---|---|---|---|---|
| NOX-020 | P1 | Extraire un module `compliance.py` sans Qt (N/A, codes, complétion) | [[Dette technique#DT-001]] | À faire |
| NOX-021 | P2 | Centraliser exigences, mapping de colonnes Excel et liste de pays dans `document_rules` | [[Dette technique#DT-002]] | À faire |
| NOX-022 | P3 | Découper `upload_document_dialog.py`, `project_dashboard_window.py`, `new_project_dialog.py` | [[Dette technique#DT-003]] | À faire |
| NOX-023 | P1 | Mettre en place `logging` fichier + messages d'erreur clairs sur `project.json` illisible | [[Dette technique#DT-004]] | À faire |
| NOX-024 | P2 | Supprimer le code mort listé | [[Dette technique#DT-005]] | À faire |
| NOX-025 | P2 | Remplacer la convention « nom contenant estimation » par une case dédiée en base | [[Dette technique#DT-006]] | À faire |
| NOX-030 | P1 | Premiers tests `pytest` : `project_manager`, `metadata_db`, `compliance`, export sur un projet jouet | [[Dette technique#DT-009]] | À faire |
| NOX-031 | P2 | Confirmer où vivent les projets (local / réseau / OneDrive) et statuer sur WAL | [[Dette technique#DT-010]] | À faire |

## Idées d'évolution (non chiffrées, à qualifier avec les utilisateurs)

- Bouton « Ouvrir le fichier Excel » après export, et confirmation avant écrasement.
- Avertir quand un `Template_BDD_*` manque avant de lancer l'export (aujourd'hui erreur au clic).
- Aperçu du document dans le `DetailPanel`.
- Import/export de la liste de références depuis Excel (aujourd'hui : CSV ou colonnes collées).
- Historique visible des événements d'une référence (la base le conserve déjà).
- Alerte d'expiration des justificatifs (nécessite une date de validité).
- Sauvegarde automatique du dossier `.nox/` avant migration ou suppression de référence.

## Fait

_(vide pour l'instant)_
