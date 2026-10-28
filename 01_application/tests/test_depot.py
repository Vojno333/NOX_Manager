"""Tâche 12 : dépôt d'un justificatif (R7 à R14), scénarios S7 à S16."""

from __future__ import annotations

from app.dataaccess import base_projet, projet_fichier
from app.models.depot import APPLICABILITE, SaisieDepot
from app.models.referentiel import EXIGENCES_CE
from app.services import applicabilite as ap
from app.services import completion, depot

CE = [c for c, _ in EXIGENCES_CE]
LIVRABLES = ["CE", "CECC", "DPE"]


def _ce(projet, cibles, fichier=None, coches=(), na=(), non_definis=(), **kw):
    etats = {
        c: ap.NA if c in na else ap.NON_DEFINI if c in non_definis else ap.APPLICABLE for c in CE
    }
    return SaisieDepot(projet, "CE", cibles, fichier=fichier, etats=etats, coches=set(coches), **kw)


def _fichier(tmp_path, nom="rapport.pdf"):
    f = tmp_path / nom
    f.write_bytes(b"%PDF")
    return f


def _completion(projet, f, r, livrable):
    lignes = completion.lignes_de_suivi(projet_fichier.lire_projet(projet))
    return next(
        ligne.completion_texte
        for ligne in lignes
        if (ligne.fournisseur, ligne.reference, ligne.livrable) == (f, r, livrable)
    )


def test_e2_formats_etendus(projet_essai, tmp_path):
    for nom in (
        "a.PDF",
        "b.doc",
        "c.xlsm",
        "d.csv",
        "e.pptx",
        "f.JPG",
        "g.tiff",
        "h.msg",
        "i.zip",
        "j.txt",
    ):
        assert depot.format_accepte(tmp_path / nom), nom
    for nom in ("a.exe", "b.html", "c", "d.7z"):
        assert not depot.format_accepte(tmp_path / nom), nom
    saisie = _ce(
        projet_essai, [("ACME", "REF-001")], _fichier(tmp_path, "virus.exe"), ["2006/42/UE"]
    )
    assert depot.verifier(saisie, LIVRABLES) == (
        "Format de fichier non accepté. Formats acceptés : PDF, Word, Excel, PowerPoint, "
        "Photos, Mails, Archives, Texte."
    )
    saisie.fichier = _fichier(tmp_path, "photo.png")
    assert depot.verifier(saisie, LIVRABLES) is None


def test_s8_s16_selection(projet_essai):
    assert depot.verifier_selection(["CE", "DPE"])[1] == (
        "La sélection multiple doit contenir un seul type de justificatif."
    )
    assert depot.verifier_selection(["CECC"], APPLICABILITE)[1].startswith(
        "La gestion de l'applicabilité n'est pas disponible pour les justificatifs CECC."
    )
    assert depot.verifier_selection(["CE", "ce"]) is None


def test_r9_livrable_non_suivi(projet_essai, tmp_path):
    saisie = _ce(projet_essai, [("ACME", "REF-001")])
    assert depot.verifier(saisie, ["DPE"]) == "Le livrable CE n'est pas activé sur ce projet."


def test_s9_r10_exigence_non_definie(projet_essai, tmp_path):
    saisie = _ce(
        projet_essai, [("ACME", "REF-001")], _fichier(tmp_path), ["2006/42/UE"], non_definis=CE[3:5]
    )
    assert depot.verifier(saisie, LIVRABLES) == (
        "2 exigence(s) sont encore «Non défini(es)». Veuillez indiquer «Applicable» ou "
        "«N/A» pour chacune avant d'importer ce document."
    )


def test_s10_r11_applicabilite_seule(projet_essai):
    saisie = _ce(projet_essai, [("DELTA", "REF-030")], na=CE)
    assert depot.verifier(saisie, LIVRABLES) is None and depot.applicabilite_seule(saisie)
    avant = len(base_projet.lire_tous(projet_essai))
    assert depot.enregistrer(saisie) == 1
    enrs = base_projet.lire_tous(projet_essai)
    assert len(enrs) == avant + 1
    assert not any(p.is_file() for p in (projet_essai / "BDD CE N999/Documents/DELTA").rglob("*"))
    assert _completion(projet_essai, "DELTA", "REF-030", "CE") == "100 %"
    assert depot.message_de_fin(saisie, 1)[0] == "Applicabilité enregistrée"


def test_s11_r12_fiche_cecc(projet_essai, tmp_path):
    fichier = _fichier(tmp_path, "cecc.pdf")
    saisie = SaisieDepot(
        projet_essai,
        "CECC",
        [("ACME", "REF-001")],
        fichier=fichier,
        champs_cecc={"manufacturer_doc": "ACME", "manufacturer_part_number": ""},
    )
    assert depot.verifier(saisie, LIVRABLES) == (
        "Pour un justificatif CECC, renseignez au minimum Fournisseur Doc, "
        "Manufacturer Part Number et Nom : CECC."
    )
    saisie.champs_cecc["manufacturer_part_number"] = "MPN-1"
    assert depot.verifier(saisie, LIVRABLES) is None  # nom CECC vide accepté (C7)
    depot.enregistrer(saisie)
    fiche = base_projet.derniere_fiche_cecc(projet_essai, "ACME", "REF-001")
    assert fiche["nom_cecc"] == "cecc.pdf"
    assert (projet_essai / "BDD CECC N999/Documents/ACME/REF-001/CECC_ACME_REF-001.pdf").is_file()
    saisie.fichier = None
    assert depot.verifier(saisie, LIVRABLES) == "Merci de choisir un fichier."


def test_s12_r12_fiche_pre_remplie(projet_essai):
    fiche = depot.fiche_cecc_initiale(projet_essai, "GAMMA", "REF-020")
    assert fiche["cecc_etat"] == "Validé" and fiche["manufacturer_part_number"] == "MPN-GAMMA"


def test_s13_r13_nom_automatique_et_collision(projet_essai, tmp_path):
    fichier = _fichier(tmp_path)
    saisie = _ce(projet_essai, [("ACME", "REF-001")], fichier, ["2006/42/UE"])
    assert depot.verifier(saisie, LIVRABLES) is None
    depot.enregistrer(saisie)
    depot.enregistrer(saisie)
    dossier = projet_essai / "BDD CE N999/Documents/ACME/REF-001"
    assert (dossier / "CE_ACME_REF-001 (1).pdf").is_file()
    assert (dossier / "CE_ACME_REF-001 (2).pdf").is_file()
    assert fichier.is_file()
    assert depot.message_de_fin(saisie, 1) == (
        "Import terminé",
        "Les modifications ont été appliquées à 1 ligne(s).",
    )


def test_e3_extension_toujours_conservee(projet_essai, tmp_path):
    saisie = _ce(
        projet_essai,
        [("ACME", "REF-001")],
        _fichier(tmp_path),
        ["2006/42/UE"],
        nom_saisi="Rapport v1.2",
    )
    assert depot.nom_final(saisie, "ACME", "REF-001") == "Rapport v1.2.pdf"
    saisie.nom_saisi = "Rapport"
    assert depot.nom_final(saisie, "ACME", "REF-001") == "Rapport.pdf"
    saisie.nom_saisi = "Rapport.PDF"
    assert depot.nom_final(saisie, "ACME", "REF-001") == "Rapport.PDF"
    saisie.nom_saisi = "Rapport.docx"
    assert depot.nom_final(saisie, "ACME", "REF-001") == "Rapport.docx.pdf"
    assert depot.nom_automatique("CE", "A B", "R/1") == "CE_A_B_R_1"


def test_s15_r14_rohs_range_dans_ce_et_dpe(projet_essai, tmp_path):
    saisie = _ce(
        projet_essai, [("ACME", "REF-002")], _fichier(tmp_path), ["2011/65/UE", "2015/863"]
    )
    assert depot.livrables_concernes(saisie, LIVRABLES) == ["CE", "DPE"]
    depot.enregistrer(saisie)
    for t in ("CE", "DPE"):
        assert (projet_essai / f"BDD {t} N999/Documents/ACME/REF-002/CE_ACME_REF-002.pdf").is_file()
    nouveaux = [e for e in base_projet.lire_tous(projet_essai) if e.nom_original == "rapport.pdf"]
    assert len(nouveaux) == 2 and all(e.livrables_rangement == ["CE", "DPE"] for e in nouveaux)
    enrs_dpe = [e for e in base_projet.lire_tous(projet_essai) if ap.vaut_pour_livrable(e, "DPE")]
    acme = [e for e in enrs_dpe if e.reference == "REF-002"]
    assert ap.etat_exigence(acme, "2011/65/UE") == ap.APPLICABLE


def test_etats_existants(projet_essai):
    etats = depot.etats_existants(projet_essai, "ACME", "REF-001", "CE", CE)
    assert etats["2006/42/UE"] == ap.APPLICABLE and etats["2014/35/UE"] == ap.NA
    assert depot.etats_existants(projet_essai, "DELTA", "REF-030", "CE", CE) is None


def test_e4_premiere_fiche_cecc_pre_remplie_par_l_article(projet_essai):
    assert depot.fiche_cecc_initiale(projet_essai, "ACME", "REF-001") == {
        "manufacturer_doc": "ACME",
        "manufacturer_part_number": "MNP-001",
    }
    # EPS / REF-040 a déjà une fiche : c'est elle qui est reprise.
    assert depot.fiche_cecc_initiale(projet_essai, "EPS", "REF-040")[
        "manufacturer_part_number"
    ] == ("MPN-EPS")
