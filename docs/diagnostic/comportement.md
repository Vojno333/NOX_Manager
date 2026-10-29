# Référence de comportement — NOX Manager

*Étape R4 de la reprise, établie le 2026-10-28. Elle porte sur ce qui s'observe de l'extérieur (pourcentages affichés, fichiers et dossiers produits, contenu des exports Excel, messages de refus), jamais sur l'intérieur du code : elle s'applique à l'ancienne comme à la nouvelle application.*

*Elle **fige le comportement actuel**, défauts compris. Les défauts repérés sont listés dans `constats.md` et ne seront corrigés qu'après la refonte. Les évolutions E1–E9 de `besoin.md` ne sont pas couvertes ici : chacune aura ses propres tests au moment de sa réalisation.*

## 1. Le jeu d'essai

`tests/reference/construire_reference.py` construit `tests/reference/projet_essai/` **au format réel des projets** : `.nox/project.json`, la base, les dossiers, les documents. Il fait ensuite produire par l'application actuelle les résultats rangés dans `tests/reference/attendu/` :

| Fichier | Contenu |
|---|---|
| `tableau_de_suivi.json` | une ligne par article × livrable, avec sa complétion, et les trois indicateurs |
| `exports.json` | pour chaque export Excel : l'onglet, puis la valeur de chaque cellule et la cible de son lien (racine du projet remplacée par `<PROJET>`) |
| `arborescence.json` | les dossiers et fichiers du projet après l'export |

Projet : affaire `AFF-ESSAI`, dossier `N999`, livrables CE, CECC et DPE.

| Article | Ce qu'il illustre | Règles |
|---|---|---|
| ACME / REF-001 | CE : 3 exigences applicables, 2 couvertes → 67 %. Une 2e ligne en doublon (n° de commande CMD-1B) | R3, R15, R17 |
| ACME / REF-002 | CE : Machine couverte par un document normal et une estimation (½). Basse tension notée N/A puis repassée Applicable sans document → 25 % | R15, R17, R18, R25 |
| BETA / REF-010 | Document RoHS déposé depuis le DPE, code écrit avec son libellé, rangé dans DPE et CE (deux copies). DPE 50 %, CE 20 % (le reste « non défini »). CECC : Validé puis Relancé → 0 % | R14, R16, R17, R19 |
| DELTA / REF-030 | DPE : document en base dont le fichier a disparu → 100 %, nom affiché sans lien | R17, R25 |
| EPS / REF-040 | CE entièrement N/A → 100 %. CECC : ancienne fiche au statut « Estimation » → 0 % | R17, R19 |
| GAMMA / REF-020 | CECC : Relancé puis Validé → 100 %. Fiche complète reprise dans l'export | R19, R25 bis |

## 2. Résultats attendus sur le jeu d'essai

### Tableau de suivi

| Article | CE | CECC | DPE |
|---|---|---|---|
| ACME / REF-001 | 67 % | 0 % | 0 % |
| ACME / REF-002 | 25 % | 0 % | 0 % |
| BETA / REF-010 | 20 % | 0 % | 50 % |
| DELTA / REF-030 | 0 % | 0 % | 100 % |
| EPS / REF-040 | 100 % | 0 % | 0 % |
| GAMMA / REF-020 | 0 % | 100 % | 0 % |
| **Indicateurs** | **35 %** | **17 %** | **25 %** |

ACME / REF-001 n'apparaît qu'une fois, avec le n° de commande **CMD-1** (première ligne gardée).

### Exports Excel (extraits ; la totalité est dans `exports.json`)

- Titre `BASE DE DONNEES <type> - AFF-ESSAI`, onglet `BDD <type> AFF-ESSAI` (R25 ter).
- Une ligne par article à partir de la ligne 5, dans l'ordre de la liste du projet.
- ACME / REF-001 : colonne F = **CMD-1B** (voir le constat C6). CE : H et L sont des liens vers `CE_ACME_REF-001.pdf`, I et M contiennent « N/A », J et K sont vides.
- ACME / REF-002, CE : H contient un lien vers le document le **plus récent**, `CE_ACME_REF-002_estimation.pdf`. I est vide (exigence repassée Applicable). J à M contiennent « N/A ».
- BETA / REF-010 : CE J et K contiennent le même lien RoHS. DPE H contient un lien vers la copie rangée dans le **dossier CE** (C8). La colonne D des exports CE et DPE contient le MPN de la fiche CECC, `MPN-BETA` (R25 quater).
- DELTA / REF-030, DPE : K contient `DPE_DELTA_REF-030.pdf` **sans lien**.
- EPS / REF-040, CECC : I contient « Estimation » (lu depuis l'ancienne clé de la fiche).
- GAMMA / REF-020, CECC : D et H contiennent `MPN-GAMMA`, K contient « Déclaration GAMMA » avec un lien vers la **dernière** fiche, suivie des colonnes L à R.
- Bas de tableau : formules (R26), dont celles du CECC, qui comptent Validé / Relancé / Non conforme / Estimation.

## 3. Scénarios d'action

Ils complètent le jeu d'essai pour les actions. Chacun se joue **sur une copie** de `projet_essai`. Le résultat attendu est observable à l'écran, sur le disque ou dans l'export.

### Projet

| # | Situation et action | Résultat attendu |
|---|---|---|
| S1 | Créer un projet sans n° d'affaire, sans emplacement, sans n° de dossier, avec une date « 2026-10-28 », ou sans livrable | Refus, avec le message correspondant : « Le Numéro de l'affaire est obligatoire. », « L'emplacement est obligatoire. », « Le numéro de dossier est obligatoire. », « La date doit être au format JJ/MM/AAAA (ex. 24/04/2026). », « Sélectionnez au moins un livrable (CE, CECC ou DPE). » (R1) |
| S2 | Créer un projet sans article, avec une ligne sans référence, ou avec 1 001 articles | Refus : « Ajoutez au moins une ligne avec un fournisseur et un N° de référence. », « La ligne N est incomplète… », « …dépasse la limite autorisée de 1000. » (R2) |
| S3 | Créer le projet `n123`, CE et DPE, 2 articles | Dossiers `BDD CE N123/Documents/<F>/<R>/` et `BDD DPE N123/…`, fichiers `BDD_CE_N123.xlsx` et `BDD_DPE_N123.xlsx` vides, pas de dossier CECC (R5) |
| S4 | Import en masse : 3 fournisseurs, 2 références | Demande de confirmation « Le nombre de fournisseurs (3) et de références (2) ne correspondent pas. » (R4) |
| S5 | Import en masse avec une cellule vide au milieu d'une colonne et une ligne entièrement vide | Les colonnes restent alignées ; la ligne vide est ignorée (R4) |
| S6 | Retirer ACME / REF-002 du projet d'essai | Trois choix proposés : « Supprimer dossiers et données », « Conserver les dossiers », « Annuler » (R6) |

### Dépôt

| # | Situation et action | Résultat attendu |
|---|---|---|
| S7 | Déposer un fichier `.png` | Refusé par le sélecteur (seuls PDF, DOCX et XLSX sont proposés) (R7) |
| S8 | Sélectionner une ligne CE et une ligne DPE, puis Importer | Refus : « La sélection multiple doit contenir un seul type de justificatif. » (R8) |
| S9 | Import CE avec une exigence laissée « non défini » | Enregistrement refusé, message citant les exigences « Non défini(es) » (R10) |
| S10 | Import CE de DELTA / REF-030, toutes les exigences réglées, aucune cochée | Aucun fichier copié ; l'applicabilité est enregistrée et la complétion recalculée (R11) |
| S11 | Import CECC sans fournisseur doc, ou sans MPN | Refus : « Pour un justificatif CECC, renseignez au minimum Fournisseur Doc, Manufacturer Part Number et Nom : CECC. » (R12). Nom CECC laissé vide : accepté, il prend le nom du fichier (C7) |
| S12 | Ouvrir un import CECC pour GAMMA / REF-020 | Fiche pré-remplie avec la dernière fiche (statut Validé, MPN-GAMMA…) (R12) |
| S13 | Import CE de `rapport.pdf` pour ACME / REF-001, nom non modifié, deux fois | Fichiers `CE_ACME_REF-001 (1).pdf` puis `CE_ACME_REF-001 (2).pdf` (le premier nom est déjà pris) ; `rapport.pdf` reste en place (R13) |
| S14 | Même import avec le nom saisi « Rapport v1.2 » | Fichier `Rapport v1.2`, sans extension (R13, avant E3) |
| S15 | Import CE couvrant RoHS pour ACME / REF-002 | Une copie dans `BDD CE …` et une dans `BDD DPE …` ; RoHS couverte côté CE et côté DPE (R14) |

### Corrections

| # | Situation et action | Résultat attendu |
|---|---|---|
| S16 | Applicabilité seule sur une ligne CECC | Refus : « La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC… » |
| S17 | Retirer le justificatif de CEM pour ACME / REF-001 | CEM reste Applicable, sans document. Le fichier est conservé, car il couvre encore Machine. Complétion 33 % (R21) |
| S18 | Puis retirer celui de Machine | Le fichier `CE_ACME_REF-001.pdf` est supprimé du disque. Complétion 0 % (R21) |
| S19 | Retirer le justificatif RoHS de BETA / REF-010 | Retiré côté CE et côté DPE, le message le signale (R21) |
| S20 | Remplacer le justificatif de Machine pour ACME / REF-001 par un document couvrant Machine et CEM | L'ancien ne justifie plus ni Machine ni CEM, et il est supprimé (R22, avant E6) |
| S21 | Vider BETA / REF-010 pour le CE | La confirmation liste les fichiers du dossier CE et signale la copie RoHS de l'autre livrable. Après confirmation : plus rien côté CE ; côté DPE, RoHS reste justifiée (R23, avant E7) |

### Export et projets

| # | Situation et action | Résultat attendu |
|---|---|---|
| S22 | Exporter deux fois de suite | Le premier export est déplacé dans `BDD <type> N999/OLD/BDD_<type>_N999_V_<AAAA-MM-JJ_HHhMM>.xlsx` ; le message liste les fichiers créés et archivés (R27) |
| S23 | Exporter alors que `BDD_CE_N999.xlsx` est ouvert dans Excel | Aucun fichier écrit ni archivé ; message « Impossible d'archiver l'ancien export… fermez-le puis relancez l'export. » (R27) |
| S24 | Ouvrir 11 projets | Seuls les 10 derniers figurent dans les récents (R28) |
| S25 | Supprimer un projet : « Retirer des projets récents » | Le dossier est intact (R29) |
| S26 | Supprimer un projet : « Supprimer définitivement », puis confirmer | Le dossier entier est effacé (R29) |
| S27 | Ouvrir `projet_essai` | Toutes les valeurs de la section 2 sont retrouvées, sans ressaisie (R31) |

## 4. Mode d'emploi

- **Sur l'ancienne application** : `py tests/reference/construire_reference.py`, et après le gel `py tests/reference/construire_reference.py 00_ancien`. Les fichiers de `attendu/` doivent rester identiques. Les scénarios S1 à S26 se jouent à la main.
- **Sur la nouvelle application** : les tests automatiques ouvriront le même `projet_essai`, compareront leurs résultats à `attendu/`, et joueront S1 à S27. Leur forme exacte sera fixée avec les choix techniques (étape R6).
- **Fin de la refonte** : la suppression de `00_ancien/` n'est possible que si toute cette référence passe sur le nouveau code.
