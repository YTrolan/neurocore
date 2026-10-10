"""Индикатор действий агента — внутри чата."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from .icons import make_icon
from .theme import C


UI = "Segoe UI"


TOOL_VERBS = {

    "read_file":   ("Читаю файл",        "file"),
    "write_file":  ("Записываю файл",    "edit"),
    "list_dir":    ("Смотрю папку",      "folder"),
    "shell":       ("Выполняю команду",  "terminal"),
    "web_search":  ("Ищу в интернете",   "search"),
    "web_fetch":   ("Открываю страницу", "globe"),
    "generate_image": ("Рисую картинку", "sparkle"),
}


def _verb_for_tool(name: str):
    if name in TOOL_VERBS:
        return TOOL_VERBS[name]
    return ("Использую " + name, "wrench")


class ActivityBar(QFrame):
    """Индикатор: иконка + текст + анимированные точки."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("activityBar")
        self.setFixedHeight(30)

        self.setStyleSheet(
            "QFrame#activityBar {"
            "  background: transparent;"
            "  border: none;"
            "}")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.icon_lbl)

        self.text_lbl = QLabel("")
        self.text_lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["accent"] + "; "
            "background: transparent; border: none; "
            "font-weight: 500;")
        lay.addWidget(self.text_lbl)

        self.dots_lbl = QLabel("")
        self.dots_lbl.setFixedWidth(20)
        self.dots_lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["accent"] + "; "
            "background: transparent; border: none; font-weight: 700;")
        lay.addWidget(self.dots_lbl)

        lay.addStretch(1)

        self._dots_phase = 0
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._tick_dots)
        self._dots_timer.setInterval(520)

    def set_text(self, text, icon="sparkle"):
        self.text_lbl.setText(text)
        try:
            pix = make_icon(icon, C["accent"], 14).pixmap(14, 14)
            self.icon_lbl.setPixmap(pix)
        except Exception as e:
            print("[activity] иконка", icon, "ошибка:", e)

        self.dots_lbl.setText(".")
        self._dots_phase = 0
        if not self._dots_timer.isActive():
            self._dots_timer.start()

    def set_done(self, text="Готово"):
        self.text_lbl.setText(text)
        try:
            pix = make_icon("check", C["success"], 14).pixmap(14, 14)
            self.icon_lbl.setPixmap(pix)
        except Exception:
            pass
        self.dots_lbl.setText("")
        self._dots_timer.stop()

    def stop(self):
        self._dots_timer.stop()

    def _tick_dots(self):
        phases = [".", "..", "..."]
        self.dots_lbl.setText(phases[self._dots_phase % 3])
        self._dots_phase += 1
