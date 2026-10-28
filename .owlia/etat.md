# État du projet
- Application : NOX Manager
- Mode : reprise
- Suivi des travaux : interne
- Palier : P2 (application de bureau PySide6, hors catalogue — décision 0002)
- Version de la méthode : 1.0
- Étape en cours : R8 — Réaliser (évolutions ; en attente : tâches 24, 32, 37, 38)
- Dernière mise à jour : 2026-10-28

## Fait
- R1 Indexer l'existant — `docs/diagnostic/arborescence.md` (≈ 2 400 lignes sur 10 300 hors périmètre, règle du tri-état écrite en trois exemplaires)
- R2 Qualifier le besoin — palier P2 confirmé : données partagées entre collègues, aucun traitement de fond, 4 actes métier (projet, dépôt, correction, export), un seul métier, pas de cloisonnement (droits gérés par la DSI sur le partage).
- R3 Lister les fonctionnalités — `docs/besoin/besoin.md` (règles R1–R31 = existant à reproduire ; évolutions E1–E14 après la refonte ; aucun point ouvert) et `docs/besoin/donnees.md`, validés point par point. Un seul profil ; R30 documents sur le partage, consultables à l'explorateur, liens Excel vers eux.
- R4 Référence de comportement — `docs/diagnostic/comportement.md` (jeu d'essai de 6 articles + 27 scénarios S1–S27) et `tests/reference/` (`construire_reference.py`, résultats de l'appli actuelle dans `attendu/`, stables). Forme adaptée : fichiers produits et valeurs affichées. Ajout de R31 (ouvrir les projets existants). Défauts C6–C10, corrections validées en E10–E13.
- R5 Ancien gelé — tout l'existant dans `00_ancien/`. Référence relancée depuis `00_ancien/` : identique. Plus aucune modification n'y entre.
- R6 Gabarit et décisions — arbitrage tranché le 2026-10-28 par l'utilisateur : **option A, application de bureau** (`docs/diagnostic/arbitrage-application-bureau.md`). Gabarit web transposé (validé) : `01_application/app/` en couches `ui → services → dataaccess → models` + `core/`, `uv run dev|test|lint|couches|build`, `AGENTS.md` réécrit pour le bureau, `manifest.json`, `config.json`, `pyproject.toml`, `README.md`, `.gitignore`, `.gitattributes`, `CLAUDE.md` → `@AGENTS.md` (ancien contenu conservé dans `docs/diagnostic/claude-ancien.md`). Décisions 0001 (palier, reprise à l'identique), 0002 (bureau hors catalogue), 0003 (données au format actuel sur le partage). E14 ajoutée (protection contre les enregistrements simultanés). Socle vérifié : tests, couches et lint au vert, référence inchangée.

- R7 Liste des tâches — `docs/travaux.md` (validée le 2026-10-28) : 23 tâches de reconstruction en 10 vagues (dernière : supprimer `00_ancien/`), puis 15 tâches d'évolution (E1 en deux temps) en 6 vagues. Toutes les règles R1–R31 et E1–E14 couvertes.

- R8 en cours — vagues 1 à 7 faites (tâches 1 à 21), chacune sur sa branche, fusionnée dans `develop` :
  - socle (1–3) : ressources, référentiels, thème, géométrie, contrôles GitHub ;
  - données (4–7) : `project.json`, base SQLite, préférences, dossiers et fichiers ;
  - règles (8–13) : applicabilité, projets, complétion et indicateurs, export Excel, dépôt, corrections ;
  - écrans (14, 15, 17–20) : accueil, dialogue de projet, composants et dialogue de dépôt, tableau de suivi, panneau de détail ;
  - référence automatisée (16) : tableau, exports et arborescence identiques à `attendu/`, y compris sur une copie du projet écrit par l'ancienne application ;
  - assemblage et fabrication (21) : `main.py` relie les écrans, `NOX_Manager.spec` versionné, `uv run build` → `dist/NOX_Manager/` (≈ 120 Mo, démarre), `docs/livraison.md`.
  - 111 tests, lint et couches au vert.
- Tâche 22 (recette) faite le 2026-10-28 avec l'utilisateur, version allégée (`docs/recette.md`) : tout conforme, vrai projet compris (`tests/reference/comparer_projet.py`, joué par l'utilisateur, projet confidentiel). Un écart, M3 / S21, fidèle à l'ancienne application, refusé par l'utilisateur → E7 (gardée à sa place, après la tâche 23).
- Tâche 23 faite le 2026-10-28 (accord de l'utilisateur) : `00_ancien/` supprimé, ancien code conservé sous l'étiquette `v1-avant-refonte` ; `AGENTS.md`, `README.md` et les docstrings y renvoient. **Reconstruction terminée.**

- Évolutions faites le 2026-10-28 (une branche et un commit par tâche, référence `attendu/` mise à jour dans la tâche) : E5 (25), E8 (26), E2 (27), E6 (28), E9 (29), E3 (30), E7 (31, corrige l'écart M3 de la recette), E11 (33), E4 (34), E13 (35), E10 (36). 121 tests au vert.

## Reste à faire
- Tâche 24 — E14 (protection contre les enregistrements simultanés) : modalité à décider avec l'utilisateur.
- Tâche 32 — E12 (fichier disparu signalé) : dépend de la tâche 24.
- Tâches 37 et 38 — E1 (lignes multiples d'un même article) : décision sur le format des données à écrire d'abord.

## Écarts et constats relevés pendant la reconstruction (à valider en recette)
- **R7, fichier glissé-déposé** : l'ancienne application ne contrôlait le format que dans le sélecteur de fichier ; un fichier glissé passait sans contrôle. Le contrôle est maintenant fait aussi au dépôt (R7 et AGENTS §7).
- **Projet déplacé ou copié** : l'ancienne application travaillait dans le dossier inscrit dans `project.json` (`project_path`), même si le projet avait été ouvert depuis un autre dossier. La nouvelle travaille dans le dossier réellement ouvert (indispensable pour la référence sur une copie).
- **Ouvrir un dossier qui n'est pas un projet** : l'ancienne application y créait un dossier `.nox` vide ; la nouvelle ne crée rien.
- **Vider une référence** : une erreur de suppression sur la copie RoHS réduite est regroupée dans le message « Suppression incomplète » au lieu d'un message séparé.
- **Exécutable** : n'embarque plus les sources `.py` en clair ni `python-docx` (inutile, constat C3).
- Comportements repris à l'identique, candidats à une évolution : après un changement des livrables suivis dans le paramétrage, les onglets du tableau ne sont mis à jour qu'à la réouverture ; au premier affichage, le tableau est trié par fournisseur décroissant.

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
- Contrôles automatiques : le workflow GitHub ne tournera qu'au premier envoi sur GitHub (rien n'est poussé pour l'instant). La référence (projet reconstruit) y est jouée avec les tests.
- Emplacement de diffusion de l'exécutable : à documenter (`docs/livraison.md`, étape 5).

## Pistes V2
- Construction et envoi des mails de relance fournisseurs. À requalifier : un envoi en masse sans personne devant l'écran ferait passer en P4.
