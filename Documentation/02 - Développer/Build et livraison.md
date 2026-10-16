---
tags: [nox, build, release]
maj: 2026-09-21
---

↑ [[00 - Index]]

# Build et livraison

## Résultat attendu

`dist/NOX_Manager/` : dossier autonome (~169 Mo au dernier build du 2026-07-21), point d'entrée `NOX_Manager.exe` (~7 Mo), dépendances dans `_internal/`. Mode **onedir**, **fenêtré** (pas de console), icône `LOGO_Nox.ico`, splash `flash.png`. Contexte : [[Décisions (ADR)#ADR-006 : Build PyInstaller onedir fenêtré avec splash]].

## Procédure recommandée

Depuis la racine du projet, dans PowerShell :

```powershell
& "C:\Users\vojnovic\AppData\Roaming\Python\Python314\Scripts\pyinstaller.exe" NOX_Manager.spec
```

Le `.spec` est plus complet que la commande de `Compilation de l'exe.txt` : il embarque en plus `LOGO_Nox.ico` dans les données. Si tu n'as que la commande CLI (pas de `.spec`), utilise-la avec **l'ajout de** `--add-data ".\LOGO_Nox.ico;."`, sinon l'icône de la fenêtre manquera à l'exécution.

Le chemin de `pyinstaller.exe` ci-dessus est celui du poste d'origine (Python 3.14, installation utilisateur) : adapter ou utiliser `python -m PyInstaller`.

## Ce que le build doit contenir

| Élément | Où dans `dist/NOX_Manager/_internal/` | Vérifié au 2026-07-21 |
|---|---|---|
| `Template_BDD_CE_N0X.xlsx`, `…CECC…`, `…DPE…` | racine | ✅ |
| `LOGO_Nox.ico` | racine | ✅ |
| `wikidocs_qt/` (dont `dpe_icon.svg`, `eu_icon.svg`) | `wikidocs_qt/` | ✅ |
| `PySide6/`, `docx/` | dossiers | ✅ |
| `openpyxl` | dans l'archive PYZ (pur Python) | non vérifié directement, l'export doit être testé |

**Tout nouveau fichier lu à l'exécution** (template, icône, image) doit être ajouté à `datas` du `.spec` (et à la commande CLI si elle subsiste).

Résolution des chemins à respecter dans le code : voir [[Architecture#Chemins de ressources (dev vs build)]].

## Points d'attention connus

- **Sources en clair** : `datas=[('wikidocs_qt','wikidocs_qt')]` copie le dossier `wikidocs_qt/` tel quel dans `_internal/`, donc **les fichiers `.py` sont livrés lisibles**, doublonnant le code compilé. Acceptable pour un outil interne ; à savoir si la diffusion s'élargit. Cela rend aussi les fichiers non suivis (par ex. `new_project_dialog2.py`) présents dans la livraison.
- **`*.spec` est dans `.gitignore`** : le fichier de build n'est pas versionné (NOX-002 dans [[Backlog]]).
- **Pas de `requirements.txt`** : le build dépend de ce qui est installé sur le poste ([[Environnement de dev]]).
- **UPX activé** (`upx=True`) : sans UPX installé, PyInstaller l'ignore. Des antivirus peuvent signaler des exécutables compressés UPX : en cas de faux positif, passer `upx=False`.
- **Pas de signature de code** (`codesign_identity=None`) : SmartScreen peut alerter au premier lancement sur un autre poste.
- **`hiddenimports=[]`** : rien n'est forcé. Si une future dépendance est importée dynamiquement, l'ajouter ici. Les warnings sont dans `build/NOX_Manager/warn-NOX_Manager.txt`.
- **`build/` et `dist/`** ne sont pas versionnés : les supprimer avant un build « propre » (`Remove-Item -Recurse -Force build, dist`).
- **Version** : aucun numéro de version n'est intégré à l'exécutable ni affiché (NOX-004 dans [[Backlog]]).

## Checklist de release

1. `git status` propre, travail commité ; mettre à jour [[Changelog]] (version et date).
2. Passer le [[Plan de test]] en mode source (`python qt_main.py`).
3. Supprimer `build/` et `dist/`, lancer le build.
4. Vérifier que `dist/NOX_Manager/_internal/` contient les éléments du tableau ci-dessus.
5. Lancer `NOX_Manager.exe` **depuis un autre dossier que le projet** (idéalement un autre poste ou un profil sans Python) :
   - splash puis accueil, icône correcte ;
   - créer un projet, importer un document, **exporter** (c'est le test qui échoue si un template manque) ;
   - rouvrir le projet depuis l'accueil.
6. Zipper `dist/NOX_Manager/` sous `NOX_Manager_<version>.zip` et le déposer à l'endroit de diffusion convenu (à documenter ici : _emplacement à renseigner_).
7. Étiqueter le commit : `git tag v<version>`.
8. Mettre à jour [[Journal de dev]].

## Mise à jour chez l'utilisateur

Remplacer le dossier `NOX_Manager` complet. Les données utilisateur (`~/.nox_manager/` et dossiers de projets) sont hors du dossier d'installation et ne sont pas touchées. Les migrations SQLite s'appliquent à l'ouverture d'un projet ([[Modèle de données#Migrations]]) : **une version plus récente peut rendre un projet illisible par une version plus ancienne** ; prévenir les utilisateurs de mettre à jour ensemble s'ils partagent des projets.
