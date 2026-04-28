from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _safe_name(value: str) -> str:
    forbidden = '<>:"/\\|?*'
    cleaned = "".join("_" if c in forbidden else c for c in str(value).strip())
    return " ".join(cleaned.split())


def folder_exists(path: Path) -> bool:
    return path.exists() and path.is_dir()


def create_folders_and_subfolders(
    base_path: Path,
    rows: Iterable[tuple[str, str]]
) -> list[Path]:
    """
    Reproduit la logique de la macro VBA :
    - col 1 = dossier principal
    - col 2 = sous-dossier
    """
    created_paths: list[Path] = []

    base_path.mkdir(parents=True, exist_ok=True)

    for folder_name, subfolder_name in rows:
        folder_name = _safe_name(folder_name)
        subfolder_name = _safe_name(subfolder_name)

        if not folder_name:
            continue

        folder_path = base_path / folder_name
        if not folder_exists(folder_path):
            folder_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(folder_path)

        if subfolder_name:
            subfolder_path = folder_path / subfolder_name
            if not folder_exists(subfolder_path):
                subfolder_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(subfolder_path)

    return created_paths