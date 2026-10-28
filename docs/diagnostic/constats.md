# Constats sur l'existant

*Constatés, non corrigés. Chacun deviendra une tâche après la refonte s'il n'est pas résolu par elle. C6 sera réglé par E1, C7 à C10 par E10 à E13 (`docs/besoin/besoin.md`).*

| # | Constat | Conséquence |
|---|---|---|
| C1 | Base SQLite (`.nox/nox_metadata.db`) ouverte directement depuis chaque poste sur le partage réseau | Deux enregistrements simultanés peuvent corrompre la base ; accès lents (~40 ms par accès disque) |
| C2 | Règle du tri-état et correspondance des codes d'exigence écrites trois fois (`document_rules.py`, `export_templates.py`, `project_dashboard_window.py`) | Risque que le tableau de suivi et l'export divergent |
| C3 | `utils.py` importe `python-docx` au démarrage pour une fonction jamais appelée | Dépendance inutile |
| C4 | `project_settings_dialog.py` (réglage des BDD activées) inaccessible depuis l'interface | Abandonné (P4 tranché) : hors périmètre de la refonte |
| C6 | **Doublon d'article : tableau de suivi et export divergent.** Le tableau garde la **première** ligne d'un couple fournisseur / référence, l'export reprend libellé, MNP et n° de commande de la **dernière** (jeu d'essai : CMD-1 à l'écran, CMD-1B dans l'Excel) | Deux informations différentes pour le même article. Disparaît avec E1 |
| C7 | **Nom CECC pas vraiment obligatoire** : laissé vide, il prend le nom du fichier avant le contrôle | R12 dit « obligatoire », l'écran ne bloque jamais |
| C8 | **Lien RoHS vers la copie la plus récente** : un document RoHS est copié dans les dossiers CE et DPE, mais les deux exports pointent vers la dernière copie (celle du CE) | L'Excel DPE renvoie vers un fichier rangé dans le dossier CE |
| C9 | **Document en base sans fichier** : il compte dans la complétion, et l'export affiche son nom sans lien | Un pourcentage peut être à 100 % alors que le fichier a disparu |
| C10 | **Liens absolus** dans les exports (chemin complet du fichier) | Si le dossier du projet est déplacé ou renommé, les liens des anciens exports sont cassés |
| C5 | `Documentation/` en retard sur le code : calcul de complétion CECC (décrit comme « Validé / statuts comptés », en réalité « dernier statut = Validé ») et suppression d'une référence (décrite comme gardant les fichiers, en réalité les supprime pour la BDD concernée) | Ne pas s'y fier sans vérifier le code ; `docs/besoin/` fait désormais foi |
