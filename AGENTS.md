# Règles du dépôt

Ces règles s'appliquent à chaque session, sans être invoquées. Elles ne se discutent pas : une question qu'elles ne tranchent pas remonte au responsable technique.

## 1. Cette application

- **Palier** : P2, en **application de bureau PySide6 hors catalogue** (décision 0002)
- **Objet** : constituer et suivre les dossiers de justificatifs de conformité (CE, DPE, CECC) par article de projet, et produire les tableaux Excel récapitulatifs
- **Échanges** : aucun ; les données vivent dans le dossier de chaque projet sur le partage réseau (décision 0003)

**Reprise terminée** (recette du 2026-10-28, `docs/recette.md`) : l'ancienne application n'est plus dans le dossier ; elle reste dans l'historique Git sous l'étiquette `v1-avant-refonte` (`git show v1-avant-refonte:wikidocs_qt/<fichier>`). Les docstrings du code citent leur source sous cette forme. Chaque évolution (E1–E14) change volontairement un résultat : elle met à jour `tests/reference/attendu/` dans sa propre tâche, en le disant dans le commit.

## 2. Avant de générer du code

Lis dans cet ordre, et uniquement ce dont la tâche a besoin :

1. `docs/decisions/` — les décisions prises pour ce projet
2. `docs/besoin/` — ce que l'application doit faire (R = existant à reproduire, E = évolutions)
3. `docs/diagnostic/comportement.md` — la référence de comportement
4. `docs/travaux.md` — la tâche en cours et ses dépendances

Une question sans réponse dans ces documents ne se tranche pas dans le code. Arrête-toi et dis ce qui manque.

## 3. Structure du code

```
01_application/app/
├─ ui/           fenêtres et dialogues Qt : affichage, saisie, appel d'un service
├─ services/     règles métier et orchestration — sans Qt, sans fichier, sans base
├─ dataaccess/   project.json, SQLite, dossiers, documents, exports Excel — seul endroit
├─ models/       objets métier (dataclasses)
├─ core/         paramétrage, chemins, erreurs, transverse
└─ main.py       point d'entrée
01_application/tests/
```

- Les dépendances descendent toujours : `ui → services → dataaccess → models`. Jamais l'inverse.
- Un gestionnaire d'événement Qt fait dix lignes au maximum : il lit la saisie, appelle un service, affiche le résultat.
- `services/` n'importe ni `PySide6`, ni `sqlite3`, ni `openpyxl` : il reçoit des valeurs, il en retourne.
- `core/` est transverse : tout le monde peut en dépendre, il ne dépend d'aucune autre couche.
- Contrôle : `uv run couches`.

## 4. Interface

- PySide6, style Fusion, palette claire, feuille de style unique dans `ui/`. Libellés visibles **en français**.
- Chaque fenêtre ou dialogue est dimensionné et centré par une fonction commune de `ui/`.
- Toute ressource lue à l'exécution (modèle Excel, icône, image) est déclarée dans `NOX_Manager.spec` et retrouvée par `core/` (développement comme exécutable fabriqué).
- Pas d'accès disque long dans le fil de l'interface : les projets vivent sur un partage réseau lent.

## 5. Pièges de version

Les versions font foi dans `pyproject.toml`. Ne les change jamais de ta propre initiative.

| Dépendance | À ne pas écrire | À écrire |
|---|---|---|
| PySide6 6.x | `exec_()`, `QtWidgets.QAction` | `exec()`, `QtGui.QAction` |
| openpyxl 3.1 | `ws.cell(row, col).value = …` sans vérifier la fusion | vérifier les cellules fusionnées avant d'écrire |
| Python ≥ 3.12 | `typing.List`, `Optional[X]` | `list[str]`, `X \| None` |

En cas de doute sur une API, vérifie dans la version installée plutôt que de produire ce qui te paraît familier.

## 6. Git

- Branches : `dev/story/<id>`, `dev/task/<id>`, `dev/fix/<id>`, `main/hotfix/<id>`. Minuscules, identifiant obligatoire et numérique : le numéro de la tâche dans `docs/travaux.md`.
- Une task part de la branche de sa story et y revient. Une story et un defect partent de `develop` et y reviennent.
- Commits : `<ref>(<idTâche>): <description>`. Pas de type, pas de `#`.
- Jamais de push direct sur `main` ni `develop`. Jamais de rebase. En cas de doute, ne pas forcer.

## 7. Sécurité

- **N'écris aucun contrôle d'accès** : les droits sont ceux du partage, posés par la DSI.
- Pas de SQL construit par concaténation : requêtes paramétrées uniquement.
- Aucun secret dans le code, les journaux ou le dépôt.
- Tout fichier déposé est contrôlé (extension autorisée, R7 / E2) avant copie.
- Noms de fichiers et dossiers issus d'une saisie : caractères interdits remplacés (`<>:"/\|?*` → `_`).
- Le paramétrage vit dans `config.json`, jamais dans la base.

## 8. Données

- Format imposé par l'existant (décision 0003) : `.nox/project.json` v3, `.nox/nox_metadata.db`, arborescence `BDD <type> <n°>/…`. Une nouvelle colonne s'ajoute par migration tolérante, jamais par recréation.
- JSON : `encoding="utf-8"`, `indent=2`, `ensure_ascii=False`. Chemins : `pathlib.Path`, et en base séparateur `/`, relatifs au dossier du projet.

## 9. Tests

- Les tests portent sur `services/` (une règle R ou E par test, citée dans son nom ou sa docstring) et sur les résultats observables : pourcentages, fichiers produits, contenu des exports.
- La référence de comportement (`tests/reference/attendu/`) doit passer sur le nouveau code. Elle ne se modifie pas pour faire passer un test.
- Jamais de test sur l'intérieur d'un service.

## 10. Ce qui remonte

Arrête-toi et demande, plutôt que de décider, dans ces cas :

- une décision absente de `docs/decisions/` ;
- une règle absente ou contradictoire dans `docs/besoin/` ;
- une différence de comportement non prévue par une évolution validée (`docs/besoin/besoin.md`) ;
- un besoin qui dépasse le palier de l'application ;
- un contrôle automatique en échec que tu ne sais pas corriger sans contourner une règle.
