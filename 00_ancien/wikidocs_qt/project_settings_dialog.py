from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .document_rules import JUSTIFICATION_TYPES


class ProjectSettingsDialog(QtWidgets.QDialog):
    settingsSaved = QtCore.Signal(dict)

    def __init__(self, project_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramétrage du projet")
        self.resize(760, 560)
        self.project_data = project_data
        self._build_ui()
        self._load_from_project()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)

        livrables_group = QtWidgets.QGroupBox("Livrables actifs", self)
        livrables_layout = QtWidgets.QHBoxLayout(livrables_group)
        self.livrable_checks = {}
        for livrable in JUSTIFICATION_TYPES:
            cb = QtWidgets.QCheckBox(livrable, self)
            self.livrable_checks[livrable] = cb
            livrables_layout.addWidget(cb)
        livrables_layout.addStretch(1)
        root.addWidget(livrables_group)

        rows_group = QtWidgets.QGroupBox("Lignes du projet", self)
        rows_layout = QtWidgets.QVBoxLayout(rows_group)

        self.table = QtWidgets.QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Fournisseur", "Référence", "MNP"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        rows_layout.addWidget(self.table, 1)

        bulk_group = QtWidgets.QGroupBox("Ajouter plusieurs lignes", self)
        bulk_layout = QtWidgets.QHBoxLayout(bulk_group)

        suppliers_group = QtWidgets.QGroupBox("Fournisseurs", self)
        suppliers_layout = QtWidgets.QVBoxLayout(suppliers_group)
        self.suppliers_edit = QtWidgets.QPlainTextEdit(self)
        self.suppliers_edit.setPlaceholderText(
            "Une ligne par fournisseur\n\n"
            "Ex.:\n"
            "MILTIADE\n"
            "ATELIERS POLY-MECA\n"
            "CROME"
        )
        suppliers_layout.addWidget(self.suppliers_edit)

        references_group = QtWidgets.QGroupBox("Références", self)
        references_layout = QtWidgets.QVBoxLayout(references_group)
        self.references_edit = QtWidgets.QPlainTextEdit(self)
        self.references_edit.setPlaceholderText(
            "Une ligne par référence\n\n"
            "Ex.:\n"
            "46847343AA00\n"
            "56271640AA00\n"
            "56271307AA00"
        )
        references_layout.addWidget(self.references_edit)

        mnp_group = QtWidgets.QGroupBox("MNP", self)
        mnp_layout = QtWidgets.QVBoxLayout(mnp_group)
        self.mnp_edit = QtWidgets.QPlainTextEdit(self)
        self.mnp_edit.setPlaceholderText(
            "Une ligne par MNP\n\n"
            "Ex.:\n"
            "MNP-001\n"
            "MNP-002\n"
            "MNP-003"
        )
        mnp_layout.addWidget(self.mnp_edit)

        bulk_layout.addWidget(suppliers_group, 1)
        bulk_layout.addWidget(references_group, 1)
        bulk_layout.addWidget(mnp_group, 1)

        rows_layout.addWidget(bulk_group)

        actions = QtWidgets.QHBoxLayout()
        self.bulk_add_button = QtWidgets.QPushButton("Ajouter à l'existant", self)
        self.delete_button = QtWidgets.QPushButton("Supprimer la sélection", self)

        self.bulk_add_button.clicked.connect(self._add_rows_from_inputs)
        self.delete_button.clicked.connect(self._delete_selected_rows)

        actions.addWidget(self.bulk_add_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        rows_layout.addLayout(actions)

        root.addWidget(rows_group, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Annuler", self)
        save_btn = QtWidgets.QPushButton("Enregistrer", self)
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        root.addLayout(buttons)

    def _load_from_project(self):
        enabled = set(self.project_data.get("enabled_bdds", JUSTIFICATION_TYPES))
        for livrable, cb in self.livrable_checks.items():
            cb.setChecked(livrable in enabled)

        for row in self.project_data.get("rows", []):
            self._append_table_row(
                row.get("supplier", ""),
                row.get("reference", ""),
                row.get("mnp", ""),
            )

    def _append_table_row(self, supplier: str, reference: str, mnp: str = ""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(supplier))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(reference))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(mnp))

    def _parse_bulk_rows(self) -> list[tuple[str, str, str]]:
        suppliers = [
            line.strip()
            for line in self.suppliers_edit.toPlainText().splitlines()
            if line.strip()
        ]

        references = [
            line.strip()
            for line in self.references_edit.toPlainText().splitlines()
            if line.strip()
        ]

        mnps = [
            line.strip()
            for line in self.mnp_edit.toPlainText().splitlines()
            if line.strip()
        ]

        max_len = max(len(suppliers), len(references), len(mnps), 0)
        rows: list[tuple[str, str, str]] = []

        for i in range(max_len):
            supplier = suppliers[i] if i < len(suppliers) else ""
            reference = references[i] if i < len(references) else ""
            mnp = mnps[i] if i < len(mnps) else ""

            if supplier:
                rows.append((supplier, reference, mnp))

        return rows

    def _add_rows_from_inputs(self):
        suppliers = [
            line.strip()
            for line in self.suppliers_edit.toPlainText().splitlines()
            if line.strip()
        ]

        references = [
            line.strip()
            for line in self.references_edit.toPlainText().splitlines()
            if line.strip()
        ]

        if not suppliers:
            QtWidgets.QMessageBox.information(
                self,
                "Ajout",
                "Ajoute au moins un fournisseur pour créer des lignes."
            )
            return

        if references and len(suppliers) != len(references):
            QtWidgets.QMessageBox.warning(
                self,
                "Ajout",
                "Le nombre de fournisseurs et de références ne correspond pas."
            )
            return

        rows = self._parse_bulk_rows()

        existing = set()
        for row in range(self.table.rowCount()):
            supplier = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            reference = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            if supplier:
                existing.add((supplier, reference))

        added_count = 0
        for supplier, reference, mnp in rows:
            key = (supplier, reference)
            if key in existing:
                continue
            existing.add(key)
            self._append_table_row(supplier, reference, mnp)
            added_count += 1

        self.suppliers_edit.clear()
        self.references_edit.clear()
        self.mnp_edit.clear()

        QtWidgets.QMessageBox.information(
            self,
            "Ajout",
            f"{added_count} ligne(s) ajoutée(s) au projet."
        )
    
    def _delete_selected_rows(self):
        selected_rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)

        if not selected_rows:
            QtWidgets.QMessageBox.information(self, "Suppression", "Sélectionne au moins une ligne.")
            return

        answer = QtWidgets.QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer {len(selected_rows)} ligne(s) sélectionnée(s) ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return

        for row in selected_rows:
            self.table.removeRow(row)

    def _collect_rows(self) -> list[dict]:
        rows = []
        seen = set()

        for row in range(self.table.rowCount()):
            supplier = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            reference = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            mnp = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""

            if not supplier:
                continue

            key = (supplier, reference)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "supplier": supplier,
                "reference": reference,
                "mnp": mnp,
            })

        return rows

    def _collect_enabled_bdds(self) -> list[str]:
        return [name for name, cb in self.livrable_checks.items() if cb.isChecked()]

    def _save(self):
        rows = self._collect_rows()
        enabled_bdds = self._collect_enabled_bdds()

        if not enabled_bdds:
            QtWidgets.QMessageBox.warning(self, "Paramétrage", "Sélectionne au moins un livrable.")
            return

        self.settingsSaved.emit({
            "rows": rows,
            "enabled_bdds": enabled_bdds,
        })
        self.accept()