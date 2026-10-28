---
tags: [nox, bugs]
maj: 2026-10-26
---

↑ [[00 - Index]]

# Bugs connus

Défauts relevés par **lecture du code** le 2026-09-21. Aucun n'a été reproduit à l'exécution : la colonne « Confiance » indique à quel point la lecture suffit. Reproduire avant de corriger ([[Plan de test]]). Une fois corrigé : supprimer l'entrée ici, la citer dans [[Journal de dev]] et [[Changelog]].

| ID           | Gravité | Sujet                                                                         | Confiance  |
| ------------ | ------- | ----------------------------------------------------------------------------- | ---------- |
| [[#BUG-003]] | Moyenne | Statuts CECC proposés ≠ statuts comptés                                       | Haute      |
| [[#BUG-006]] | Basse   | Colonne MPN écrite deux fois dans l'export CECC                               | À vérifier |

## BUG-003
**Statuts CECC.** L'import propose « A demander, Demandé, Relancé, Non conforme, Validé » ; les calculs ne connaissent que « Validé, Relancé, Non conforme, Estimation » (`CECC_STATUSES`). « A demander » et « Demandé » sont ignorés au dénominateur, et « Estimation » ne peut pas être saisi. À trancher avec le métier : quelle est la liste officielle ? (NOX-011 dans [[Backlog]]).

## BUG-006
**MPN en double.** `_fill_cecc_sheet` écrit `manufacturer_part_number` en colonnes D et H. Peut être voulu par le template ; à vérifier sur `Template_BDD_CECC_N0X.xlsx` avant d'y toucher.
