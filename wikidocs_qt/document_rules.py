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
    ("2014/35/UE", "Directive Basse Tension"),
    ("2011/65/UE", "RoHS"),
    ("2015/863", "RoHS (amendement)"),
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

# ── Résolution de l'applicabilité (partagée dashboard / export / dialogue) ──
# États : 0 = N/A, 1 = Non défini, 2 = Applicable (cf. ThreeStateToggle).
REQ_NA = 0
REQ_UNDEFINED = 1
REQ_APPLICABLE = 2

# Les deux textes RoHS sont affichés séparément (colonnes J et K du template
# CE) mais forment UNE seule exigence : renseigner l'un renseigne l'autre,
# ainsi que la colonne RoHS du DPE. 2015/863 est donc un alias de 2011/65/UE.
ROHS_CODE = "2011/65/UE"
_CODE_ALIASES = {"2015/863": ROHS_CODE}


def normalize_requirement_code(code: str) -> str:
    """« 1907/2006 — REACh » / « 1907/2006 | REACh » → « 1907/2006 ».

    Les alias sont ramenés à leur code de référence (2015/863 → 2011/65/UE).
    """
    code = str(code or "").strip()
    for sep in (" — ", " | "):
        if sep in code:
            code = code.split(sep, 1)[0].strip()
    return _CODE_ALIASES.get(code, code)


def is_rohs_code(code: str) -> bool:
    return normalize_requirement_code(code) == ROHS_CODE or "rohs" in str(code or "").lower()


def code_matches(a: str, b: str) -> bool:
    return normalize_requirement_code(a) == normalize_requirement_code(b)


def doc_has_file(doc: dict) -> bool:
    """Faux pour un enregistrement « applicabilité seule » (aucun document)."""
    return bool(str(doc.get("relative_path") or "").strip())


def requirement_state(docs: list[dict], code: str) -> int:
    """État d'applicabilité du code selon le DERNIER enregistrement le mentionnant.

    Un code est « Applicable » s'il figure dans `applicable_codes` ou dans
    `requirement_codes` (un document couvrant une exigence la rend applicable),
    « N/A » s'il figure dans `not_applicable_codes`. Aucun enregistrement ne
    le mentionne → « Non défini ».
    """
    for doc in sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True):
        applicable = list(doc.get("applicable_codes") or []) + list(doc.get("requirement_codes") or [])
        if any(code_matches(c, code) for c in applicable):
            return REQ_APPLICABLE
        if any(code_matches(c, code) for c in (doc.get("not_applicable_codes") or [])):
            return REQ_NA
    return REQ_UNDEFINED
