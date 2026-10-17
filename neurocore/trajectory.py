"""Trajectory view: timeline of tool calls."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from .icons import make_icon
from .theme import C


class StepCard(QFrame):
    def __init__(self, idx, tool_name, args, result, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            "QFrame#card { background: " + C["card"] +
            "; border: 1px solid " + C["border_soft"] +
            "; border-radius: 10px; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(8)

        num = QLabel(str(idx))
        num.setFixedSize(22, 22)
        num.setAlignment(Qt.AlignCenter)
        num.setStyleSheet(
            "background: " + C["accent"] + "; color: white; "
            "border-radius: 11px; font-weight: 700; font-size: 11px;")
        head.addWidget(num)

        ic = QLabel()
        ic.setPixmap(make_icon("wrench", C["warning"], 14).pixmap(14, 14))
        head.addWidget(ic)

        name = QLabel(tool_name)
        name.setStyleSheet("font-weight: 600; font-size: 13px;")
        head.addWidget(name)
        head.addStretch(1)
        lay.addLayout(head)

        if args:
            args_str = ", ".join(k + "=" + repr(v)[:60]
                                  for k, v in args.items())
            a = QLabel(args_str)
            a.setWordWrap(True)
            a.setStyleSheet("font-family: Consolas; font-size: 11px; "
                             "color: " + C["text_dim"] + ";")
            lay.addWidget(a)

        if result:
            body = QFrame()
            body.setStyleSheet(
                "background: " + C["code_bg"] + "; border-radius: 8px;")
            bl = QVBoxLayout(body)
            bl.setContentsMargins(10, 8, 10, 8)
            short = result if len(result) < 500 else result[:500] + "…"
            r = QLabel(short)
            r.setWordWrap(True)
            r.setTextInteractionFlags(Qt.TextSelectableByMouse)
            r.setStyleSheet(
                "font-family: Consolas; font-size: 11px; "
                "color: " + C["code_text"] + ";")
            bl.addWidget(r)
            lay.addWidget(body)


class TrajectoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("main")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(self.scroll)

        self.inner = QWidget()
        self.lay = QVBoxLayout(self.inner)
        self.lay.setContentsMargins(60, 20, 60, 30)
        self.lay.setSpacing(10)
        self.lay.addStretch(1)
        self.scroll.setWidget(self.inner)

        self._steps = 0
        self._placeholder = None
        self._show_empty()

    def _clear(self):
        while self.lay.count() > 1:
            it = self.lay.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        self._steps = 0
        self._placeholder = None

    def _show_empty(self):
        w = QLabel("Пока пусто.\n\nТраектория покажет шаги агента после "
                    "первого запроса.")
        w.setAlignment(Qt.AlignCenter)
        w.setStyleSheet("color: " + C["text_mute"] + "; font-size: 13px;")
        self.lay.insertWidget(0, w)
        self._placeholder = w

    def clear(self):
        self._clear()
        self._show_empty()

    def add_step(self, tool_name, args):
        if self._placeholder:
            self._placeholder.deleteLater()
            self._placeholder = None
        self._steps += 1
        card = StepCard(self._steps, tool_name, args, None)
        self.lay.insertWidget(self.lay.count() - 1, card)
        # запоминаем "открытый" степ, чтобы дозаполнить результатом
        self._open = card
        QTimer.singleShot(30, self._scroll_end)

    def set_result(self, result):
        if not hasattr(self, "_open") or self._open is None:
            return
        # дорисовываем result блок
        card = self._open
        lay = card.layout()
        body = QFrame()
        body.setStyleSheet(
            "background: " + C["code_bg"] + "; border-radius: 8px;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(10, 8, 10, 8)
        short = result if len(result) < 500 else result[:500] + "…"
        r = QLabel(short)
        r.setWordWrap(True)
        r.setTextInteractionFlags(Qt.TextSelectableByMouse)
        r.setStyleSheet(
            "font-family: Consolas; font-size: 11px; "
            "color: " + C["code_text"] + ";")
        bl.addWidget(r)
        lay.addWidget(body)
        self._open = None

    def _scroll_end(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
