"""Настоящий PowerShell в виджете Qt через PTY."""
import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from .theme import C


try:
    import pyte
except ImportError:
    pyte = None

try:
    from winpty import PtyProcess
    HAS_WINPTY = True
except ImportError:
    HAS_WINPTY = False


COLS = 120
ROWS = 32




SHELL_COMMANDS = {
    # key -> (argv, display_name)
    "cmd": (
        ["cmd.exe"],
        "cmd",
    ),
    "powershell": (
        ["powershell.exe", "-NoLogo", "-NoProfile"],
        "PowerShell",
    ),
    "pwsh": (
        ["pwsh.exe", "-NoLogo", "-NoProfile"],
        "pwsh",
    ),
    "bash": (
        ["bash.exe", "-i"],
        "Git Bash",
    ),
    "wsl": (
        ["wsl.exe", "bash", "-l"],
        "WSL",
    ),
}


def shell_argv(kind: str):
    """Вернуть argv для оболочки по её ключу."""
    entry = SHELL_COMMANDS.get((kind or "powershell").lower())
    if entry:
        return list(entry[0])
    return list(SHELL_COMMANDS["powershell"][0])

class TerminalWidget(QWidget):
    """Настоящий терминал: PowerShell через Windows ConPTY."""

    data_ready = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cwd = str(Path.cwd())
        self.shell_kind = "powershell"
        self.pty = None
        self.screen = None
        self.stream = None
        self._reader = None
        self._running = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setFont(QFont("Consolas", 10))
        self.view.setStyleSheet(
            "QPlainTextEdit { background: #0c0c0c; border: none; "
            "color: #cccccc; padding: 4px 6px; "
            "selection-background-color: #264f78; }")
        self.view.setUndoRedoEnabled(False)
        self.view.setMaximumBlockCount(10000)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setTextInteractionFlags(Qt.NoTextInteraction)
        self.view.setFocusPolicy(Qt.StrongFocus)
        self.view.installEventFilter(self)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        lay.addWidget(self.view)

        self.data_ready.connect(self._render)

        QTimer.singleShot(50, self._start)

    # ---------- запуск ----------
    def _shell_argv(self):
        """argv текущей оболочки."""
        return shell_argv(self.shell_kind)

    def set_shell(self, kind: str):
        """Сменить оболочку и перезапустить PTY."""
        kind = (kind or "powershell").lower()
        if kind == getattr(self, "shell_kind", None):
            return
        self.shell_kind = kind
        # остановить текущий PTY
        try:
            if self.pty is not None:
                try:
                    self.pty.terminate(force=True)
                except Exception:
                    pass
                self.pty = None
        except Exception:
            pass
        self._running = False
        # сообщить в терминал
        try:
            name = SHELL_COMMANDS.get(kind, ("", kind))[1]
            self.view.setPlainText(
                "⚠  Смена оболочки на " + name + "...\n\n"
            )
        except Exception:
            pass
        # перезапустить
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, self._start)

    def _start(self):
        if not HAS_WINPTY:
            self.view.setPlainText(
                "⚠  pywinpty не установлен\n\n"
                "pip install pywinpty pyte")
            return
        if not pyte:
            self.view.setPlainText(
                "⚠  pyte не установлен\n\n"
                "pip install pyte")
            return

        self.screen = pyte.HistoryScreen(COLS, ROWS, history=10000)
        self.stream = pyte.ByteStream(self.screen)

        try:
            # Запускаем настоящий PowerShell через ConPTY
            self.pty = PtyProcess.spawn(
                shell_argv(self.shell_kind),
                cwd=self.cwd,
                dimensions=(ROWS, COLS),
            )
            print("[terminal] запущен PowerShell, pid=", self.pty.pid)
        except Exception as e:
            self.view.setPlainText(
                "⚠  Не удалось запустить PowerShell:\n\n" + str(e))
            print("[terminal] ошибка:", e)
            return

        self._running = True
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.view.setFocus()

    # ---------- чтение из PTY ----------
    def _read_loop(self):
        while self._running:
            try:
                data = self.pty.read(4096)
                if not data:
                    break
                # pywinpty отдаёт str, pyte.ByteStream ждёт bytes
                if isinstance(data, str):
                    data = data.encode("utf-8", errors="replace")
                self.stream.feed(data)
                self.data_ready.emit()
            except EOFError:
                break
            except Exception as e:
                print("[terminal] read error:", e)
                break
        self._running = False

    # ---------- рендер ----------
    def _render(self):
        if not self.screen:
            return

        lines = []

        # история (scrollback)
        for line in self.screen.history.top:
            max_x = max(line.keys()) if line else -1
            s = []
            for x in range(max_x + 1):
                ch = line.get(x)
                s.append(ch.data if ch else " ")
            lines.append("".join(s).rstrip())

        # текущий экран
        for y in range(self.screen.lines):
            row = self.screen.buffer[y]
            s = []
            for x in range(self.screen.columns):
                ch = row.get(x)
                s.append(ch.data if ch else " ")
            lines.append("".join(s).rstrip())

        # убрать пустые снизу
        while lines and not lines[-1]:
            lines.pop()

        # курсор
        cy = self.screen.cursor.y
        cx = self.screen.cursor.x
        display_start = len(self.screen.history.top)
        absolute_y = display_start + cy

        if absolute_y < len(lines):
            line = lines[absolute_y]
            if cx > len(line):
                lines[absolute_y] = line + " " * (cx - len(line)) + "▏"
            else:
                lines[absolute_y] = line[:cx] + "▏" + line[cx:]
        else:
            lines.append(" " * cx + "▏")

        text = "\n".join(lines)

        if self.view.toPlainText() != text:
            self.view.setPlainText(text)
            # в самый низ
            cur = self.view.textCursor()
            cur.movePosition(cur.MoveOperation.End)
            self.view.setTextCursor(cur)

    # ---------- клавиатура ----------
    def _send(self, seq):
        if not self.pty or not self._running:
            return False
        try:
            self.pty.write(seq)
            return True
        except Exception as e:
            print("[terminal] write error:", e)
            return False

    def eventFilter(self, obj, event):
        if obj is not self.view:
            return super().eventFilter(obj, event)
        if event.type() != event.Type.KeyPress:
            return super().eventFilter(obj, event)

        e = event
        key = e.key()
        mods = e.modifiers()

        # Ctrl+буква
        if (mods & Qt.ControlModifier) and Qt.Key_A <= key <= Qt.Key_Z:
            self._send(chr(key - Qt.Key_A + 1))
            return True

        # специальные клавиши
        specials = {
            Qt.Key_Return: "\r",
            Qt.Key_Enter: "\r",
            Qt.Key_Backspace: "\x7f",
            Qt.Key_Tab: "\t",
            Qt.Key_Escape: "\x1b",
            Qt.Key_Up: "\x1b[A",
            Qt.Key_Down: "\x1b[B",
            Qt.Key_Right: "\x1b[C",
            Qt.Key_Left: "\x1b[D",
            Qt.Key_Home: "\x1b[H",
            Qt.Key_End: "\x1b[F",
            Qt.Key_Delete: "\x1b[3~",
            Qt.Key_PageUp: "\x1b[5~",
            Qt.Key_PageDown: "\x1b[6~",
            Qt.Key_F1: "\x1bOP",
            Qt.Key_F2: "\x1bOQ",
            Qt.Key_F3: "\x1bOR",
            Qt.Key_F4: "\x1bOS",
        }
        if key in specials:
            self._send(specials[key])
            return True

        # обычный текст
        text = e.text()
        if text:
            self._send(text)
            return True

        return True

    # ---------- API ----------
    def set_workspace(self, path):
        """Послать в шелл cd."""
        self.cwd = str(path)
        if self._running:
            self._send('cd "' + self.cwd + '"\r')
        self.view.setFocus()

    def closeEvent(self, event):
        self._running = False
        try:
            if self.pty:
                self.pty.close()
        except Exception:
            pass
        super().closeEvent(event)

