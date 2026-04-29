from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .document_rules import JUSTIFICATION_TYPES


LEGACY_PROJECT_FILE = ".nox_project.json"
PROJECT_META_DIRNAME = ".nox"
PROJECT_FILE = "project.json"
APP_STATE_FILE = "nox_state.json"


def get_project_hidden_dir(project_dir: Path) -> Path:
    hidden_dir = project_dir / PROJECT_META_DIRNAME
    hidden_dir.mkdir(parents=True, exist_ok=True)
    return hidden_dir


def get_project_file_path(project_dir: Path) -> Path:
    return get_project_hidden_dir(project_dir) / PROJECT_FILE


def _normalize_rows(rows):
    normalized = []
    seen = set()

    for row in rows or []:
        if isinstance(row, dict):
            supplier = str(row.get("supplier", "")).strip()
            reference = str(row.get("reference", "")).strip()
            label = str(row.get("label", "")).strip()
            mnp = str(row.get("mnp", "")).strip()
            order_number = str(row.get("order_number", "")).strip()
        else:
            supplier = str(row[0]).strip()
            reference = str(row[1]).strip()
            label = ""
            mnp = ""
            order_number = ""

        if not supplier or not reference:
            continue

        key = (supplier, reference)
        if key in seen:
            continue

        seen.add(key)

        normalized.append({
            "supplier": supplier,
            "reference": reference,
            "label": label,
            "mnp": mnp,
            "order_number": order_number,
        })

    return normalized


def _normalize_enabled_bdds(enabled_bdds):
    values = [str(v).strip().upper() for v in (enabled_bdds or JUSTIFICATION_TYPES)]
    ordered = [bdd for bdd in JUSTIFICATION_TYPES if bdd in values]
    return ordered or list(JUSTIFICATION_TYPES)


class ProjectManager:
    def __init__(self):
        self.app_data_dir = Path.home() / ".nox_manager"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.app_data_dir / APP_STATE_FILE

    def _default_state(self) -> dict:
        return {
            "recent_projects": [],
            "recent_locations": [],
            "default_location": "",
        }

    def _load_state(self) -> dict:
        if not self.state_file.exists():
            return self._default_state()
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return self._default_state()

    def _save_state(self, state: dict) -> None:
        self.state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_recent_project(self, name: str, path: Path) -> None:
        state = self._load_state()
        path_str = str(path.resolve())

        projects = [p for p in state["recent_projects"] if p.get("path") != path_str]
        projects.insert(
            0,
            {
                "name": name,
                "path": path_str,
                "last_opened": datetime.now().isoformat(),
            },
        )
        state["recent_projects"] = projects[:10]
        self._save_state(state)

    def get_recent_projects(self) -> list[dict]:
        return self._load_state().get("recent_projects", [])
    
    def remove_recent_project(self, path: str | Path) -> None:
        state = self._load_state()
        path_str = str(Path(path).resolve())

        state["recent_projects"] = [
            project for project in state.get("recent_projects", [])
            if str(Path(project.get("path", "")).resolve()) != path_str
        ]

        self._save_state(state)

    def add_recent_location(self, path: Path) -> None:
        state = self._load_state()
        path_str = str(path.resolve())

        locations = [p for p in state["recent_locations"] if p != path_str]
        locations.insert(0, path_str)

        state["recent_locations"] = locations[:10]
        state["default_location"] = path_str
        self._save_state(state)

    def get_recent_locations(self) -> list[str]:
        return self._load_state().get("recent_locations", [])

    def get_default_location(self) -> str:
        return self._load_state().get("default_location", "")

    def create_project_file(
        self,
        project_dir: Path,
        project_name: str,
        dossier_number: str,
        date_code: str,
        rows=None,
        enabled_bdds=None,
    ) -> Path:
        project_dir.mkdir(parents=True, exist_ok=True)

        project_file = get_project_file_path(project_dir)
        data = {
            "project_name": project_name,
            "project_path": str(project_dir.resolve()),
            "dossier_number": dossier_number,
            "date_code": date_code,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "project_meta_dir": PROJECT_META_DIRNAME,
            "project_file_version": 3,
            "rows": _normalize_rows(rows or []),
            "enabled_bdds": _normalize_enabled_bdds(enabled_bdds),
        }

        project_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        legacy_file = project_dir / LEGACY_PROJECT_FILE
        if legacy_file.exists():
            try:
                legacy_file.unlink()
            except Exception:
                pass

        self.add_recent_project(project_name, project_dir)
        self.add_recent_location(project_dir.parent)

        return project_file

    def save_project(self, project_dir: Path, data: dict) -> Path:
        existing = self.load_project(project_dir) or {}
        merged = dict(existing)
        merged.update(data)

        merged["project_path"] = str(project_dir.resolve())
        merged["rows"] = _normalize_rows(merged.get("rows", []))
        merged["enabled_bdds"] = _normalize_enabled_bdds(merged.get("enabled_bdds"))
        merged["updated_at"] = datetime.now().isoformat()
        merged["project_file_version"] = max(int(existing.get("project_file_version", 2)), 3)

        project_file = get_project_file_path(project_dir)
        project_file.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return project_file

    def load_project(self, project_dir: Path) -> Optional[dict]:
        candidates = [
            get_project_file_path(project_dir),
            project_dir / LEGACY_PROJECT_FILE,
        ]

        for project_file in candidates:
            if not project_file.exists():
                continue
            try:
                data = json.loads(project_file.read_text(encoding="utf-8"))

                if "project_path" not in data:
                    data["project_path"] = str(project_dir.resolve())

                if "rows" not in data:
                    data["rows"] = []
                else:
                    data["rows"] = _normalize_rows(data["rows"])

                if "enabled_bdds" not in data:
                    data["enabled_bdds"] = list(JUSTIFICATION_TYPES)
                else:
                    data["enabled_bdds"] = _normalize_enabled_bdds(data["enabled_bdds"])

                if "project_file_version" not in data:
                    data["project_file_version"] = 3

                return data
            except Exception:
                continue

        return None