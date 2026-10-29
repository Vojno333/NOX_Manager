# 0002 — Application de bureau PySide6, livrée en exécutable, hors catalogue

Statut : Accepté (arbitrage, option A) · Date : 2026-10-28

## Pourquoi
Le catalogue impose en P2 une application web (FastAPI, Jinja2 / HTMX, un conteneur). Avec un serveur, le compte du serveur lirait tous les dossiers de projets : chaque utilisateur verrait tous les projets, au mépris des droits posés par la DSI sur le partage, et reprendre ces droits ferait passer en P3. Le métier exige un exécutable installé sur les postes, toutes les données restant sur le partage. Détail : `docs/diagnostic/arbitrage-application-bureau.md`.

## Ce qui est décidé
- Application de bureau **PySide6**, fabriquée par **PyInstaller** en dossier autonome (`onedir`, fenêtré, avec écran de démarrage), comme aujourd'hui.
- La méthode est **transposée** :
  - `01_application/app/` en couches `ui → services → dataaccess → models`, plus `core/` transverse ;
  - outillage `uv`, `ruff`, `pytest`, PyInstaller ;
  - commandes `uv run dev | test | lint | couches | build`.
- Le fichier de fabrication `NOX_Manager.spec` est versionné. C'est l'unique procédure de fabrication.

## Ce que cela implique
- Obligatoire : `services/` ne connaît ni Qt ni la base ; seul `dataaccess/` lit ou écrit des fichiers, la base ou les Excel ; `ui/` ne contient aucune règle métier.
- Obligatoire : toute ressource lue à l'exécution (modèle Excel, icône) est déclarée dans le `.spec`.
- Plus possible : le serveur, le contrat d'interface `docs/api/`, le conteneur et la connexion par le proxy du gabarit, qui n'ont pas d'objet ici.
- Les droits restent ceux du partage : l'application n'écrit aucun contrôle d'accès.
- Hors catalogue : le catalogue de la méthode doit évoluer pour couvrir ce cas. Remonté par l'arbitre au responsable de la méthode.
- Livraison : un zip du dossier fabriqué. L'emplacement de diffusion reste à documenter.
