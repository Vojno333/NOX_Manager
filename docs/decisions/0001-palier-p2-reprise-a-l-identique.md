# 0001 — Palier P2, reconstruction à l'identique puis évolutions

Statut : Accepté · Date : 2026-10-28

## Pourquoi
NOX Manager a été construit hors méthode. Il fallait fixer son palier et le périmètre de la reprise. Les informations doivent être partagées entre collègues ; l'application compte 4 actes métier et un seul métier ; aucun traitement ne tourne en fond ; il n'y a pas de cloisonnement des données (les droits sont gérés par la DSI sur le partage).

## Ce qui est décidé
Palier **P2**. La reprise reconstruit d'abord l'application **à l'identique** (règles R1–R31 de `docs/besoin/besoin.md`, vérifiées par `docs/diagnostic/comportement.md`), puis réalise les évolutions E1–E14, une tâche chacune.

## Ce que cela implique
- Toute différence de comportement pendant la reconstruction est un défaut ou une question, jamais une amélioration discrète.
- `00_ancien/` est gelé ; sa suppression est la dernière tâche de la reconstruction, possible seulement quand la référence de comportement passe sur le nouveau code.
- Les relances fournisseurs par mail (piste V2) seront requalifiées : un envoi en masse sans personne devant l'écran ferait passer en P4.
