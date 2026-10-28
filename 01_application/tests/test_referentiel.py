"""Tâche 1 : ressources livrées et référentiels métier."""

from __future__ import annotations

import pytest

from app.core.config import ressource
from app.models import referentiel as ref


@pytest.mark.parametrize(
    "nom",
    [
        "Template_BDD_CE_N0X.xlsx",
        "Template_BDD_CECC_N0X.xlsx",
        "Template_BDD_DPE_N0X.xlsx",
        "LOGO_Nox.ico",
        "flash.png",
        "eu_icon.svg",
        "dpe_icon.svg",
    ],
)
def test_ressources_presentes(nom):
    assert ressource(nom).stat().st_size > 0


def test_ressource_absente():
    with pytest.raises(FileNotFoundError):
        ressource("absente.xlsx")


def test_chaque_exigence_a_sa_colonne():
    assert [c for c, _ in ref.EXIGENCES_CE] == [c for c in ref.COLONNES_CE if c != "AUTRES"]
    assert [c for c, _ in ref.EXIGENCES_DPE] == list(ref.COLONNES_DPE)
    for colonnes in (ref.COLONNES_CE, ref.COLONNES_DPE):
        assert len(set(colonnes.values())) == len(colonnes)


def test_rohs_alias_et_commun_aux_deux_livrables():
    assert ref.ALIAS_CODES["2015/863"] == ref.CODE_ROHS == "2011/65/UE"
    assert ref.CODE_ROHS in ref.COLONNES_CE and ref.CODE_ROHS in ref.COLONNES_DPE
    assert (ref.COLONNES_CE["2011/65/UE"], ref.COLONNES_CE["2015/863"]) == ("J", "K")


def test_les_5_statuts_officiels():
    assert ref.STATUTS_CECC == ("A demander", "Demandé", "Relancé", "Non conforme", "Validé")
    assert ref.STATUT_VALIDE in ref.STATUTS_CECC
    assert ref.STATUT_ESTIMATION not in ref.STATUTS_CECC


def test_champs_cecc_colonnes_g_a_s():
    assert [col for _, _, col in ref.CHAMPS_CECC] == list("GHIJKLMNOPQRS")
    cles = {cle for cle, _, _ in ref.CHAMPS_CECC}
    assert set(ref.ANCIENNES_CLES_CECC) <= cles


def test_pays_au_format_code_libelle():
    assert len(ref.PAYS_ORIGINE_4A) == 74
    assert all(p[2] == "-" and p[:2].isupper() for p in ref.PAYS_ORIGINE_4A)
