"""Fenêtre de filtre d'une colonne du tableau de suivi (cases à cocher, recherche).

Reprise de `00_ancien/wikidocs_qt/filter_popup.py`.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.ui.geometrie import ajuster_et_centrer


class FilterPopup(QtWidgets.QDialog):
    def __init__(
        self, title: str, values: list[str], checked_values: set[str] | None = None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        ajuster_et_centrer(self, 320, 420, largeur_min=260, hauteur_min=320)

        self.all_values = list(dict.fromkeys(values))
        self.checked_values = set(checked_values or self.all_values)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.search_edit = QtWidgets.QLineEdit(self)
        self.search_edit.setPlaceholderText("Rechercher...")
        self.search_edit.textChanged.connect(self._refresh_list)
        layout.addWidget(self.search_edit)

        top_buttons = QtWidgets.QHBoxLayout()
        self.check_all_btn = QtWidgets.QPushButton("Tout cocher", self)
        self.uncheck_all_btn = QtWidgets.QPushButton("Tout décocher", self)
        self.check_all_btn.clicked.connect(self._check_all_visible)
        self.uncheck_all_btn.clicked.connect(self._uncheck_all_visible)
        top_buttons.addWidget(self.check_all_btn)
        top_buttons.addWidget(self.uncheck_all_btn)
        layout.addLayout(top_buttons)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)

        self.ok_button = QtWidgets.QPushButton("OK", self)
        self.cancel_button = QtWidgets.QPushButton("Annuler", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self._refresh_list()

    def _filtered_values(self) -> list[str]:
        text = self.search_edit.text().strip().lower()
        if not text:
            return self.all_values
        return [v for v in self.all_values if text in v.lower()]

    def _refresh_list(self):
        text = self.search_edit.text().strip()
        filtered = self._filtered_values()

        if text:
            # Comportement Excel : taper du texte sélectionne automatiquement
            # exactement les résultats trouvés (et seulement eux) — comme dans
            # la liste déroulante de filtre d'Excel, la recherche remplace la
            # sélection plutôt que de la préserver en arrière-plan.
            self.checked_values = set(filtered)

        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        for value in filtered:
            item = QtWidgets.QListWidgetItem(value)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(
                QtCore.Qt.Checked if value in self.checked_values else QtCore.Qt.Unchecked
            )
            self.list_widget.addItem(item)

        self.list_widget.blockSignals(False)

    def _on_item_changed(self, item: QtWidgets.QListWidgetItem):
        if item.checkState() == QtCore.Qt.Checked:
            self.checked_values.add(item.text())
        else:
            self.checked_values.discard(item.text())

    def _check_all_visible(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(QtCore.Qt.Checked)

    def _uncheck_all_visible(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(QtCore.Qt.Unchecked)

    def get_checked_values(self) -> set[str]:
        return set(self.checked_values)
