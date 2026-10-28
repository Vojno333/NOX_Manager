# État du projet
- Application : NOX Manager
- Mode : reprise
- Suivi des travaux : interne
- Palier : P2 (application de bureau PySide6, hors catalogue — décision 0002)
- Version de la méthode : 1.0
- Étape en cours : R8 — Réaliser (prochaine tâche : 10)
- Dernière mise à jour : 2026-10-28

## Fait
- R1 Indexer l'existant — `docs/diagnostic/arborescence.md` (≈ 2 400 lignes sur 10 300 hors périmètre, règle du tri-état écrite en trois exemplaires)
- R2 Qualifier le besoin — palier P2 confirmé : données partagées entre collègues, aucun traitement de fond, 4 actes métier (projet, dépôt, correction, export), un seul métier, pas de cloisonnement (droits gérés par la DSI sur le partage).
- R3 Lister les fonctionnalités — `docs/besoin/besoin.md` (règles R1–R31 = existant à reproduire ; évolutions E1–E14 après la refonte ; aucun point ouvert) et `docs/besoin/donnees.md`, validés point par point. Un seul profil ; R30 documents sur le partage, consultables à l'explorateur, liens Excel vers eux.
- R4 Référence de comportement — `docs/diagnostic/comportement.md` (jeu d'essai de 6 articles + 27 scénarios S1–S27) et `tests/reference/` (`construire_reference.py`, résultats de l'appli actuelle dans `attendu/`, stables). Forme adaptée : fichiers produits et valeurs affichées. Ajout de R31 (ouvrir les projets existants). Défauts C6–C10, corrections validées en E10–E13.
- R5 Ancien gelé — tout l'existant dans `00_ancien/`. Référence relancée depuis `00_ancien/` : identique. Plus aucune modification n'y entre.
- R6 Gabarit et décisions — arbitrage tranché le 2026-10-28 par l'utilisateur : **option A, application de bureau** (`docs/diagnostic/arbitrage-application-bureau.md`). Gabarit web transposé (validé) : `01_application/app/` en couches `ui → services → dataaccess → models` + `core/`, `uv run dev|test|lint|couches|build`, `AGENTS.md` réécrit pour le bureau, `manifest.json`, `config.json`, `pyproject.toml`, `README.md`, `.gitignore`, `.gitattributes`, `CLAUDE.md` → `@AGENTS.md` (ancien contenu conservé dans `docs/diagnostic/claude-ancien.md`). Décisions 0001 (palier, reprise à l'identique), 0002 (bureau hors catalogue), 0003 (données au format actuel sur le partage). E14 ajoutée (protection contre les enregistrements simultanés). Socle vérifié : tests, couches et lint au vert, référence inchangée.

- R7 Liste des tâches — `docs/travaux.md` (validée le 2026-10-28) : 23 tâches de reconstruction en 10 vagues (dernière : supprimer `00_ancien/`), puis 15 tâches d'évolution (E1 en deux temps) en 6 vagues. Toutes les règles R1–R31 et E1–E14 couvertes.

- R8 en cours — tâche 1 (ressources et référentiels) faite : `ressources/`, `core/config.ressource()`, `models/referentiel.py`.
- Tâche 2 (thème et géométrie) faite : `ui/theme.py` (feuille de style identique à l'ancienne), `ui/geometrie.py`.
- Tâche 3 (contrôles automatiques) faite : `.github/workflows/controles.yml` (Windows, Python 3.14 : mise en forme, lint, tests, couches). Vague 1 terminée.

## Reste à faire
- R8 Réaliser, une tâche à la fois : vague 2 (tâches 4, 5, 6, 7)

## Angles morts signalés en R7
- E1 suppose un changement du format des données (identifiant de ligne) : décision à écrire avant la tâche 37.
- E14 : modalité du verrou à préciser avec l'utilisateur avant la tâche 24.
- Tâche 22 (recette) : demande l'utilisateur et une copie d'un vrai projet du partage.

## En attente d'arbitrage
- aucune

## À ne pas oublier
- Commits autorisés le 2026-10-28. Étiquette `v1-avant-refonte` posée sur d7f13be, reprise commitée sur `develop` (`uv.lock` versionné). Chaque tâche est fusionnée localement dans `develop` (choix de l'utilisateur) ; rien n'est poussé sur GitHub.
- Liste des pays (menu CECC) : Algérie, Belgique et Chine y figurent deux fois. Reprise à l'identique ; à proposer en évolution.
- Faire remonter au responsable de la méthode le besoin d'une option « application de bureau » dans le catalogue (décision 0002).
- Contrôles automatiques : le workflow GitHub ne tournera qu'au premier envoi sur GitHub (rien n'est poussé pour l'instant). La référence y sera branchée par la tâche 16.
- Emplacement de diffusion de l'exécutable : à documenter.

## Pistes V2
- Construction et envoi des mails de relance fournisseurs. À requalifier : un envoi en masse sans personne devant l'écran ferait passer en P4.
