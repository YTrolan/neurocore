"""Command palette — modal overlay."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                                QPushButton, QVBoxLayout, QWidget)

from .icons import make_icon
from .theme import C


class CommandPalette(QWidget):
    """Полноэкранный overlay с затемнением + центрированный popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setStyleSheet("background: rgba(0, 0, 0, 120);")
        self.hide()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 100, 0, 0)
        outer.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.popup = QFrame()
        self.popup.setObjectName("palettePopup")
        self.popup.setFixedWidth(600)
        self.popup.setStyleSheet(
            "QFrame#palettePopup { background: " + C["card"] +
            "; border: 1px solid " + C["border"] +
            "; border-radius: 14px; }")
        outer.addWidget(self.popup)

        pl = QVBoxLayout(self.popup)
        pl.setContentsMargins(14, 14, 14, 14)
        pl.setSpacing(8)

        row = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(make_icon("search", C["text_dim"], 16).pixmap(16, 16))
        ic.setFixedSize(24, 24)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(
            "background: transparent; border: none; padding: 0;")
        row.addWidget(ic)
        self.search = QLineEdit()
        self.search.setObjectName("paletteSearch")
        self.search.setPlaceholderText("Введи команду…")
        self.search.setStyleSheet(
            "QLineEdit#paletteSearch {"
            "  background: transparent;"
            "  border: none;"
            "  color: " + C["text"] + ";"
            "  font-size: 14px;"
            "  padding: 8px 4px;"
            "}"
            "QLineEdit#paletteSearch:hover,"
            "QLineEdit#paletteSearch:focus {"
            "  background: transparent;"
            "  border: none;"
            "}")
        row.addWidget(self.search, 1)
        pl.addLayout(row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: " + C["border_soft"] + ";")
        pl.addWidget(sep)

        self.results_wrap = QVBoxLayout()
        self.results_wrap.setSpacing(2)
        pl.addLayout(self.results_wrap)

        self._commands = []
        self.search.textChanged.connect(self._render)
        QShortcut(QKeySequence("Esc"), self, self.hide)
        QShortcut(QKeySequence("Return"), self.search, self._run_first)

    def set_commands(self, commands):
        self._commands = commands

    def mousePressEvent(self, event):
        """Клик вне попапа — закрыть."""
        if hasattr(self, "popup") and self.popup:
            g = self.popup.geometry()
            if not g.contains(event.pos()):
                self.hide()
                return
        super().mousePressEvent(event)

    def open(self):
        if self.parent():
            self.setGeometry(self.parent().rect())
        # сбросить возможные эффекты прозрачности
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        for w in (self, getattr(self, "popup", None)):
            if w is None:
                continue
            eff = w.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                eff.setOpacity(1.0)
        self.show()
        self.raise_()
        self.search.clear()
        self.search.setFocus()
        self._render("")

    def _render(self, q):
        while self.results_wrap.count():
            it = self.results_wrap.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        q = (q or "").lower()
        shown = 0
        for name, shortcut, cb in self._commands:
            if q and q not in name.lower():
                continue
            btn = QPushButton(
                "  " + name + ("      " + shortcut if shortcut else ""))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; "
                "color: " + C["text"] + "; text-align: left; "
                "padding: 6px 12px; border-radius: 6px; font-size: 13px; }"
                "QPushButton:hover { background: " + C["card_hover"] + "; }")
            btn.clicked.connect(
                lambda _=False, c=cb: (self.hide(), c()))
            self.results_wrap.addWidget(btn)
            shown += 1
            if shown >= 10:
                break

    def _run_first(self):
        for i in range(self.results_wrap.count()):
            w = self.results_wrap.itemAt(i).widget()
            if w:
                w.click()
                return
