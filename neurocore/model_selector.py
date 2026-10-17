"""Селектор модели: top-level прозрачное окно + вложенный QFrame."""
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .icons import make_icon
from .theme import C


class ModelSelector(QWidget):
    changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._models = []
        self._current = ""
        self._popup = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.frame = QFrame()
        self.frame.setObjectName("modelSelFrame")
        self.frame.setCursor(Qt.PointingHandCursor)
        self.frame.setStyleSheet(
            "QFrame#modelSelFrame { background: transparent; "
            "border: none; border-radius: 6px; }"
            "QFrame#modelSelFrame:hover { background: " + C["card_hover"] + "; }")
        self.frame.mousePressEvent = self._on_click

        fl = QHBoxLayout(self.frame)
        fl.setContentsMargins(10, 4, 10, 4)
        fl.setSpacing(6)

        self.lbl = QLabel("—")
        self.lbl.setStyleSheet(
            "QLabel { background: transparent; border: none; "
            "color: " + C["text_dim"] + "; "
            "font-family: Segoe UI; font-size: 13px; font-weight: 500; }")
        fl.addWidget(self.lbl)

        chev = QLabel("▾")
        chev.setStyleSheet(
            "QLabel { background: transparent; border: none; "
            "color: " + C["text_mute"] + "; font-size: 10px; }")
        fl.addWidget(chev)

        lay.addWidget(self.frame)
        self._refresh_text()

    def _refresh_text(self):
        self.lbl.setText(self._current or "—")

    def set_models(self, models, current=None):
        self._models = list(models or [])
        if current and current in self._models:
            self._current = current
        elif self._models:
            self._current = self._models[0]
        else:
            self._current = ""
        self._refresh_text()

    def current(self):
        return self._current

    def set_current(self, name):
        if name in self._models:
            self._current = name
            self._refresh_text()

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        color = C["text_mute"] if not enabled else C["text_dim"]
        self.lbl.setStyleSheet(
            "QLabel { background: transparent; border: none; "
            "color: " + color + "; "
            "font-family: Segoe UI; font-size: 13px; font-weight: 500; }")

    def _on_click(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle()

    def _toggle(self):
        if self._popup and self._popup.isVisible():
            self._popup.close()
            self._popup = None
            return
        self._open()

    def _open(self):
        if not self._models:
            return

        # Внешнее окно — прозрачное, БЕЗ рамки
        win = QWidget(None, Qt.Popup | Qt.FramelessWindowHint)
        win.setAttribute(Qt.WA_TranslucentBackground, True)
        win.setAttribute(Qt.WA_NoSystemBackground, True)

        # Layout без отступов — QFrame вплотную к краям окна
        outer = QVBoxLayout(win)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Вложенный QFrame — рисует фон, рамку и скругление
        card = QFrame()
        card.setObjectName("modelPopup")
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet(
            "QFrame#modelPopup {"
            "  background-color: " + C["card"] + ";"
            "  border: 1px solid " + C["border"] + ";"
            "  border-radius: 10px;"
            "}")
        card.setFixedWidth(240)
        outer.addWidget(card)

        # Внутри — список моделей
        vl = QVBoxLayout(card)
        vl.setContentsMargins(5, 5, 5, 5)
        vl.setSpacing(1)

        for name in self._models:
            item = QFrame()
            item.setObjectName("modelItem")
            item.setCursor(Qt.PointingHandCursor)
            item.setFixedHeight(34)
            is_active = (name == self._current)
            bg = C["card_hover"] if is_active else "transparent"
            item.setAttribute(Qt.WA_StyledBackground, True)
            item.setStyleSheet(
                "QFrame#modelItem { background: " + bg + "; "
                "border: none; border-radius: 7px; }"
                "QFrame#modelItem:hover { background: " + C["card_hover"] + "; }")

            il = QHBoxLayout(item)
            il.setContentsMargins(8, 2, 14, 2)
            il.setSpacing(8)

            if is_active:
                chk = QLabel()
                chk.setFixedSize(14, 14)
                chk.setPixmap(make_icon("check", C["accent"], 12).pixmap(12, 12))
                chk.setStyleSheet("background: transparent;")
                il.addWidget(chk)
            else:
                sp = QLabel()
                sp.setFixedSize(14, 14)
                sp.setStyleSheet("background: transparent;")
                il.addWidget(sp)

            t = QLabel(name)
            t.setStyleSheet(
                "QLabel { background: transparent; border: none; "
                "font-family: Segoe UI; font-size: 13px; "
                "color: " + C["text"] + "; }")
            il.addWidget(t, 1)

            item.mousePressEvent = (
                lambda e, n=name: self._select(n)
                if e.button() == Qt.LeftButton else None)

            vl.addWidget(item)

        win.adjustSize()
        self._popup = win
        self._place_popup()
        win.show()
        win.raise_()

    def _place_popup(self):
        frame_bottom_right = self.frame.mapToGlobal(
            QPoint(self.frame.width(), self.frame.height()))
        frame_top_right = self.frame.mapToGlobal(
            QPoint(self.frame.width(), 0))

        pw = self._popup.width()
        ph = self._popup.height()

        screen = QApplication.primaryScreen().availableGeometry()

        x = frame_bottom_right.x() - pw
        y = frame_bottom_right.y() + 2

        if y + ph > screen.bottom():
            y = frame_top_right.y() - ph - 2

        if x < screen.left():
            x = screen.left() + 4
        if x + pw > screen.right():
            x = screen.right() - pw - 4

        self._popup.move(x, y)

    def _select(self, name):
        self._current = name
        self._refresh_text()
        if self._popup:
            self._popup.close()
            self._popup = None
        self.changed.emit(name)
