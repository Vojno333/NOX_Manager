---
tags: [nox, test, recette]
maj: 2026-10-23
---

↑ [[00 - Index]]

# Plan de test (recette manuelle)

Il n'y a **aucun test automatisé** ([[Dette technique#DT-009]]). Ce plan est à jouer avant chaque release ([[Build et livraison]]) et après toute modification touchant les zones concernées. Cocher, dater, signaler les écarts dans [[Bugs connus]].

## Jeu d'essai standard

Créer un projet jetable hors du dépôt (`C:\Temp\NOX_Test\`), n° de dossier `TEST001`, avec 3 références :

| Fournisseur | Référence | Libellé | MNP |
|---|---|---|---|
| VisioParts | VIS-001 | Vis inox M6 x 20 | MNP-001 |
| TechnoVis | VIS-002 | Écrou frein M6 | MNP-002 |
| FixPro | TV-010 | Rondelle plate M6 | MNP-003 |

Prévoir 3 petits fichiers : `rohs.pdf`, `reach_estimation.pdf` (le mot « estimation » est significatif), `cecc.pdf`.

## Scénarios

### Démarrage
- [ ] Splash affiché (build) puis accueil maximisé, icône correcte.
- [ ] Premier lancement sans `~/.nox_manager/` : dossier créé, liste des projets vide sans erreur.

### Création de projet
- [ ] Création avec les 3 BDD : dossiers `BDD CE/CECC/DPE TEST001/Documents/<Fournisseur>/<Référence>` créés, `.nox/project.json` présent.
- [ ] Création avec **seulement CE et DPE** : pas de dossier CECC.
- [ ] Références en double, ou sans fournisseur : ignorées.
- [ ] Nom de fournisseur avec `/` ou `:` : remplacé par `_` dans le dossier.
- [ ] Saisie en masse (CSV et colonnes collées).

### Édition de projet
- [ ] Ajouter une référence : dossier créé, ligne dans le dashboard.
- [ ] Retirer une référence **avec documents** : vérifier ce qui se passe (dossier supprimé ? base nettoyée ?) et comparer avec [[Flux fonctionnels#1. Création d'un projet]].
- [ ] Désactiver une BDD : la colonne/les lignes correspondantes disparaissent, aucun fichier n'est supprimé.

### Ouverture / projets récents
- [ ] Le projet apparaît en tête des récents, statistiques cohérentes.
- [ ] Projet déplacé ou supprimé à la main : comportement à l'ouverture (message d'erreur attendu, pas de plantage).
- [ ] « Retirer des récents » conserve le dossier ; « Supprimer définitivement » demande **deux** confirmations et supprime le dossier (tester **uniquement** sur le jeu d'essai).

### Applicabilité
- [ ] Sélectionner VIS-001 en CE → « Gérer l'applicabilité » : tout « Non défini » par défaut.
- [ ] Enregistrement refusé s'il reste des « Non défini ».
- [ ] Passer une exigence en N/A puis Applicable : la complétion et le détail suivent le **dernier** état ([[Règles métier#Résolution du N/A]]).
- [ ] CECC : l'applicabilité est refusée avec un message clair.

### Import
- [ ] Import de `rohs.pdf` sur VIS-001 en CE avec RoHS coché : fichier copié dans **CE et DPE** si les deux sont activés.
- [ ] Import sans aucune exigence cochée : aucun fichier copié, applicabilité enregistrée.
- [ ] Import en lot sur 2 références du même type ; sélection mixte CE+DPE refusée.
- [ ] Même fichier importé deux fois : deuxième copie nommée ` (1)`.
- [ ] `reach_estimation.pdf` couvrant REACh : complétion de l'exigence à 0 (estimation) ; renommer sans « estimation » : à 100 %.
- [ ] CECC : refus si *Fournisseur Doc*, *MPN* ou *Nom : CECC* manquent ; puis valeurs bien enregistrées (statut, catégorie, licence, pays).
- [ ] Extension non prévue (ex. `.txt`) : comportement du sélecteur.
- [ ] Fichier ouvert dans Excel/Word pendant la copie : message d'erreur, aucune ligne SQLite orpheline.

### Dashboard
- [ ] KPI CE / CECC / DPE cohérents avec la moyenne des lignes.
- [ ] Filtres de colonnes, puces de filtres actifs, réinitialisation.
- [ ] Sélection multiple de même type OK ; de types différents refusé.
- [ ] Clic sur un document du panneau de détail : ouverture dans l'application par défaut.
- [ ] Redimensionnement, écran plus petit ou mise à l'échelle 125/150 % : rien d'inaccessible ([[Conventions de code#Qt / PySide6]]).

### Export
- [ ] Un fichier `BDD_<type>_TEST001.xlsx` par BDD activée, dans le dossier `BDD <type> TEST001/`.
- [ ] Ouvrir dans Excel : en-tête projet, une ligne par référence, N/A affichés, liens hypertexte fonctionnels, formules de pied de tableau calculées, mise en forme conditionnelle étendue.
- [ ] **Cas de non-régression BUG-002** : exigence N/A puis Applicable avec document → doit apparaître avec un lien, pas « N/A ».
- [ ] **Cas de non-régression BUG-001** : statut CECC et n° de licence saisis → présents dans les colonnes du fichier CECC.
- [ ] Template manquant : message d'erreur explicite (renommer temporairement un template).
- [ ] Export répété : l'ancien fichier est déplacé dans `OLD/` sous `BDD_<type>_<n°>_V_<date>.xlsx` ; deux exports dans la même minute → suffixe ` (2)`.
- [ ] Un export ouvert dans Excel : message clair et **aucun** fichier modifié ni archivé (y compris pour les autres BDD).

### Build (release uniquement)
- [ ] Toutes les vérifications ci-dessus jouées **avec `NOX_Manager.exe`**, sur un poste sans Python.

## Compatibilité de données
- [ ] Ouvrir un projet créé par une **version précédente** : migration silencieuse, aucune donnée perdue.
- [ ] Projet contenant l'ancien `.nox_project.json` seul : chargé, converti à la première sauvegarde.

## Automatisation à viser (NOX-030 dans [[Backlog]])
Priorité aux tests sans interface : `project_manager` (normalisation des lignes, récents), `metadata_db` (insertion, migration d'une base ancienne, suppression), `compliance` une fois extrait, export sur projet jouet (relire le `.xlsx` avec openpyxl et vérifier valeurs et liens).
