#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import  unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from docx import Document 




def norm_text(s: str) -> str:
    """Normalisation légère (NFKC, ligatures/soft hyphen, trim, lower)."""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u00ad", "")
    s = s.replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = " ".join(s.split())
    return s.lower()

def norm_rel(rel: str) -> str:
    """Chemin relatif POSIX sans slash de tête (unifie \\ /)."""
    return (rel or "").replace("\\", "/").lstrip("/")


def human_size(n: int) -> str:
    """Format lisible des tailles (o/Ko/Mo/Go/To)."""
    size = float(n or 0)
    for u in ["o", "Ko", "Mo", "Go", "To"]:
        if size < 1024 or u == "To":
            return f"{int(size)} {u}" if u == "o" else f"{size:.1f} {u}"
        size /= 1024.0


def fmt_dt(ts: float | int | None) -> str:
    """Format timestamp -> 'JJ/MM/AAAA HH:MM' (ou '—')."""
    if not ts:
        return "—"
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


def norm_no_diacritics(s: str) -> str:
    """Normalise (NFKC→NFD) + supprime diacritiques/ligatures + lower (pour matching insensible aux accents)."""
    import unicodedata
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u00ad", "").replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = " ".join(s.split())
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()


def search_rects_with_words(page, query: str):
    """Renvoie des rectangles de mots correspondant à 'query' (normalisée) +  Utilisé pour simuler un surlignage côté rendu PDF."""
    qn = norm_text(query)
    if not qn:
        return []
    words = page.get_text("words") or []
    words.sort(key=lambda w: (round(w[1], 1), w[0]))
    rects = []
    i = 0
    while i < len(words):
        x0,y0,x1,y1, w = words[i]
        buf = norm_text(w)
        if not buf:
            i += 1; continue
        j = i
        x0_all, y0_all, x1_all, y1_all = x0,y0,x1,y1
        while j+1 < len(words) and len(buf) < len(qn) and qn.startswith(buf):
            x0n,y0n,x1n,y1n, wn = words[j+1]
            wn_norm = norm_text(wn)
            if not wn_norm:
                j += 1; continue
            raw_prev = words[j][4] if len(words[j]) >= 5 else ""
            if isinstance(raw_prev, str) and raw_prev.endswith("-"):
                candidate = buf[:-1] + wn_norm
            else:
                candidate = buf + " " + wn_norm
            candidate = " ".join(candidate.split())
            if qn.startswith(candidate):
                buf = candidate
                x0_all = min(x0_all, x0n); y0_all = min(y0_all, y0n)
                x1_all = max(x1_all, x1n); y1_all = max(y1_all, y1n)
                j += 1
            else:
                break
        if buf == qn:
            rects.append((x0_all, y0_all, x1_all, y1_all))
            i = j + 1
        else:
            i += 1
    return rects

