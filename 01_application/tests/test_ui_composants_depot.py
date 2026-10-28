"""Tâche 17 : composants du dépôt (R10, R14), hors écran."""

from __future__ import annotations

import pytest
from PySide6 import QtWidgets

from app.services import applicabilite as ap
from app.ui.composants_depot import CEPage, DPEPage, ThreeStateToggle


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _ligne(page, code):
    return next(r for r in page._req_rows if ap.codes_egaux(r.code, code))


def test_bascule_trois_etats(app):
    bascule = ThreeStateToggle()
    assert bascule.is_undefined()
    bascule.set_state(ap.APPLICABLE, animated=False)
    assert bascule.is_applicable() and bascule.get_state() == 2
    bascule.set_state(ap.NA, animated=False)
    assert bascule.is_not_applicable()


def test_r14_rohs_synchronisee_en_ce(app):
    page = CEPage()
    _ligne(page, "2011/65/UE").set_state(ap.APPLICABLE)
    assert _ligne(page, "2015/863").is_applicable()
    _ligne(page, "2015/863").set_row_checked(True)
    assert _ligne(page, "2011/65/UE").is_row_checked()
    _ligne(page, "2015/863").set_state(ap.NA)
    assert _ligne(page, "2011/65/UE").is_not_applicable()


def test_r10_pages_et_compteurs(app):
    ce, dpe = CEPage(), DPEPage()
    assert [r.code for r in ce._req_rows][:3] == ["2006/42/UE", "2014/35/UE", "2011/65/UE"]
    assert len(dpe._req_rows) == 12
    assert len(ce.unknown_applicability_requirements()) == 6
    _ligne(dpe, "1907/2006").set_state(ap.APPLICABLE)
    _ligne(dpe, "1907/2006").set_row_checked(True)
    # R16 : la page DPE enregistre le code avec son libellé.
    assert dpe.checked_applicable_requirements()[0] == ["1907/2006 — REACh"]
    assert dpe.applicable_count() == 1
