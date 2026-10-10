"""NeuroCore — тема в стиле DeepSeek Harness."""

C = {
    # ---------- ФОНЫ ----------
    "bg":           "#1a1a1a",   # фон окна и чата
    "bg_alt":       "#141414",   # темнее — для code/input
    "sidebar":      "#141414",   # sidebar = тот же фон, что чат
    "card":         "#262626",
    "card_hover":   "#2f2f2f",
    "card_active":  "#333333",

    # ---------- ГРАНИЦЫ (едва заметные) ----------
    "border":       "#333333",
    "border_soft":  "#262626",

    # ---------- ТЕКСТ ----------
    "text":         "#e8e8e8",
    "text_dim":     "#a0a0a0",
    "text_mute":    "#707070",

    # ---------- АКЦЕНТ ----------
    "accent":       "#4a7aff",
    "accent_hover": "#5b8aff",
    "accent_dim":   "#2a3a5c",

    # ---------- БЛОКИ ----------
    "user_bubble":  "#2f2f2f",   # СЕРЫЙ, не синий
    "code_inline_fg": "#d4d4d4",
    "code_inline_bg": "rgba(255, 255, 255, 18)",
    "code_bg":      "#141414",
    "code_text":    "#d4d4d4",

    # ---------- СТАТУСЫ ----------
    "success":      "#4ade80",
    "danger":       "#ef4444",
    "danger_bg":    "#2a1414",
    "warning":      "#f59e0b",
    "badge_bg":     "#2a2010",
    "badge_fg":     "#f59e0b",

    "modal_bg":     "#1f1f1f",
    "overlay":      "#000000",
}


_T = """
* {
    font-family: "Inter", "Segoe UI", "SF Pro Text", sans-serif;
    font-size: 13px;
    color: @@text@@;
    outline: none;
}

QWidget { background: transparent; color: @@text@@; }
QMainWindow { background-color: @@bg@@; }
QWidget#root { background: transparent; }
QWidget#main { background-color: @@bg@@; }

/* ---------- SIDEBAR (тот же фон что и чат) ---------- */
QWidget#sidebar {
    background-color: @@sidebar@@;
    border-right: 1px solid @@border_soft@@;
}

/* ---------- TOPBAR (без нижней линии) ---------- */
QWidget#topbar {
    background-color: @@bg@@;
    border: none;
}

QWidget#titlebar {
    background-color: @@bg@@;
    border-bottom: 1px solid @@border_soft@@;
}

/* ---------- LABELS ---------- */
QLabel, QLabel * { background: transparent; color: @@text@@; }
QLabel#dim { color: @@text_dim@@; }
QLabel#mute { color: @@text_mute@@; font-size: 11px; }
QLabel#h1 { font-size: 24px; font-weight: 700; }
QLabel#title { font-size: 14px; font-weight: 600; }
QLabel#code {
    font-family: "Consolas", "JetBrains Mono", monospace;
    font-size: 12px; color: @@code_text@@;
}
QLabel#badge {
    background-color: @@badge_bg@@;
    color: @@badge_fg@@;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 6px;
}
QLabel#titlebarTitle {
    color: @@text@@;
    font-size: 13px;
    font-weight: 500;
}

/* ---------- КНОПКИ ---------- */
QPushButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
    color: @@text@@;
    text-align: left;
}
QPushButton:hover { background-color: @@card_hover@@; }
QPushButton:pressed { background-color: @@card_active@@; }

QPushButton#primary {
    background-color: @@accent@@;
    color: #ffffff;
    text-align: center;
    padding: 8px 20px;
    font-weight: 600;
    border-radius: 10px;
}
QPushButton#primary:hover { background-color: @@accent_hover@@; }

/* Кнопка "Новая сессия" — полупрозрачная, БЕЗ РАМКИ (как в DSH) */
QPushButton#newSessionBig {
    background-color: @@card@@;
    border: none;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    border-radius: 10px;
    color: @@text@@;
}
QPushButton#newSessionBig:hover {
    background-color: @@card_hover@@;
}

QPushButton#sidebarItem {
    background: transparent;
    padding: 7px 12px;
    color: @@text_dim@@;
    border-radius: 8px;
    font-size: 13px;
}
QPushButton#sidebarItem:hover {
    background-color: @@card_hover@@;
    color: @@text@@;
}

QPushButton#workspaceItem {
    background: transparent;
    padding: 7px 12px;
    color: @@text_dim@@;
    border-radius: 8px;
    text-align: left;
    font-size: 13px;
}
QPushButton#workspaceItem:hover {
    background-color: @@card_hover@@;
    color: @@text@@;
}

QPushButton#chipBtn {
    background: transparent;
    border: none;
    padding: 2px 8px;
    color: @@text_mute@@;
    font-size: 12px;
    border-radius: 6px;
    text-align: left;
}
QPushButton#chipBtn:hover { color: @@text@@; }

QPushButton#pillBtn {
    background-color: transparent;
    border: 1px solid #2a2a2a;
    padding: 4px 12px;
    border-radius: 14px;
    color: @@text_dim@@;
    font-size: 12px;
    text-align: center;
}
QPushButton#pillBtn:hover {
    background-color: @@card@@;
    color: @@text@@;
    border-color: @@border@@;
}

QPushButton#iconBtn {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 0;
}
QPushButton#iconBtn:hover { background-color: @@card_hover@@; }

QPushButton#showMore {
    color: @@text_mute@@;
    font-size: 11px;
    padding: 4px 12px;
    text-align: left;
    border-radius: 6px;
    background: transparent;
}
QPushButton#showMore:hover {
    color: @@text@@;
    background-color: @@card@@;
}

/* Вкладки Чат/Траектория — минималистичные */
QPushButton#tabBtn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    padding: 6px 14px 10px 14px;
    color: @@text_mute@@;
    font-size: 13px;
}
QPushButton#tabBtn:hover { color: @@text@@; }
QPushButton#tabBtn[active="true"] {
    color: @@text@@;
    font-weight: 500;
    border-bottom: 2px solid @@text@@;
}

QToolButton#winBtn, QToolButton#winClose {
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
}
QToolButton#winBtn:hover { background-color: @@card_hover@@; }
QToolButton#winClose:hover { background-color: #c42b1c; }
QToolButton#winClose:pressed { background-color: #a02015; }

QToolButton#sendBtn {
    background-color: @@accent@@;
    border: none;
    border-radius: 16px;
    padding: 0;
}
QToolButton#sendBtn:hover { background-color: @@accent_hover@@; }
QToolButton#sendBtn:pressed { background-color: #3a6ae8; }
QToolButton#sendBtn:disabled { background-color: @@card_active@@; }

QToolButton#stopActiveBtn {
    background-color: #dc2626;
    border: none;
    border-radius: 16px;
    padding: 0;
}
QToolButton#stopActiveBtn:hover { background-color: #ef4444; }

/* ---------- ПОЛЯ ВВОДА ---------- */
QLineEdit {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px 10px;
    color: @@text@@;
    selection-background-color: @@accent@@;
}
QLineEdit:hover, QLineEdit:focus { background: transparent; }

QTextEdit, QPlainTextEdit {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: @@text@@;
    padding: 6px;
    selection-background-color: @@accent@@;
}

QComboBox {
    background-color: transparent;
    border: none;
    padding: 5px 10px;
    border-radius: 8px;
    color: @@text_dim@@;
    font-size: 12px;
}
QComboBox:hover {
    background-color: @@card@@;
    color: @@text@@;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; width: 0; height: 0; }
QComboBox QAbstractItemView {
    background-color: @@card@@;
    border: 1px solid @@border@@;
    border-radius: 10px;
    padding: 4px;
    color: @@text@@;
    selection-background-color: @@card_active@@;
    outline: none;
}

QCheckBox { spacing: 8px; padding: 4px 0; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid @@border@@;
    background: transparent;
}
QCheckBox::indicator:checked {
    background: @@accent@@;
    border-color: @@accent@@;
}

/* ---------- СКРОЛЛБАР (тонкий, как в DSH) ---------- */
QScrollArea, QScrollArea > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 4px 2px;
    border: none;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 45);
    min-height: 32px;
    border-radius: 3px;
    margin: 0 1px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 100);
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 45);
    min-width: 32px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(255, 255, 255, 100);
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { width: 0; }

/* ---------- КАРТОЧКИ И БЛОКИ ---------- */
QFrame#inputWrap {
    background-color: #1f1f1f;
    border: 1px solid #2a2a2a;
    border-radius: 24px;
}

QFrame#userBubble {
    background-color: @@user_bubble@@;
    border: none;
    border-radius: 18px;
}

QFrame#codeBlock {
    background-color: @@code_bg@@;
    border: 1px solid @@border_soft@@;
    border-radius: 10px;
}

QFrame#card {
    background-color: @@card@@;
    border: 1px solid @@border_soft@@;
    border-radius: 12px;
}

QFrame#toolCall {
    background-color: @@card@@;
    border: 1px solid @@border_soft@@;
    border-radius: 10px;
}

QFrame#modal {
    background-color: @@modal_bg@@;
    border: 1px solid @@border@@;
    border-radius: 14px;
}

QFrame#activityBar {
    background: transparent;
    border: none;
}

/* ---------- МЕНЮ ---------- */
QMenu {
    background-color: @@card@@;
    border: 1px solid @@border@@;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 28px 7px 14px;
    border-radius: 6px;
    color: @@text@@;
}
QMenu::item:selected { background-color: @@card_active@@; }
QMenu::separator {
    height: 1px;
    background: @@border_soft@@;
    margin: 4px 8px;
}


QPushButton#dialogCancelBtn {
    background-color: transparent;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 6px 16px;
    color: @@text@@;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#dialogCancelBtn:hover {
    background-color: @@card_hover@@;
    border-color: @@text_mute@@;
}

QPushButton#dialogOkBtn {
    background-color: rgba(255, 255, 255, 22);
    border: none;
    border-radius: 8px;
    padding: 6px 16px;
    color: @@text@@;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#dialogOkBtn:hover {
    background-color: rgba(255, 255, 255, 35);
}
QPushButton#dialogOkBtn:disabled {
    background-color: rgba(255, 255, 255, 8);
    color: @@text_mute@@;
}

QToolTip {
    background-color: @@card@@;
    color: @@text@@;
    border: 1px solid @@border@@;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 12px;
}
"""


def build_qss():
    q = _T
    for k, v in C.items():
        q = q.replace("@@" + k + "@@", v)
    return q


QSS = build_qss()
