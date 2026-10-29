"""Une ligne du tableau de suivi : un article pour un livrable."""

from __future__ import annotations

from dataclasses import dataclass, field

from .enregistrement import Enregistrement


@dataclass
class LigneSuivi:
    fournisseur: str
    reference: str
    libelle: str
    n_commande: str
    mnp: str
    livrable: str
    completion: float  # de 0 à 1
    enregistrements: list[Enregistrement] = field(default_factory=list)
    id_ligne: str = ""  # E1 : ligne de l'article (lignes multiples activées)

    @property
    def completion_texte(self) -> str:
        return f"{round(self.completion * 100)} %"

    @property
    def nb_documents(self) -> int:
        return len(self.enregistrements)

    def valeur(self, colonne: str) -> str:
        """Texte d'une colonne filtrable : fournisseur, reference, libelle, livrable, completion."""
        if colonne == "completion":
            return self.completion_texte
        return str(getattr(self, colonne, ""))
