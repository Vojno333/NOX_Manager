# CLAUDE.md

## Rôle de l'application

**NOX Manager** est une application de bureau Windows (PySide6 / Qt) qui sert à constituer et suivre les dossiers de justificatifs de conformité d'un projet, par couple *fournisseur / référence* d'article.

Trois types de « BDD » (`JUSTIFICATION_TYPES = ("CE", "CECC", "DPE")`, définis dans [wikidocs_qt/document_rules.py](wikidocs_qt/document_rules.py)) :

| BDD | Contenu | Exigences |
|---|---|---|
| **CE** | Marquage CE | `CE_REQUIREMENTS` (Machine, RoHS, EMC, ESP…) |
| **DPE** | Exigences environnementales | `DPE_REQUIREMENTS` (RoHS, DEEE, REACh, POP…) |
| **CECC** | Contrôle export | `CECC_FREE_FIELDS` (champs libres : ECCN, licence, pays d'origine, code douanier…) et `CECC_STATUSES` |

Flux utilisateur : créer un projet (liste de références) → déposer des documents (PDF/DOCX/XLSX) et cocher l'applicabilité de chaque exigence (**tri-état** : applicable / non applicable / non renseigné) → suivre l'avancement dans le dashboard → **exporter** les fichiers Excel `Template_BDD_*_N0X.xlsx` remplis (liens hypertexte vers les documents).

L'interface et les libellés sont **en français**.

## Point d'entrée

[qt_main.py](qt_main.py) → `run()` : crée la `QApplication` (style Fusion, palette claire, feuille de style de [wikidocs_qt/theme.py](wikidocs_qt/theme.py)), charge `LOGO_Nox.ico` via `_base_dir()` (qui gère `sys._MEIPASS` en build PyInstaller), ferme le splash `pyi_splash` puis ouvre `HomeWindow` en plein écran.

```powershell
python qt_main.py
```

Pas de `requirements.txt` : dépendances à installer à la main — `PySide6`, `openpyxl`, `python-docx` (importé par [wikidocs_qt/utils.py](wikidocs_qt/utils.py), donc requis dès le lancement) et `pyinstaller` pour le build. Python 3.14 côté build (cf. chemin dans `Compilation de l'exe.txt`). Aucune suite de tests automatisée.

## Architecture (package `wikidocs_qt/`)

| Fichier | Rôle |
|---|---|
| `home_window.py` | `HomeWindow` : accueil, projets récents, ouverture/création de projet |
| `new_project_dialog.py` | `NewProjectDialog` : création/édition d'un projet (lignes fournisseur/référence/libellé/MNP/n° commande, import en masse) |
| `project_dashboard_window.py` | `ProjectDashboardWindow`, `MainTab`, `DetailPanel`, KPI, filtres : tableau de suivi du projet + lancement de l'export |
| `upload_document_dialog.py` | `UploadDocumentDialog` (pages `CEPage` / `DPEPage` / `CECCPage`, `ThreeStateToggle`, `DropZone`) : dépôt d'un justificatif et saisie des exigences |
| `project_settings_dialog.py` | Réglages d'un projet (BDD activées, etc.) |
| `filter_popup.py` | Popup de filtre des en-têtes du tableau |
| `project_manager.py` | `ProjectManager` : état applicatif + lecture/écriture de `project.json` |
| `metadata_db.py` | SQLite par projet : table `uploaded_documents` (migrations `ALTER TABLE` tolérantes) |
| `export_templates.py` | Remplissage des trois templates Excel avec `openpyxl` (copie de lignes/styles, mise en forme conditionnelle, formules de pied de tableau) |
| `project_structure.py` | Création de l'arborescence de dossiers (logique reprise d'une macro VBA) |
| `document_rules.py` | Constantes métier (types de BDD, exigences, statuts CECC) |
| `window_geometry.py` | `fit_and_center()` : dimensionne et centre toute fenêtre/dialogue sur le bon écran |
| `theme.py` | Feuille de style Qt globale |
| `utils.py` | Normalisation de texte, `human_size`, `fmt_dt`, recherche de mots dans un PDF |

### Persistance

- **Par projet**, dans `<dossier projet>/.nox/` : `project.json` (nom, n° de dossier, `rows`, `enabled_bdds`, `project_file_version` = 3) et `nox_metadata.db` (SQLite, WAL). Ancien format `.nox_project.json` encore lu en repli puis supprimé à la création.
- **Par utilisateur** : `~/.nox_manager/nox_state.json` (10 projets et emplacements récents, emplacement par défaut).
- Les documents déposés sont copiés (`shutil.copy2`) dans l'arborescence du projet ; `relative_path` en base est stocké **en séparateurs `/`, relatif au dossier projet**.
- Les colonnes `*_json` de `uploaded_documents` contiennent des listes/dicts JSON (`ensure_ascii=False`). Toute nouvelle colonne doit être ajoutée via la boucle de migration de `init_metadata_db`.

## Build PyInstaller

Sortie : dossier **onedir** `dist/NOX_Manager/NOX_Manager.exe` (fenêtré, sans console, icône `LOGO_Nox.ico`, splash `flash.png`, UPX activé).

Deux façons, décrites dans [Compilation de l'exe.txt](Compilation%20de%20l'exe.txt) et [NOX_Manager.spec](NOX_Manager.spec) :

```powershell
# Recommandé : via le .spec (embarque aussi LOGO_Nox.ico dans les données)
& "C:\Users\vojnovic\AppData\Roaming\Python\Python314\Scripts\pyinstaller.exe" NOX_Manager.spec

# Ou ligne de commande complète (cf. Compilation de l'exe.txt)
pyinstaller --onedir --windowed --name NOX_Manager --icon=LOGO_Nox.ico --splash flash.png `
  --add-data "wikidocs_qt;wikidocs_qt" `
  --add-data ".\Template_BDD_CE_N0X.xlsx;." --add-data ".\Template_BDD_CECC_N0X.xlsx;." --add-data ".\Template_BDD_DPE_N0X.xlsx;." `
  qt_main.py
```

Points d'attention :

- Les **trois `Template_BDD_*_N0X.xlsx`**, `wikidocs_qt/` (dont `dpe_icon.svg`, `eu_icon.svg`) et `LOGO_Nox.ico` doivent être dans `datas`. Tout nouvel asset (icône, template…) doit y être ajouté.
- La commande CLI de `Compilation de l'exe.txt` **n'ajoute pas** `LOGO_Nox.ico` en données : sans lui, l'icône de fenêtre est absente à l'exécution (le `.spec` l'inclut, lui).
- `export_templates.py` retrouve les templates via `Path(__file__).parent.parent` : ils doivent rester **à la racine des données** (`.`) à côté du dossier `wikidocs_qt`, en dev comme en build.
- `*.spec`, `build/` et `dist/` sont dans `.gitignore` : le `.spec` n'est donc pas versionné ; le sauvegarder ailleurs si besoin.
- Le splash n'est fermé que si `pyi_splash` existe et est actif (le `try/except ImportError` de `qt_main.py` le rend inoffensif en mode dev).

## Conventions

- **Langue** : code, identifiants et commentaires en anglais/français mélangés ; docstrings et textes UI en **français**. Garder le français pour tout libellé visible.
- Modules : `from __future__ import annotations`, type hints modernes (`list[str]`, `X | None`), `pathlib.Path` partout (jamais de chaînes de chemins), imports **relatifs** dans le package (`from .metadata_db import …`).
- Fichiers JSON : `encoding="utf-8"`, `indent=2`, `ensure_ascii=False`.
- Fonctions privées préfixées `_` ; une classe Qt par widget, chaque fenêtre/dialogue est dimensionné via `fit_and_center()` (à réutiliser pour toute nouvelle fenêtre).
- Style Qt : Fusion + `theme.get_app_stylesheet()` ; couleurs de référence bleu `#2563EB`, texte `#111827`, fond `#f5f6f8`. Police `Segoe UI` 10 sur Windows.
- Noms de fichiers/dossiers issus de saisies utilisateur : passer par `_safe_name()` (`project_structure.py`).
- Toucher au tri-état d'applicabilité ou aux codes d'exigence : vérifier aussi `export_templates.py` (`_is_not_applicable`, `_code_matches`) et le dashboard, qui interprètent les mêmes données.

## Fichiers à part

- [Test_interface.py](Test_interface.py) : maquette autonome de l'accueil (constantes de couleurs, widgets de test) ; **non importée** par l'application ni packagée.
- `wikidocs_qt/new_project_dialog2.py` : variante non suivie par git de `new_project_dialog.py` **sans le champ MNP** ; non importée. Ne pas la confondre avec la version active.
- [Documentation/](Documentation/00%20-%20Index.md) : notes de développement (coffre Obsidian, non suivi par git pour l'instant). Point d'entrée : `00 - Index.md` ; **en cas de divergence avec ce fichier, `Documentation/` fait foi**. Consulter `Bugs connus.md` avant de toucher au CECC, au N/A ou à l'export, et mettre à jour `Journal de dev.md` / `Changelog.md` après un changement notable.
- Le dépôt contient un historique court ; l'état de travail comporte des modifications non commitées (UI, dashboard, dialogues).
