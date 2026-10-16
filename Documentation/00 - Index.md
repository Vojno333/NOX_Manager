---
tags: [nox, index]
maj: 2026-09-21
---

# 00 - Index : documentation NOX Manager

Point d'entrée unique. Le fichier `CLAUDE.md` à la racine du dépôt est le résumé pour l'assistant de code ; en cas de divergence, **cette documentation fait foi**.

> Notes rédigées à partir de la lecture du code (rien exécuté). Ce qui est interprété est marqué « à valider ».

## Par où commencer ?

| Je veux… | Aller à |
|---|---|
| Comprendre l'application | [[Architecture]] puis [[Règles métier]] |
| Lancer / modifier le code | [[Environnement de dev]] puis [[Conventions de code]] |
| Livrer une version | [[Build et livraison]] puis [[Plan de test]] |
| Savoir ce qui est cassé | [[Bugs connus]] |
| Savoir quoi faire ensuite | [[Backlog]] |
| Utiliser l'application | [[Guide utilisateur]] |

## 01 - Comprendre

- [[Architecture]] : modules, dépendances, cycle de vie
- [[Modèle de données]] : `project.json`, SQLite, arborescence disque
- [[Règles métier]] : BDD CE / DPE / CECC, tri-état, complétion
- [[Flux fonctionnels]] : création, import, applicabilité, export, suppression
- [[Glossaire]] : vocabulaire du domaine et du code

## 02 - Développer

- [[Environnement de dev]] : installer, lancer, déboguer
- [[Conventions de code]] : style, pièges Qt, checklist avant commit
- [[Build et livraison]] : PyInstaller, checklist de release
- [[Plan de test]] : recette manuelle (pas de tests automatisés)

## 03 - Piloter

- [[Backlog]] : tâches priorisées (NOX-xxx)
- [[Bugs connus]] : défauts constatés (BUG-xxx)
- [[Dette technique]] : refactorings à planifier (DT-xxx)
- [[Décisions (ADR)]] : choix d'architecture (ADR-xxx)
- [[Journal de dev]] : historique daté du travail
- [[Changelog]] : historique par version, côté utilisateur

## 04 - Utilisateurs

- [[Guide utilisateur]] : mode d'emploi et dépannage

## Modèles (`_Modèles/`)

[[Modèle - Entrée de journal]] · [[Modèle - ADR]] · [[Modèle - Bug]]

## Identifiants

`BUG-` défaut · `DT-` dette technique · `NOX-` tâche du backlog · `ADR-` décision. Ne jamais réutiliser un numéro.

## Règles de tenue à jour

- Une session de travail = une entrée dans [[Journal de dev]] (modèle : [[Modèle - Entrée de journal]]).
- Changement visible par l'utilisateur = une ligne dans [[Changelog]].
- Choix structurant = une entrée dans [[Décisions (ADR)]] (modèle : [[Modèle - ADR]]).
- Bug corrigé = retiré de [[Bugs connus]] et cité dans le journal (modèle : [[Modèle - Bug]]).
- **Un fait = une note.** Ailleurs, on écrit une ligne et un lien.
