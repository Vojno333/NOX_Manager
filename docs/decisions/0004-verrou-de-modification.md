# 0004 — Verrou de modification d'un projet (E14)

*Date : 2026-10-28. Statut : acceptée (modalité choisie par l'utilisateur ; durées fixées pendant la réalisation).*

## Contexte

Les projets vivent sur le partage réseau ; plusieurs personnes peuvent ouvrir le même projet. Deux enregistrements simultanés dans la base SQLite sur un partage SMB risquent de la corrompre (constat C1). E14 demande que la deuxième personne soit prévenue et ouvre le projet en lecture seule.

## Décision

- **Lecture seule stricte** (choix de l'utilisateur) : la première personne qui ouvre un projet le tient en modification. Les suivantes voient « Projet ouvert en modification par <utilisateur> sur le poste <poste> depuis <heure> » et l'ouvrent en **lecture seule** : consulter, ouvrir les documents, exporter. Aucun moyen de forcer.
- **Verrou** : le fichier `.nox/verrou.json` du projet (utilisateur Windows, poste, ouverture, dernier signe de vie). Il est créé de façon exclusive (un seul gagnant si deux personnes ouvrent en même temps), rafraîchi **toutes les 2 minutes** tant que le tableau de suivi est ouvert, et supprimé à sa fermeture.
- **Poste planté** : un verrou sans signe de vie depuis **15 minutes** est considéré comme abandonné ; le projet s'ouvre alors normalement en modification. Les deux durées sont dans `config.json` (`verrou_rafraichissement_minutes`, `verrou_peremption_minutes`).
- Le même utilisateur sur le même poste n'est pas bloqué par son propre verrou.

## Conséquences

- Le format des données reste celui de la décision 0003 : `verrou.json` est un fichier en plus, ignoré par l'ancienne application. **L'ancienne application ne pose ni ne respecte ce verrou** : tant que des postes l'utilisent, la protection n'est pas garantie.
- Exporter en lecture seule reste possible : l'export n'écrit pas dans la base.
