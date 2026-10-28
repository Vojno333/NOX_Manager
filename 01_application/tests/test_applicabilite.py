"""Tâche 8 : applicabilité (R14, R15, R16, R18)."""

from __future__ import annotations

from app.models.enregistrement import Enregistrement
from app.services import applicabilite as ap


def _enr(at, source="CE", **kw):
    return Enregistrement("F", "R", source, depose_le=at, **kw)


def test_r15_na_puis_applicable_donne_applicable():
    enrs = [
        _enr("2026-01-01", codes_na=["2014/35/UE"]),
        _enr("2026-01-02", codes_applicables=["2014/35/UE"]),
    ]
    assert ap.etat_exigence(enrs, "2014/35/UE") == ap.APPLICABLE
    assert ap.etat_exigence(enrs[:1], "2014/35/UE") == ap.NA
    assert ap.etat_exigence(enrs, "2006/42/UE") == ap.NON_DEFINI


def test_r15_un_document_rend_l_exigence_applicable():
    enrs = [
        _enr("2026-01-02", codes_couverts=["2006/42/UE"]),
        _enr("2026-01-01", codes_na=["2006/42/UE"]),
    ]
    assert ap.etat_exigence(enrs, "2006/42/UE") == ap.APPLICABLE


def test_r16_code_ecrit_avec_son_libelle():
    assert ap.normaliser_code("1907/2006 | REACh") == "1907/2006"
    assert ap.codes_egaux("1907/2006 — REACh", "1907/2006")


def test_r14_alias_rohs():
    assert ap.codes_egaux("2015/863", "2011/65/UE")
    assert ap.est_rohs("2011/65/UE — RoHS") and ap.est_rohs("2015/863")
    assert not ap.est_rohs("2006/42/UE")


def test_r14_document_rohs_vaut_pour_ce_et_dpe():
    rohs = _enr("x", source="DPE", codes_couverts=["2011/65/UE — RoHS"])
    assert ap.vaut_pour_livrable(rohs, "CE") and ap.vaut_pour_livrable(rohs, "DPE")
    assert not ap.vaut_pour_livrable(rohs, "CECC")
    reach = _enr("x", source="DPE", codes_couverts=["1907/2006"])
    assert not ap.vaut_pour_livrable(reach, "CE")
    range_ce = _enr("x", source="DPE", livrables_rangement=["DPE", "CE"])
    assert ap.vaut_pour_livrable(range_ce, "ce")


def test_r18_estimation_reperee_au_nom_du_fichier():
    assert ap.est_estimation(_enr("x", nom_stocke="CE_A_R_Estimation.pdf"))
    assert not ap.est_estimation(_enr("x", nom_stocke="CE_A_R.pdf"))


def test_statut_cecc_lu_dans_l_ancienne_cle():
    assert ap.statut_cecc({"status": "Estimation"}) == "Estimation"
    assert ap.statut_cecc({"cecc_etat": "Validé", "status": "Relancé"}) == "Validé"
    assert ap.statut_cecc(None) == ""
