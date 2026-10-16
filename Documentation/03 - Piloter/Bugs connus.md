---
tags: [nox, bugs]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Bugs connus

Défauts relevés par **lecture du code** le 2026-09-21. Aucun n'a été reproduit à l'exécution : la colonne « Confiance » indique à quel point la lecture suffit. Reproduire avant de corriger ([[Plan de test]]). Une fois corrigé : supprimer l'entrée ici, la citer dans [[Journal de dev]] et [[Changelog]].

| ID           | Gravité | Sujet                                                                         | Confiance  |
| ------------ | ------- | ----------------------------------------------------------------------------- | ---------- |
| [[#BUG-001]] | Haute   | Clés CECC incohérentes entre import, dashboard et export                      | Haute      |
| [[#BUG-002]] | Haute   | N/A interprété différemment par l'export et le dashboard                      | Haute      |
| [[#BUG-003]] | Moyenne | Statuts CECC proposés ≠ statuts comptés                                       | Haute      |
| [[#BUG-004]] | Moyenne | Export : liste des références différente de celle du dashboard                | Moyenne    |
| [[#BUG-005]] | Moyenne | Suppression de référence : base vidée, fichiers conservés et toujours comptés | Haute      |
| [[#BUG-006]] | Basse   | Colonne MPN écrite deux fois dans l'export CECC                               | À vérifier |

## BUG-001
**Clés CECC incohérentes.** `CECCPage.get_fields` (`upload_document_dialog.py`, ~l.1085-1190) enregistre dans `cecc_fields` les clés du tableau de gauche ; le dashboard (`project_dashboard_window.py:1276`) et l'export (`export_templates.py:575-595`) lisent celles de droite.

| Donnée | Clé écrite à l'import | Clé lue (dashboard / export) |
|---|---|---|
| Statut CECC | `cecc_etat` | `status` |
| Catégorie export | `categorie` | `categorie_export` |
| Licence Oui/Non | `licence_yn` | `licence` |
| N° de licence | `licence_number` | `numero_licence` |
| Pays d'origine 4a | `pays_origine` | `pays_origine_4a` |

Seules `manufacturer_doc`, `manufacturer_part_number`, `nom_cecc` et `cecc_classement` coïncident.

**Conséquences probables** : la complétion CECC reste à 0 % (aucun `status` lu), et les colonnes I, M, N, O, P de l'export CECC sortent vides.
**Piste** : unifier autour de `CECC_FREE_FIELDS` (`document_rules.py`) comme unique source de clés ; prévoir une **migration de lecture** pour les bases existantes (accepter les anciennes clés). Voir NOX-010 dans [[Backlog]].

## BUG-002
**N/A : deux règles différentes.**
- Dashboard (`_is_not_applicable`) : le **dernier** événement mentionnant le code gagne.
- Export (`export_templates._is_not_applicable`) : **un** événement N/A dans tout l'historique suffit.

Scénario : une exigence est marquée N/A, puis repassée « Applicable » avec un document. Le dashboard l'affiche applicable et couverte ; l'export écrit « N/A » dans la cellule et n'y met pas le lien.
**Piste** : une seule fonction de résolution, dans un module sans Qt (voir [[Dette technique#DT-001]]).

## BUG-003
**Statuts CECC.** L'import propose « A demander, Demandé, Relancé, Non conforme, Validé » ; les calculs ne connaissent que « Validé, Relancé, Non conforme, Estimation » (`CECC_STATUSES`). « A demander » et « Demandé » sont ignorés au dénominateur, et « Estimation » ne peut pas être saisi. À trancher avec le métier : quelle est la liste officielle ? (NOX-011 dans [[Backlog]]).

## BUG-004
**Liste des références.** Le dashboard part de `project.json` (`rows`) et ne scanne les dossiers qu'en repli. L'export ne scanne que les dossiers `Documents/` et **s'arrête à la première BDD qui contient des références** (`break`). Une référence dont le dossier a été supprimé ou renommé manuellement disparaît de l'export mais pas du dashboard, et inversement.

## BUG-005
**Suppression d'une référence.** `_on_delete_row` (dashboard) supprime les lignes SQLite mais pas les fichiers, alors que la boîte de dialogue dit « Supprimer tous les documents de … ». Le compteur « Documents » continue de compter les fichiers présents sur disque. Décider : soit supprimer aussi les fichiers (avec confirmation explicite), soit changer le libellé.

## BUG-006
**MPN en double.** `_fill_cecc_sheet` écrit `manufacturer_part_number` en colonnes D et H. Peut être voulu par le template ; à vérifier sur `Template_BDD_CECC_N0X.xlsx` avant d'y toucher.
