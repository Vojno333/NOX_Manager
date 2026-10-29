# 0005 — Lignes multiples d'un même article (E1)

*Date : 2026-10-28. Statut : acceptée. Diffusion décrite par l'utilisateur : la nouvelle version remplace l'ancienne poste par poste, en copiant l'exécutable ; les deux versions cohabitent donc un temps.*

## Contexte

E1 : la ligne entière (fournisseur, référence, libellé, MNP, n° de commande) devient unique ; un même couple fournisseur / référence peut figurer sur plusieurs lignes, chacune avec ses justificatifs, son applicabilité, sa complétion et sa ligne d'export. L'ancienne application ne connaît que le couple : elle ne garde que la première ligne, et réécrit `project.json` sans les lignes en double.

## Décision

- **Interrupteur** `lignes_multiples` dans `config.json`, à `false` par défaut. Tant qu'il est à `false`, rien ne change (R3 : le premier gagne). On le passe à `true` sur tous les postes **quand l'ancienne application n'est plus utilisée nulle part**.
- **Identifiant de ligne** : avec l'interrupteur à `true`, chaque ligne de `project.json` reçoit une clé `line_id` (8 caractères hexadécimaux), conservée ensuite. Les lignes strictement identiques sont fusionnées.
- **Rattachement des enregistrements** : nouvelle colonne `line_id` de `uploaded_documents` (migration tolérante, `''` par défaut). Un enregistrement appartient à la ligne dont il porte l'identifiant ; un enregistrement sans identifiant (`''`, cas de tous les enregistrements existants et de ceux de l'ancienne application) appartient à la **première** ligne de son couple. Un dépôt sur un article qui n'a qu'une ligne est enregistré sans identifiant : il reste lisible par l'ancienne application.
- **Rangement** : article sur une seule ligne → `<F>/<R>/` (inchangé) ; à partir de deux lignes → `<F>/<R>/<N° de commande>/`, avec un suffixe `_1`, `_2`… quand plusieurs lignes du couple ont le même n° de commande ou n'en ont pas. Les documents déjà déposés restent où ils sont (le chemin est en base).
- **Export** : avec l'interrupteur à `true`, une ligne d'export par ligne du projet, avec ses propres libellé, MNP et n° de commande (corrige le constat C6) ; à `false`, comportement actuel.

## Conséquences

- Passer l'interrupteur à `true` alors qu'un poste utilise encore l'ancienne application expose à la perte des lignes en double si ce poste réenregistre le paramétrage du projet.
- `project_file_version` reste 3 : la clé `line_id` est ignorée par l'ancienne application.

## Avenant du 2026-10-29 : livrée activée

*Décision de l'utilisateur, après la recette des évolutions (V9, V10 conformes).*

- L'interrupteur est livré à `true` dans `config.json`. Raison : aucun projet n'a de doublon aujourd'hui, et au moment de la diffusion plus aucun poste n'aura l'ancienne application ; la condition d'activation est donc remplie dès la livraison.
- Garde-fou : sur un projet sans doublon (tous les projets existants), E1 activée donne les mêmes complétions et les mêmes exports qu'E1 désactivée (`test_e1_sans_doublon_meme_resultat`).
- Consigne : ne plus lancer l'ancienne application sur un projet dès qu'un poste a la nouvelle version. Si un poste devait la garder, ne jamais y modifier le paramétrage d'un projet (risque décrit ci-dessus).
- Les tests ne dépendent pas du réglage livré : E1 y est désactivée par défaut (référence R3) et activée dans ses propres tests.
