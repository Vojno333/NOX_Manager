---
tags: [nox, metier]
maj: 2026-09-21
---

↑ [[00 - Index]] · Vocabulaire : [[Glossaire]]

# Règles métier

Source de vérité du code : `wikidocs_qt/document_rules.py`. Les règles de calcul sont dans `project_dashboard_window.py` et `export_templates.py` ([[Architecture]]).

## Les trois BDD

| BDD | Objet | Contenu suivi |
|---|---|---|
| **CE** | Conformité marquage CE | 4 exigences réglementaires |
| **DPE** | Exigences environnementales / produits | 12 exigences réglementaires |
| **CECC** | Contrôle export | 1 justificatif + champs libres + un statut |

### CE (`CE_REQUIREMENTS`)

| Code | Libellé | Colonne Excel |
|---|---|---|
| 2006/42/UE | Directive Machine | H |
| 2011/65/UE | RoHS | J |
| 2014/30/UE | Compatibilité électromagnétique (EMC) | L |
| 2014/68/UE | Équipement sous pression | M |
| AUTRES | (retiré de `CE_REQUIREMENTS` dans l'état non commité) | N |

### DPE (`DPE_REQUIREMENTS`)

| Code | Libellé | Col. | Code | Libellé | Col. |
|---|---|---|---|---|---|
| 2011/65/UE | RoHS | H | 528/2012 | Biocides | P |
| 2012/19/UE | DEEE | I | 2013/59/Euratom | Rayonnements ionisants | Q |
| 2006/66/CE | Piles et accumulateurs | J | 2017/821 | Devoir de diligence | R |
| 1907/2006 | REACh | K | 2016/1628 | Gaz et particules polluants | S |
| 2019/1021 | POP | L | 517/2014 | Gaz à effet de serre fluorés | N |
| 1005/2009 | SAO | M | 2017/852 | Mercure | O |

### CECC (`CECC_FREE_FIELDS`, `CECC_STATUSES`)

14 champs libres (fournisseur du document, MPN, nom CECC, classement, catégorie EAR99/ECCN/ML ITAR, licence O/N, n° de licence, pays d'origine, valeurs USD, composants contrôlés, code douanier…) et 4 statuts attendus par les calculs : **Validé, Relancé, Non conforme, Estimation**.

⚠️ L'import propose d'autres valeurs (« A demander », « Demandé »…) et d'autres clés : voir [[Bugs connus#BUG-001]].

## Applicabilité tri-état

Pour CE et DPE, chaque exigence d'une référence a un état choisi via `ThreeStateToggle` :

| État | Valeur | Couleur | Sens |
|---|---|---|---|
| N/A | 0 | rouge | Exigence non applicable à cet article |
| Non défini | 1 | gris | Pas encore tranché |
| Applicable | 2 | bleu | À justifier |

- En mode import, l'utilisateur ne peut pas enregistrer tant qu'il reste des exigences « Non défini » : message « … sont encore « Non défini(es) » ».
- L'applicabilité n'est **pas** disponible pour CECC (message dédié, l'option est masquée).
- On ne peut pas importer dans une BDD non activée (`enabled_bdds`).

## Résolution du N/A

Une exigence peut avoir été notée N/A puis « Applicable » plus tard. Le **dashboard** applique la règle : *le dernier événement (par `uploaded_at`) qui mentionne le code gagne* :

1. Si le code figure dans `requirement_codes` → applicable.
2. Sinon s'il figure dans `not_applicable_codes` → N/A.
3. Sinon on passe à l'événement précédent ; aucun événement → applicable (non N/A).

L'**export Excel** applique une règle différente (« un seul N/A dans tout l'historique suffit ») : c'est le [[Bugs connus#BUG-002]]. La règle de référence est celle du dashboard.

## Correspondance des codes

`_code_matches` compare les codes après normalisation : tout ce qui suit ` — ` ou ` | ` est ignoré. Ainsi `1907/2006`, `1907/2006 — REACh` et `1907/2006 | REACh` sont équivalents.

## Calcul de complétion (colonne « Complétion » et KPI)

**CE / DPE** (par ligne) :

```
applicables = exigences de la BDD qui ne sont pas N/A
si aucune applicable → 100 %
score(exigence) = (documents couvrant l'exigence − documents « estimation») / documents couvrant l'exigence
                  (0 si aucun document)
complétion = moyenne des scores des exigences applicables
```

**CECC** (par ligne) : `nb statuts « Validé » / nb statuts dans {Validé, Relancé, Non conforme, Estimation}` (0 si aucun statut).

**KPI** du haut du dashboard : moyenne arrondie des complétions des lignes de chaque type.

### Convention « estimation »

Un document est traité comme une **estimation** (donc à demi-valeur pour la complétion) si son **nom de fichier stocké contient « estimation »** (insensible à la casse). Il n'existe pas de case à cocher : c'est une convention de nommage. Le pied de tableau Excel utilise la même idée (`*estimation*` sur le texte de la cellule, qui est le nom du fichier). Toute évolution doit préserver ou remplacer explicitement cette convention ([[Dette technique#DT-006]]).

## Documents partagés CE / DPE (RoHS)

La directive `2011/65/UE` figure en CE **et** en DPE. Quand un document CE (ou DPE) couvre le RoHS, `_storage_types` le copie dans les deux BDD si elles sont activées ; `_doc_applies_to_type` fait aussi valoir un document RoHS pour les deux types dans les calculs.

## Export Excel

- Sorties : `BDD <type> <n°>/BDD_<type>_<n°>.xlsx`, pour chaque BDD activée, à partir des templates `Template_BDD_<type>_N0X.xlsx`.
- Ligne de données à partir de la ligne 5 ; pied de tableau aux lignes 235/236 du template, déplacé selon le nombre de références.
- Une cellule d'exigence contient : « N/A » si N/A, sinon un **lien hypertexte** vers le document le plus récent couvrant l'exigence (texte = nom du fichier), sinon vide.
- Pied de tableau : formules `AVERAGE` / `COUNTA` / `COUNTIF` (« prouvé » vs « estimé »). Ne pas les remplacer par des valeurs calculées en Python.
- Les couples (fournisseur, référence) exportés viennent du **scan des dossiers** `Documents/`, pas de `project.json` : voir [[Bugs connus#BUG-004]].
