"""Tâche 24 : E14, protection contre les enregistrements simultanés (décision 0004)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from PySide6 import QtWidgets

from app.dataaccess import projet_fichier
from app.dataaccess import verrou as fichier_verrou
from app.services import verrou
from app.ui.tableau_de_suivi import FenetreSuivi

MOI = ("moi", "PC-1")
COLLEGUE = ("collegue", "PC-2")


def test_e14_le_premier_tient_le_projet(tmp_path):
    assert verrou.prendre(tmp_path, MOI) is None
    autre = verrou.prendre(tmp_path, COLLEGUE)
    assert (autre.utilisateur, autre.poste) == MOI
    assert verrou.message_lecture_seule(autre).startswith(
        "Projet ouvert en modification par moi sur le poste PC-1 depuis le "
    )


def test_e14_mon_propre_verrou_ne_me_bloque_pas(tmp_path):
    assert verrou.prendre(tmp_path, MOI) is None
    assert verrou.prendre(tmp_path, MOI) is None


def test_e14_liberation_a_la_fermeture(tmp_path):
    verrou.prendre(tmp_path, MOI)
    verrou.rendre(tmp_path, COLLEGUE)  # pas le sien : sans effet
    assert verrou.prendre(tmp_path, COLLEGUE) is not None
    verrou.rendre(tmp_path, MOI)
    assert verrou.prendre(tmp_path, COLLEGUE) is None


def test_e14_verrou_abandonne_apres_15_minutes(tmp_path):
    verrou.prendre(tmp_path, MOI)
    v = fichier_verrou.lire(tmp_path)
    v.rafraichi = (datetime.now() - timedelta(minutes=16)).isoformat()
    fichier_verrou.ecrire(tmp_path, v)
    assert verrou.prendre(tmp_path, COLLEGUE) is None
    assert fichier_verrou.lire(tmp_path).utilisateur == "collegue"


def test_e14_signe_de_vie(tmp_path):
    verrou.prendre(tmp_path, MOI)
    v = fichier_verrou.lire(tmp_path)
    v.rafraichi = (datetime.now() - timedelta(minutes=14)).isoformat()
    fichier_verrou.ecrire(tmp_path, v)
    verrou.rafraichir(tmp_path, MOI)
    v = fichier_verrou.lire(tmp_path)
    v.rafraichi = (datetime.fromisoformat(v.rafraichi) - timedelta(minutes=2)).isoformat()
    fichier_verrou.ecrire(tmp_path, v)
    assert verrou.prendre(tmp_path, COLLEGUE) is not None


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_e14_lecture_seule_dans_le_tableau(app, projet_essai):
    verrou.prendre(projet_essai, COLLEGUE)
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    assert fenetre.lecture_seule
    assert fenetre.windowTitle() == "NOX_Manager — N999 — lecture seule"
    assert fenetre._boutons_modification
    assert not any(b.isEnabled() for b in fenetre._boutons_modification)
    ligne = fenetre._toutes_les_lignes[0]
    fenetre._sur_ligne_selectionnee(ligne)
    assert not fenetre.detail_panel._btn_delete.isEnabled()
    fenetre.close()
    # Fermer en lecture seule ne libère pas le verrou du collègue.
    assert fichier_verrou.lire(projet_essai).utilisateur == "collegue"


def test_e14_ouverture_normale_puis_liberation(app, projet_essai):
    fenetre = FenetreSuivi(projet_fichier.lire_projet(projet_essai))
    assert not fenetre.lecture_seule
    assert fichier_verrou.lire(projet_essai) is not None
    fenetre.close()
    assert fichier_verrou.lire(projet_essai) is None
