---
tags: [nox, glossaire]
maj: 2026-10-23
---

↑ [[00 - Index]]

# Glossaire

Vocabulaire du domaine et du code. Les définitions métier sont **déduites du code** ; les faire valider par le métier.

| Terme | Définition | Dans le code |
|---|---|---|
| **NOX / N0X** | Nom du produit / du gabarit de suivi | `NOX_Manager`, `Template_BDD_*_N0X.xlsx` |
| **BDD** | « Base de données » de justificatifs : un livrable Excel + son dossier de documents. Trois types | `JUSTIFICATION_TYPES = ("CE","CECC","DPE")` |
| **CE** | Conformité européenne (marquage CE) : directives Machine, Basse Tension, RoHS (2011/65/UE + 2015/863), CEM, ESP | `CE_REQUIREMENTS` |
| **DPE** | Exigences réglementaires environnementales/produits (RoHS, DEEE, REACh, POP…) | `DPE_REQUIREMENTS` |
| **CECC** | Contrôle à l'export (classement EAR99/ECCN/ML ITAR, licence, pays d'origine, code douanier) | `CECC_FREE_FIELDS`, `CECC_STATUSES` |
| **Exigence** | Un texte réglementaire à justifier pour un article, identifié par son code (ex. `1907/2006`) | `requirement_codes`, `*_REQUIREMENTS` |
| **Code d'exigence** | Numéro de directive ou règlement ; comparé sans le suffixe ` — libellé` / ` \| libellé` | `_code_matches` |
| **Justificatif** | Document (PDF/DOCX/XLSX) qui prouve la conformité à une ou plusieurs exigences | `uploaded_documents` |
| **Applicabilité** | État d'une exigence pour un article : N/A, Non défini, Applicable | `ThreeStateToggle`, `not_applicable_codes` |
| **N/A** | Non applicable : exigence exclue du calcul | `not_applicable_codes_json` |
| **Complétion** | Pourcentage d'avancement d'une ligne (article × BDD) | `completion_value` |
| **Estimation** | Justificatif provisoire ; reconnu par le mot dans le nom du fichier ; compte moins dans la complétion | [[Règles métier#Convention « estimation »]] |
| **Prouvé / estimé** | Deux lignes de synthèse en pied des tableaux Excel : taux avec justificatifs fermes / taux incluant les estimations | `proved_row`, `estimated_row` |
| **Article / ligne** | Un couple (fournisseur, référence) du projet | `rows`, `_scan_supplier_reference_pairs` |
| **Fournisseur** | Société qui fournit l'article | `supplier` |
| **Référence** | Référence de l'article | `reference` |
| **MNP / MPN** | Manufacturer Part Number (référence constructeur). Le projet stocke `mnp` par ligne ; le CECC stocke `manufacturer_part_number` par document | `mnp`, `manufacturer_part_number` |
| **N° de dossier** | Identifiant du dossier projet, dans tous les noms de dossiers et fichiers | `dossier_number` |
| **Code date** | Code date saisi à la création du projet | `date_code` |
| **RoHS** | Directive `2011/65/UE`, commune à CE et DPE | `_is_rohs_code` |
| **Événement** | Une ligne de `uploaded_documents` : import de document **ou** enregistrement d'applicabilité | [[Modèle de données#Ce qu'une ligne représente]] |
| **Projet récent** | Entrée de `nox_state.json`, jusqu'à 10 | `ProjectManager` |
| **`.nox/`** | Dossier caché de métadonnées à la racine d'un projet | `PROJECT_META_DIRNAME` |
| **Dashboard** | Fenêtre de suivi d'un projet | `ProjectDashboardWindow` |
| **KPI** | Indicateurs du haut du dashboard : moyenne de complétion par BDD | `KpiCard` |
| **Onedir / onefile** | Modes PyInstaller : dossier vs exécutable unique. Le projet livre en onedir | `NOX_Manager.spec` |
| **`wikidocs_qt`** | Nom historique du package Python (ancien nom du projet) | dossier `wikidocs_qt/` |
