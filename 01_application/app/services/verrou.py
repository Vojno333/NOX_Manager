"""Protection contre les enregistrements simultanés (E14, décision 0004).

La première personne qui ouvre un projet le tient en modification ; les
suivantes l'ouvrent en lecture seule. Un verrou sans signe de vie depuis
`verrou_peremption_minutes` est considéré comme abandonné (poste planté).
"""

from __future__ import annotations

import getpass
import socket
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import reglages
from app.dataaccess import verrou as fichier_verrou
from app.models.verrou import Verrou


def moi() -> tuple[str, str]:
    """(utilisateur Windows, poste)."""
    try:
        utilisateur = getpass.getuser()
    except Exception:  # aucun nom disponible
        utilisateur = "Utilisateur"
    return utilisateur, socket.gethostname()


def rafraichissement_ms() -> int:
    return int(reglages()["verrou_rafraichissement_minutes"]) * 60 * 1000


def _abandonne(v: Verrou, maintenant: datetime) -> bool:
    peremption = timedelta(minutes=int(reglages()["verrou_peremption_minutes"]))
    try:
        return maintenant - datetime.fromisoformat(v.rafraichi) > peremption
    except ValueError:
        return True


def prendre(dossier: Path, qui: tuple[str, str] | None = None) -> Verrou | None:
    """Tente de prendre le projet en modification.

    Retourne None si c'est fait (ou si le verrou était déjà le nôtre), sinon le
    verrou de la personne qui tient le projet : il faut l'ouvrir en lecture seule.
    """
    utilisateur, poste = qui or moi()
    maintenant = datetime.now()
    nouveau = Verrou(utilisateur, poste, maintenant.isoformat(), maintenant.isoformat())
    if fichier_verrou.creer(dossier, nouveau):
        return None
    actuel = fichier_verrou.lire(dossier)
    if actuel and (actuel.utilisateur, actuel.poste) == (utilisateur, poste):
        fichier_verrou.ecrire(dossier, nouveau)
        return None
    if actuel is None or _abandonne(actuel, maintenant):
        fichier_verrou.ecrire(dossier, nouveau)
        return None
    return actuel


def rafraichir(dossier: Path, qui: tuple[str, str] | None = None) -> None:
    """Signe de vie, seulement si le verrou est toujours le nôtre."""
    utilisateur, poste = qui or moi()
    actuel = fichier_verrou.lire(dossier)
    if actuel and (actuel.utilisateur, actuel.poste) == (utilisateur, poste):
        actuel.rafraichi = datetime.now().isoformat()
        fichier_verrou.ecrire(dossier, actuel)


def rendre(dossier: Path, qui: tuple[str, str] | None = None) -> None:
    """Libère le projet, seulement si le verrou est le nôtre."""
    utilisateur, poste = qui or moi()
    actuel = fichier_verrou.lire(dossier)
    if actuel and (actuel.utilisateur, actuel.poste) == (utilisateur, poste):
        fichier_verrou.supprimer(dossier)


def message_lecture_seule(v: Verrou) -> str:
    try:
        heure = datetime.fromisoformat(v.depuis).strftime("%d/%m/%Y à %H:%M")
    except ValueError:
        heure = v.depuis
    return (
        f"Projet ouvert en modification par {v.utilisateur} sur le poste {v.poste} "
        f"depuis le {heure}.\n\nVous l'ouvrez en lecture seule : vous pouvez consulter, "
        "ouvrir les documents et exporter, mais pas modifier."
    )
