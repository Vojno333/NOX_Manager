---
tags: [nox, utilisateur]
maj: 2026-09-21
---

↑ [[00 - Index]] · Détail technique des parcours : [[Flux fonctionnels]] · Vocabulaire : [[Glossaire]]

# Guide utilisateur : NOX Manager

Version rédigée à partir du fonctionnement observé dans le code ; à relire avec un utilisateur réel. À destination des personnes qui utilisent l'application, pas des développeurs. Termes : [[Glossaire]].

## À quoi ça sert

Pour chaque **article** (un fournisseur + une référence) de ton projet, NOX Manager t'aide à rassembler et suivre les justificatifs de conformité :

- **CE** : marquage CE (Directive Machine, RoHS, CEM, équipements sous pression) ;
- **DPE** : exigences environnementales (RoHS, DEEE, REACh, POP…) ;
- **CECC** : contrôle à l'export.

Il te dit **où tu en es** (pourcentage de complétion) et produit les **tableaux Excel** à livrer.

## Démarrage rapide

1. **Nouveau projet** : donne un nom, un numéro de dossier, choisis l'emplacement et les livrables (CE / CECC / DPE) à suivre, puis saisis ou colle la liste des articles.
2. Ouvre le projet : le **tableau de bord** liste chaque article × chaque livrable.
3. Pour chaque article : **règle l'applicabilité** puis **importe** les documents.
4. Clique sur **Exporter** pour générer les tableaux Excel.

## Applicabilité : N/A, Non défini, Applicable

Pour CE et DPE, indique pour chaque exigence :

| Choix | Quand |
|---|---|
| **Applicable** | L'exigence concerne l'article : il faudra un document |
| **N/A** | L'exigence ne concerne pas l'article : elle est ignorée dans le calcul |
| **Non défini** | Tu n'as pas encore tranché. Tu ne pourras **pas** importer tant qu'il en reste |

## Importer un document

1. Sélectionne une ou plusieurs lignes du tableau (**même type** de livrable).
2. Clique sur **Importer**, choisis le fichier (PDF, Word ou Excel), ou glisse-le.
3. Règle l'applicabilité, puis **coche les exigences que ce document couvre**.
4. Vérifie le nom final du fichier, puis valide.

Bon à savoir :
- Le fichier est **copié** dans le dossier du projet ; ton original n'est pas déplacé.
- Le RoHS est commun à CE et DPE : le document est rangé dans les deux.
- Si tu ne coches aucune exigence, aucun fichier n'est copié : seule l'applicabilité est enregistrée.
- **Si le document est une estimation, mets le mot « estimation » dans son nom** : il ne comptera alors que partiellement dans le pourcentage. ([[Règles métier#Convention « estimation »]])

### CECC
Renseigne au minimum le **fournisseur du document**, le **Manufacturer Part Number** et le **nom CECC**, puis les autres champs (classement, catégorie, licence, pays d'origine…).

## Lire le tableau de bord

- **Complétion** : moyenne de l'avancement des exigences applicables (CE/DPE) ou part de justificatifs « Validé » (CECC).
- **Filtres** : clique sur l'icône de filtre d'un en-tête de colonne.
- **Panneau de détail** : sélectionne une ligne pour voir ses exigences et ses documents ; clique sur un document pour l'ouvrir.

## Exporter

Le bouton d'export crée, dans le dossier de chaque livrable, un fichier `BDD_<type>_<numéro>.xlsx`. **Il écrase le précédent** : ne fais pas de saisie manuelle dans ce fichier, refais l'export à la place. Ferme le fichier dans Excel avant d'exporter.

## Supprimer

| Action | Effet |
|---|---|
| Retirer des projets récents | Le projet reste sur le disque |
| Supprimer définitivement | **Supprime tout le dossier du projet**, sans corbeille |
| Supprimer une référence (tableau de bord) | Efface son historique dans l'application ; à vérifier si les fichiers restent (voir [[Bugs connus#BUG-005]]) |

## Dépannage

| Symptôme | Piste |
|---|---|
| L'application ne démarre pas | Ne pas déplacer `NOX_Manager.exe` hors de son dossier ; relancer depuis le dossier complet |
| Export : « Template introuvable » | Le dossier d'installation est incomplet : réinstaller la version complète |
| Export : erreur d'écriture | Le fichier Excel est ouvert : le fermer |
| Projet absent des récents | **Ouvrir un projet existant** et choisir son dossier |
| Complétion CECC à 0 % / colonnes CECC vides dans l'Excel | Défaut connu, en cours de traitement ([[Bugs connus#BUG-001]]) |
| Tout est étrange après une mise à jour | Ne pas mélanger deux versions sur le même projet partagé ([[Build et livraison#Mise à jour chez l'utilisateur]]) |

Pour signaler un problème : donner la version, le scénario, une capture, et **le fichier `<projet>\.nox\project.json`** (sans document confidentiel).
