# home_mockup.py
from __future__ import annotations

import sys
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt


BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
BLUE_LIGHT = "#EFF6FF"
BORDER = "#E5EAF3"
TEXT = "#0F172A"
MUTED = "#64748B"
BG = "#F8FAFC"
WHITE = "#FFFFFF"
RED = "#EF4444"


class IconLabel(QtWidgets.QLabel):
    def __init__(self, emoji: str, size: int = 18):
        super().__init__(emoji)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(28, 28)
        self.setStyleSheet(f"""
            QLabel {{
                background: {BLUE_LIGHT};
                border-radius: 8px;
                font-size: {size}px;
            }}
        """)


class SideButton(QtWidgets.QPushButton):
    def __init__(self, text: str, icon: str = "", active: bool = False):
        super().__init__(f"{icon}   {text}")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 18px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                color: {BLUE if active else "#475569"};
                background: {BLUE_LIGHT if active else "transparent"};
            }}
            QPushButton:hover {{
                background: {BLUE_LIGHT};
                color: {BLUE};
            }}
        """)


class ProjectCard(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, title, path, date, docs, refs, selected=False):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(135)

        self.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border: 1px solid {BLUE if selected else BORDER};
                border-radius: 12px;
            }}
        """)

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)

        folder = QtWidgets.QLabel("📁")
        folder.setAlignment(Qt.AlignCenter)
        folder.setFixedSize(62, 62)
        folder.setStyleSheet(f"""
            QLabel {{
                background: {BLUE_LIGHT};
                border-radius: 10px;
                font-size: 30px;
            }}
        """)
        root.addWidget(folder)

        content = QtWidgets.QVBoxLayout()
        content.setSpacing(10)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"font-size: 19px; font-weight: 700; color: {TEXT}; border: none;")
        path_label = QtWidgets.QLabel(path)
        path_label.setStyleSheet(f"font-size: 13px; color: {MUTED}; border: none;")

        content.addWidget(title_label)
        content.addWidget(path_label)

        stats = QtWidgets.QHBoxLayout()
        stats.setSpacing(28)

        stats.addWidget(self.stat("📅", "Dernière ouverture", date))
        stats.addWidget(self.stat("📁", "Documents", str(docs)))
        stats.addWidget(self.stat("📄", "Références", str(refs)))
        stats.addStretch()

        content.addLayout(stats)
        root.addLayout(content, 1)

        actions = QtWidgets.QVBoxLayout()
        actions.setSpacing(14)

        top = QtWidgets.QHBoxLayout()
        star = QtWidgets.QLabel("☆")
        menu = QtWidgets.QLabel("⋮")
        for w in (star, menu):
            w.setAlignment(Qt.AlignCenter)
            w.setStyleSheet(f"font-size: 22px; color: {MUTED}; border: none;")
        top.addWidget(star)
        top.addWidget(menu)

        open_btn = QtWidgets.QPushButton("Ouvrir   ↪")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setFixedSize(115, 44)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE if selected else WHITE};
                color: {WHITE if selected else BLUE};
                border: 1px solid {BLUE if selected else BORDER};
                border-radius: 9px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BLUE_DARK};
                color: white;
            }}
        """)

        actions.addLayout(top)
        actions.addStretch()
        actions.addWidget(open_btn)

        root.addLayout(actions)

    def stat(self, icon, label, value):
        box = QtWidgets.QHBoxLayout()
        box.setSpacing(8)

        ic = QtWidgets.QLabel(icon)
        ic.setStyleSheet("font-size: 18px; border: none;")

        texts = QtWidgets.QVBoxLayout()
        l1 = QtWidgets.QLabel(label)
        l2 = QtWidgets.QLabel(value)
        l1.setStyleSheet(f"font-size: 11px; color: {MUTED}; border: none;")
        l2.setStyleSheet(f"font-size: 13px; color: {TEXT}; border: none;")

        texts.addWidget(l1)
        texts.addWidget(l2)

        box.addWidget(ic)
        box.addLayout(texts)

        wrapper = QtWidgets.QWidget()
        wrapper.setLayout(box)
        return wrapper


class HomeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NOX_Manager")
        self.resize(1680, 900)
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BG};
            }}
            QLabel {{
                color: {TEXT};
            }}
        """)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main = QtWidgets.QVBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self.header())

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(self.sidebar())
        body.addWidget(self.center_area(), 1)
        body.addWidget(self.right_panel())
        main.addLayout(body, 1)

    def header(self):
        frame = QtWidgets.QFrame()
        frame.setFixedHeight(105)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(24)

        logo = QtWidgets.QLabel("🛡️")
        logo.setFixedSize(28, 28)
        logo.setAlignment(Qt.AlignCenter)

        title = QtWidgets.QLabel("NOX_Manager")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {TEXT};")

        layout.addWidget(logo)
        layout.addWidget(title)

        search = QtWidgets.QLineEdit()
        search.setPlaceholderText("Rechercher par nom, numéro d'affaire ou emplacement...")
        search.setFixedHeight(46)
        search.setMinimumWidth(560)
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding-left: 42px;
                font-size: 14px;
                color: {TEXT};
            }}
        """)

        search_box = QtWidgets.QFrame()
        search_box.setFixedWidth(690)
        search_box.setStyleSheet("border: none;")
        search_layout = QtWidgets.QHBoxLayout(search_box)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_layout.addWidget(search)

        layout.addStretch()
        layout.addWidget(search_box)
        layout.addStretch()

        version = QtWidgets.QLabel("ⓘ  Version 1.1.0")
        version.setStyleSheet(f"font-size: 13px; color: {MUTED};")
        layout.addWidget(version)

        user_box = QtWidgets.QFrame()
        user_box.setFixedWidth(220)
        user_box.setStyleSheet(f"border-left: 1px solid {BORDER};")

        user_layout = QtWidgets.QHBoxLayout(user_box)
        user_layout.setContentsMargins(28, 0, 0, 0)

        avatar = QtWidgets.QLabel("V")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(42, 42)
        avatar.setStyleSheet("""
            QLabel {
                background: #4F46E5;
                color: white;
                border-radius: 21px;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        user_text = QtWidgets.QVBoxLayout()
        user_name = QtWidgets.QLabel("Utilisateur")
        user_login = QtWidgets.QLabel("vojnovic")
        user_name.setStyleSheet("font-weight: 700; font-size: 13px;")
        user_login.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        user_text.addWidget(user_name)
        user_text.addWidget(user_login)

        user_layout.addWidget(avatar)
        user_layout.addLayout(user_text)
        user_layout.addStretch()
        user_layout.addWidget(QtWidgets.QLabel("⌄"))

        layout.addWidget(user_box)
        return frame

    def sidebar(self):
        frame = QtWidgets.QFrame()
        frame.setFixedWidth(285)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border-right: 1px solid {BORDER};
            }}
        """)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)

        new_btn = QtWidgets.QPushButton("+   Nouveau projet")
        new_btn.setFixedHeight(54)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 700;
            }}
        """)

        open_btn = QtWidgets.QPushButton("📁   Ouvrir un projet")
        open_btn.setFixedHeight(54)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                text-align: left;
                padding-left: 52px;
            }}
        """)

        layout.addWidget(new_btn)
        layout.addWidget(open_btn)
        layout.addSpacing(20)

        layout.addWidget(SideButton("Projets récents", "◷", True))
        layout.addWidget(SideButton("Favoris", "☆"))
        layout.addWidget(SideButton("Tous les projets", "□"))

        self.separator(layout)

        layout.addWidget(SideButton("Actualiser", "⟳"))
        layout.addWidget(SideButton("Paramètres", "⚙"))

        layout.addStretch()

        tip = QtWidgets.QFrame()
        tip.setFixedHeight(125)
        tip.setStyleSheet(f"""
            QFrame {{
                background: #F8FBFF;
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)

        tip_layout = QtWidgets.QVBoxLayout(tip)
        tip_layout.setContentsMargins(18, 14, 18, 14)

        tip_title = QtWidgets.QLabel("💡  Astuce")
        tip_title.setStyleSheet(f"font-weight: 700; color: {BLUE}; font-size: 13px;")
        tip_text = QtWidgets.QLabel("Épinglez vos projets favoris\nen cliquant sur l’étoile ⭐\nsur une carte.")
        tip_text.setStyleSheet(f"color: {MUTED}; font-size: 12px; line-height: 1.4;")
        tip_layout.addWidget(tip_title)
        tip_layout.addWidget(tip_text)

        layout.addWidget(tip)

        self.separator(layout)

        layout.addWidget(SideButton("Réduire le menu", "‹"))

        return frame

    def separator(self, layout):
        line = QtWidgets.QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {BORDER};")
        layout.addSpacing(10)
        layout.addWidget(line)
        layout.addSpacing(10)

    def center_area(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(f"background: {BG}; border: none;")

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(40, 34, 34, 34)
        layout.setSpacing(20)

        top = QtWidgets.QHBoxLayout()

        titles = QtWidgets.QVBoxLayout()
        h1 = QtWidgets.QLabel("Projets récents")
        h1.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {TEXT};")
        sub = QtWidgets.QLabel("Accédez rapidement à vos projets récemment ouverts.")
        sub.setStyleSheet(f"font-size: 14px; color: {MUTED};")

        titles.addWidget(h1)
        titles.addWidget(sub)

        top.addLayout(titles)
        top.addStretch()

        view_btns = QtWidgets.QFrame()
        view_btns.setFixedSize(100, 46)
        view_btns.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)

        vb = QtWidgets.QHBoxLayout(view_btns)
        vb.setContentsMargins(10, 6, 10, 6)
        vb.addWidget(QtWidgets.QLabel("▦"))
        vb.addWidget(QtWidgets.QLabel("☷"))

        top.addWidget(view_btns)

        layout.addLayout(top)

        card1 = ProjectCard(
            "test",
            r"C:\Users\vojnovic\Documents\Test_Serveur\NOX_manager\test",
            "29/04/2026 11:13",
            128,
            42,
            True,
        )
        card2 = ProjectCard(
            "2026",
            r"C:\Users\vojnovic\Documents\Test_Serveur\NOX_manager\2026",
            "29/04/2026 10:58",
            87,
            31,
            False,
        )

        layout.addWidget(card1)
        layout.addWidget(card2)

        empty = QtWidgets.QFrame()
        empty.setFixedHeight(235)
        empty.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border: 1px dashed #CBD5E1;
                border-radius: 12px;
            }}
        """)

        empty_layout = QtWidgets.QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignCenter)

        ico = QtWidgets.QLabel("📂◷")
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet(f"font-size: 42px; color: {BLUE}; border: none;")

        t = QtWidgets.QLabel("Vous ne trouvez pas votre projet ?")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {TEXT}; border: none;")

        p = QtWidgets.QLabel("Ouvrez un projet existant ou créez-en un nouveau\npour commencer.")
        p.setAlignment(Qt.AlignCenter)
        p.setStyleSheet(f"font-size: 13px; color: {MUTED}; border: none;")

        b = QtWidgets.QPushButton("📁  Ouvrir un projet")
        b.setFixedSize(165, 42)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-weight: 600;
                color: {TEXT};
            }}
        """)

        empty_layout.addWidget(ico)
        empty_layout.addWidget(t)
        empty_layout.addWidget(p)
        empty_layout.addWidget(b)

        layout.addWidget(empty, alignment=Qt.AlignCenter)
        layout.addStretch()

        return frame

    def right_panel(self):
        frame = QtWidgets.QFrame()
        frame.setFixedWidth(445)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border-left: 1px solid {BORDER};
            }}
        """)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(30, 34, 30, 30)
        layout.setSpacing(24)

        title = QtWidgets.QLabel("Projet sélectionné")
        title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {TEXT};")
        layout.addWidget(title)

        header = QtWidgets.QHBoxLayout()

        folder = QtWidgets.QLabel("📁")
        folder.setFixedSize(96, 96)
        folder.setAlignment(Qt.AlignCenter)
        folder.setStyleSheet(f"""
            QLabel {{
                background: {BLUE_LIGHT};
                border-radius: 14px;
                font-size: 48px;
            }}
        """)

        infos = QtWidgets.QVBoxLayout()
        name = QtWidgets.QLabel("test")
        name.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {TEXT};")

        badge = QtWidgets.QLabel("◷ Projet récent")
        badge.setFixedWidth(110)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {BLUE_LIGHT};
                color: {BLUE};
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)

        infos.addStretch()
        infos.addWidget(name)
        infos.addWidget(badge)
        infos.addStretch()

        header.addWidget(folder)
        header.addSpacing(20)
        header.addLayout(infos)
        layout.addLayout(header)

        details = [
            ("💼", "Numéro d’affaire", "test"),
            ("📁", "Emplacement", r"C:\Users\vojnovic\Documents\Test_Serveur\NOX_manager\test"),
            ("📅", "Dernière ouverture", "29/04/2026 11:13"),
            ("📄", "Nombre de références", "42"),
            ("📁", "Nombre de documents", "128"),
            ("📅", "Créé le", "20/04/2026 09:15"),
        ]

        for icon, label, value in details:
            layout.addWidget(self.detail_row(icon, label, value))

        layout.addStretch()

        open_btn = QtWidgets.QPushButton("Ouvrir le projet   ↪")
        open_btn.setFixedHeight(54)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 9px;
                font-size: 15px;
                font-weight: 700;
            }}
        """)
        layout.addWidget(open_btn)

        delete_btn = QtWidgets.QPushButton("🗑  Supprimer de la liste")
        delete_btn.setFixedHeight(54)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                color: {RED};
                border: 1px solid #FCA5A5;
                border-radius: 9px;
                font-size: 15px;
                font-weight: 700;
            }}
        """)
        layout.addWidget(delete_btn)

        return frame

    def detail_row(self, icon, label, value):
        row = QtWidgets.QWidget()
        row.setStyleSheet("border: none;")

        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        ic = QtWidgets.QLabel(icon)
        ic.setFixedSize(30, 30)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"""
            QLabel {{
                background: #F8FAFC;
                border-radius: 6px;
                font-size: 15px;
            }}
        """)

        text = QtWidgets.QVBoxLayout()
        l1 = QtWidgets.QLabel(label)
        l1.setStyleSheet(f"font-size: 12px; color: {MUTED}; font-weight: 600;")
        l2 = QtWidgets.QLabel(value)
        l2.setWordWrap(True)
        l2.setStyleSheet(f"font-size: 13px; color: {TEXT};")

        text.addWidget(l1)
        text.addWidget(l2)

        layout.addWidget(ic)
        layout.addLayout(text)

        return row


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    font = QtGui.QFont("Segoe UI")
    app.setFont(font)

    window = HomeWindow()
    window.show()

    sys.exit(app.exec())