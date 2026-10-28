# Besoin — NOX Manager

*Reconstitué depuis le code et `Documentation/` le 2026-10-28 (reprise, palier P2), puis validé point par point le même jour. Les règles R décrivent l'existant, que la refonte reproduit à l'identique. Les évolutions E viennent après.*

## Objet

Constituer et suivre, pour chaque projet, les dossiers de justificatifs de conformité de chaque article (couple fournisseur / référence), selon trois livrables :

- **CE** : marquage CE ;
- **DPE** : exigences environnementales ;
- **CECC** : contrôle export.

L'application produit ensuite les tableaux Excel récapitulatifs, qui renvoient vers les documents déposés.

## Ce qu'elle permet de faire

1. **Créer ou modifier un projet** : numéro d'affaire, numéro de dossier, date, livrables suivis (CE, CECC, DPE), et la liste des articles (fournisseur, référence, libellé, MNP, n° de commande). On peut saisir les articles un par un ou les coller en masse, et télécharger un modèle de fichier d'import.
2. **Déposer un justificatif** pour un ou plusieurs articles d'un même livrable :
   - CE / DPE : régler l'applicabilité de chaque exigence (applicable, non applicable, non défini) et cocher celles que le document couvre ;
   - CECC : renseigner la fiche export (fournisseur, MPN, nom, statut, classement, catégorie, licence, pays d'origine, valeurs…).
3. **Corriger** :
   - régler l'applicabilité seule, sans document (CE / DPE) ;
   - remplacer le justificatif d'une exigence ;
   - retirer le justificatif d'une exigence ;
   - vider un article pour un livrable donné.
4. **Produire les tableaux Excel** des livrables suivis, en archivant la version précédente.

S'y ajoutent des fonctions de consultation : retrouver un projet (projets récents, recherche, ouverture d'un dossier), consulter le tableau de suivi (avancement par article, indicateurs par livrable, filtres par colonne, détail des exigences et documents d'un article), et ouvrir un document.

## Ce qu'elle ne fait pas

- Elle ne lit pas le contenu des documents : c'est la personne qui dit ce qu'un document couvre.
- Elle ne gère pas les droits : la DSI les attribue sur le partage réseau, par un processus externe.
- Elle ne relance pas les fournisseurs (piste V2).
- Elle ne suit pas de date de validité ni d'expiration des justificatifs.
- Elle ne conserve pas d'historique consultable des modifications (la base garde les événements, mais rien ne les affiche).
- Il n'y a pas d'applicabilité pour le CECC.

## Qui l'utilise

Les ingénieurs conformité, qui constituent les dossiers, et les chefs de projet, qui consultent l'avancement et exportent.

**L'application ne fait pas de différence entre eux** : toute personne qui a accès au dossier du projet sur le partage peut tout faire. Les accès sont gérés par la DSI, en dehors de l'application.

## Règles à respecter

**Projet**
- R1. Le numéro d'affaire, l'emplacement, le numéro de dossier, une date au format JJ/MM/AAAA et au moins un livrable sont obligatoires.
- R2. Un article exige un fournisseur et une référence. Un projet contient au moins 1 article et au plus 1 000.
- R3. Le couple fournisseur / référence est unique dans un projet. En cas de doublon, la première ligne est gardée. À l'import en masse, un doublon d'une ligne déjà présente est ignoré. *Comportement actuel, reproduit tel quel par la refonte ; voir l'évolution E1.*
- R4. À l'import en masse, les colonnes sont alignées ligne à ligne : une cellule vide, sur une ligne dont au moins une autre colonne est remplie, reste vide sans décaler les autres. Une ligne entièrement vide est ignorée. Si le nombre de fournisseurs et le nombre de références diffèrent, l'application demande confirmation.
- R5. Le numéro de dossier est mis en majuscules. Il entre dans le nom des dossiers et des fichiers de chaque livrable.
- R6. Retirer un article d'un projet existant propose trois choix : supprimer aussi ses dossiers et ses données, les conserver, ou annuler.

**Dépôt**
- R7. Seuls les fichiers PDF, Word (.docx) et Excel (.xlsx) sont acceptés. *Comportement actuel ; voir E2.*
- R8. Un dépôt groupé ne concerne que des articles d'un même livrable.
- R9. On ne peut pas déposer dans un livrable que le projet ne suit pas.
- R10. CE / DPE : on ne peut pas enregistrer tant qu'une exigence est « non défini ».
- R11. CE / DPE : si aucune exigence n'est cochée comme couverte, aucun fichier n'est conservé. Seule l'applicabilité est enregistrée.
- R12. CECC : le fournisseur du document, le MPN et le nom CECC sont obligatoires, ainsi qu'un fichier. Si le nom CECC est laissé vide, il prend le nom du fichier (constat C7). La fiche est pré-remplie avec la dernière fiche CECC de l'article. *Voir E4.*
- R13. Le fichier déposé est nommé automatiquement `Type_Fournisseur_Référence.ext`, sauf si la personne saisit un autre nom. Si un fichier du même nom existe déjà, un suffixe ` (1)`, ` (2)`… est ajouté. L'original n'est jamais déplacé. Le nom automatique garde l'extension d'origine. Un nom saisi qui contient un point est pris tel quel. *Comportement actuel ; voir E3.*
- R14. RoHS (2011/65/UE) est une seule exigence, affichée deux fois en CE (avec l'amendement 2015/863) et présente aussi en DPE. Régler l'une règle les autres. Un document RoHS est rangé, retiré ou remplacé dans les deux livrables s'ils sont suivis.

**Applicabilité et calculs**
- R15. L'état d'une exigence est celui du **dernier** enregistrement qui la mentionne. Couvrir une exigence par un document la rend applicable. Si aucun enregistrement ne la mentionne, elle est « non défini ».
- R16. Les codes d'exigence sont comparés sans leur libellé : « 1907/2006 », « 1907/2006 — REACh » et « 1907/2006 | REACh » sont équivalents.
- R17. Complétion d'un article en CE / DPE : moyenne, sur les exigences applicables, de la part des documents couvrants qui ne sont pas des estimations. Une exigence sans document compte pour 0. S'il n'y a aucune exigence applicable, la complétion est de 100 %. RoHS ne compte qu'une fois. Une exigence « non défini » est traitée comme applicable.
- R18. Un document est une **estimation** si son nom contient le mot « estimation » (majuscules ou minuscules). Cette définition sert à l'export Excel (R26) et, aujourd'hui, au calcul de complétion (R17). *Voir E5.*
- R19. Complétion d'un article en CECC : 100 % si son statut CECC **le plus récent** est « Validé », sinon 0 % (y compris s'il n'a aucune fiche CECC). Statuts officiels, proposés à la saisie : A demander, Demandé, Relancé, Non conforme, Validé.
- R20. L'indicateur d'un livrable est la moyenne arrondie des complétions de ses articles. Il suit les filtres actifs du tableau de suivi.

**Corrections**
- R21. Retirer le justificatif d'une exigence la laisse « applicable », sans document. Un fichier qui ne justifie plus aucune exigence est supprimé. Pour RoHS, le retrait vaut pour CE et DPE. Une confirmation est demandée.
- R22. Remplacer le justificatif d'une exigence : le nouveau document remplace les anciens pour toutes les exigences qu'il couvre. *Comportement actuel ; voir E6.*
- R23. Vider un article pour un livrable supprime ses enregistrements et ses fichiers **dans ce seul livrable**, après une confirmation qui liste les fichiers. Une copie RoHS rangée dans l'autre livrable est conservée, mais ne vaut plus que pour RoHS. *Comportement actuel ; voir E7.*

**Export**
- R24. Un fichier est produit par livrable suivi, à partir de son modèle : `BDD <type> <n°>/BDD_<type>_<n°>.xlsx`. Les articles et leurs informations viennent de la liste du projet.
- R25. Une cellule d'exigence contient « N/A » si l'exigence n'est pas applicable. Sinon, elle contient un lien vers le document le plus récent qui la couvre (le texte affiché est le nom du fichier). Sinon, elle est vide.
- R25 bis. Export CECC : chaque article reprend sa **dernière** fiche CECC. La colonne K contient le nom CECC (ou, à défaut, le nom du fichier), avec un lien vers le document. Les colonnes D et H contiennent le MPN de la fiche, ou à défaut le MNP de l'article. *Comportement actuel ; voir E8.*
- R25 quater. Exports CE et DPE : la colonne D contient le MPN de la dernière fiche CECC de l'article, ou à défaut son MNP. Un document dont le fichier a disparu est affiché par son nom, sans lien.
- R25 ter. Chaque export porte le titre « BASE DE DONNEES <type> - <numéro d'affaire> » et un onglet nommé « BDD <type> <numéro d'affaire> ». *Comportement actuel ; voir E9.*
- R26. Les totaux de bas de tableau restent des formules Excel (prouvé / estimé), pas des valeurs figées.
- R27. Avant d'écrire, l'export précédent est déplacé dans `OLD/`, renommé avec la date de sa dernière modification. Si l'un des fichiers est ouvert dans Excel, rien n'est écrit et un message le signale.

**Projets**
- R28. Chaque personne retrouve ses 10 derniers projets et ses 10 derniers emplacements.
- R29. Retirer un projet des récents le laisse intact. Le supprimer définitivement efface tout son dossier, après une double confirmation.

**Rangement**
- R30. Les documents déposés restent rangés dans le dossier du projet sur le partage réseau, dans l'arborescence `BDD <type> <n°>/Documents/<Fournisseur>/<Référence>/`. On peut les consulter directement avec l'explorateur Windows, et les liens de l'export Excel y pointent.

**Continuité**
- R31. La nouvelle application ouvre les projets existants créés par l'application actuelle et permet de continuer à travailler dessus : liste des articles, documents, applicabilité, fiches CECC, exports archivés. Aucune ressaisie n'est nécessaire.

## Points non tranchés

- ~~P1. **Statuts CECC**~~ Tranché le 2026-10-28 : la liste officielle est celle de la saisie (R19), et le calcul actuel est confirmé.
- ~~P2. **Estimation** : faut-il garder la convention du mot dans le nom du fichier, ou en faire une case à cocher ?~~ Tranché le 2026-10-28 : on garde la convention, voir E5.
- ~~P3. **MPN en double**~~ Tranché le 2026-10-28, voir E8.
- ~~P4. **Réglages de projet**~~ Tranché le 2026-10-28 : les livrables se changent en modifiant le projet. L'écran séparé est abandonné.
- ~~P5. **Nom du projet**~~ Tranché le 2026-10-28 : c'est le numéro d'affaire (voir `donnees.md`).
- ~~P6. **Dossiers sur le partage**~~ Tranché le 2026-10-28, devenu R30.
- ~~P7. **Supprimer définitivement un projet**~~ Tranché le 2026-10-28 : la suppression reste possible depuis l'application, pour tous (R29).
- ~~P8. **Chef de projet**~~ Tranché le 2026-10-28 : pas de différenciation, tout le monde peut tout faire.
- ~~P9. **Lignes multiples d'un même couple (E1)**~~ Tranché le 2026-10-28 : chaque ligne a ses propres justificatifs (voir E1).
- ~~P10. **Formats acceptés (E2)**~~ Tranché le 2026-10-28, voir E2.
- ~~P11. **Pré-remplissage CECC (E4)**~~ Tranché le 2026-10-28 : seuls le fournisseur et le MNP sont repris (voir E4).
- ~~P13. **Rangement des lignes multiples (E1)**~~ Tranché le 2026-10-28, voir E1.

*Aucun point ouvert au 2026-10-28.*

## Évolutions validées, à réaliser après la refonte

*La refonte reproduit d'abord l'existant à l'identique. Ces changements viennent ensuite, chacun comme une tâche.*

- E1. **Unicité sur la ligne complète** : ce n'est plus le couple fournisseur / référence qui est unique, mais la ligne entière (fournisseur, référence, MNP, libellé, n° de commande). Le même couple peut apparaître plusieurs fois. Seules les lignes strictement identiques sont fusionnées. **Chaque ligne a ses propres justificatifs, sa propre applicabilité et sa propre complétion**, et elle occupe sa propre ligne dans l'export. Remplace R3.
  - Rangement : un article présent sur une seule ligne reste dans `<Fournisseur>/<Référence>/`. À partir de deux lignes, chacune a un sous-dossier `<Fournisseur>/<Référence>/<N° de commande>/`. Si plusieurs lignes ont le même n° de commande, ou n'en ont pas, on ajoute un suffixe `_1`, `_2`… Complète R30.
- E2. **Formats de fichiers étendus** : liste fermée, validée le 2026-10-28. Remplace R7.
  - PDF : .pdf
  - Word : .doc, .docx
  - Excel : .xls, .xlsx, .xlsm, .csv
  - PowerPoint : .ppt, .pptx
  - Photos : .jpg, .jpeg, .png, .tif, .tiff, .bmp
  - Mails : .msg, .eml
  - Archives : .zip
  - Texte : .txt
- E3. **Extension toujours conservée** : même quand la personne saisit un nom, l'extension du fichier d'origine est gardée. Complète R13.
- E4. **Premier remplissage de la fiche CECC** : s'il n'existe pas encore de fiche CECC pour l'article, la fiche est pré-remplie avec les informations de l'article : le fournisseur dans « Fournisseur doc / MANUFACTURER », le MNP dans « Manufacturer Part Number ». Complète R12.
- E5. **Dans l'outil, une estimation vaut un validé** (l'estimation est déclarative, sous la responsabilité de l'ingénieur) :
  - R17 : une exigence applicable couverte par au moins un document compte pour 100 %, estimation ou non ;
  - R19 : un statut le plus récent « Estimation » (présent seulement dans d'anciennes fiches, car il n'est plus proposé à la saisie) compte comme « Validé ».
  L'export Excel ne change pas : il garde la distinction « prouvé / estimé » (R18, R26).
- E6. **Remplacement limité aux exigences sélectionnées** : dans le détail d'un article, on peut sélectionner une ou plusieurs exigences, puis « Remplacer ». Le nouveau document remplace l'ancien **pour ces seules exigences**. Si plusieurs exigences sont sélectionnées, une alerte prévient que le remplacement s'applique à toutes. Remplace R22.
- E7. **Vider un article vide aussi le RoHS de l'autre livrable** : RoHS étant une seule exigence, vider un article en CE (ou en DPE) supprime aussi le justificatif RoHS de cet article rangé dans l'autre livrable. La confirmation le signale. Remplace l'exception RoHS de R23.
- E8. **Colonnes D et H de l'export CECC distinctes** : la colonne D contient toujours le MNP saisi pour l'article dans le projet, et la colonne H toujours le MPN de la fiche CECC (vide sans fiche). Remplace la partie D / H de R25 bis.
- E9. **Titre des exports au numéro de dossier** : le titre de chaque export Excel devient « BASE DE DONNEES <type> - <numéro de dossier> », au lieu du numéro d'affaire, et l'onglet devient « BDD <type> <numéro de dossier> ». Remplace R25 ter.

*Corrections de défauts constatés en R4 (`docs/diagnostic/constats.md`), validées le 2026-10-28 :*

- E10. **Nom CECC vraiment obligatoire** (C7) : un dépôt CECC sans nom CECC est refusé, comme pour le fournisseur doc et le MPN. Le nom n'est plus repris automatiquement du fichier.
- E11. **Chaque export pointe vers son propre dossier** (C8) : pour un document RoHS rangé dans les deux livrables, l'Excel CE pointe vers la copie du dossier CE, et l'Excel DPE vers celle du dossier DPE.
- E12. **Fichier disparu signalé** (C9) : un document enregistré dont le fichier n'est plus sur le disque est signalé dans le tableau de suivi.
- E13. **Liens relatifs dans les exports** (C10) : les liens de l'Excel sont relatifs au dossier du projet. Ils restent valides si le projet est déplacé ou renommé.

*Ajoutée le 2026-10-28, à l'étape R6 :*

- E14. **Protection contre les enregistrements simultanés** (C1) : quand une personne ouvre un projet en modification, les autres sont prévenues (« projet ouvert en modification par X ») et l'ouvrent en lecture seule. La modalité exacte sera précisée au moment de la tâche.
