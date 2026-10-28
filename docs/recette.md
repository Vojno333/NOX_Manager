# Recette — NOX Manager (tâche 22)

*Ouverte le 2026-10-28. On joue les scénarios de `docs/diagnostic/comportement.md` sur l'exécutable `dist/NOX_Manager/NOX_Manager.exe`, jamais sur un projet en service : uniquement sur des copies.*

**Copies utilisées**
- Projet d'essai : `C:\Users\vojnovic\Desktop\Recette NOX\projet_essai` (dossier N999, affaire AFF-ESSAI).
- Vrai projet du partage : confidentiel ; comparé par l'utilisateur sur son poste avec `tests/reference/comparer_projet.py` (seul le verdict est affiché).

Résultat : ✅ conforme à la main · 🤖 couvert par les tests automatiques (`uv run test`, à travers les services et souvent les écrans réels) · ❌ écart · — non joué.

*Recette allégée, décidée avec l'utilisateur le 2026-10-28 : S1 à S10 et S27 joués à la main ; S11 à S26 couverts par les tests automatiques ; la recette manuelle se limite aux 6 vérifications de la section 7, qui portent sur ce que les tests ne voient pas (souris, explorateur, Excel, vrai projet).*

## 1. Ouvrir le projet d'essai (S27)

| # | Action | Attendu | Résultat | Remarque |
|---|---|---|---|---|
| S27 | Accueil → Ouvrir un projet → `Recette NOX\projet_essai` | Tableau de suivi : CE 35 %, CECC 17 %, DPE 25 % ; ACME / REF-001 CE 67 %, ACME / REF-002 CE 25 %, BETA / REF-010 CE 20 % et DPE 50 %, DELTA / REF-030 DPE 100 %, EPS / REF-040 CE 100 %, GAMMA / REF-020 CECC 100 % | ✅ | Joué le 2026-10-28 sur l'exécutable |

## 2. Projet

| # | Action | Attendu | Résultat | Remarque |
|---|---|---|---|---|
| S1 | Nouveau projet : laisser vide le n° d'affaire, puis l'emplacement, puis le n° de dossier ; date « 2026-10-28 » ; aucun livrable | Refus avec le message correspondant à chaque cas | ✅ | Les 5 messages conformes |
| S2 | Aucun article ; une ligne sans référence | « Ajoutez au moins une ligne… », « La ligne N est incomplète… » | ✅ | Limite de 1 000 couverte par les tests automatiques |
| S3 | Créer le projet `n123` dans `Recette NOX\n123`, CE et DPE, 2 articles | Dossiers `BDD CE N123/Documents/<F>/<R>/` et `BDD DPE N123/…`, fichiers `BDD_CE_N123.xlsx` et `BDD_DPE_N123.xlsx` vides, pas de dossier CECC | ✅ | |
| S4 | Import en masse : 3 fournisseurs, 2 références | Question « Le nombre de fournisseurs (3) et de références (2) ne correspondent pas. » | ✅ | |
| S5 | Import en masse avec une cellule vide au milieu d'une colonne et une ligne entièrement vide | Colonnes alignées, ligne vide ignorée | ✅ | |
| S6 | Paramétrage du projet d'essai : retirer ACME / REF-002, enregistrer | Trois choix : « Supprimer dossiers et données », « Conserver les dossiers », « Annuler l'enregistrement » | ✅ | |

## 3. Dépôt

| # | Action | Attendu | Résultat | Remarque |
|---|---|---|---|---|
| S7 | Importer : le sélecteur de fichier ; puis glisser un `.png` | Seuls PDF, DOCX, XLSX proposés ; le `.png` glissé est refusé à l'enregistrement (écart voulu, voir `.owlia/etat.md`) | ✅ | Liste des formats élargie par E2 (tâche 27) |
| S8 | Sélectionner une ligne CE et une ligne DPE, puis Importer | « La sélection multiple doit contenir un seul type de justificatif. » | ✅ | |
| S9 | Import CE avec une exigence laissée « Non défini » et un document | Refus citant les exigences « Non défini(es) » | ✅ | |
| S10 | DELTA / REF-030 CE : régler toutes les exigences, n'en cocher aucune, sans fichier | Aucun fichier copié, applicabilité enregistrée, complétion recalculée | ✅ | DELTA / REF-030 CE à 100 % |
| S11 | Import CECC sans fournisseur doc ou sans MPN ; puis avec le nom CECC vide | Refus ; puis accepté, le nom prend celui du fichier | 🤖 | `test_depot::test_s11_r12_fiche_cecc` |
| S12 | Import CECC pour GAMMA / REF-020 | Fiche pré-remplie (Validé, MPN-GAMMA…) | 🤖 | `test_depot::test_s12…, test_ui_dialogue_depot::test_s12…` |
| S13 | Import CE de `rapport.pdf` pour ACME / REF-001, nom non modifié, deux fois | `CE_ACME_REF-001 (1).pdf` puis `(2).pdf` ; l'original reste en place | 🤖 | `test_depot::test_s13…, test_ui_dialogue_depot::test_s13…` |
| S14 | Même import avec le nom « Rapport v1.2 » | Fichier `Rapport v1.2`, sans extension | 🤖 | `test_depot::test_s14…` |
| S15 | Import CE couvrant RoHS pour ACME / REF-002 | Une copie dans `BDD CE …` et une dans `BDD DPE …` ; RoHS couverte des deux côtés | 🤖 | `test_depot::test_s15…` |
| S16 | Applicabilité sur une ligne CECC | « La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC… » | 🤖 | `test_depot::test_s8_s16_selection` |

## 4. Corrections (panneau de détail, clic droit sur un document)

| # | Action | Attendu | Résultat | Remarque |
|---|---|---|---|---|
| S17 | ACME / REF-001 CE : supprimer le justificatif de 2014/30/UE | CEM reste Applicable sans document, fichier conservé, 33 % | 🤖 | `test_corrections::test_s17_s18…, test_ui_panneau_detail::test_s17…` |
| S18 | Puis celui de 2006/42/UE | `CE_ACME_REF-001.pdf` supprimé du disque, 0 % | 🤖 | `test_corrections::test_s17_s18…` |
| S19 | BETA / REF-010 CE : supprimer le justificatif RoHS | Retiré côté CE et côté DPE ; le message le signale | 🤖 | `test_corrections::test_s19…` |
| S20 | ACME / REF-001 : remplacer le justificatif de Machine par un document couvrant Machine et CEM | L'ancien ne justifie plus ni Machine ni CEM et il est supprimé | 🤖 | `test_corrections::test_s20…` |
| S21 | BETA / REF-010 CE : Supprimer la référence | Confirmation listant les fichiers du dossier CE et signalant la copie RoHS ; après : plus rien côté CE, RoHS toujours justifiée côté DPE | 🤖 | `test_corrections::test_s21…, test_ui_panneau_detail::test_s21…` |

## 5. Export et projets

| # | Action | Attendu | Résultat | Remarque |
|---|---|---|---|---|
| S22 | Exporter deux fois de suite | Le premier export part dans `BDD <type> N999/OLD/BDD_<type>_N999_V_<date>.xlsx` ; le message liste créés et archivés | 🤖 | `test_export::test_s22…` |
| S23 | Exporter avec `BDD_CE_N999.xlsx` ouvert dans Excel | Rien n'est écrit ; « Impossible d'archiver l'ancien export… fermez-le puis relancez l'export. » | 🤖 | `test_export::test_s23… (verrou Windows)` |
| S24 | Ouvrir 11 projets | Seuls les 10 derniers dans les récents | 🤖 | `test_etat_utilisateur::test_r28…, test_ui_accueil::test_s24…` |
| S25 | Supprimer un projet → « Retirer des projets récents » | Dossier intact | 🤖 | `test_projets::test_s25_s26…` |
| S26 | Supprimer un projet → « Supprimer définitivement », confirmer | Dossier entier effacé (à jouer sur `Recette NOX\n123`) | 🤖 | `test_projets::test_s25_s26…` |

## 6. Vrai projet du partage (copie)

| Vérification | Attendu | Résultat | Remarque |
|---|---|---|---|
| Ouvrir la copie avec la nouvelle application | Mêmes pourcentages et indicateurs qu'avec l'ancienne sur la même copie | | |
| Exporter avec chacune des deux applications | Mêmes contenus de cellules (hors liens, qui pointent vers la copie) | | |

## 7. Vérifications manuelles (recette allégée)

| # | Vérification | Attendu | Résultat | Remarque |
|---|---|---|---|---|
| M1 | S11 / S13 à la souris : dépôt CE par glisser-déposer, dépôt CECC par Parcourir | Fichiers rangés et nommés comme S11 / S13, messages « Import terminé » | ✅ | |
| M2 | S15 : dépôt CE couvrant RoHS, vérifier dans l'explorateur | Une copie dans `BDD CE …` et une dans `BDD DPE …` | ✅ | Copie DPE retirée ensuite par une manipulation de l'utilisateur ; dépôt rejoué : deux copies |
| M3 | S17 à S21 au clic droit : Ouvrir un document, Supprimer un justificatif, puis « Supprimer la référence » | Document ouvert dans son application ; suppressions comme S17 / S21 | ❌ → E7 | Après « Supprimer la référence » en CE, la copie RoHS du DPE reste et BETA / REF-010 CE reste à 20 %. Identique à l'ancienne application ; l'utilisateur attend que le vidage s'applique aux deux livrables (dossier et affichage) : c'est E7 (tâche 31) |
| M4 | S22 : exporter deux fois, ouvrir l'Excel produit | Ancien export dans `OLD/` ; dans Excel : liens cliquables, N/A, formules du pied de tableau | ✅ | |
| M5 | S23 : exporter avec l'Excel ouvert dans Excel | Message « fermez-le puis relancez l'export », rien d'écrit | ✅ | |
| M6 | Vrai projet : `comparer_projet.py` | « VERDICT : CONFORME » | ✅ | Joué par l'utilisateur sur son poste ; aucun contenu transmis |

## Bilan (2026-10-28)

S1 à S10 et S27 conformes à la main ; S11 à S26 couverts par les tests automatiques ; M1, M2, M4, M5, M6 conformes. Un seul écart, M3, qui reproduit fidèlement l'ancienne application et sera corrigé par E7. La nouvelle application refait ce que fait l'ancienne, y compris sur un vrai projet.

## Écarts constatés

- **M3 / S21** : vider un article dans un livrable laisse la copie RoHS de l'autre livrable, qui continue de compter (BETA / REF-010 CE à 20 %). Comportement de l'ancienne application, refusé par l'utilisateur : corrigé par **E7** (tâche 31).
