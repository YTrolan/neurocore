"""Панель кода — как в Cursor/Copilot."""
import re
from pathlib import Path

from PySide6.QtCore import (Qt, QTimer, Signal, QSize, QFileSystemWatcher,
                             QRegularExpression)
from PySide6.QtGui import (QFont, QSyntaxHighlighter, QTextCharFormat, QColor,
                            QTextCursor, QPainter)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QPlainTextEdit, QApplication,
)

from .theme import C


UI = "Segoe UI"
MONO = "Consolas"

CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


# ============================================================
# Подсветка синтаксиса (Python / JS / JSON)
# ============================================================
class PyHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, lang="python"):
        super().__init__(doc)
        self.lang = lang
        self._rules = []
        self._build()

    def _fmt(self, color, bold=False, italic=False):
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(700)
        if italic:
            f.setFontItalic(True)
        return f

    def _build(self):
        # ключевые слова
        kw = self._fmt("#c586c0", bold=True)
        kw_py = (
            "False|None|True|and|as|assert|async|await|break|class|continue|"
            "def|del|elif|else|except|finally|for|from|global|if|import|in|"
            "is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|"
            "match|case|self|cls"
        )
        for word in kw_py.split("|"):
            self._rules.append((
                QRegularExpression(r"\b" + word + r"\b"), kw))

        # встроенные
        bi = self._fmt("#4ec9b0")
        for word in ("print|len|str|int|float|list|dict|set|tuple|range|"
                     "enumerate|zip|map|filter|sum|min|max|abs|sorted|"
                     "type|isinstance|hasattr|getattr|setattr").split("|"):
            self._rules.append((
                QRegularExpression(r"\b" + word + r"\b"), bi))

        # строки
        st = self._fmt("#ce9178")
        self._rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), st))
        self._rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), st))

        # комментарии
        cm = self._fmt("#6a9955", italic=True)
        self._rules.append((QRegularExpression(r"#[^\n]*"), cm))

        # числа
        num = self._fmt("#b5cea8")
        self._rules.append((
            QRegularExpression(r"\b\d+(\.\d+)?\b"), num))

        # декораторы
        dec = self._fmt("#dcdcaa", italic=True)
        self._rules.append((QRegularExpression(r"@\w+"), dec))

        # функции
        fn = self._fmt("#dcdcaa")
        self._rules.append((
            QRegularExpression(r"\b[A-Za-z_]\w*(?=\()"), fn))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ============================================================
# Номера строк
# ============================================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    """Просмотрщик кода с номерами строк и подсветкой."""

    def __init__(self, parent=None, lang="python"):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(MONO, 10))
        self.setStyleSheet(
            "QPlainTextEdit { background: #0e0e0e; border: none; "
            "color: #d4d4d4; padding: 6px 4px; "
            "selection-background-color: #264f78; }")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(32)

        self._highlighter = PyHighlighter(self.document(), lang)
        self._line_area = LineNumberArea(self)

        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_area)
        self.cursorPositionChanged.connect(self._highlight_current)

        self._update_margin(0)
        self._highlight_current()

    def line_number_width(self):
        digits = max(3, len(str(self.blockCount())))
        return 20 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_margin(self, _):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(),
                                    self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_margin(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(
            cr.left(), cr.top(), self.line_number_width(), cr.height())

    def paint_line_numbers(self, event):
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor("#0e0e0e"))

        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block)
                    .translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setFont(self.font())
        painter.setPen(QColor("#606060"))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    0, top,
                    self._line_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1

    def _highlight_current(self):
        pass


# ============================================================
# Основная панель
# ============================================================
class CodePanel(QWidget):
    """Панель справа — открывает файлы и код."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("codePanel")
        self.setMinimumWidth(400)
        self.setStyleSheet(
            "QWidget#codePanel { background: " + C["bg"] + "; "
            "border-left: 1px solid " + C["border_soft"] + "; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # заголовок
        head = QWidget()
        head.setFixedHeight(42)
        head.setStyleSheet(
            "background: " + C["card"] + "; "
            "border-bottom: 1px solid " + C["border_soft"] + ";")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(14, 4, 10, 4)
        hl.setSpacing(8)

        self.file_lbl = QLabel("Код")
        self.file_lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "font-weight: 600; color: " + C["text"] + "; "
            "background: transparent;")
        hl.addWidget(self.file_lbl)

        self.lang_lbl = QLabel("")
        self.lang_lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 11px; "
            "color: " + C["text_mute"] + "; background: transparent; "
            "padding: 2px 8px; border-radius: 4px;")
        hl.addWidget(self.lang_lbl)

        hl.addStretch(1)

        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setFixedHeight(26)
        self.copy_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "padding: 2px 10px; border-radius: 6px; "
            "color: " + C["text_mute"] + "; font-size: 11px; }"
            "QPushButton:hover { background: " + C["card_hover"] + "; "
            "color: " + C["text"] + "; }")
        self.copy_btn.clicked.connect(self._copy)
        hl.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(26)
        self.save_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "padding: 2px 10px; border-radius: 6px; "
            "color: " + C["text_mute"] + "; font-size: 11px; }"
            "QPushButton:hover { background: " + C["card_hover"] + "; "
            "color: " + C["text"] + "; }")
        self.save_btn.clicked.connect(self._save)
        self.save_btn.hide()
        hl.addWidget(self.save_btn)

        cls = QPushButton("X")
        cls.setCursor(Qt.PointingHandCursor)
        cls.setFixedSize(26, 26)
        cls.setToolTip("Закрыть (Ctrl+E)")
        cls.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "border-radius: 6px; padding: 0; "
            "color: " + C["text_dim"] + "; font-weight: 700; }"
            "QPushButton:hover { background: " + C["danger"] + "; "
            "color: #ffffff; }")
        cls.clicked.connect(self._on_close)
        hl.addWidget(cls)

        lay.addWidget(head)

        # путь к файлу
        self.path_lbl = QLabel("")
        self.path_lbl.setStyleSheet(
            "font-family: " + MONO + "; font-size: 10px; "
            "color: " + C["text_mute"] + "; "
            "padding: 4px 14px 4px 14px; "
            "background: " + C["bg_alt"] + "; "
            "border-bottom: 1px solid " + C["border_soft"] + ";")
        self.path_lbl.hide()
        lay.addWidget(self.path_lbl)

        # редактор
        self.editor = CodeEditor(self, lang="python")
        lay.addWidget(self.editor, 1)

        # пустое состояние
        self.empty = QLabel("Здесь появится код,\\nкогда агент его напишет")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text_mute"] + ";")
        lay.addWidget(self.empty)

        # следим за изменениями файла
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._current_path = None

        # стриминг
        self._stream_buf = ""
        self._stream_timer = None
        self._stream_speed = 8

        self._update_empty()

    # ---------- API ----------
    def open_file(self, path):
        """Открыть файл для просмотра."""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        self._current_path = str(p.resolve())
        self.file_lbl.setText(p.name)
        self.path_lbl.setText(str(p.parent))
        self.path_lbl.show()

        ext = p.suffix.lower()
        lang = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".json": "JSON", ".html": "HTML", ".css": "CSS",
            ".md": "Markdown", ".bat": "Batch", ".sh": "Shell",
            ".java": "Java", ".cpp": "C++", ".c": "C",
            ".toml": "TOML", ".yml": "YAML", ".yaml": "YAML",
        }.get(ext, ext.lstrip(".").upper() or "TEXT")
        self.lang_lbl.setText(lang)

        self.editor.setPlainText(text)
        self._autosize()

        # следить за файлом
        try:
            if self._watcher.files():
                self._watcher.removePaths(self._watcher.files())
            self._watcher.addPath(self._current_path)
        except Exception:
            pass

        self.empty.hide()
        self.save_btn.show()

        if not self.isVisible():
            self.show()

    def show_code(self, code, lang="python", stream=True, filename="code"):
        """Показать произвольный код с анимацией."""
        self._current_path = None
        self.file_lbl.setText(filename)
        self.path_lbl.hide()
        self.lang_lbl.setText(lang.capitalize())
        self.empty.hide()
        self.save_btn.hide()
        self.editor.setPlainText("")

        if not self.isVisible():
            self.show()

        if stream:
            self._start_stream(code)
        else:
            self.editor.setPlainText(code)
            self._autosize()

    def _start_stream(self, code):
        self._stop_stream()
        self._stream_buf = code
        self._stream_timer = QTimer(self)
        self._stream_timer.timeout.connect(self._stream_tick)
        self._stream_timer.start(self._stream_speed)

    def _stream_tick(self):
        if not self._stream_buf:
            self._stop_stream()
            return
        chunk = self._stream_buf[:20]
        self._stream_buf = self._stream_buf[20:]
        self.editor.insertPlainText(chunk)
        # автопрокрутка
        sb = self.editor.verticalScrollBar()
        sb.setValue(sb.maximum())
        self._autosize()

    def _stop_stream(self):
        if self._stream_timer:
            self._stream_timer.stop()
            self._stream_timer = None
        self._stream_buf = ""

    def clear(self):
        self._stop_stream()
        self.editor.setPlainText("")
        self._current_path = None
        self.file_lbl.setText("Код")
        self.path_lbl.hide()
        self.lang_lbl.setText("")
        self.save_btn.hide()
        self._update_empty()

    def _on_close(self):
        self._stop_stream()
        self.hide()
        self.closed.emit()

    def _on_file_changed(self, path):
        # перечитать файл
        if path == self._current_path and Path(path).exists():
            QTimer.singleShot(200, lambda: self.open_file(path))

    def _copy(self):
        QApplication.clipboard().setText(self.editor.toPlainText())

    def _save(self):
        if not self._current_path:
            return
        try:
            Path(self._current_path).write_text(
                self.editor.toPlainText(), encoding="utf-8")
        except Exception as e:
            print(f"[code_panel] save error: {e}", flush=True)

    def _autosize(self):
        # прокрутка вниз
        sb = self.editor.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _update_empty(self):
        if self.editor.toPlainText():
            self.empty.hide()
        else:
            self.empty.show()


def extract_code_blocks(text):
    """Список (lang, code) из текста."""
    return [(m.group(1).strip() or "text", m.group(2))
            for m in CODE_BLOCK_RE.finditer(text)
            if m.group(2).strip()]


def extract_file_paths(text):
    """Найти пути к файлам с кодом в тексте (например 'в файле app.py')."""
    exts = r"(py|js|ts|json|html|css|md|txt|bat|sh|java|cpp|c|toml|yml|yaml)"
    paths = set()
    for m in re.finditer(rf"[\w./\\-]+\.{exts}\b", text):
        paths.add(m.group(0))
    return paths
