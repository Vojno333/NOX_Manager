# NOX Manager

Application de bureau Windows (PySide6) qui constitue et suit les dossiers de justificatifs de conformité (CE, DPE, CECC) par article de projet, et produit les tableaux Excel récapitulatifs. Les projets vivent sur le partage réseau.

## Lancer sur votre poste

```
uv sync --extra dev
uv run dev
```

## Les commandes

| Commande | Ce qu'elle fait |
|---|---|
| `uv run dev` | lance l'application |
| `uv run test` | joue les tests |
| `uv run lint` | met le code en forme et signale les erreurs |
| `uv run couches` | vérifie que les dépendances entre couches descendent |
| `uv run build` | fabrique l'exécutable dans `dist/NOX_Manager/` |

Rien d'autre à installer que `uv`.

## Reprise en cours

L'ancienne application est gelée dans `00_ancien/`. Elle reste utilisable (`py 00_ancien/qt_main.py`) et sert de référence jusqu'à la fin de la reconstruction.

## Où se trouve quoi

```
01_application/app/
├── ui/           fenêtres et dialogues Qt
├── services/     règles métier et orchestration
├── dataaccess/   project.json, base SQLite, dossiers, exports Excel — seul endroit
├── models/       objets métier
├── core/         paramétrage, chemins, transverse
└── main.py
```

| Dossier | Contenu |
|---|---|
| `docs/decisions/` | les décisions prises |
| `docs/besoin/` | ce que l'application doit faire |
| `docs/diagnostic/` | l'état de l'existant, les constats, la référence de comportement |
| `docs/travaux.md` | la liste des tâches |
| `tests/reference/` | le projet d'essai et les résultats attendus |
| `.owlia/etat.md` | où en est le projet |

`config.json` contient les réglages ordinaires. Il n'y a aucun secret dans cette application.

Pour reprendre le travail, taper `/owlia`.
