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

# Champs CECC : (clé enregistrée dans `cecc_fields`, libellé, colonne de
# l'export CECC). Les clés sont celles qu'écrit `CECCPage` (dialogue
# d'import) : source unique pour le panneau de détail et l'export.
CECC_FREE_FIELDS = [
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
    ("composant_export_10_1", "Composant contrôlés à l'export et intégrés dans l'article (10.1)", "S"),
]

# Anciennes clés lues en repli (cf. BUG-001 : dashboard et export lisaient
# ces noms, que le dialogue n'a jamais écrits).
_CECC_LEGACY_KEYS = {
    "cecc_etat": ("status",),
    "categorie": ("categorie_export",),
    "licence_yn": ("licence",),
    "licence_number": ("numero_licence",),
    "pays_origine": ("pays_origine_4a",),
    "ear99_value": ("ear99_value_usd",),
    "eccn_value": ("eccn_value_usd",),
    "composant_export_10_1": ("composants_controles_export",),
}


def cecc_field(cecc_fields: dict | None, key: str) -> str:
    """Valeur d'un champ CECC, en acceptant les anciennes clés."""
    fields = cecc_fields or {}
    for k in (key, *_CECC_LEGACY_KEYS.get(key, ())):
        value = str(fields.get(k) or "").strip()
        if value:
            return value
    return ""

CECC_STATUSES = (
    "Validé",
    "Relancé",
    "Non conforme",
    "Estimation",
)


def cecc_status(cecc_fields: dict | None) -> str:
    """Statut CECC d'un enregistrement (`cecc_etat`, repli `status`)."""
    return cecc_field(cecc_fields, "cecc_etat")

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
