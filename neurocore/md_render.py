"""Markdown → набор виджетов Qt для чата."""
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QVBoxLayout,
                                QWidget)

from .icons import make_icon
from .theme import C


UI = "Segoe UI"
MONO = "Consolas"


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _inline_md(text: str) -> str:
    """**bold**, *italic*, `code`, [link](url), замена ссылок."""
    s = _esc(text)

    # код — раньше всего, чтобы внутри него не парсилось
    codes = []
    def stash_code(m):
        codes.append(m.group(1))
        return "@@CODE" + str(len(codes) - 1) + "@@"
    s = re.sub(r"`([^`]+)`", stash_code, s)

    # жирный
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    # курсив
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", s)
    # зачёркнутый
    s = re.sub(r"~~([^~]+)~~", r"<s>\1</s>", s)
    # ссылки markdown
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" style="color:' + C["accent"] + r';">\1</a>',
        s)
    # авто-ссылки
    s = re.sub(
        r"(?<![\"=])(https?://[^\s<]+)",
        r'<a href="\1" style="color:' + C["accent"] + r';">\1</a>',
        s)

    # вернуть код
    for i, code in enumerate(codes):
        s = s.replace(
            "@@CODE" + str(i) + "@@",
            '<code style="background:' + C["code_inline_bg"] +
            '; color:' + C["code_inline_fg"] +
            '; padding:1px 5px; border-radius:4px; '
            'font-family:' + MONO + '; font-size:12px;">'
            + _esc(code) + '</code>')
    return s


def _is_table_sep(line: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]+\|?\s*$", line))


class HRule(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet("background: " + C["border_soft"] + ";")


class Heading(QWidget):
    SIZES = {1: 22, 2: 18, 3: 16, 4: 14, 5: 13, 6: 12}

    def __init__(self, level, text, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8 if level <= 2 else 6, 0, 4)
        lbl = QLabel(_inline_md(text))
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            "font-family: " + UI + "; "
            "font-size: " + str(self.SIZES.get(level, 13)) + "px; "
            "font-weight: 700; color: " + C["text"] + ";")
        lay.addWidget(lbl)


class Paragraph(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 4)
        lbl = QLabel(_inline_md(text))
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        lbl.setOpenExternalLinks(True)
        lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 14px; "
            "line-height: 165%; color: " + C["text"] + ";")
        lay.addWidget(lbl)


class ListItem(QWidget):
    def __init__(self, marker, text, indent=0, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6 + indent * 18, 1, 0, 1)
        lay.setSpacing(8)

        m = QLabel(marker)
        m.setFixedWidth(20)
        m.setAlignment(Qt.AlignRight | Qt.AlignTop)
        m.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text_mute"] + "; padding-top: 3px;")
        lay.addWidget(m)

        lbl = QLabel(_inline_md(text))
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        lbl.setOpenExternalLinks(True)
        lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 14px; "
            "line-height: 160%; color: " + C["text"] + ";")
        lay.addWidget(lbl, 1)


class Blockquote(QWidget):
    def __init__(self, lines, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(10)

        bar = QFrame()
        bar.setFixedWidth(3)
        bar.setStyleSheet(
            "background: " + C["accent"] + "; border-radius: 2px;")
        lay.addWidget(bar)

        inner = QVBoxLayout()
        inner.setContentsMargins(0, 2, 0, 2)
        inner.setSpacing(2)
        text = "\n".join(lines)
        for line in text.split("\n"):
            if not line.strip():
                continue
            lbl = QLabel(_inline_md(line))
            lbl.setTextFormat(Qt.RichText)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                "font-family: " + UI + "; font-size: 13px; "
                "font-style: italic; color: " + C["text_dim"] + ";")
            inner.addWidget(lbl)
        lay.addLayout(inner, 1)


class CodeBlock(QFrame):
    def __init__(self, lang, code, parent=None):
        super().__init__(parent)
        self.setObjectName("codeBlock")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(
            "color: " + C["accent"] + "; font-size: 8px; padding-right: 2px;")
        head.addWidget(dot)
        lng = QLabel((lang or "code").lower())
        lng.setStyleSheet(
            "font-family: " + MONO + "; font-size: 11px; "
            "color: " + C["text_mute"] + ";")
        head.addWidget(lng)
        head.addStretch(1)

        cp = QLabel("Копировать")
        cp.setCursor(Qt.PointingHandCursor)
        cp.setStyleSheet(
            "color: " + C["text_mute"] + "; font-size: 11px; "
            "padding: 2px 8px; border-radius: 6px;")
        cp.setProperty("role", "copy")
        def _copy(_):
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(code)
            cp.setText("Скопировано")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1200, lambda: cp.setText("Копировать"))
        cp.mousePressEvent = _copy
        head.addWidget(cp)
        lay.addLayout(head)

        body = QLabel(_esc(code))
        body.setTextFormat(Qt.PlainText)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setFont(QFont(MONO, 11))
        body.setStyleSheet(
            "font-family: " + MONO + "; font-size: 12px; "
            "color: " + C["code_text"] + "; background: transparent;")
        lay.addWidget(body)


class Table(QWidget):
    def __init__(self, headers, rows, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 6)
        lay.setSpacing(0)

        wrap = QFrame()
        wrap.setStyleSheet(
            "QFrame { background: " + C["card"] + "; "
            "border: 1px solid " + C["border_soft"] + "; "
            "border-radius: 10px; }")
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)

        # --- веса колонок по средней длине содержимого ---
        ncols = max(len(headers), max((len(r) for r in rows), default=0))
        if ncols == 0:
            lay.addWidget(wrap)
            return

        def avg_len(idx):
            total, cnt = 0, 0
            if idx < len(headers):
                total += len(str(headers[idx]))
                cnt += 1
            for r in rows:
                if idx < len(r):
                    total += len(str(r[idx]))
                    cnt += 1
            return total / cnt if cnt else 1

        weights = [max(1, int(avg_len(i) ** 0.7)) for i in range(ncols)]
        # нормируем: минимальный вес 1, максимальный не больше 6
        max_w = max(weights) if weights else 1
        weights = [max(1, min(6, int(w * 6 / max_w))) for w in weights]

        def make_row(cells, header=False, zebra=False):
            row = QWidget()
            if zebra and not header:
                row.setStyleSheet(
                    "background: rgba(255,255,255,0.02);")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 10, 14, 10)
            rl.setSpacing(14)

            # выравниваем количество ячеек
            cells = list(cells) + [""] * (ncols - len(cells))

            for idx, cell in enumerate(cells):
                l = QLabel(_inline_md(str(cell)))
                l.setTextFormat(Qt.RichText)
                l.setWordWrap(True)
                l.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                l.setMinimumWidth(40)
                weight = "700" if header else "400"
                color = C["text"] if header else C["text_dim"]
                l.setStyleSheet(
                    "font-family: " + UI + "; font-size: 12px; "
                    "font-weight: " + weight + "; color: " + color + "; "
                    "background: transparent;")
                rl.addWidget(l, weights[idx] if idx < len(weights) else 1)
            return row

        def add_sep():
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(
                "background: " + C["border_soft"] + ";")
            wl.addWidget(sep)

        # --- заголовок ---
        header_row = make_row(headers, header=True)
        header_row.setStyleSheet(
            "background: rgba(255,255,255,0.03);")
        wl.addWidget(header_row)
        add_sep()

        # --- строки с разделителями ---
        for i, r in enumerate(rows):
            wl.addWidget(make_row(r, header=False, zebra=(i % 2 == 1)))
            if i < len(rows) - 1:
                add_sep()

        lay.addWidget(wrap)


def parse(text: str):
    """Возвращает список виджетов."""
    widgets = []
    lines = text.split("\n")
    i = 0

    in_code = False
    code_lang = ""
    code_buf = []
    list_buf = []          # [(marker, text, indent)]
    quote_buf = []
    para_buf = []
    table_buf = []

    def flush_para():
        nonlocal para_buf
        if para_buf:
            widgets.append(Paragraph("\n".join(para_buf)))
            para_buf = []

    def flush_list():
        nonlocal list_buf
        if list_buf:
            for marker, txt, indent in list_buf:
                widgets.append(ListItem(marker, txt, indent))
            list_buf = []

    def flush_quote():
        nonlocal quote_buf
        if quote_buf:
            widgets.append(Blockquote(quote_buf))
            quote_buf = []

    def flush_table():
        nonlocal table_buf
        if len(table_buf) >= 2:
            headers = [c.strip() for c in table_buf[0].strip("|").split("|")]
            rows = []
            for r in table_buf[2:]:
                rows.append([c.strip() for c in r.strip("|").split("|")])
            widgets.append(Table(headers, rows))
        table_buf = []

    def flush_all():
        flush_para(); flush_list(); flush_quote(); flush_table()

    while i < len(lines):
        line = lines[i]

        # код-блок
        if line.strip().startswith("```"):
            if in_code:
                widgets.append(CodeBlock(code_lang, "\n".join(code_buf)))
                code_buf = []
                code_lang = ""
                in_code = False
            else:
                flush_all()
                in_code = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # пустая — конец блока
        if not line.strip():
            flush_all()
            i += 1
            continue

        # hr
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            flush_all()
            widgets.append(HRule())
            i += 1
            continue

        # заголовок
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            flush_all()
            widgets.append(Heading(len(h.group(1)), h.group(2).strip()))
            i += 1
            continue

        # цитата
        if line.strip().startswith(">"):
            flush_para(); flush_list(); flush_table()
            quote_buf.append(line.lstrip().lstrip(">").strip())
            i += 1
            continue
        else:
            flush_quote()

        # таблица
        if "|" in line and not line.strip().startswith("- "):
            if not table_buf and (i + 1 < len(lines) and _is_table_sep(lines[i + 1])):
                flush_para(); flush_list()
                table_buf.append(line)
                i += 1
                continue
            elif table_buf:
                table_buf.append(line)
                i += 1
                continue

        # списки
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
        if m:
            flush_para(); flush_table()
            indent = len(m.group(1)) // 2
            marker_raw = m.group(2)
            marker = "•" if marker_raw in ("-", "*", "+") else marker_raw
            list_buf.append((marker, m.group(3), indent))
            i += 1
            continue
        else:
            flush_list()

        para_buf.append(line)
        i += 1

    if in_code and code_buf:
        widgets.append(CodeBlock(code_lang, "\n".join(code_buf)))
    flush_all()
    return widgets
