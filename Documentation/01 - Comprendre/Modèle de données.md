---
tags: [nox, donnees]
maj: 2026-09-21
---

↑ [[00 - Index]] · Vocabulaire : [[Glossaire]]

# Modèle de données

Trois emplacements de stockage.

## 1. État utilisateur : `~/.nox_manager/nox_state.json`

Géré par `ProjectManager` ([[Architecture]]). Créé au premier lancement.

```json
{
  "recent_projects": [{"name": "…", "path": "C:\\…", "last_opened": "2026-04-30T10:12:00"}],
  "recent_locations": ["C:\\…"],
  "default_location": "C:\\…"
}
```

- 10 projets et 10 emplacements maximum, les plus récents en premier.
- Fichier corrompu ou absent → état par défaut silencieux (aucun message).

## 2. Projet : `<dossier projet>/.nox/project.json`

Version courante : `project_file_version = 3`.

| Clé | Type | Rôle |
|---|---|---|
| `project_name` | str | Nom affiché |
| `project_path` | str | Chemin absolu (réécrit à chaque `save_project`) |
| `dossier_number` | str | Numéro de dossier, entre dans tous les noms de dossiers/fichiers |
| `date_code` | str | Code date saisi à la création |
| `created_at` / `updated_at` | ISO 8601 | Horodatage |
| `project_meta_dir` | str | Toujours `.nox` |
| `project_file_version` | int | 3 |
| `rows` | list[dict] | Références du projet (voir ci-dessous) |
| `enabled_bdds` | list[str] | Sous-ensemble ordonné de `["CE", "CECC", "DPE"]` |

Une ligne de `rows` : `supplier`, `reference`, `label`, `mnp`, `order_number` (toutes en chaînes). Normalisation (`_normalize_rows`) : les lignes sans fournisseur **ou** sans référence sont supprimées ; les doublons `(supplier, reference)` sont dédupliqués (le premier gagne).

Compatibilité : l'ancien `.nox_project.json` (à la racine du projet) est encore lu en repli, et supprimé à la création d'un nouveau `project.json`.

> Le code d'export mentionne une clé `not_applicable_requirements` (`_get_not_applicable_map`) : **elle n'existe pas dans le format réel** et la fonction n'est jamais appelée. Voir [[Dette technique#DT-005]].

## 3. Métadonnées documentaires : `<dossier projet>/.nox/nox_metadata.db` (SQLite)

Mode `WAL`, `synchronous=NORMAL`. Une seule table :

```sql
uploaded_documents (
  id                         INTEGER PRIMARY KEY AUTOINCREMENT,
  supplier                   TEXT NOT NULL,
  reference                  TEXT NOT NULL,
  source_justification_type  TEXT NOT NULL,   -- 'CE' | 'DPE' | 'CECC'
  stored_in_bdds_json        TEXT NOT NULL,   -- ex. ["CE","DPE"]
  requirement_codes_json     TEXT NOT NULL,   -- exigences COUVERTES par le document
  requirement_labels_json    TEXT NOT NULL,
  cecc_fields_json           TEXT NOT NULL,   -- dict, voir ci-dessous
  original_filename          TEXT NOT NULL,
  stored_filename            TEXT NOT NULL,
  relative_path              TEXT NOT NULL,   -- relatif au dossier projet, séparateur '/'
  uploaded_at                TEXT NOT NULL,   -- ISO 8601
  not_applicable_codes_json  TEXT NOT NULL DEFAULT '[]',
  not_applicable_labels_json TEXT NOT NULL DEFAULT '[]'
)
```

### Ce qu'une ligne représente

Une ligne n'est **pas seulement un document** : c'est un **événement d'import ou d'applicabilité**, horodaté.

| Cas | `stored_filename` / `relative_path` | `requirement_codes` | `not_applicable_codes` |
|---|---|---|---|
| Import d'un document | rempli | exigences cochées et « Applicable » | exigences marquées N/A au moment de l'import |
| Mode « Applicabilité » (ou import sans exigence cochée) | **vide** | toutes les exigences « Applicable » | exigences N/A |
| CECC | rempli | vide | vide (les données sont dans `cecc_fields`) |

L'état courant d'une exigence se déduit du **dernier événement qui la mentionne** (voir [[Règles métier#Résolution du N/A]]). L'historique n'est jamais purgé, sauf par suppression de la référence (`delete_uploaded_documents_for_rows`, qui supprime **par (supplier, reference)**).

### Le dictionnaire `cecc_fields`

Clés écrites par l'import (`CECCPage.get_fields`), telles que lues dans le code :

`manufacturer_doc`, `licence_yn`, `manufacturer_part_number`, `licence_number`, `cecc_etat`, `cecc_date`, `nom_cecc`, `pays_origine`, `cecc_classement`, `ear99_value`, `categorie`, `eccn_value`, `composant_export_10_1`, …

⚠️ Ces clés **ne correspondent pas** à celles lues par le dashboard et l'export : détail et table de correspondance dans [[Bugs connus#BUG-001]] (source unique).

### Migrations

`init_metadata_db` crée la table si besoin puis tente un `ALTER TABLE … ADD COLUMN` pour les colonnes ajoutées après coup (les `OperationalError` « colonne déjà existante » sont ignorées). **Toute nouvelle colonne doit être ajoutée à cette boucle** et à `CREATE TABLE`, sinon les bases existantes casseront.

## Arborescence disque d'un projet

```
<dossier projet>/
├── .nox/
│   ├── project.json
│   └── nox_metadata.db (+ -wal, -shm)
├── BDD CE   <dossier_number>/
│   ├── BDD_CE_<dossier_number>.xlsx        ← créé vide (touch), écrasé par l'export
│   └── Documents/<Fournisseur>/<Référence>/<fichiers>
├── BDD CECC <dossier_number>/ …
└── BDD DPE  <dossier_number>/ …
```

- Un dossier `BDD <type> …` n'existe que pour les BDD activées (`enabled_bdds`).
- Les noms de dossiers passent par `_safe_name` (caractères `<>:"/\|?*` remplacés par `_`).
- Le nom final d'un fichier importé est construit par `_auto_name` (ou saisi par l'utilisateur) ; en cas de collision, `_unique_target_path` ajoute ` (1)`, ` (2)`…
- Un fichier importé pour un couple est **copié** (`shutil.copy2`), une fois par BDD cible ; l'original n'est pas déplacé.

## Sauvegarde et sauvegardabilité

- Tout l'état d'un projet est dans son dossier : copier le dossier suffit à le déplacer (`project_path` est réécrit à la sauvegarde ; les `relative_path` restent valides).
- Ne pas copier `nox_metadata.db` sans ses fichiers `-wal` / `-shm` si l'application est ouverte.
- Le `.gitignore` exclut `*.db`, `*.sqlite`, `*.nox`, `Projects/`, `Documents/`, `exports/` : aucune donnée de projet ne doit être commitée.
