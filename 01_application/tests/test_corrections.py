"""Tâche 13 : corrections (R21, R22, R23), scénarios S17 à S21."""

from __future__ import annotations

from datetime import datetime

from app.dataaccess import base_projet, projet_fichier
from app.models.depot import SaisieDepot
from app.models.referentiel import EXIGENCES_CE
from app.services import applicabilite as ap
from app.services import completion, corrections, depot

CE_ACME = "BDD CE N999/Documents/ACME/REF-001/CE_ACME_REF-001.pdf"


def _completion(projet, f, r, livrable):
    lignes = completion.lignes_de_suivi(projet_fichier.lire_projet(projet))
    return next(
        ligne
        for ligne in lignes
        if (ligne.fournisseur, ligne.reference, ligne.livrable) == (f, r, livrable)
    )


def _retirer(projet, f, r, livrable, code):
    docs = corrections.documents_justifiant(projet, f, r, livrable, code)
    return docs, corrections.retirer_exigences(projet, docs, [code])


def test_s17_s18_r21_retirer_le_justificatif_d_une_exigence(projet_essai):
    docs, (supprimes, erreurs) = _retirer(projet_essai, "ACME", "REF-001", "CE", "2014/30/UE")
    assert len(docs) == 1 and supprimes == [] and erreurs == []
    assert (projet_essai / CE_ACME).is_file()
    ligne = _completion(projet_essai, "ACME", "REF-001", "CE")
    assert ligne.completion_texte == "33 %"
    assert ap.etat_exigence(ligne.enregistrements, "2014/30/UE") == ap.APPLICABLE

    _, (supprimes, _) = _retirer(projet_essai, "ACME", "REF-001", "CE", "2006/42/UE")
    assert supprimes == ["CE_ACME_REF-001.pdf"]
    assert not (projet_essai / CE_ACME).exists()
    assert _completion(projet_essai, "ACME", "REF-001", "CE").completion_texte == "0 %"


def test_s19_r21_retirer_rohs_retire_des_deux_cotes(projet_essai):
    docs = corrections.documents_justifiant(projet_essai, "BETA", "REF-010", "CE", "2011/65/UE")
    message = corrections.message_retrait("BETA", "REF-010", "2011/65/UE", docs)
    assert message.endswith("RoHS est commun au CE et au DPE : le retrait s'applique aux deux.")
    corrections.retirer_exigences(projet_essai, docs, ["2011/65/UE"])
    for t in ("CE", "DPE"):
        ligne = _completion(projet_essai, "BETA", "REF-010", t)
        assert not any(e.a_un_fichier for e in ligne.enregistrements if ap.couvre(e, "2011/65/UE"))
    assert not (projet_essai / "BDD DPE N999/Documents/BETA/REF-010/DPE_BETA_REF-010.pdf").exists()


def _remplacer(projet, tmp_path, coches, selection):
    debut = datetime.now().isoformat()
    nouveau = tmp_path / "nouveau.pdf"
    nouveau.write_bytes(b"%PDF")
    etats = {c: ap.APPLICABLE for c, _ in EXIGENCES_CE}
    saisie = SaisieDepot(
        projet, "CE", [("ACME", "REF-001")], fichier=nouveau, etats=etats, coches=set(coches)
    )
    depot.enregistrer(saisie)
    return corrections.remplacer_apres_depot(projet, "ACME", "REF-001", debut, selection), debut


def _ancien_acme(projet, debut):
    anciens = [e for e in base_projet.lire_tous(projet) if e.depose_le < debut]
    return next(e for e in anciens if e.reference == "REF-001")


def test_e6_remplacement_limite_a_l_exigence_selectionnee(projet_essai, tmp_path):
    # Nouveau document couvrant Machine et CEM, remplacement demandé pour Machine seule.
    (supprimes, _), debut = _remplacer(
        projet_essai, tmp_path, {"2006/42/UE", "2014/30/UE"}, ["2006/42/UE"]
    )
    assert supprimes == []
    ancien = _ancien_acme(projet_essai, debut)
    assert ancien.codes_couverts == ["2014/30/UE"] and ancien.a_un_fichier
    assert (projet_essai / CE_ACME).is_file()


def test_e6_plusieurs_exigences_selectionnees(projet_essai, tmp_path):
    selection = ["2006/42/UE", "2014/30/UE"]
    assert corrections.message_remplacement(selection).startswith(
        "Le nouveau document remplacera l'ancien pour les 2 exigences sélectionnées"
    )
    assert corrections.message_remplacement(["2006/42/UE"]) is None
    (supprimes, _), debut = _remplacer(projet_essai, tmp_path, set(selection), selection)
    assert supprimes == ["CE_ACME_REF-001.pdf"]
    assert not _ancien_acme(projet_essai, debut).a_un_fichier


def test_e6_exigence_selectionnee_mais_non_couverte_par_le_nouveau(projet_essai, tmp_path):
    (supprimes, _), debut = _remplacer(projet_essai, tmp_path, {"2006/42/UE"}, ["2014/30/UE"])
    assert supprimes == []
    ancien = _ancien_acme(projet_essai, debut)
    assert ancien.codes_couverts == ["2006/42/UE", "2014/30/UE"]


BETA_CE = "BDD CE N999/Documents/BETA/REF-010/DPE_BETA_REF-010.pdf"
BETA_DPE = "BDD DPE N999/Documents/BETA/REF-010/DPE_BETA_REF-010.pdf"


def test_e7_vider_en_ce_retire_aussi_le_rohs_du_dpe(projet_essai):
    plan = corrections.preparer_vidage(projet_essai, "N999", "BETA", "REF-010", "CE")
    assert [f.name for f in plan.fichiers] == ["DPE_BETA_REF-010.pdf"]
    message = plan.message_confirmation()
    assert message.startswith("Supprimer les informations CE de BETA / REF-010 ?")
    assert "• 1 fichier(s) du dossier « BDD CE N999 » :\n• DPE_BETA_REF-010.pdf" in message
    assert "son justificatif rangé dans « BDD DPE N999 » est aussi retiré" in message
    assert corrections.vider(projet_essai, plan) == []
    assert not (projet_essai / BETA_CE).exists() and not (projet_essai / BETA_DPE).exists()
    # Plus rien ne justifie RoHS, ni en CE ni en DPE.
    for t in ("CE", "DPE"):
        ligne = _completion(projet_essai, "BETA", "REF-010", t)
        assert not any(e.a_un_fichier for e in ligne.enregistrements)
    dpe = _completion(projet_essai, "BETA", "REF-010", "DPE")
    assert dpe.completion_texte == "0 %"
    # L'applicabilité du DPE est conservée : RoHS et REACh restent applicables.
    assert ap.etat_exigence(dpe.enregistrements, "1907/2006") == ap.APPLICABLE
    assert ap.etat_exigence(dpe.enregistrements, "2011/65/UE") == ap.APPLICABLE


def test_e7_vider_en_dpe_retire_aussi_le_rohs_du_ce(projet_essai):
    plan = corrections.preparer_vidage(projet_essai, "N999", "BETA", "REF-010", "DPE")
    assert [e.chemin_relatif for e in plan.rohs_autre] == [BETA_CE]
    corrections.vider(projet_essai, plan)
    assert not (projet_essai / BETA_CE).exists()
    assert _completion(projet_essai, "BETA", "REF-010", "CE").completion_texte == "0 %"


def test_e7_sans_rohs_dans_l_autre_livrable_rien_n_est_signale(projet_essai):
    plan = corrections.preparer_vidage(projet_essai, "N999", "ACME", "REF-001", "CE")
    assert plan.rohs_autre == [] and "RoHS est commun" not in plan.message_confirmation()


def test_r23_rien_a_vider(projet_essai):
    plan = corrections.preparer_vidage(projet_essai, "N999", "DELTA", "REF-030", "CECC")
    assert plan.vide
    assert plan.message_rien() == "Aucune information ni aucun document CECC pour DELTA / REF-030."


def test_e7_copie_saisie_depuis_ce_livrable_retiree_aussi(projet_essai, tmp_path):
    fichier = tmp_path / "r.pdf"
    fichier.write_bytes(b"%PDF")
    etats = {c: ap.APPLICABLE for c, _ in EXIGENCES_CE}
    depot.enregistrer(
        SaisieDepot(
            projet_essai,
            "CE",
            [("ACME", "REF-002")],
            fichier=fichier,
            etats=etats,
            coches={"2011/65/UE", "2015/863", "2006/42/UE"},
        )
    )
    plan = corrections.preparer_vidage(projet_essai, "N999", "ACME", "REF-002", "CE")
    (copie_dpe,) = plan.a_reduire
    assert copie_dpe.chemin_relatif.startswith("BDD DPE")
    corrections.vider(projet_essai, plan)
    (copie,) = [e for e in base_projet.lire_tous(projet_essai) if e.id == copie_dpe.id]
    assert copie.codes_couverts == [] and not copie.a_un_fichier
    assert not (projet_essai / copie_dpe.chemin_relatif).exists()
