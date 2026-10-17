"""Стилизованные диалоги — overlay внутри главного окна."""
from PySide6.QtCore import QEvent, QEventLoop, Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .icons import make_icon
from .theme import QSS, C

UI = "Segoe UI"


# ============================================================
# Overlay — диалоги внутри главного окна
# ============================================================
class DialogOverlay(QWidget):
    """Универсальный overlay для диалогов внутри главного окна."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dialogOverlay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet(
            "QWidget#dialogOverlay { background: rgba(0, 0, 0, 160); }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)

        self.card = QFrame()
        self.card.setObjectName("modal")
        self.card.setMinimumWidth(340)
        self.card.setMaximumWidth(440)
        self.card.setStyleSheet(
            "QFrame#modal { background: " + C["card"] + "; "
            "border: 1px solid " + C["border"] + "; "
            "border-radius: 14px; }")

        self.card_lay = QVBoxLayout(self.card)
        self.card_lay.setContentsMargins(20, 18, 20, 16)
        self.card_lay.setSpacing(16)

        self.head = QHBoxLayout()
        self.head.setSpacing(14)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(32, 32)
        self.icon_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        self.head.addWidget(self.icon_lbl, 0, Qt.AlignTop)

        # блок заголовок + подтекст
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.title_lbl = QLabel("")
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 14px; "
            "font-weight: 600; color: " + C["text"] + "; "
            "background: transparent; border: none;")
        text_col.addWidget(self.title_lbl)

        self.text_lbl = QLabel("")
        self.text_lbl.setWordWrap(True)
        self.text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.text_lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text_dim"] + "; line-height: 150%; "
            "background: transparent; border: none;")
        text_col.addWidget(self.text_lbl)

        self.head.addLayout(text_col, 1)

        self.card_lay.addLayout(self.head)

        self.input_edit = None

        self.btn_row = QHBoxLayout()
        self.btn_row.setSpacing(10)
        self.btn_row.setContentsMargins(0, 4, 0, 0)
        self.btn_row.addStretch(1)  # слева
        self.card_lay.addLayout(self.btn_row)
        self._btn_row_needs_right_stretch = True
        # маркер для центрирования ниже

        row.addWidget(self.card, 0)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

        self.hide()
        self._result = None
        self._loop = None
        self._input_text = ""

        if parent is not None:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.window() and event.type() == QEvent.Resize:
            if self.isVisible():
                self.setGeometry(self.window().rect())
        return super().eventFilter(obj, event)

    def _clear_buttons(self):
        while self.btn_row.count():
            it = self.btn_row.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        # симметричные stretch слева и справа → кнопки в центре
        self.btn_row.addStretch(1)

    def _clear_input(self):
        if self.input_edit is not None:
            try:
                self.card_lay.removeWidget(self.input_edit)
                self.input_edit.deleteLater()
            except Exception:
                pass
            self.input_edit = None

    def _make_button(self, label, kind, result):
        b = QPushButton(label)
        b.setCursor(Qt.PointingHandCursor)
        b.setFixedHeight(34)
        b.setMinimumWidth(88)
        if kind == "primary":
            b.setStyleSheet(
                "QPushButton { background: rgba(255, 255, 255, 22); "
                "color: " + C["text"] + "; border: none; border-radius: 8px; "
                "padding: 8px 18px; font-weight: 500; font-size: 13px; }"
                "QPushButton:hover { background: rgba(255, 255, 255, 35); }"
                "QPushButton:pressed { background: rgba(255, 255, 255, 45); }")
        elif kind == "danger":
            b.setStyleSheet(
                "QPushButton { background: rgba(220, 80, 80, 200); "
                "color: #ffffff; border: none; border-radius: 8px; "
                "padding: 8px 18px; font-weight: 500; font-size: 13px; }"
                "QPushButton:hover { background: rgba(239, 98, 98, 220); }")
        else:
            b.setStyleSheet(
                "QPushButton { background: transparent; "
                "color: " + C["text"] + "; "
                "border: 1px solid " + C["border"] + "; "
                "border-radius: 8px; padding: 8px 18px; "
                "font-size: 13px; font-weight: 500; }"
                "QPushButton:hover { background: " + C["card_hover"] + "; "
                "border-color: " + C["text_mute"] + "; }")
        b.clicked.connect(lambda _=False, r=result: self._finish(r))
        return b

    def _finish(self, result):
        self._result = result
        if self.input_edit is not None:
            self._input_text = self.input_edit.text()
        self.hide()
        if self._loop is not None:
            self._loop.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._finish(QDialog.Rejected)
        else:
            super().keyPressEvent(event)

    def _show(self, text, icon, icon_color, buttons, with_input=False,
              input_default="", input_placeholder="", password=False,
              title=None):
        self._clear_buttons()
        self._clear_input()
        self._result = None
        self._input_text = ""

        # Разделение: если title не задан, но текст короткий (<=60) —
        # используем как заголовок, подтекст пустой
        if title is None:
            if len(text) <= 70:
                self.title_lbl.setText(text)
                self.text_lbl.setText("")
            else:
                self.title_lbl.setText("")
                self.text_lbl.setText(text)
        else:
            self.title_lbl.setText(title)
            self.text_lbl.setText(text)

        if icon_color is None:
            icon_color = {
                "question": C["accent"],
                "warning": C["warning"],
                "error": C["danger"],
                "alert": C["danger"],
                "info": C["accent"],
                "success": C["success"],
                "check": C["success"],
            }.get(icon, C["accent"])
        # иконка: если её нет — скрываем метку и текст занимает всю ширину
        pix = None
        try:
            pix = make_icon(icon, icon_color, 22).pixmap(22, 22)
        except Exception:
            pix = None
        if pix is not None and not pix.isNull():
            self.icon_lbl.setPixmap(pix)
            self.icon_lbl.setFixedSize(28, 28)
            self.icon_lbl.show()
        else:
            self.icon_lbl.clear()
            self.icon_lbl.setFixedSize(0, 0)
            self.icon_lbl.hide()

        if with_input:
            self.input_edit = QLineEdit()
            self.input_edit.setText(input_default)
            self.input_edit.setPlaceholderText(input_placeholder)
            if password:
                self.input_edit.setEchoMode(QLineEdit.Password)
            self.input_edit.setFixedHeight(38)
            self.input_edit.setStyleSheet(
                "QLineEdit { background: " + C["bg_alt"] + "; "
                "border: 1px solid " + C["border"] + "; "
                "border-radius: 8px; padding: 8px 12px; "
                "font-size: 13px; color: " + C["text"] + "; }"
                "QLineEdit:focus { border: 1px solid " + C["accent"] + "; }")
            self.input_edit.returnPressed.connect(
                lambda: self._finish(QDialog.Accepted))
            self.card_lay.insertWidget(self.card_lay.count() - 1,
                                       self.input_edit)

        for label, kind, result in buttons:
            self.btn_row.addWidget(
                self._make_button(label, kind, result))

        self.btn_row.addStretch(1)  # справа для симметрии
        w = self.window()
        if w is not None:
            self.setGeometry(w.rect())
        self.show()
        self.raise_()

        if with_input and self.input_edit is not None:
            self.input_edit.setFocus()
            self.input_edit.selectAll()
        else:
            self.setFocus()

    def _run(self):
        self._loop = QEventLoop()
        self._loop.exec()
        self._loop = None

    # публичный API
    def message(self, text, icon="info", icon_color=None, buttons=None):
        buttons = buttons or [("OK", "primary", QDialog.Accepted)]
        self._show(text, icon, icon_color, buttons)
        self._run()
        return self._result

    def question(self, text, yes_text="Да", no_text="Нет", danger=False,
                 title=None):
        buttons = [
            (no_text, "secondary", QDialog.Rejected),
            (yes_text, "danger" if danger else "primary", QDialog.Accepted),
        ]
        self._show(text, "question", None, buttons, title=title)
        self._run()
        return self._result == QDialog.Accepted

    def ask_input(self, text, default="", placeholder="", password=False,
                  ok_text="OK", cancel_text="Отмена"):
        buttons = [
            (cancel_text, "secondary", QDialog.Rejected),
            (ok_text, "primary", QDialog.Accepted),
        ]
        self._show(text, "info", None, buttons,
                   with_input=True,
                   input_default=default,
                   input_placeholder=placeholder,
                   password=password)
        self._run()
        if self._result == QDialog.Accepted:
            return self._input_text, True
        return "", False


# ============================================================
# Fallback QDialog (если parent не главное окно)
# ============================================================
def _apply_theme(dlg):
    dlg.setStyleSheet(QSS)


class MessageDialog(QDialog):
    def __init__(self, parent=None, title="NeuroCore", text="",
                 icon="info", icon_color=None, buttons=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        _apply_theme(self)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        if icon_color is None:
            icon_color = C["accent"]
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(16)
        head = QHBoxLayout()
        head.setSpacing(16)
        ic = QLabel()
        try:
            ic.setPixmap(make_icon(icon, icon_color, 26).pixmap(26, 26))
        except Exception:
            pass
        ic.setFixedSize(38, 38)
        ic.setAlignment(Qt.AlignCenter)
        head.addWidget(ic, 0, Qt.AlignTop)
        txt = QLabel(text)
        txt.setWordWrap(True)
        txt.setStyleSheet(
            "font-family: " + UI + "; font-size: 14px; "
            "color: " + C["text"] + ";")
        head.addWidget(txt, 1)
        lay.addLayout(head)
        btns_row = QHBoxLayout()
        btns_row.setSpacing(8)
        btns_row.addStretch(1)
        buttons = buttons or [("OK", "primary", QDialog.Accepted)]
        for label, kind, result in buttons:
            b = QPushButton(label)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(36)
            b.setMinimumWidth(100)
            b.clicked.connect(lambda _=False, r=result: self.done(r))
            btns_row.addWidget(b)
        lay.addLayout(btns_row)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class InputDialog(QDialog):
    def __init__(self, parent=None, title="NeuroCore", text="",
                 default="", placeholder="", password=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        _apply_theme(self)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(14)
        if text:
            t = QLabel(text)
            t.setWordWrap(True)
            t.setStyleSheet(
                "font-family: " + UI + "; font-size: 13px; "
                "color: " + C["text"] + ";")
            lay.addWidget(t)
        self.edit = QLineEdit()
        self.edit.setText(default)
        self.edit.setPlaceholderText(placeholder)
        if password:
            self.edit.setEchoMode(QLineEdit.Password)
        self.edit.setFixedHeight(38)
        lay.addWidget(self.edit)
        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addStretch(1)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        btns.addWidget(ok)
        lay.addLayout(btns)
        self.edit.returnPressed.connect(self.accept)
        self.edit.selectAll()

    def get_text(self):
        return self.edit.text()


# ============================================================
# Публичный API
# ============================================================
def _get_overlay(parent):
    if parent is None:
        return None
    try:
        win = parent.window() if hasattr(parent, "window") else parent
    except Exception:
        return None
    ov = getattr(win, "dialog_overlay", None)
    return ov if isinstance(ov, DialogOverlay) else None


def info(parent, text, title="NeuroCore", icon="info"):
    ov = _get_overlay(parent)
    if ov is not None:
        ov.message(text, icon=icon)
        return True
    d = MessageDialog(parent, title, text, icon)
    d.exec()
    return True


def warning(parent, text, title="NeuroCore"):
    ov = _get_overlay(parent)
    if ov is not None:
        ov.message(text, icon="warning", icon_color=C["warning"])
        return True
    d = MessageDialog(parent, title, text, "warning", icon_color=C["warning"])
    d.exec()
    return True


def error(parent, text, title="Ошибка"):
    ov = _get_overlay(parent)
    if ov is not None:
        ov.message(text, icon="alert", icon_color=C["danger"])
        return True
    d = MessageDialog(parent, title, text, "alert", icon_color=C["danger"])
    d.exec()
    return True


def success(parent, text, title="Готово"):
    ov = _get_overlay(parent)
    if ov is not None:
        ov.message(text, icon="check", icon_color=C["success"])
        return True
    d = MessageDialog(parent, title, text, "check", icon_color=C["success"])
    d.exec()
    return True


def question(parent, text, title=None,
             yes_text="Да", no_text="Нет", danger=False):
    ov = _get_overlay(parent)
    if ov is not None:
        return ov.question(text, yes_text=yes_text, no_text=no_text,
                           danger=danger, title=title)
    d = MessageDialog(parent, title, text, "question",
                      buttons=[
                          (no_text, "secondary", QDialog.Rejected),
                          (yes_text, "danger" if danger else "primary",
                           QDialog.Accepted),
                      ])
    return d.exec() == QDialog.Accepted


def ask_text(parent, title, text="", default="", placeholder="",
             password=False):
    ov = _get_overlay(parent)
    if ov is not None:
        return ov.ask_input(text or title, default=default,
                            placeholder=placeholder, password=password)
    d = InputDialog(parent, title, text, default, placeholder, password)
    if d.exec() == QDialog.Accepted:
        return d.get_text(), True
    return "", False
