# Données — NOX Manager

*Reconstitué depuis le code le 2026-10-28. Les règles citées renvoient à `besoin.md`.*

## Projet

- **Numéro d'affaire** — obligatoire. Il apparaît dans le titre et le nom d'onglet de chaque export Excel et dans les projets récents. Le titre de la fenêtre affiche, lui, le numéro de dossier.
- **Numéro de dossier** — obligatoire, en majuscules (R5).
- **Code date** — obligatoire, JJ/MM/AAAA.
- **Emplacement** — obligatoire : le dossier qui accueille le projet.
- **Livrables suivis** — au moins un parmi CE, CECC, DPE, dans cet ordre.
- Date de création, date de mise à jour.

Un projet contient de 1 à 1 000 **articles** (R2).

## Article

- **Fournisseur** — obligatoire.
- **Référence** — obligatoire.
- Libellé, MNP, n° de commande — facultatifs.

Le couple fournisseur / référence est unique dans le projet (R3). Il identifie l'article dans tous les enregistrements.

## Enregistrement de justificatif

Un enregistrement n'est pas seulement un document : c'est un **événement daté** de dépôt ou de réglage d'applicabilité. Les enregistrements ne sont jamais modifiés pour refaire l'histoire, à deux exceptions près : le retrait d'une exigence couverte (R21) et la suppression (R23, R6).

- **Article** (fournisseur, référence) — obligatoire.
- **Livrable de saisie** — CE, DPE ou CECC.
- **Livrables de rangement** — ceux où le fichier a été copié (deux livrables pour un document RoHS, R14).
- **Exigences couvertes** — codes et libellés. Ce sont les exigences que **ce fichier** justifie. La liste est vide sans fichier.
- **Exigences applicables** — codes.
- **Exigences non applicables** — codes et libellés.
- **Fiche CECC** — les 13 champs de la liste ci-dessous (CECC uniquement).
- **Fichier** — nom d'origine, nom de rangement, emplacement relatif au projet. Ces champs sont vides pour un réglage d'applicabilité seule.
- **Date** — obligatoire. C'est elle qui départage les enregistrements (R15).

Un enregistrement appartient à un article. Un article a zéro, un ou plusieurs enregistrements.

## Listes de référence

**Exigences CE** : 2006/42/UE Directive Machine · 2014/35/UE Basse Tension · 2011/65/UE RoHS · 2015/863 RoHS (amendement, même exigence que 2011/65/UE) · 2014/30/UE CEM · 2014/68/UE Équipements sous pression.

**Exigences DPE** : 2011/65/UE RoHS · 2012/19/UE DEEE · 2006/66/CE Piles et accumulateurs · 1907/2006 REACh · 2019/1021 POP · 1005/2009 SAO · 517/2014 Gaz à effet de serre fluorés · 2017/852 Mercure · 528/2012 Biocides · 2013/59/Euratom Rayonnements ionisants · 2017/821 Devoir de diligence · 2016/1628 Gaz et particules polluants.

**Fiche CECC** (champ — colonne de l'export) : Fournisseur doc (G, obligatoire) · Manufacturer Part Number (H, obligatoire) · Statut (I) · Date (J) · Nom CECC (K, obligatoire) · Classement : NC, DU, DI (L) · Catégorie EAR99 / ECCN / ML ITAR (M) · Licence Oui / Non (N) · N° de licence (O) · Pays d'origine 4a, liste ISO (P) · Valeur EAR99 en USD (Q) · Valeur ECCN en USD (R) · Composants contrôlés intégrés (10.1) (S).

**Statuts CECC** : A demander · Demandé · Relancé · Non conforme · Validé. D'anciennes fiches peuvent porter « Estimation » (voir E5).

## Préférences par personne

- 10 projets récents (nom, emplacement, date de dernière ouverture).
- 10 emplacements récents.
- Emplacement par défaut.

## Fichiers produits

- Les documents déposés, rangés par livrable, fournisseur et référence (R30).
- Un tableau Excel par livrable suivi, et ses versions précédentes archivées dans `OLD/` (R24, R27).
