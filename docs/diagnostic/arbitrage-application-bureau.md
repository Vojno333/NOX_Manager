# Arbitrage demandé — NOX Manager : application de bureau hors catalogue

*Pour le référent technique. Rédigé le 2026-10-28, à l'étape R6 de la reprise.*

## La question

Le métier demande que NOX Manager **reste un exécutable installé sur les postes**, avec toutes les données sur le partage réseau. Le catalogue ne prévoit pas d'application de bureau : à partir de P2, il impose FastAPI, Jinja2 / HTMX, un conteneur et une connexion portée par le proxy.

**Faut-il ouvrir le catalogue à une application de bureau pour ce cas, ou maintenir l'application web ?**

## Contexte

- Application de conformité produit (justificatifs CE, DPE et contrôle export, par article de projet). Utilisée par les ingénieurs conformité et les chefs de projet, sans différence de droits dans l'application.
- Qualifiée **P2** : données partagées entre collègues, 4 actes métier, un seul métier, pas de traitement de fond.
- Existant : application PySide6 (Qt) compilée avec PyInstaller. Chaque projet est un dossier sur un partage SMB, avec `.nox/project.json` et une base SQLite `.nox/nox_metadata.db`. Il n'y a **aucun serveur**.
- Besoin validé (`docs/besoin/besoin.md`) :
  - **R30** : les documents restent dans l'arborescence du projet sur le partage, consultables avec l'explorateur Windows, et les liens des exports Excel y pointent ;
  - **R31** : la nouvelle application ouvre les projets existants sans ressaisie.
- **Les droits** sont gérés par la DSI, au niveau des dossiers du partage : chacun ne voit que les projets auxquels il a accès.

## Pourquoi le métier refuse l'application web

Avec un serveur, c'est le **compte du serveur** qui lit les dossiers. Toute personne connectée verrait donc tous les projets, quels que soient ses droits sur le partage. Reproduire les droits de la DSI, dossier par dossier, ferait basculer en P3 (« chacun ne voit que ce qui le concerne »). Le métier préfère que le partage continue de filtrer l'accès.

## Les options

| Option | Ce qu'elle coûte |
|---|---|
| **A. Ouvrir le catalogue à une application de bureau** (PySide6 + SQLite par projet sur le partage, PyInstaller) | Le métier conserve son fonctionnement et les droits DSI restent intacts. Mais il faut définir les règles du catalogue pour ce type d'application (couches, tests, livraison). Le risque d'accès concurrent à SQLite sur SMB demeure (constat C1) et devrait être encadré, par exemple par un verrou par projet, sans le mode WAL sur le partage. |
| **B. Application web P2 sans cloisonnement** | Conforme au catalogue. Tous les utilisateurs de l'application voient tous les projets, et le métier doit l'accepter (il le refuse aujourd'hui). Le conteneur doit monter le partage en lecture et écriture. Les liens Excel doivent cibler des chemins UNC ou être relatifs (E13). |
| **C. Application web P3 avec reprise des droits** | Conforme au catalogue, et chacun ne voit que ses projets. Mais un développeur responsable est obligatoire, il faut reproduire les droits du partage, et le coût est de plusieurs semaines. |

## Ce qui avance en attendant

Le diagnostic, la description du besoin et la référence de comportement sont **indépendants de la technique** et terminés. Le découpage en tâches peut être préparé. Le gabarit, les décisions techniques et le code attendent l'arbitrage.
