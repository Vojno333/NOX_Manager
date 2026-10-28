"""Panneau de détail d'un article : exigences et documents, ouverture d'un
document, clic droit Ouvrir / Remplacer / Supprimer, boutons Modifier et
Supprimer la référence.

Repris de `00_ancien/wikidocs_qt/project_dashboard_window.py` (`DetailPanel`).
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.models.suivi import LigneSuivi
from app.ui.elements_suivi import (
    ALT_ROW,
    BLUE,
    BLUE_DARK,
    BLUE_LIGHT,
    DARK,
    F_BODY,
    F_BOLD,
    F_H1,
    F_SMALL,
    GRAY_BORDER,
    GRAY_CARD,
    GRAY_LIGHT,
    GRAY_TEXT,
    GREEN_OK,
    RED_BG,
    RED_KO,
    TYPE_COLORS,
    WHITE,
    TypeBadge,
    _completion_badge,
    _hline,
    _make_label,
)


class DetailPanel(QtWidgets.QFrame):
    requestModify = QtCore.Signal(object)  # LigneSuivi
    requestDelete = QtCore.Signal(object)  # LigneSuivi
    requestOpenDoc = QtCore.Signal(str)  # emits file path
    requestReplaceJustif = QtCore.Signal(object, str)  # LigneSuivi, code
    requestDeleteJustif = QtCore.Signal(object, str)  # LigneSuivi, code

    _CODE_ROLE = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(360)
        self.resize(500, self.height())
        self.setStyleSheet(f"""
            DetailPanel {{
                background:{WHITE};
                border:1px solid {GRAY_CARD};
                border-radius:12px;
            }}
        """)
        self._row_data: LigneSuivi | None = None
        self._nb_docs = 0
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._hdr = QtWidgets.QWidget()
        self._hdr.setStyleSheet(f"background:{WHITE}; border-radius:12px 12px 0 0;")
        hdr_lay = QtWidgets.QVBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(16, 14, 16, 12)
        hdr_lay.setSpacing(4)

        title_row = QtWidgets.QHBoxLayout()
        title_row.setSpacing(8)
        self._lbl_title = _make_label("—", F_H1, DARK)
        self._lbl_title.setWordWrap(True)
        title_row.addWidget(self._lbl_title, 1)
        self._badge = TypeBadge("CE")
        self._badge.hide()
        title_row.addWidget(self._badge)
        hdr_lay.addLayout(title_row)

        self._lbl_sub = _make_label("", F_SMALL, GRAY_TEXT)
        hdr_lay.addWidget(self._lbl_sub)
        root.addWidget(self._hdr)
        root.addWidget(_hline())

        # Scroll body
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent;")
        body_w = QtWidgets.QWidget()
        body_w.setStyleSheet("background:transparent;")
        self._body = QtWidgets.QVBoxLayout(body_w)
        self._body.setContentsMargins(16, 12, 16, 12)
        self._body.setSpacing(12)
        scroll.setWidget(body_w)
        root.addWidget(scroll, 1)

        # Sections (created once, shown/hidden per selection)
        self._lbl_docs_title = _make_label("Documents liés", F_BOLD, DARK)
        self._body.addWidget(self._lbl_docs_title)

        self._tbl_docs = self._make_doc_table()
        self._body.addWidget(self._tbl_docs, 1)

        self._body.addWidget(_hline())

        self._lbl_info_title = _make_label("Informations", F_BOLD, DARK)
        self._body.addWidget(self._lbl_info_title)

        self._info_widget = QtWidgets.QWidget()
        self._info_widget.setStyleSheet("background:transparent;")
        self._info_lay = QtWidgets.QVBoxLayout(self._info_widget)
        self._info_lay.setContentsMargins(0, 0, 0, 0)
        self._info_lay.setSpacing(4)
        self._body.addWidget(self._info_widget)

        # Footer buttons
        root.addWidget(_hline())
        footer = QtWidgets.QWidget()
        footer.setStyleSheet(f"background:{WHITE}; border-radius:0 0 12px 12px;")
        footer_lay = QtWidgets.QVBoxLayout(footer)
        footer_lay.setContentsMargins(14, 10, 14, 12)
        footer_lay.setSpacing(6)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_modify = QtWidgets.QPushButton("✏   Modifier la référence")
        self._btn_modify.setFont(F_BOLD)
        self._btn_modify.setCursor(Qt.PointingHandCursor)
        self._btn_modify.setFixedHeight(34)
        self._btn_modify.setStyleSheet(f"""
            QPushButton {{
                background:{BLUE}; color:{WHITE};
                border:none; border-radius:8px; padding:0 12px; font-size:8pt;
            }}
            QPushButton:hover {{ background:{BLUE_DARK}; }}
        """)
        self._btn_modify.clicked.connect(self._on_modify)

        self._btn_view = QtWidgets.QPushButton("📄  Voir les documents (0)")
        self._btn_view.setFont(F_BODY)
        self._btn_view.setCursor(Qt.PointingHandCursor)
        self._btn_view.setFixedHeight(34)
        self._btn_view.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE}; color:{DARK};
                border:1px solid {GRAY_BORDER}; border-radius:8px; padding:0 10px; font-size:8pt;
            }}
            QPushButton:hover {{ background:{GRAY_LIGHT}; }}
        """)
        btn_row.addWidget(self._btn_modify, 1)
        btn_row.addWidget(self._btn_view, 1)
        footer_lay.addLayout(btn_row)

        self._btn_delete = QtWidgets.QPushButton("🗑   Supprimer la référence")
        self._btn_delete.setToolTip(
            "Supprime les informations et les documents de cette référence "
            "pour la BDD affichée uniquement (CE, DPE ou CECC)"
        )
        self._btn_delete.setFont(F_BODY)
        self._btn_delete.setCursor(Qt.PointingHandCursor)
        self._btn_delete.setFixedHeight(34)
        self._btn_delete.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE}; color:{RED_KO};
                border:1px solid #FCA5A5; border-radius:8px; padding:0 12px; font-size:8pt;
            }}
            QPushButton:hover {{ background:{RED_BG}; }}
        """)
        self._btn_delete.clicked.connect(self._on_delete)
        footer_lay.addWidget(self._btn_delete)
        root.addWidget(footer)

    def _reset_doc_table(self):
        rows = self._tbl_docs.rowCount()
        cols = self._tbl_docs.columnCount()

        for r in range(rows):
            for c in range(cols):
                self._tbl_docs.removeCellWidget(r, c)

        self._tbl_docs.clearContents()
        self._tbl_docs.setRowCount(0)

    def _make_doc_table(self) -> QtWidgets.QTableWidget:
        t = QtWidgets.QTableWidget(0, 3)
        t.setHorizontalHeaderLabels(["Exigence", "Applicabilité", "Nom du document"])
        t.horizontalHeader().setFont(F_BOLD)
        t.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        t.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        t.setColumnWidth(1, 115)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        t.setSelectionMode(QtWidgets.QTableWidget.NoSelection)
        t.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        t.setMinimumHeight(300)
        t.setStyleSheet(f"""
            QTableWidget {{
                border:1px solid {GRAY_BORDER}; border-radius:8px;
                font-size:8pt; background:{WHITE};
                alternate-background-color:{ALT_ROW};
            }}
            QHeaderView::section {{
                background:{GRAY_LIGHT}; color:{GRAY_TEXT};
                border:none; border-bottom:1px solid {GRAY_BORDER};
                padding:5px 6px; font-weight:700; font-size:8pt;
            }}
            QTableWidget::item {{ padding:4px 6px; color:{DARK}; }}
        """)
        t.cellClicked.connect(self._on_doc_clicked)
        t.setContextMenuPolicy(Qt.CustomContextMenu)
        t.customContextMenuRequested.connect(self._on_doc_context_menu)
        return t

    # ── Public API ────────────────────────────────────────────────────────────
    def clear(self):
        self._row_data = None
        self._lbl_title.setText("Sélectionne une ligne")
        self._lbl_sub.setText("")
        self._badge.hide()
        self._tbl_docs.setRowCount(0)
        self._clear_info()
        self._btn_modify.setEnabled(False)
        self._btn_view.setEnabled(False)
        self._btn_delete.setEnabled(False)

    def populate(self, row_data: LigneSuivi, detail_rows: list[dict]):
        self._row_data = row_data
        supplier = row_data.fournisseur
        reference = row_data.reference
        jtype = row_data.livrable
        docs = row_data.enregistrements
        self._nb_docs = len(docs)

        # Header
        self._lbl_title.setText(f"{supplier}  –  {reference}")
        self._badge.setText(jtype)
        bg, fg = TYPE_COLORS.get(jtype, ("#F1F5F9", "#374151"))
        self._badge.setStyleSheet(f"""
            background:{bg}; color:{fg};
            border-radius:10px; padding:2px 10px;
            font-size:9pt; font-weight:700;
        """)
        self._badge.show()
        self._lbl_sub.setText(f"Type : {jtype}    ·    {self._nb_docs} document(s) enregistré(s)")

        # Documents liés table
        self._reset_doc_table()
        is_cecc = jtype == "CECC"
        if is_cecc:
            self._tbl_docs.setColumnCount(2)
            self._tbl_docs.setHorizontalHeaderLabels(["Champ", "Valeur"])
            self._tbl_docs.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        else:
            self._tbl_docs.setColumnCount(3)
            self._tbl_docs.setHorizontalHeaderLabels(
                ["Exigence", "Applicabilité", "Nom du document"]
            )
            self._tbl_docs.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
            self._tbl_docs.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            self._tbl_docs.setColumnWidth(1, 115)

        self._tbl_docs.setRowCount(len(detail_rows))
        for i, detail in enumerate(detail_rows):
            applicability = str(detail.get("applicability", "Applicable"))
            req_item = QtWidgets.QTableWidgetItem(str(detail.get("requirement", "")))
            req_item.setData(Qt.UserRole, detail.get("path", ""))
            self._tbl_docs.setItem(i, 0, req_item)

            if not is_cecc:
                app_label = QtWidgets.QLabel(applicability)
                app_label.setAlignment(Qt.AlignCenter)
                app_label.setStyleSheet("background:transparent; font-weight:700;")

                if applicability == "Applicable":
                    app_label.setStyleSheet(
                        f"color:{GREEN_OK}; background:transparent; font-weight:700;"
                    )
                elif applicability == "Non applicable":
                    app_label.setStyleSheet(
                        f"color:{GRAY_TEXT}; background:transparent; font-weight:700;"
                    )
                else:
                    app_label.setStyleSheet(
                        f"color:{RED_KO}; background:transparent; font-weight:700;"
                    )

                self._tbl_docs.setCellWidget(i, 1, app_label)
                doc_col = 2
            else:
                doc_col = 1

            filename = str(detail.get("filename", "") or "")
            file_item = QtWidgets.QTableWidgetItem(filename)
            if filename:
                file_item.setForeground(QColor(BLUE))
                font = file_item.font()
                font.setUnderline(True)
                file_item.setFont(font)
                file_item.setToolTip(
                    "Cliquer pour ouvrir"
                    if is_cecc
                    else "Cliquer pour ouvrir · clic droit pour remplacer ou supprimer"
                )
            file_item.setData(Qt.UserRole, detail.get("path", ""))
            file_item.setData(self._CODE_ROLE, detail.get("code", ""))
            self._tbl_docs.setItem(i, doc_col, file_item)

        self._tbl_docs.resizeRowsToContents()

        # Informations section
        self._clear_info()
        pct_str = row_data.completion_texte
        try:
            pct_val = int(str(pct_str).replace("%", "").replace(" ", ""))
        except ValueError:
            pct_val = -1

        info_items = [
            ("👤", "Fournisseur", supplier),
            ("📋", "Référence", reference),
            ("📦", "Type", jtype),
            ("📄", "Nb de documents", str(self._nb_docs)),
            ("✅", "Complétude", pct_str),
        ]
        for icon, label, value in info_items:
            row_w = QtWidgets.QWidget()
            row_w.setStyleSheet("background:transparent;")
            row_h = QtWidgets.QHBoxLayout(row_w)
            row_h.setContentsMargins(0, 0, 0, 0)
            row_h.setSpacing(6)

            icon_lbl = _make_label(icon, F_BODY, GRAY_TEXT)
            icon_lbl.setFixedWidth(16)
            label_lbl = _make_label(label, F_SMALL, GRAY_TEXT)
            label_lbl.setFixedWidth(110)

            if label == "Complétude" and pct_val >= 0:
                val_w = _completion_badge(pct_str)
            else:
                val_w = _make_label(value, F_SMALL, DARK)

            row_h.addWidget(icon_lbl)
            row_h.addWidget(label_lbl)
            row_h.addWidget(val_w)
            row_h.addStretch(1)
            self._info_lay.addWidget(row_w)

        # Buttons
        self._btn_view.setText(f"📄  Voir les documents ({self._nb_docs})")
        self._btn_modify.setEnabled(True)
        self._btn_view.setEnabled(True)
        self._btn_delete.setEnabled(True)

    def _clear_info(self):
        while self._info_lay.count():
            item = self._info_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_doc_clicked(self, row: int, col: int):
        doc_col = 1 if self._tbl_docs.columnCount() == 2 else 2
        if col != doc_col:
            return
        item = self._tbl_docs.item(row, doc_col)
        if item:
            path = item.data(Qt.UserRole)
            if path:
                self.requestOpenDoc.emit(str(path))

    def _on_doc_context_menu(self, pos: QtCore.QPoint):
        """Clic droit sur un nom de document (CE / DPE uniquement)."""
        if not self._row_data or self._tbl_docs.columnCount() != 3:
            return
        index = self._tbl_docs.indexAt(pos)
        if not index.isValid() or index.column() != 2:
            return
        item = self._tbl_docs.item(index.row(), 2)
        if not item or not item.text():
            return
        path = str(item.data(Qt.UserRole) or "")
        code = str(item.data(self._CODE_ROLE) or "")
        if not code:
            return

        menu = QtWidgets.QMenu(self._tbl_docs)
        # Fond explicite : sinon le menu hérite du « background:transparent »
        # du panneau et s'affiche sur fond noir.
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setFont(F_BODY)
        menu.setStyleSheet(f"""
            QMenu {{
                background:{WHITE}; color:{DARK};
                border:1px solid {GRAY_CARD}; border-radius:8px;
                padding:4px;
            }}
            QMenu::item {{
                background:transparent; color:{DARK};
                padding:7px 18px 7px 12px; border-radius:6px;
            }}
            QMenu::item:selected {{ background:{BLUE_LIGHT}; color:{BLUE}; }}
            QMenu::item:disabled {{ color:{GRAY_TEXT}; }}
            QMenu::separator {{ height:1px; background:{GRAY_BORDER}; margin:4px 6px; }}
        """)
        row_data = self._row_data
        act_open = menu.addAction("Ouvrir le document")
        act_open.setEnabled(bool(path))
        act_open.triggered.connect(lambda: self.requestOpenDoc.emit(path))
        menu.addAction("Remplacer le justificatif…").triggered.connect(
            lambda: self.requestReplaceJustif.emit(row_data, code)
        )
        menu.addSeparator()

        # Action destructive en rouge : QMenu::item ne permet pas de styler
        # une action précise, d'où un QLabel dans un QWidgetAction.
        delete_lbl = QtWidgets.QLabel("Supprimer le justificatif")
        delete_lbl.setFont(F_BODY)
        delete_lbl.setStyleSheet(f"""
            QLabel {{
                color:{RED_KO}; background:transparent;
                padding:7px 18px 7px 12px; border-radius:6px;
            }}
            QLabel:hover {{ background:{RED_BG}; }}
        """)
        act_delete = QtWidgets.QWidgetAction(menu)
        act_delete.setDefaultWidget(delete_lbl)
        act_delete.triggered.connect(lambda: self.requestDeleteJustif.emit(row_data, code))
        menu.addAction(act_delete)

        def _on_delete_clicked(_event):
            menu.close()
            # Après la fermeture du menu : la confirmation est modale.
            QtCore.QTimer.singleShot(0, act_delete.trigger)

        delete_lbl.mouseReleaseEvent = _on_delete_clicked

        menu.exec(self._tbl_docs.viewport().mapToGlobal(pos))

    def _on_modify(self):
        if self._row_data:
            self.requestModify.emit(self._row_data)

    def _on_delete(self):
        if self._row_data:
            self.requestDelete.emit(self._row_data)
