---
tags: [nox, changelog]
maj: 2026-10-23
---

↑ [[00 - Index]]

# Changelog

Vue « livraison » : ce que voit l'utilisateur, par version. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/). Le détail du travail est dans [[Journal de dev]].

Numérotation proposée : `MAJEUR.MINEUR.CORRECTIF` (ex. 1.1.0). Il n'existe pas encore de numéro de version dans le code (NOX-004 dans [[Backlog]]) : la version courante est appelée « v1 » par le premier commit.

## [Non publié]

### Ajouté
- Fenêtres et dialogues centrés sur l'écran de la fenêtre parente et bornés à la taille disponible (`window_geometry.py`).
- Icônes SVG DPE et UE dans le dashboard.
- Réglages de projet : colonne et saisie en masse du **MNP** (`ProjectSettingsDialog`).
- Icône et regroupement corrects de l'application dans la barre des tâches Windows.
- Icône de l'application affichée aussi sur la fenêtre d'accueil, y compris dans la version compilée.

### Modifié
- Splash `flash.png` allégé (1,43 Mo → 58 Ko).
- `AUTRES` retiré de la liste des exigences CE.
- Accueil, dashboard et dialogues de projet/import retouchés (à détailler par l'auteur).
- Création de projet : `.nox` et les dossiers `BDD CE/CECC/DPE …` sont créés directement dans l'emplacement choisi, sans dossier intermédiaire nommé d'après le numéro de l'affaire.
- Accueil (liste des projets récents) et dashboard (titre de fenêtre, badge) affichent le **numéro de dossier** au lieu du numéro de l'affaire.

### Ajouté (CE)
- Exigences CE **2014/35/UE (Basse Tension)** et **2015/863 (RoHS, amendement)** : saisie dans le dialogue, panneau de détail et colonnes I et K de l'export CE (déjà présentes dans le template mais jamais remplies).
- Les deux RoHS (2011/65/UE et 2015/863) sont liées : renseigner l'une renseigne l'autre, ainsi que RoHS côté DPE, y compris pour un N/A posé via « Applicabilité ».

### Corrigé
- Page CECC du dialogue d'import : l'aperçu du nom final ne se mettait pas à jour pendant la saisie (erreur `changed() only accepts 0 argument(s)`).
- Applicabilité : modifier l'applicabilité d'une référence (bouton « Applicabilité » ou import sans exigence cochée) ne masque plus les documents déjà déposés (nom, lien et complétude restent corrects dans le dashboard et l'export). À la réouverture, les exigences « Non défini » le restent au lieu de repasser « Applicable ».
- Export Excel : une exigence marquée N/A puis repassée « Applicable » n'est plus exportée en « N/A » (même règle que le dashboard).
- Import en masse : une ligne vide dans une des 5 colonnes (fournisseur/référence/libellé/MNP/n° commande) décalait les lignes suivantes de cette colonne vers le haut, désalignant les dossiers importés. Les lignes vides restent maintenant à leur position ; seules les lignes totalement vides sont ignorées, une fois l'alignement garanti.
- Export Excel : les colonnes Libellé, MPN et N° de commande n'étaient jamais renseignées. L'export utilise désormais les mêmes données que le dashboard (`project.json` → `rows`) pour déterminer la liste des références et leurs informations, au lieu d'un scan des dossiers sur disque qui pouvait diverger de l'interface (références manquantes, textes désalignés par la normalisation des noms de dossiers).

## [v1.0] : 2026-04-28 → 2026-04-30

### Ajouté
- Création de projet avec références fournisseur/référence, BDD CE / CECC / DPE activables.
- Dashboard de suivi : KPI par BDD, filtres de colonnes, panneau de détail.
- Import de justificatifs PDF/DOCX/XLSX, import en lot, copie dans l'arborescence du projet.
- **Applicabilité tri-état** (N/A / Non défini / Applicable) pour CE et DPE.
- Export vers les templates Excel `Template_BDD_*_N0X.xlsx` avec liens hypertexte et formules de synthèse.
- Build Windows `NOX_Manager.exe` (PyInstaller, onedir, splash).

### Modifié
- Refonte de l'affichage du dashboard et amélioration du tableau (2026-04-30).
