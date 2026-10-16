---
tags: [nox, adr]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Décisions d'architecture (ADR)

Chaque entrée : contexte, décision, conséquences. Les ADR 001 à 008 ont été **reconstituées le 2026-09-21 à partir du code** : elles décrivent ce qui est en place, pas nécessairement les raisons initiales. Corrige le champ « Contexte » quand tu te souviens de la vraie raison. Statuts : `Acceptée`, `À valider`, `Remplacée par ADR-xxx`, `Proposée`.

Modèle pour une nouvelle décision : [[Modèle - ADR]].

---

## ADR-001 : Application de bureau PySide6, sans serveur
**Statut** : Acceptée (déduite du code)
**Contexte** : outil utilisé par des personnes sous Windows, données sous forme de dossiers et de documents.
**Décision** : application Qt (PySide6) monoposte, pas de serveur, pas de base centrale.
**Conséquences** : déploiement simple (un dossier), travail hors ligne. Mais pas de collaboration simultanée native ni de vue transverse entre projets.

## ADR-002 : Données du projet dans le dossier du projet (`.nox/`)
**Statut** : Acceptée (déduite du code)
**Décision** : `project.json` + `nox_metadata.db` dans `<projet>/.nox/` ; seul l'historique des projets récents est dans `~/.nox_manager/`.
**Conséquences** : un projet se copie/archive en bloc ; les `relative_path` restent valides après déplacement. Voir [[Modèle de données]]. Risque : sauvegarde partielle qui oublie `.nox/` (dossier caché).

## ADR-003 : Un événement par import (historique en base) plutôt qu'un état par exigence
**Statut** : Acceptée (déduite du code)
**Décision** : `uploaded_documents` reçoit une ligne à chaque import **et** à chaque enregistrement d'applicabilité ; l'état courant se déduit du dernier événement.
**Conséquences** : historique complet gratuit, pas de mise à jour destructive. Mais l'état n'est jamais stocké : chaque lecteur doit refaire la résolution, et deux lecteurs l'ont faite différemment ([[Bugs connus#BUG-002]]). → voir ADR-009.

## ADR-004 : SQLite pour les métadonnées, JSON pour la configuration
**Statut** : Acceptée (déduite du code)
**Décision** : JSON lisible pour `project.json` et l'état utilisateur ; SQLite (WAL) pour les documents. Les listes et dictionnaires sont sérialisés en colonnes `*_json`.
**Conséquences** : pas de requête SQL possible sur les exigences (tout est filtré en Python) ; acceptable à cette échelle. Migrations par `ALTER TABLE` tolérants. Voir [[Dette technique#DT-010]] pour WAL.

## ADR-005 : Export par remplissage de templates Excel existants
**Statut** : Acceptée (déduite du code)
**Décision** : les livrables sont les fichiers `Template_BDD_*_N0X.xlsx` (mise en forme fournie par le métier), remplis avec openpyxl, formules de synthèse conservées dans Excel.
**Conséquences** : rendu identique aux gabarits attendus ; mais le code dépend de positions fixes (ligne 5, colonnes H…S, pied à la ligne 235/236). **Modifier un template impose de modifier `export_templates.py`.** Les templates sont livrés avec l'exécutable.

## ADR-006 : Build PyInstaller onedir fenêtré avec splash
**Statut** : Acceptée (déduite de `NOX_Manager.spec`)
**Décision** : `--onedir --windowed`, splash `flash.png`, UPX activé. Voir [[Build et livraison]].
**Conséquences** : démarrage plus rapide qu'un onefile, mise à jour = remplacer le dossier. Pas de console : sans journal fichier, les erreurs sont invisibles ([[Dette technique#DT-004]]).

## ADR-007 : RoHS partagé entre CE et DPE
**Statut** : Acceptée (déduite du code)
**Décision** : un justificatif couvrant `2011/65/UE` est copié dans les deux BDD (si activées) et compte pour les deux.
**Conséquences** : pas de double saisie. Coût : deux copies physiques du fichier.

## ADR-008 : Applicabilité tri-état
**Statut** : Acceptée (commit `12f8997`, 2026-04-29)
**Décision** : N/A / Non défini / Applicable ; « Non défini » bloque l'import. CECC en est exclu.
**Conséquences** : force à trancher chaque exigence explicitement ; permet le calcul de complétion sur les seules exigences applicables. Voir [[Règles métier#Applicabilité tri-état]].

## ADR-009 : Extraire la logique de conformité hors de l'UI
**Statut** : Proposée · **Date** : 2026-09-21
**Contexte** : dashboard et export dupliquent la résolution du N/A, la correspondance des codes et (partiellement) le calcul de complétion ; ils ont divergé.
**Décision proposée** : un module `compliance.py` sans dépendance Qt, unique source de ces règles ; le dashboard et l'export l'appellent.
**Conséquences** : corrige [[Bugs connus#BUG-002]] à la racine, permet des tests unitaires (NOX-030 dans [[Backlog]]). Coût : refactoring du dashboard (~250 lignes concernées).

## ADR-010 : `CECC_FREE_FIELDS` comme unique source des clés CECC
**Statut** : Proposée · **Date** : 2026-09-21
**Contexte** : trois modules utilisent trois jeux de clés ([[Bugs connus#BUG-001]]).
**Décision proposée** : les clés de `document_rules.CECC_FREE_FIELDS` font foi ; l'import les génère depuis cette liste, le dashboard et l'export les lisent ; lecture rétro-compatible des anciennes clés de la base.
**Conséquences** : plus de dérive silencieuse. Nécessite de trancher les libellés et les statuts (NOX-011 dans [[Backlog]]).
