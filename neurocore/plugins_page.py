"""Full-screen plugins page."""
import shutil
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .extensions import OFFICIAL_PLUGINS, PLUGIN_DIR, load_plugin_states, save_plugin_states
from .icons import make_icon
from .theme import C


class Toggle(QPushButton):
    """iOS-style toggle switch."""
    changed = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.toggled.connect(self._on_toggle)

    def _refresh(self):
        on = self.isChecked()
        self.setText("")
        self.setStyleSheet(
            "QPushButton { border-radius: 12px; border: none; "
            "background: " + (C["accent"] if on else "#4a4a4a") + "; }"
            "QPushButton:hover { background: " +
            (C["accent_hover"] if on else "#5a5a5a") + "; }"
        )

    def _on_toggle(self, checked):
        self._refresh()
        self.changed.emit(checked)


class PluginRow(QFrame):
    toggled = Signal(str, bool)

    def __init__(self, plugin, enabled, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setObjectName("pluginRow")
        self.setFixedHeight(80)
        self.setStyleSheet(
            "QFrame#pluginRow { background: transparent; "
            "border: none; border-bottom: 1px solid " + C["border_soft"] + "; }"
            "QFrame#pluginRow:hover { background: " + C["card"] + "; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(16)

        # icon
        ic = QLabel()
        ic.setPixmap(make_icon(plugin["icon"], C["text_dim"], 22).pixmap(22, 22))
        ic.setFixedSize(44, 44)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(
            "background: " + C["card"] + "; border-radius: 12px; "
            "border: 1px solid " + C["border_soft"] + ";")
        lay.addWidget(ic)

        # text
        col = QVBoxLayout()
        col.setSpacing(4)
        head = QHBoxLayout()
        head.setSpacing(8)
        name = QLabel(plugin["name"])
        name.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: " + C["text"] + ";")
        head.addWidget(name)
        if plugin.get("experimental"):
            b = QLabel("Экспериментальный")
            b.setStyleSheet(
                "background: " + C["card"] + "; color: " + C["text_mute"] +
                "; font-size: 10px; padding: 2px 8px; border-radius: 4px; "
                "border: 1px solid " + C["border_soft"] + ";")
            head.addWidget(b)
        head.addStretch(1)
        col.addLayout(head)

        desc = QLabel(plugin["description"])
        desc.setStyleSheet(
            "font-size: 12px; color: " + C["text_dim"] + ";")
        desc.setWordWrap(True)
        col.addWidget(desc)

        lay.addLayout(col, 1)

        # toggle
        t = Toggle(enabled)
        t.changed.connect(lambda v: self.toggled.emit(plugin["id"], v))
        lay.addWidget(t)


class PluginsPage(QWidget):
    back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("root")
        self.states = load_plugin_states()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # header
        head = QWidget()
        head.setFixedHeight(80)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(28, 20, 28, 12)
        hl.setSpacing(12)

        # кнопка назад
        back_btn = QPushButton()
        back_btn.setIcon(make_icon("arrow_left", C["text_dim"], 16))
        back_btn.setIconSize(QSize(16, 16))
        back_btn.setFixedSize(34, 34)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setToolTip("Назад к чату")
        back_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "border-radius: 8px; }"
            "QPushButton:hover { background: " + C["card_hover"] + "; }")
        back_btn.clicked.connect(self.back.emit)
        hl.addWidget(back_btn)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Плагины")
        title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: " + C["text"] + ";")
        title_col.addWidget(title)

        sub = QHBoxLayout()
        sub.setSpacing(6)
        sub.addWidget(QLabel("Установка, включение и настройка плагинов"))
        info = QLabel()
        info.setPixmap(make_icon("info", C["text_mute"], 12).pixmap(12, 12))
        sub.addWidget(info)
        sub.addStretch(1)
        title_col.addLayout(sub)
        for i in range(sub.count()):
            w = sub.itemAt(i).widget()
            if isinstance(w, QLabel) and w.text():
                w.setStyleSheet("font-size: 12px; color: " + C["text_mute"] + ";")
        hl.addLayout(title_col, 1)

        refresh = QPushButton()
        refresh.setIcon(make_icon("refresh", C["text_dim"], 15))
        refresh.setIconSize(QSize(15, 15))
        refresh.setFixedSize(34, 34)
        refresh.setCursor(Qt.PointingHandCursor)
        refresh.setToolTip("Обновить")
        refresh.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "border-radius: 8px; }"
            "QPushButton:hover { background: " + C["card_hover"] + "; }")
        refresh.clicked.connect(self._refresh_all)
        hl.addWidget(refresh)

        add = QPushButton("  Добавить плагин")
        add.setObjectName("primary")
        add.setIcon(make_icon("plus", "#ffffff", 14))
        add.setIconSize(QSize(14, 14))
        add.setCursor(Qt.PointingHandCursor)
        add.setFixedHeight(36)
        add.clicked.connect(self._add_plugin)
        hl.addWidget(add)

        lay.addWidget(head)

        # section title
        sec = QWidget()
        sec.setFixedHeight(38)
        sl = QHBoxLayout(sec)
        sl.setContentsMargins(28, 4, 28, 4)
        sl.setSpacing(8)
        st = QLabel("Официальные")
        st.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: " + C["text"] + ";")
        sl.addWidget(st)
        self.count_label = QLabel(str(len(OFFICIAL_PLUGINS)))
        self.count_label.setStyleSheet(
            "color: " + C["text_mute"] + "; font-size: 12px;")
        sl.addWidget(self.count_label)
        sl.addStretch(1)
        lay.addWidget(sec)

        # scroll list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_w = QWidget()
        self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setContentsMargins(28, 0, 28, 20)
        self.list_l.setSpacing(0)
        self.list_l.addStretch(1)
        scroll.setWidget(self.list_w)
        lay.addWidget(scroll, 1)

        self._populate()

    def _populate(self):
        while self.list_l.count() > 1:
            it = self.list_l.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        for i, p in enumerate(OFFICIAL_PLUGINS):
            enabled = self.states.get(p["id"], p["default"])
            row = PluginRow(p, enabled)
            row.toggled.connect(self._on_toggle)
            self.list_l.insertWidget(i, row)

    def _on_toggle(self, pid, val):
        self.states[pid] = val
        save_plugin_states(self.states)

    def _refresh_all(self):
        self.states = load_plugin_states()
        self._populate()

    def _add_plugin(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбери .py файл плагина", "", "Python (*.py)")
        if not path:
            return
        try:
            dst = PLUGIN_DIR / Path(path).name
            shutil.copy(path, dst)
            QMessageBox.information(
                self, "NeuroCore",
                "Плагин скопирован в " + str(PLUGIN_DIR) +
                "\nОн появится в списке после перезапуска.")
        except Exception as e:
            QMessageBox.warning(self, "NeuroCore", "Ошибка: " + str(e))
