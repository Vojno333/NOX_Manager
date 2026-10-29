"""Verrou de modification d'un projet (E14)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Verrou:
    utilisateur: str
    poste: str
    depuis: str  # date ISO d'ouverture
    rafraichi: str  # date ISO du dernier signe de vie
