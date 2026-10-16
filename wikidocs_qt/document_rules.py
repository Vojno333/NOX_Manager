from __future__ import annotations

JUSTIFICATION_TYPES = ("CE", "CECC", "DPE")

DPE_REQUIREMENTS = [
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
]

CE_REQUIREMENTS = [
    ("2006/42/UE", "Directive Machine"),
    ("2011/65/UE", "RoHS"),
    ("2014/30/UE", "Compatibilité électromagnétique EMC"),
    ("2014/68/UE", "Directive équipement sous préssion"),
]

CECC_FREE_FIELDS = [
    ("manufacturer_doc", "Fournisseur Doc / MANUFACTURER"),
    ("manufacturer_part_number", "Manufacturer Part Number"),
    ("nom_cecc", "Nom : CECC"),
    ("cecc_classement", "CECC Classement"),
    ("categorie_export", "Catégorie (EAR99 / Code ECCN / Code ML ITAR)"),
    ("licence", "Licence Oui / Non"),
    ("numero_licence", "N° Licence"),
    ("pays_origine_4a", "Pays Origine 4a"),
    ("ear99_value_usd", "EAR99 Value (USD)"),
    ("eccn_value_usd", "ECCN value (USD)"),
    ("composants_controles_export", "Composant controlés à l'export et intégrés dans l'article"),
    ("pays_origine", "Pays d'origine"),
    ("classement_export", "Classement à l'export"),
    ("code_douanier", "Code douanier / Tariff Code"),
]

CECC_STATUSES = (
    "Validé",
    "Relancé",
    "Non conforme",
    "Estimation",
)