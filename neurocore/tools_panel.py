"""Right-side tools panel: files / terminal / browser."""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QDesktopServices
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog,
                                QFrame, QHBoxLayout, QLabel, QLineEdit,
                                QListWidget, QListWidgetItem, QPushButton,
                                QSizePolicy, QSplitter, QStackedWidget,
                                QTextEdit, QTreeWidget, QTreeWidgetItem,
                                QVBoxLayout, QWidget)

from .icons import make_icon
from .theme import C
from .plugins_page import PluginsPage
from .terminal_widget import TerminalWidget


try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except Exception:
    HAS_WEBENGINE = False


def _btn(name, color=None, size=16, tooltip=""):
    b = QPushButton()
    b.setIcon(make_icon(name, color or C["text_dim"], size))
    b.setIconSize(QSize(size, size))
    b.setCursor(Qt.PointingHandCursor)
    b.setFixedSize(size + 14, size + 14)
    b.setStyleSheet(
        "QPushButton { background: transparent; border: none; "
        "border-radius: 6px; }"
        "QPushButton:hover { background: " + C["card_hover"] + "; }")
    if tooltip:
        b.setToolTip(tooltip)
    return b


# ============================================================
# Start screen
# ============================================================
class ToolCard(QFrame):
    clicked = Signal()

    def __init__(self, icon, title, subtitle, shortcut, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(72)
        self.setStyleSheet(
            "QFrame#card { background: " + C["card"] + "; "
            "border: 1px solid " + C["border_soft"] + "; "
            "border-radius: 10px; }"
            "QFrame#card:hover { background: " + C["card_hover"] + "; "
            "border: 1px solid " + C["border"] + "; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)

        ic = QLabel()
        ic.setPixmap(make_icon(icon, C["text_dim"], 22).pixmap(22, 22))
        ic.setFixedSize(28, 28)
        lay.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("font-size: 13px; font-weight: 600;")
        col.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("mute")
        col.addWidget(s)
        lay.addLayout(col, 1)

        if shortcut:
            sc = QLabel(shortcut)
            sc.setObjectName("mute")
            lay.addWidget(sc)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StartScreen(QWidget):
    open_files = Signal()
    open_terminal = Signal()
    open_browser = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addStretch(1)

        wrap = QVBoxLayout()
        wrap.setSpacing(14)

        ic = QLabel()
        ic.setPixmap(make_icon("compass", C["text_mute"], 44).pixmap(44, 44))
        ic.setAlignment(Qt.AlignCenter)
        wrap.addWidget(ic)
        wrap.addSpacing(20)

        # селектор оболочки

        shell_row = QHBoxLayout()

        shell_row.setContentsMargins(0, 0, 0, 0)

        shell_row.setSpacing(8)

        shell_lbl = QLabel("Оболочка:")

        shell_lbl.setStyleSheet(

            "font-family: Segoe UI; font-size: 12px; "

            "color: " + C["text_mute"] + ";")

        shell_row.addWidget(shell_lbl)

        self._shell_selector_btn = QPushButton("PowerShell  v")

        self._shell_selector_btn.setObjectName("pillBtn")

        self._shell_selector_btn.setCursor(Qt.PointingHandCursor)

        self._shell_selector_btn.setFixedHeight(26)

        self._shell_selector_btn.clicked.connect(self._show_shell_selector_menu)

        shell_row.addWidget(self._shell_selector_btn)

        shell_row.addStretch(1)

        wrap.addLayout(shell_row)

        wrap.addSpacing(6)


        self._shell_kind = "powershell"


        cards = [
            ("folder", "Файлы workspace",
             "Файлы в рабочей папке сессии", "Ctrl+P",
             self.open_files),
            ("terminal", "Новый терминал",
             "Запуск команд в рабочей папке сессии", "Ctrl+`",
             self.open_terminal),
            ("globe", "Браузер",
             "Открывать веб-страницы", "Ctrl+T",
             self.open_browser),
        ]
        for icon, title, sub, sc, sig in cards:
            card = ToolCard(icon, title, sub, sc)
            card.clicked.connect(sig.emit)
            wrap.addWidget(card)

        lay.addLayout(wrap)
        lay.addStretch(1)


# ============================================================
# File browser
# ============================================================
    SHELL_OPTIONS = [
        ("cmd", "cmd"),
        ("powershell", "PowerShell"),
        ("bash", "Git Bash"),
        ("wsl", "WSL"),
    ]

    def _show_shell_selector_menu(self):
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        for key, label in self.SHELL_OPTIONS:
            act = menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(getattr(self, "_shell_kind", "powershell") == key)
            act.triggered.connect(
                lambda _=False, k=key: self._set_shell_kind(k)
            )

        pos = self._shell_selector_btn.mapToGlobal(QPoint(0, 0))
        menu_h = menu.sizeHint().height()
        pos.setY(pos.y() - menu_h - 4)
        menu.exec(pos)

    def _set_shell_kind(self, key):
        self._shell_kind = key
        labels = dict(self.SHELL_OPTIONS)
        try:
            self._shell_selector_btn.setText(labels.get(key, key) + "  v")
        except Exception:
            pass
        try:
            if hasattr(self, "terminal"):
                if hasattr(self.terminal, "set_shell"):
                    self.terminal.set_shell(key)
                else:
                    self.terminal.shell_kind = key
        except Exception as e:
            print(f"[shell] terminal: {e}", flush=True)
        try:
            w = self.window()
            if hasattr(w, "_on_shell_changed"):
                w._on_shell_changed(key)
        except Exception:
            pass
        print(f"[shell] выбрана оболочка: {key}", flush=True)

class FileBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workspace = Path.cwd()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        bar = QHBoxLayout()
        bar.setSpacing(4)
        up = _btn("arrow_left", C["text_dim"], 14, "Вверх")
        up.clicked.connect(self._go_up)
        bar.addWidget(up)
        home = _btn("folder", C["text_dim"], 14, "Открыть папку")
        home.clicked.connect(self._pick_folder)
        bar.addWidget(home)
        ref = _btn("refresh", C["text_dim"], 14, "Обновить")
        ref.clicked.connect(self.refresh)
        bar.addWidget(ref)
        self.path_label = QLabel(str(self.workspace))
        self.path_label.setObjectName("mute")
        self.path_label.setStyleSheet(
            "font-family: Consolas; font-size: 10px; padding: 0 6px;")
        bar.addWidget(self.path_label, 1)
        lay.addLayout(bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setStyleSheet(
            "QTreeWidget { background: " + C["card"] + "; "
            "border: 1px solid " + C["border_soft"] + "; "
            "border-radius: 8px; padding: 4px; }"
            "QTreeWidget::item { padding: 3px 2px; border-radius: 4px; }"
            "QTreeWidget::item:hover { background: " + C["card_hover"] + "; }"
            "QTreeWidget::item:selected { background: " + C["accent"] + "; }")
        self.tree.itemDoubleClicked.connect(self._open_item)
        lay.addWidget(self.tree, 1)

        self.refresh()

    def set_workspace(self, path):
        self.workspace = Path(path)
        self.refresh()

    def refresh(self):
        self.tree.clear()
        self.path_label.setText(str(self.workspace))
        try:
            self._populate(self.workspace, self.tree.invisibleRootItem())
        except Exception as e:
            it = QTreeWidgetItem(["⚠ " + str(e)])
            self.tree.addTopLevelItem(it)

    def _populate(self, path, parent):
        try:
            entries = sorted(path.iterdir(),
                              key=lambda e: (not e.is_dir(), e.name.lower()))
        except Exception:
            return
        for e in entries:
            if e.name.startswith(".") and e.name not in (".env", ".gitignore"):
                continue
            icon_name = "folder" if e.is_dir() else "file"
            it = QTreeWidgetItem([" " + e.name])
            it.setIcon(0, make_icon(icon_name,
                                     C["text_dim"] if e.is_dir() else C["text_mute"],
                                     14))
            it.setData(0, Qt.UserRole, str(e))
            parent.addChild(it)
            if e.is_dir():
                # добавка-заглушка для раскрытия
                ph = QTreeWidgetItem(["…"])
                ph.setData(0, Qt.UserRole, None)
                it.addChild(ph)

    def _go_up(self):
        parent = self.workspace.parent
        if parent != self.workspace:
            self.workspace = parent
            self.refresh()

    def _pick_folder(self):
        p = QFileDialog.getExistingDirectory(
            self, "Рабочая папка", str(self.workspace))
        if p:
            self.workspace = Path(p)
            self.refresh()

    def _open_item(self, item, _col):
        path_str = item.data(0, Qt.UserRole)
        if not path_str:
            return
        p = Path(path_str)
        if p.is_dir():
            self.workspace = p
            self.refresh()
        else:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content) > 200_000:
                    content = content[:200_000] + "\n\n…(обрезано)"
                self._show_file(p.name, content)
            except Exception as e:
                self._show_file(p.name, "Ошибка: " + str(e))

    def _show_file(self, name, content):
        dlg = QFrame(self.window())
        dlg.setWindowFlags(Qt.Popup)
        dlg.setStyleSheet(
            "QFrame { background: " + C["card"] + "; border: 1px solid " +
            C["border"] + "; border-radius: 10px; }")
        dlg.resize(720, 520)
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(14, 12, 14, 12)
        head = QHBoxLayout()
        t = QLabel(name)
        t.setStyleSheet("font-weight: 600;")
        head.addWidget(t)
        head.addStretch(1)
        close = _btn("close", C["text_dim"], 14, "Закрыть")
        close.clicked.connect(dlg.close)
        head.addWidget(close)
        vl.addLayout(head)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setFont(QFont("Consolas", 11))
        view.setStyleSheet(
            "background: " + C["code_bg"] + "; border: none; "
            "border-radius: 8px; padding: 8px; color: " + C["code_text"] + ";")
        view.setPlainText(content)
        vl.addWidget(view, 1)
        dlg.move(self.mapToGlobal(self.rect().center()) - dlg.rect().center())
        dlg.show()


# ============================================================
# Terminal
# ============================================================
class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cwd = Path.cwd()
        self.history = []
        self.hist_idx = -1

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 11))
        self.output.setStyleSheet(
            "background: " + C["code_bg"] + "; border: none; "
            "border-radius: 8px; padding: 8px; color: " + C["code_text"] + ";")
        lay.addWidget(self.output, 1)

        row = QHBoxLayout()
        row.setSpacing(6)
        prompt = QLabel("›")
        prompt.setStyleSheet(
            "color: " + C["accent"] + "; font-weight: 700; "
            "font-family: Consolas; font-size: 14px;")
        row.addWidget(prompt)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Введи команду и нажми Enter")
        self.input.setStyleSheet(
            "background: " + C["card"] + "; border: 1px solid " +
            C["border_soft"] + "; border-radius: 8px; padding: 8px 10px; "
            "font-family: Consolas; font-size: 12px;")
        self.input.returnPressed.connect(self._run)
        self.input.installEventFilter(self)
        row.addWidget(self.input, 1)
        lay.addLayout(row)

        self._print("Терминал NeuroCore — рабочая папка: " + str(self.cwd), "mute")
        self._print("Команды выполняются в отдельном процессе.\n", "mute")

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                self._hist(-1)
                return True
            if key == Qt.Key_Down:
                self._hist(1)
                return True
        return super().eventFilter(obj, event)

    def _hist(self, delta):
        if not self.history:
            return
        self.hist_idx = max(0, min(len(self.history) - 1,
                                    (self.hist_idx if self.hist_idx >= 0
                                     else len(self.history)) + delta))
        self.input.setText(self.history[self.hist_idx])

    def _print(self, text, kind="out"):
        colors = {
            "out": C["code_text"],
            "cmd": C["accent"],
            "err": C["danger"],
            "mute": C["text_mute"],
        }
        color = colors.get(kind, C["code_text"])
        self.output.append(
            '<span style="color:' + color + '; white-space: pre-wrap;">'
            + text.replace("<", "&lt;").replace(">", "&gt;")
            + '</span>')

    def _run(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.history.append(cmd)
        self.hist_idx = -1
        self.input.clear()

        if cmd.lower() in ("cls", "clear"):
            self.output.clear()
            return
        if cmd.startswith("cd "):
            target = cmd[3:].strip().strip('"')
            new = (self.cwd / target).resolve()
            if new.is_dir():
                self.cwd = new
                self._print("→ " + str(self.cwd), "mute")
            else:
                self._print("cd: нет такой папки: " + target, "err")
            return

        self._print("$ " + cmd, "cmd")

        try:
            if sys.platform == "win32":
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive",
                     "-Command", cmd],
                    cwd=str(self.cwd), capture_output=True, text=True,
                    timeout=60)
            else:
                proc = subprocess.run(
                    cmd, shell=True, cwd=str(self.cwd),
                    capture_output=True, text=True, timeout=60)
            if proc.stdout:
                self._print(proc.stdout.rstrip(), "out")
            if proc.stderr:
                self._print(proc.stderr.rstrip(), "err")
            if not proc.stdout and not proc.stderr:
                self._print("[exit=" + str(proc.returncode) + "]", "mute")
        except subprocess.TimeoutExpired:
            self._print("[timeout 60s]", "err")
        except Exception as e:
            self._print("[error] " + type(e).__name__ + ": " + str(e), "err")
        self._print("", "out")


# ============================================================
# Browser
# ============================================================
class BrowserWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        bar = QHBoxLayout()
        bar.setSpacing(4)

        back = _btn("arrow_left", C["text_dim"], 14, "Назад")
        bar.addWidget(back)
        ref = _btn("refresh", C["text_dim"], 14, "Обновить")
        bar.addWidget(ref)
        ext = _btn("external", C["text_dim"], 14, "Открыть в системе")
        bar.addWidget(ext)

        self.url = QLineEdit()
        self.url.setPlaceholderText("https://…")
        self.url.setStyleSheet(
            "background: " + C["card"] + "; border: 1px solid " +
            C["border_soft"] + "; border-radius: 8px; padding: 6px 10px; "
            "font-size: 12px;")
        bar.addWidget(self.url, 1)
        lay.addLayout(bar)

        if HAS_WEBENGINE:
            self.view = QWebEngineView()
            lay.addWidget(self.view, 1)
            self.view.urlChanged.connect(
                lambda u: self.url.setText(u.toString()))
            back.clicked.connect(self.view.back)
            ref.clicked.connect(self.view.reload)
            ext.clicked.connect(
                lambda: QDesktopServices.openUrl(self.view.url())
                if False else None)
            self._go = lambda u: self.view.setUrl(u)
        else:
            self.view = QTextEdit()
            self.view.setReadOnly(True)
            self.view.setFont(QFont("Consolas", 11))
            self.view.setStyleSheet(
                "background: " + C["code_bg"] + "; border: none; "
                "border-radius: 8px; padding: 8px; color: " + C["code_text"] + ";")
            self.view.setPlainText(
                "QtWebEngine не установлен.\n\n"
                "Чтобы открывать страницы прямо в панели, выполни:\n\n"
                "    pip install PySide6-Addons\n\n"
                "Пока страницы будут открываться в системном браузере.\n\n"
                "Введи URL и нажми Enter.")
            lay.addWidget(self.view, 1)
            back.clicked.connect(lambda: None)
            ref.clicked.connect(lambda: None)
            ext.clicked.connect(
                lambda: __import__("webbrowser").open(self.url.text()))
            self._go = lambda u: __import__("webbrowser").open(u)

        self.url.returnPressed.connect(self._on_enter)

    def _on_enter(self):
        u = self.url.text().strip()
        if not u:
            return
        if not u.startswith(("http://", "https://", "file://")):
            u = "https://" + u
        self.url.setText(u)
        self._go(u)


# ============================================================
# Main panel
# ============================================================
class ToolsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("main")
        self.setMinimumWidth(320)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # header
        head = QWidget()
        head.setFixedHeight(44)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(14, 6, 10, 6)
        hl.setSpacing(6)

        self.back_btn = _btn("arrow_left", C["text_dim"], 14, "Назад")
        self.back_btn.clicked.connect(self.go_start)
        self.back_btn.hide()
        hl.addWidget(self.back_btn)

        self.title = QLabel("Начало")
        self.title.setStyleSheet("font-size: 13px; font-weight: 600;")
        hl.addWidget(self.title)
        hl.addStretch(1)

        self.refresh_btn = _btn("refresh", C["text_dim"], 14, "Обновить")
        self.refresh_btn.hide()
        hl.addWidget(self.refresh_btn)

        self.full_btn = _btn("panel_right", C["text_dim"], 14, "На весь экран")
        hl.addWidget(self.full_btn)

        lay.addWidget(head)

        # content
        self.stack = QStackedWidget()

        self.start = StartScreen()
        self.start.open_files.connect(lambda: self.go(1))
        self.start.open_terminal.connect(lambda: self.go(2))
        self.start.open_browser.connect(lambda: self.go(3))
        self.stack.addWidget(self.start)

        self.files = FileBrowser()
        self.stack.addWidget(self.files)

        self.terminal = TerminalWidget()
        self.stack.addWidget(self.terminal)

        self.browser = BrowserWidget()
        self.stack.addWidget(self.browser)
        self.plugins = PluginsPage()
        self.stack.addWidget(self.plugins)

        lay.addWidget(self.stack, 1)

        self.go_start()

    def go_start(self):
        self.stack.setCurrentIndex(0)
        self.title.setText("Начало")
        self.back_btn.hide()
        self.refresh_btn.hide()

    def go(self, idx):
        self.stack.setCurrentIndex(idx)
        names = {1: "Файлы workspace", 2: "Терминал", 3: "Браузер", 4: "Плагины"}
        self.title.setText(names.get(idx, "Инструменты"))
        self.back_btn.show()

        # подключаем refresh-кнопку под текущий инструмент
        try:
            try:
                try:
                    self.refresh_btn.clicked.disconnect()
                except (RuntimeError, TypeError):
                    pass
            except (RuntimeError, TypeError):
                pass
        except Exception:
            pass
        if idx == 1:
            self.refresh_btn.show()
            self.refresh_btn.clicked.connect(self.files.refresh)
        elif idx == 2:
            self.refresh_btn.hide()
        elif idx == 3:
            self.refresh_btn.show()
            self.refresh_btn.clicked.connect(
                lambda: self.browser.url.returnPressed.emit())

        elif idx == 4:
            self.refresh_btn.hide()
    def set_workspace(self, path):
        self.files.set_workspace(path)
        self.terminal.cwd = Path(path)
        self.terminal._print("→ cwd: " + str(path), "mute")
