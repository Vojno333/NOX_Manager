"""Référentiels métier : exigences, champs CECC, colonnes des exports Excel.

Repris de `00_ancien/wikidocs_qt/document_rules.py`, `export_templates.py`
(dictionnaires de colonnes) et `upload_document_dialog.py` (menus CECC).
Données seules : les règles qui s'en servent vivent dans `services/`.
"""

from __future__ import annotations

LIVRABLES = ("CE", "CECC", "DPE")

# (code, libellé), dans l'ordre d'affichage.
EXIGENCES_CE = (
    ("2006/42/UE", "Directive Machine"),
    ("2014/35/UE", "Directive Basse Tension"),
    ("2011/65/UE", "RoHS"),
    ("2015/863", "RoHS (amendement)"),
    ("2014/30/UE", "Compatibilité électromagnétique EMC"),
    ("2014/68/UE", "Directive équipement sous préssion"),
)

EXIGENCES_DPE = (
    ("2011/65/UE", "RoHS"),
    ("2012/19/UE", "DEEE"),
    ("2006/66/CE", "Piles et accumulateurs"),
    ("1907/2006", "REACh"),
    ("2019/1021", "POP"),
    ("1005/2009", "SAO"),
    ("517/2014", "Gaz à effet de serre fluorés"),
    ("2017/852", "Mercure"),
    ("528/2012", "Biocides"),
    ("2013/59/Euratom", "Rayonnements ionisants"),
    ("2017/821", "Devoir de diligence"),
    ("2016/1628", "Les gaz polluants et les particules polluantes"),
)

# RoHS est une seule exigence (R14) : 2015/863 est un alias de 2011/65/UE,
# affiché à part en CE (colonnes J et K) et présent aussi en DPE.
CODE_ROHS = "2011/65/UE"
ALIAS_CODES = {"2015/863": CODE_ROHS}

# Exigence → colonne de l'export (R25). « AUTRES » est reprise telle quelle :
# aucune exigence ne porte ce code aujourd'hui, la colonne N reste donc vide.
COLONNES_CE = {
    "2006/42/UE": "H",
    "2014/35/UE": "I",
    "2011/65/UE": "J",
    "2015/863": "K",
    "2014/30/UE": "L",
    "2014/68/UE": "M",
    "AUTRES": "N",
}

COLONNES_DPE = {
    "2011/65/UE": "H",
    "2012/19/UE": "I",
    "2006/66/CE": "J",
    "1907/2006": "K",
    "2019/1021": "L",
    "1005/2009": "M",
    "517/2014": "N",
    "2017/852": "O",
    "528/2012": "P",
    "2013/59/Euratom": "Q",
    "2017/821": "R",
    "2016/1628": "S",
}

# Champs de la fiche CECC : (clé enregistrée, libellé, colonne de l'export CECC).
CHAMPS_CECC = (
    ("manufacturer_doc", "Fournisseur Doc / MANUFACTURER", "G"),
    ("manufacturer_part_number", "Manufacturer Part Number", "H"),
    ("cecc_etat", "Statut CECC", "I"),
    ("cecc_date", "CECC : Date", "J"),
    ("nom_cecc", "Nom : CECC", "K"),
    ("cecc_classement", "CECC Classement", "L"),
    ("categorie", "Catégorie (EAR99 / Code ECCN / Code ML ITAR)", "M"),
    ("licence_yn", "Licence Oui / Non", "N"),
    ("licence_number", "N° Licence", "O"),
    ("pays_origine", "Pays Origine 4a", "P"),
    ("ear99_value", "EAR99 Value (USD)", "Q"),
    ("eccn_value", "ECCN value (USD)", "R"),
    (
        "composant_export_10_1",
        "Composant contrôlés à l'export et intégrés dans l'article (10.1)",
        "S",
    ),
)

# Anciennes clés, lues en repli quand la clé actuelle est vide.
ANCIENNES_CLES_CECC = {
    "cecc_etat": ("status",),
    "categorie": ("categorie_export",),
    "licence_yn": ("licence",),
    "licence_number": ("numero_licence",),
    "pays_origine": ("pays_origine_4a",),
    "ear99_value": ("ear99_value_usd",),
    "eccn_value": ("eccn_value_usd",),
    "composant_export_10_1": ("composants_controles_export",),
}

# Statuts officiels, proposés à la saisie (R19). « Estimation » ne se saisit
# plus mais figure dans d'anciennes fiches.
STATUTS_CECC = ("A demander", "Demandé", "Relancé", "Non conforme", "Validé")
STATUT_VALIDE = "Validé"
STATUT_ESTIMATION = "Estimation"

CLASSEMENTS_CECC = ("NC", "DU", "DI (Défense item)")
LICENCE_OUI_NON = ("Oui", "Non")

# Pays d'origine (point 4a du CECC), dans l'ordre du menu actuel, doublons compris.
PAYS_ORIGINE_4A = (
    "AF-Afghanistan",
    "AX-Îles Åland",
    "AL-Albanie",
    "DZ-Algérie",
    "AS-Samoa américaines",
    "AD-Andorre",
    "AO-Angola",
    "AI-Anguilla",
    "AQ-Antarctique",
    "AG-Antigua-et-Barbuda",
    "AR-Argentine",
    "AM-Arménie",
    "AW-Aruba",
    "AU-Australie",
    "AT-Autriche",
    "AZ-Azerbaïdjan",
    "BS-Bahamas",
    "BH-Bahreïn",
    "BD-Bangladesh",
    "BB-Barbade",
    "BY-Biélorussie",
    "BE-Belgique",
    "BZ-Belize",
    "BJ-Bénin",
    "BM-Bermudes",
    "BT-Bhoutan",
    "BO-Bolivie",
    "BA-Bosnie-Herzégovine",
    "BW-Botswana",
    "BV-Île Bouvet",
    "BR-Brésil",
    "VG-British Virgin Islands",
    "IO-Territoire britannique de l’Océan Indien",
    "BN-Brunei Darussalam",
    "BG-Bulgarie",
    "BF-Burkina Faso",
    "BI-Burundi",
    "KH-Cambodge",
    "CM-Cameroun",
    "CA-Canada",
    "CV-Cap-Vert",
    "KY-Iles Cayman",
    "CF-République centrafricaine",
    "TD-Tchad",
    "CL-Chili",
    "CN-Chine",
    "HK-Hong Kong",
    "MO-Macao",
    "FR-France",
    "DE-Allemagne",
    "GB-Royaume-Uni",
    "US-États-Unis",
    "JP-Japon",
    "IT-Italie",
    "ES-Espagne",
    "CH-Suisse",
    "BE-Belgique",
    "NL-Pays-Bas",
    "PT-Portugal",
    "PL-Pologne",
    "RO-Roumanie",
    "RU-Russie",
    "UA-Ukraine",
    "CN-Chine",
    "KR-Corée du Sud",
    "TW-Taiwan",
    "VN-Viêt Nam",
    "IN-Inde",
    "MX-Mexique",
    "MA-Maroc",
    "TN-Tunisie",
    "DZ-Algérie",
    "ZA-Afrique du Sud",
    "ZW-Zimbabwe",
)
