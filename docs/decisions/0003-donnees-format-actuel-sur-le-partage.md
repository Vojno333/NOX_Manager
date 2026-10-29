# 0003 — Données au format actuel, dans le dossier de chaque projet sur le partage

Statut : Accepté · Date : 2026-10-28

## Pourquoi
La nouvelle application doit ouvrir les projets existants sans ressaisie (R31). Les documents doivent rester consultables avec l'explorateur, et les liens des exports doivent y pointer (R30). Il n'y a pas de serveur : chaque poste lit et écrit directement sur le partage.

## Ce qui est décidé
- **Par projet**, dans son dossier sur le partage, au format actuel inchangé :
  - `.nox/project.json` (version 3) ;
  - `.nox/nox_metadata.db` (SQLite, table `uploaded_documents`) ;
  - les dossiers `BDD <type> <n°>/Documents/<Fournisseur>/<Référence>/` ;
  - les exports et leur dossier `OLD/`.
- **Par utilisateur** : `~/.nox_manager/nox_state.json`, pour les projets et emplacements récents.
- **Paramétrage de l'application** : `config.json`, livré avec l'exécutable. Il n'y a aucun secret, donc pas de `.env`.
- La base est utilisée **exactement comme aujourd'hui** pendant la reconstruction (mode WAL compris). L'accès se fait par le module `sqlite3`, en requêtes paramétrées.

## Ce que cela implique
- Toute évolution du format reste lisible par la version précédente, ou bien elle s'accompagne d'une consigne de mise à jour simultanée de tous les postes.
- Le risque d'enregistrements simultanés sur le partage (constat C1) demeure jusqu'à l'évolution E14.
- Pas de SQLAlchemy : le schéma est imposé par l'existant, et des requêtes paramétrées suffisent.
