# Livraison — NOX Manager

*Établi le 2026-10-28 (tâche 21). Reprend `Documentation/02 - Développer/Build et livraison.md`, adapté au nouveau code.*

## Fabriquer l'exécutable

```powershell
uv sync --extra dev
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
uv run build
```

Résultat : `dist/NOX_Manager/NOX_Manager.exe` (onedir, fenêtré, icône `LOGO_Nox.ico`, écran de démarrage `flash.png`), environ 120 Mo. La recette du `NOX_Manager.spec` (versionné à la racine) :

| Élément | Dans `dist/NOX_Manager/_internal/` |
|---|---|
| `ressources/` : les 3 `Template_BDD_*_N0X.xlsx`, `LOGO_Nox.ico`, `flash.png`, `eu_icon.svg`, `dpe_icon.svg` | `ressources/` |
| `config.json` | racine |
| code de l'application | compilé dans l'archive (plus de sources `.py` en clair, contrairement à l'ancienne application) |

Toute nouvelle ressource lue à l'exécution va dans `ressources/`, et `app.core.config.ressource()` la retrouve en développement comme dans l'exécutable : rien à ajouter au `.spec`.

## Liste de vérification

1. `git status` propre ; contrôles au vert : `uv run lint`, `uv run test` (référence comprise), `uv run couches`.
2. Supprimer `build/` et `dist/`, puis `uv run build`.
3. Vérifier que `_internal/ressources/` contient les 7 fichiers et que `_internal/config.json` est présent.
4. Lancer `NOX_Manager.exe` **depuis un autre dossier que le dépôt**, idéalement sur un autre poste, sans Python :
   - écran de démarrage, puis accueil, avec l'icône correcte dans la barre des tâches ;
   - créer un projet, importer un document, **exporter** (si un modèle manque, c'est ce test qui échoue) ;
   - rouvrir le projet depuis l'accueil ;
   - ouvrir un projet existant du partage (R31).
5. Zipper `dist/NOX_Manager/` sous `NOX_Manager_<version>.zip` et le déposer à l'endroit de diffusion (**à renseigner**).
6. Le référent technique pose l'étiquette de version (`git tag v<version>`).

## Réglages (`config.json`, à côté de l'exécutable dans `_internal/`)

| Réglage | Valeur livrée | Rôle |
|---|---|---|
| `lignes_multiples` | `false` | E1, décision 0005. À passer à `true` **sur tous les postes en même temps**, une fois que plus aucun poste n'utilise l'ancienne application : un même article peut alors figurer sur plusieurs lignes. |
| `verrou_rafraichissement_minutes` | `2` | E14, décision 0004 : fréquence du signe de vie d'un projet ouvert en modification. |
| `verrou_peremption_minutes` | `15` | E14 : au-delà, un verrou sans signe de vie (poste planté) est abandonné. |

Pendant la diffusion poste par poste, l'ancienne application ne respecte pas le verrou de modification (E14) : prévenir les collègues de ne pas modifier un même projet à deux tant que tous les postes ne sont pas passés.

## Mise à jour chez l'utilisateur

Remplacer le dossier `NOX_Manager` complet. Les données (`~/.nox_manager/` et les dossiers des projets sur le partage) sont hors du dossier d'installation : elles ne sont pas touchées. Le format des données est inchangé (décision 0003) : l'ancienne et la nouvelle application lisent les mêmes projets.

## Points d'attention

- **UPX** activé : ignoré s'il n'est pas installé. En cas de faux positif d'un antivirus, passer `upx=False` dans le `.spec`.
- **Pas de signature de code** : SmartScreen peut alerter au premier lancement sur un autre poste.
- **Version** : le numéro affiché à l'accueil est celui de `app/ui/accueil.py` (`VERSION`), repris de l'ancienne application (1.1.0).
