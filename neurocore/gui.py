import getpass
"""NeuroCore — основной интерфейс (до веб-стиля)."""
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (QEasingCurve, QEvent, QPoint, QParallelAnimationGroup, QPropertyAnimation,
                             QSize, Qt, QThread, QTimer, Signal)
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                                QFileDialog, QFrame, QGraphicsOpacityEffect,
                                QToolButton,
                                QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                                QMainWindow, QMenu, QMessageBox, QPushButton,
                                QScrollArea, QSizePolicy, QSplitter,
                                QStackedWidget, QTextEdit, QVBoxLayout,
                                QWidget)

from . import config as cfgmod
from . import providers as provmod
from .activity import ActivityBar
from .animations import (PulsingDots, animate_height, animate_max_width, cross_fade, fade_in, fade_out, fade_and_scale, fade_and_slide_y, pop_in, pulse_scale, slide_fade_in, slide_in_x, slide_in_y, slide_panel, smooth_scroll)
from .agent.loop import Agent
from .clipboard import try_get_image_path, is_image_in_clipboard
from .core.message import Message, Role
from .dialogs import PresetDialog, ProviderDialog
from .extensions import (PLUGIN_DIR, PLUGIN_TEMPLATE, PRESET_DIR,
                         load_plugins, load_presets, save_preset, delete_preset,
                         load_plugin_states)
from .icons import make_icon
from .image_preview import AttachThumb, ImagePreview, extract_image_paths
from .code_panel import CodePanel, extract_code_blocks
from .md_render import parse as md_parse
from .model_selector import ModelSelector
from .palette import CommandPalette
from .plugins_page import PluginsPage
from .stylish_dialogs import (info as sd_info,
                                warning as sd_warning,
                                error as sd_error,
                                success as sd_success,
                                question as sd_question,
                                ask_text as sd_ask_text)
from .stylish_dialogs import DialogOverlay
from .sessions import DIR as SESSION_DIR
from .sessions import Session
from .theme import C, QSS
from .token_manager import (save_token, load_token,
                              fetch_token_via_browser)
from .tools.builtin.files import ListDirTool, ReadFileTool, WriteFileTool
from .tools.builtin.gui_control import ALL_DESKTOP_TOOLS
from .tools.builtin.browser_control import ALL_BROWSER_TOOLS
from .tools.builtin.deepseek_search import DeepSeekSearchTool
from .tools.builtin.image import GenerateImageTool
from .tools.builtin.shell import ShellTool
from .tools.builtin.web import WebFetchTool, WebSearchTool
from .tools.registry import ToolRegistry
from .tools_panel import ToolsPanel
from .trajectory import TrajectoryView

VERSION = "3.0.0"
CONFIG_DIR = Path.home() / ".neurocore"
CONFIG_FILE = CONFIG_DIR / "config.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

MONO = "Consolas"
UI = "Segoe UI"

def open_in_explorer(path):
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as e:
        sd_warning(None, str(e))

def time_ago(ts):
    d = time.time() - ts
    if d < 60:
        return "сейчас"
    if d < 3600:
        return str(int(d / 60)) + "мин"
    if d < 86400:
        return str(int(d / 3600)) + "ч"
    if d < 86400 * 30:
        return str(int(d / 86400)) + "д"
    return datetime.fromtimestamp(ts).strftime("%d.%m")

def now_hm():
    return datetime.now().strftime("%H:%M")

def ibtn(name, color=None, size=16, tip="", pad=6):
    b = QPushButton()
    b.setIcon(make_icon(name, color or C["text_dim"], size))
    b.setIconSize(QSize(size, size))
    b.setCursor(Qt.PointingHandCursor)
    b.setFixedSize(size + pad * 2, size + pad * 2)
    b.setObjectName("iconBtn")
    if tip:
        b.setToolTip(tip)
    return b

# ============================================================
class AgentWorker(QThread):
    event = Signal(str, dict)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, agent, text, attachments=None):
        super().__init__()
        self.agent = agent
        self.text = text
        self.attachments = attachments or []
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            self.agent.on_event = lambda ev, **d: self.event.emit(ev, d)
            self.agent.should_stop = lambda: self._stop
            self.done.emit(self.agent.run(self.text,
                                            attachments=self.attachments))
        except Exception as e:
            self.error.emit(type(e).__name__ + ": " + str(e))

# ============================================================
class UserBubble(QWidget):
    def __init__(self, text, attachments=None, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 14, 0, 2)
        lay.setSpacing(6)

        row = QHBoxLayout()
        row.addStretch(1)

        col = QVBoxLayout()
        col.setSpacing(6)

        # картинки-вложения
        if attachments:
            for path in attachments:
                prev = ImagePreview(path)
                col.addWidget(prev, alignment=Qt.AlignRight)

        # текст (если есть)
        if text and text.strip():
            b = QFrame()
            b.setObjectName("userBubble")
            bl = QVBoxLayout(b)
            bl.setContentsMargins(16, 10, 16, 10)
            msg = QLabel(text)
            msg.setWordWrap(True)
            msg.setMaximumWidth(560)
            msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
            msg.setStyleSheet(
                "font-family: " + UI + "; font-size: 13px; "
                "color: " + C["text"] + ";")
            bl.addWidget(msg)
            col.addWidget(b, alignment=Qt.AlignRight)

        row.addLayout(col)
        lay.addLayout(row)

        # метаданные
        meta = QHBoxLayout()
        meta.setContentsMargins(0, 0, 6, 0)
        meta.setSpacing(4)
        meta.addStretch(1)
        t = QLabel(now_hm())
        t.setObjectName("mute")
        meta.addWidget(t)
        copy_text = text if text else "(вложение)"
        cp = ibtn("copy", C["text_mute"], 11, "Копировать", 4)
        cp.clicked.connect(lambda: QApplication.clipboard().setText(copy_text))
        meta.addWidget(cp)
        lay.addLayout(meta)

class ToolCallBlock(QFrame):
    def __init__(self, name, args, parent=None):
        super().__init__(parent)
        self.setObjectName("toolCall")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)
        ic = QLabel()
        ic.setPixmap(make_icon("wrench", C["warning"], 13).pixmap(13, 13))
        lay.addWidget(ic)
        args_str = ", ".join(k + "=" + repr(v)
                              for k, v in (args or {}).items())
        if len(args_str) > 90:
            args_str = args_str[:90] + "…"
        nm = QLabel(name + "(" + args_str + ")")
        nm.setStyleSheet(
            "font-family: " + MONO + "; font-size: 11px; "
            "color: " + C["text_dim"] + ";")
        lay.addWidget(nm, 1)
        self.st = QLabel("выполняется")
        self.st.setObjectName("mute")
        lay.addWidget(self.st)

    def set_result(self, result):
        short = result if len(result) < 60 else result[:60] + "…"
        short = short.replace("\n", " ")
        self.st.setText("→ " + short)

class AssistantBlock(QWidget):
    def __init__(self, text, elapsed=None, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 16)
        lay.setSpacing(6)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        av = QLabel()
        av.setPixmap(make_icon("brain", C["accent"], 16).pixmap(16, 16))
        av.setFixedSize(28, 28)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(
            "background: " + C["card"] + "; border-radius: 14px;")
        head.addWidget(av)
        name = QLabel("NeuroCore")
        name.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "font-weight: 600; color: " + C["text"] + ";")
        head.addWidget(name)
        if elapsed is not None:
            comp = QLabel("· " + str(int(elapsed)) + " с")
            comp.setObjectName("mute")
            head.addWidget(comp)
            arr = ibtn("chevron_down", C["text_mute"], 11, "", 4)
            arr.clicked.connect(
                lambda: self.body.setVisible(not self.body.isVisible()))
            head.addWidget(arr)
        head.addStretch(1)
        lay.addLayout(head)

        self.body = QWidget()
        bl = QVBoxLayout(self.body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(6)
        self._render(bl, text)
        lay.addWidget(self.body)

        acts = QHBoxLayout()
        acts.setContentsMargins(0, 2, 0, 0)
        acts.setSpacing(1)
        for icon, tip in [("copy", "Копировать"), ("thumbs_up", "Хорошо"),
                            ("thumbs_down", "Плохо"), ("share", "Поделиться")]:
            b = ibtn(icon, C["text_mute"], 13, tip, 5)
            if icon in ("copy", "share"):
                b.clicked.connect(
                    lambda _=False, t=text: QApplication.clipboard().setText(t))
            acts.addWidget(b)
        acts.addSpacing(12)
        usage = QLabel("Использовано: " + str(len(text.split())) + " токенов")
        usage.setObjectName("mute")
        acts.addWidget(usage)
        acts.addSpacing(10)
        t = QLabel(now_hm())
        t.setObjectName("mute")
        acts.addWidget(t)
        acts.addStretch(1)
        lay.addLayout(acts)

    def _render(self, parent_layout, text):
        for w in md_parse(text):
            parent_layout.addWidget(w)

class ThinkingBlock(QFrame):
    def __init__(self, iteration, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 4)
        lay.setSpacing(8)
        ic = QLabel()
        ic.setPixmap(make_icon("sparkle", C["accent"], 12).pixmap(12, 12))
        lay.addWidget(ic)
        lbl = QLabel("NeuroCore думает")
        lbl.setStyleSheet(
            "font-family: " + UI + "; font-size: 12px; "
            "color: " + C["text_dim"] + ";")
        lay.addWidget(lbl)

        self.dots = PulsingDots()
        lay.addWidget(self.dots)

        it = QLabel("· итерация " + str(iteration))
        it.setObjectName("mute")
        lay.addWidget(it)
        lay.addStretch(1)

        # появление сдвигом + увеличенная точка
        QTimer.singleShot(10, lambda: fade_and_slide_y(
            self, duration=300, offset=8))

class ChatArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.inner = QWidget()
        self.lay = QVBoxLayout(self.inner)
        self.lay.setContentsMargins(64, 20, 64, 32)
        self.lay.setSpacing(4)
        self.lay.addStretch(1)
        self.setWidget(self.inner)
        self._tools = []
        self._user_at_bottom = True

        # ---------- автопрокрутка за растущим контентом ----------
        self._user_at_bottom = True
        self._auto_scroll_enabled = True
        sb = self.verticalScrollBar()
        if sb is not None:
            sb.valueChanged.connect(self._on_scroll_value)
            sb.rangeChanged.connect(self._on_scroll_range)
            if not hasattr(self, "_scroll_anim"):
                self._scroll_anim = None
        self._activity_row = None
        self._activity_widget = None
        self._scroll_anim = None

    def wheelEvent(self, event):
        """Плавный скролл колесом с инерцией."""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        sb = self.verticalScrollBar()
        if sb is None:
            return

        # сколько «ноток» колеса
        delta_pixels = event.angleDelta().y()
        # множитель: одна нота = -120°, хотим ~140px за щелчок
        step = int(-delta_pixels / 120 * 180)

        # текущая целевая позиция
        cur = sb.value()
        # если идёт анимация — берём её конец как базу
        base = getattr(self, "_scroll_target", cur)
        if not hasattr(self, "_scroll_target"):
            self._scroll_target = cur

        target = base + step
        # ограничиваем
        target = max(sb.minimum(), min(sb.maximum(), target))
        self._scroll_target = target

        # останавливаем предыдущую анимацию
        if hasattr(self, "_wheel_anim") and self._wheel_anim is not None:
            try:
                self._wheel_anim.stop()
            except Exception:
                pass

        anim = QPropertyAnimation(sb, b"value", self)
        anim.setDuration(480)
        anim.setStartValue(cur)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutSine)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._wheel_anim = anim

        # синхронизируем _scroll_target когда анимация завершится
        def _sync():
            self._scroll_target = sb.value()
        anim.finished.connect(_sync)

        event.accept()

    def add(self, w, anim=True, batch=False):
        self.lay.insertWidget(self.lay.count() - 1, w)
        if anim:
            try:
                w.adjustSize()
            except Exception:
                pass
            try:
                eff = QGraphicsOpacityEffect(w)
                eff.setOpacity(0.0)
                w.setGraphicsEffect(eff)

                fade = QPropertyAnimation(eff, b"opacity", w)
                fade.setDuration(220)
                fade.setStartValue(0.0)
                fade.setEndValue(1.0)
                fade.setEasingCurve(QEasingCurve.OutCubic)

                # после анимации — вернуть виджету полную высоту
                def _restore():
                    try:
                        w.setMaximumHeight(16777215)
                        w.setGraphicsEffect(None)
                    except Exception:
                        pass

                fade.finished.connect(_restore)
                fade.start(QParallelAnimationGroup.DeleteWhenStopped)
                w._fade_anim = fade
            except Exception:
                pass
        if not batch:
            QTimer.singleShot(60, lambda: self.to_end(smooth=True, duration=320))
    def _on_scroll_value(self, value):
        """Пользователь сам поскроллил — проверяем, внизу ли он."""
        sb = self.verticalScrollBar()
        if sb is None:
            return
        # если до конца меньше 30px — считаем что внизу
        self._user_at_bottom = (sb.maximum() - value) < 30

    def _on_scroll_range(self, min_val, max_val):
        """Контент вырос — тянем вниз если пользователь не ушёл наверх."""
        if not self._auto_scroll_enabled:
            return
        if not self._user_at_bottom:
            return
        # запускаем плавный доезд
        self.to_end(smooth=True, duration=320)

    def to_end(self, smooth=True, duration=560):
        """Плавно прокрутить вниз с easing."""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        sb = self.verticalScrollBar()
        if sb is None:
            return
        target = sb.maximum()

        # если до конца меньше 3px — уже там
        if abs(sb.value() - target) < 3:
            return

        if not smooth:
            sb.setValue(target)
            return

        # останавливаем предыдущую анимацию
        if hasattr(self, "_scroll_anim") and self._scroll_anim is not None:
            try:
                self._scroll_anim.stop()
            except Exception:
                pass

        anim = QPropertyAnimation(sb, b"value", self)
        anim.setDuration(duration)
        anim.setStartValue(sb.value())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._scroll_anim = anim

    def clear_all(self):
        while self.lay.count() > 1:
            it = self.lay.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self._tools = []
    def tool_call(self, name, args):
        b = ToolCallBlock(name, args)
        self.add(b)
        self._tools.append(b)

    # ---------- индикатор активности ----------
    def show_activity(self, text, icon="sparkle"):
        """Показать индикатор в конце чата."""
        from .activity import ActivityBar
        if self._activity_row is None:
            # создаём одноразовый контейнер
            from PySide6.QtWidgets import QWidget, QHBoxLayout
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(4, 10, 4, 4)
            rl.setSpacing(0)
            act = ActivityBar()
            rl.addWidget(act)
            rl.addStretch(1)
            # вставляем перед stretch
            self.lay.insertWidget(self.lay.count() - 1, row)
            self._activity_row = row
            self._activity_widget = act
            QTimer.singleShot(40, lambda: self.to_end(smooth=True, duration=300))
        # обновляем текст
        try:
            self._activity_widget.set_text(text, icon)
        except Exception as e:
            print("[chat activity] ошибка:", e)

    def finish_activity(self, text="Готово"):
        """Показать 'Готово' и удалить через 1.2с."""
        if self._activity_widget is None:
            return
        try:
            self._activity_widget.set_done(text)
        except Exception:
            pass
        row = self._activity_row
        self._activity_row = None
        self._activity_widget = None
        self._scroll_anim = None
        QTimer.singleShot(1200, lambda: self._remove_activity_row(row))

    def hide_activity(self):
        row = self._activity_row
        self._activity_row = None
        self._activity_widget = None
        self._scroll_anim = None
        self._remove_activity_row(row)

    def _remove_activity_row(self, row):
        if row is None:
            return
        try:
            row.deleteLater()
        except Exception:
            pass

    def tool_result(self, r):
        if self._tools:
            self._tools.pop(0).set_result(r)

# ============================================================
class Sidebar(QWidget):
    new_session = Signal()
    session_selected = Signal(str)
    session_menu = Signal(str, QPoint)
    open_settings = Signal(str)
    open_plugins = Signal()
    toggle_palette = Signal()
    add_workspace_requested = Signal()
    workspace_selected = Signal(str)
    workspace_menu = Signal(str, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 44, 12, 12)
        lay.setSpacing(4)

        # ---------- бренд-строка (как deepseek harness) ----------
        brand = QHBoxLayout()
        brand.setContentsMargins(4, 4, 4, 10)
        brand.setSpacing(6)
        li = QLabel()
        li.setPixmap(make_icon("brain", C["text"], 18).pixmap(18, 18))
        brand.addWidget(li)
        ln = QLabel("NeuroCore")
        ln.setStyleSheet(
            "font-family: " + UI + "; font-size: 14px; "
            "font-weight: 600; color: " + C["text"] + ";")
        brand.addWidget(ln)
        badge = QLabel("HARNESS")
        badge.setObjectName("badge")
        badge.setStyleSheet(
            "background: #2a2a2a; color: " + C["text_dim"] + "; "
            "font-size: 9px; font-weight: 700; padding: 2px 6px; "
            "border-radius: 4px;")
        brand.addWidget(badge)
        brand.addStretch(1)
        lay.addLayout(brand)

        # ---------- новая сессия (компактная плашка) ----------
        nb = QPushButton("   Новая сессия")
        nb.setObjectName("newSessionBig")
        nb.setIcon(make_icon("plus", C["text"], 14))
        nb.setIconSize(QSize(14, 14))
        nb.setCursor(Qt.PointingHandCursor)
        nb.setFixedHeight(34)
        nb.clicked.connect(self.new_session.emit)
        lay.addWidget(nb)

        lay.addSpacing(8)

        # ---------- plugins / automation ----------
        pb = QPushButton("  Плагины")
        pb.setObjectName("sidebarItem")
        pb.setIcon(make_icon("puzzle", C["text_dim"], 14))
        pb.setIconSize(QSize(14, 14))
        pb.setCursor(Qt.PointingHandCursor)
        pb.setFixedHeight(28)
        pb.clicked.connect(self.open_plugins.emit)
        lay.addWidget(pb)

        ab = QPushButton("  Автоматизация")
        ab.setObjectName("sidebarItem")
        ab.setIcon(make_icon("command", C["text_dim"], 14))
        ab.setIconSize(QSize(14, 14))
        ab.setCursor(Qt.PointingHandCursor)
        ab.setFixedHeight(28)
        ab.clicked.connect(self.toggle_palette.emit)
        lay.addWidget(ab)

        lay.addSpacing(14)

        # ---------- section: workspace ----------
        wh = QHBoxLayout()
        wh.setContentsMargins(6, 0, 4, 4)
        wh.setSpacing(2)
        wl = QLabel("Workspace")
        wl.setObjectName("mute")
        wh.addWidget(wl)
        wh.addStretch(1)
        self.search_inp = QLineEdit()
        self.search_inp.setPlaceholderText("")
        self.search_inp.setStyleSheet(
            "background: transparent; border: none; color: " +
            C["text"] + "; max-width: 0;")
        self.search_inp.textChanged.connect(lambda _: self._refresh())
        wh.addWidget(self.search_inp)
        sr = ibtn("search", C["text_mute"], 12, "Поиск", 4)
        sr.clicked.connect(self._focus_search)
        wh.addWidget(sr)
        add_ws = ibtn("folder_plus", C["text_mute"], 12, "Добавить", 4)
        add_ws.clicked.connect(self.add_workspace_requested.emit)
        wh.addWidget(add_ws)
        lay.addLayout(wh)

        # ---------- список workspace ----------
        self.ws_box = QVBoxLayout()
        self.ws_box.setSpacing(1)
        self.ws_box.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self.ws_box)
        self._rebuild_workspaces()

        lay.addSpacing(10)

        # ---------- section: sessions ----------
        sh = QLabel("Sessions")
        sh.setObjectName("mute")
        sh.setContentsMargins(6, 0, 0, 4)
        lay.addWidget(sh)

        # ---------- список сессий ----------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_w = QWidget()
        self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setContentsMargins(0, 0, 0, 0)
        self.list_l.setSpacing(1)
        self.list_l.addStretch(1)
        self.scroll.setWidget(self.list_w)
        lay.addWidget(self.scroll, 1)

        # нижний блок — Настройки
        self.settings_btn = QPushButton("   Настройки")
        self.settings_btn.setObjectName("sidebarItem")
        self.settings_btn.setIcon(
            make_icon("settings", C["text_dim"], 15))
        self.settings_btn.setIconSize(QSize(15, 15))
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFixedHeight(32)
        self.settings_btn.clicked.connect(
            lambda: self.open_settings.emit("account"))
        lay.addWidget(self.settings_btn)

        self._show_more = False
        self._active = None
        self._refresh()

        # ---------- user row внизу ----------
        lay.addSpacing(8)

    def _focus_search(self):
        self.search_inp.setFocus()

    def _rebuild_workspaces(self):
        while self.ws_box.count():
            it = self.ws_box.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        cfg = cfgmod.load()
        active = cfg.get("active_workspace", "По умолчанию")
        for ws in cfgmod.get_workspaces(cfg):
            row = QWidget()
            row.setFixedHeight(30)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(2)
            b = QPushButton("   " + ws["name"])
            b.setObjectName("workspaceItem")
            is_active = ws["name"] == active
            b.setIcon(make_icon("folder",
                                 C["accent"] if is_active else C["text_dim"], 14))
            b.setIconSize(QSize(14, 14))
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(30)
            if is_active:
                b.setStyleSheet(
                    "QPushButton#workspaceItem { background: " + C["card"] +
                    "; color: " + C["text"] + "; border-radius: 8px; "
                    "text-align: left; padding: 6px 12px; font-weight: 600; }")
            b.clicked.connect(
                lambda _=False, n=ws["name"]:
                self.workspace_selected.emit(n))
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(
                lambda pos, n=ws["name"], w=b:
                self.workspace_menu.emit(n, w.mapToGlobal(pos)))
            rl.addWidget(b, 1)
            self.ws_box.addWidget(row)

    def _refresh(self):
        while self.list_l.count() > 1:
            it = self.list_l.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        sessions = Session.all()
        sessions = [s for s in sessions if s.messages]
        q = self.search_inp.text().lower().strip()
        if q:
            sessions = [s for s in sessions if q in s.title.lower()]
        cfg = cfgmod.load()
        active_ws = cfg.get("active_workspace", "По умолчанию")
        if active_ws != "По умолчанию":
            sessions = [s for s in sessions
                        if getattr(s, "workspace", "") == active_ws]
        shown = sessions if self._show_more else sessions[:5]

        if not sessions:
            e = QLabel("Пока нет сессий")
            e.setObjectName("mute")
            e.setContentsMargins(12, 12, 0, 0)
            self.list_l.insertWidget(0, e)
            return

        for i, s in enumerate(shown):
            row = QWidget()
            row.setFixedHeight(32)
            active = s.id == self._active
            if active:
                row.setStyleSheet(
                    "background: " + C["card"] + "; border-radius: 8px;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 0, 10, 0)
            rl.setSpacing(8)
            title = QLabel(s.title)
            title.setStyleSheet(
                "font-family: " + UI + "; font-size: 12px; color: " +
                (C["text"] if active else C["text_dim"]) + "; "
                "background: transparent;")
            title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            rl.addWidget(title, 1)
            t = QLabel(time_ago(s.updated))
            t.setStyleSheet(
                "font-family: " + UI + "; font-size: 11px; color: " +
                C["text_mute"] + "; background: transparent;")
            rl.addWidget(t)
            row.mousePressEvent = (
                lambda e, sid=s.id: self.session_selected.emit(sid))
            row.setContextMenuPolicy(Qt.CustomContextMenu)
            row.customContextMenuRequested.connect(
                lambda pos, sid=s.id, w=row:
                self.session_menu.emit(sid, w.mapToGlobal(pos)))
            row.setCursor(Qt.PointingHandCursor)
            self.list_l.insertWidget(i, row)

        if not self._show_more and len(sessions) > 5:
            more = QPushButton("Показать ещё " + str(len(sessions) - 5) +
                                " сессий")
            more.setObjectName("showMore")
            more.setCursor(Qt.PointingHandCursor)
            more.setFixedHeight(28)
            more.clicked.connect(self._expand)
            self.list_l.insertWidget(len(shown), more)

    def _expand(self):
        self._show_more = True
        self._refresh()

    def set_active(self, sid):
        self._active = sid
        self._refresh()

# ============================================================
class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setFixedHeight(52)
        self.setMouseTracking(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 8, 24, 8)
        lay.setSpacing(10)
        self.title = QLabel("Новая сессия")
        self.title.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "font-weight: 600; color: " + C["text_dim"] + ";")
        lay.addWidget(self.title)
        mode = QLabel("◐  Стандартный режим")
        mode.setObjectName("mute")
        lay.addWidget(mode)
        lay.addStretch(1)
        self.dots_btn = ibtn("dots", C["text_dim"], 15, "Меню", 6)
        lay.addWidget(self.dots_btn)
        self.tools_btn = ibtn("panel_right", C["text_dim"], 15,
                                "Инструменты (Ctrl+B)", 6)
        # кнопка панели кода
        self.code_btn = ibtn("file", C["text_dim"], 15, "Код (Ctrl+E)", 6)
        self.code_btn.clicked.connect(lambda: self.window().toggle_code_panel() if hasattr(self.window(), "toggle_code_panel") else None)
        lay.addWidget(self.tools_btn)
        lay.addWidget(self.code_btn)

# ============================================================
class TabsRow(QWidget):
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(2)
        self.tabs = []
        for i, label in enumerate(["Чат", "Траектория"]):
            b = QPushButton(label)
            b.setObjectName("tabBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(36)
            b.clicked.connect(
                lambda _=False, idx=i: self.tab_changed.emit(idx))
            lay.addWidget(b)
            self.tabs.append(b)
        lay.addStretch(1)
        self.set_active(0)

    def set_active(self, idx):
        for i, b in enumerate(self.tabs):
            b.setProperty("active", "true" if i == idx else "false")
            b.style().unpolish(b)
            b.style().polish(b)

# ============================================================
class FullAccessDialog(QDialog):
    """Диалог подтверждения полного доступа к системе."""

    def __init__(self, parent=None):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            QCheckBox, QPushButton,
        )

        super().__init__(parent)
        self.setWindowTitle("Включить полный доступ?")
        self.setModal(True)
        self.setFixedWidth(500)
        try:
            self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        except Exception:
            pass

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # -------- заголовок с иконкой --------
        h = QHBoxLayout()
        h.setSpacing(10)
        ic = QLabel()
        try:
            ic.setPixmap(make_icon("shield", C["danger"], 20).pixmap(20, 20))
        except Exception:
            pass
        h.addWidget(ic)

        title = QLabel("Включить полный доступ?")
        title.setStyleSheet(
            "font-family: " + UI + "; font-size: 15px; "
            "font-weight: 600; color: " + C["text"] + ";"
        )
        h.addWidget(title)
        h.addStretch(1)
        lay.addLayout(h)

        # -------- поясняющий текст --------
        body = QLabel(
            "Полный доступ сокращает количество подтверждений и позволяет "
            "агенту выполнять действия напрямую: изменять файлы, запускать "
            "команды, обращаться к сети.\n\n"
            "Команды выполняются от имени вашего пользователя Windows. "
            "Используйте только если доверяете текущей задаче."
        )
        body.setWordWrap(True)
        body.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text_dim"] + ";"
        )
        lay.addWidget(body)

        # -------- чекбокс подтверждения --------
        self.check = QCheckBox("Я понимаю риски и хочу продолжить")
        self.check.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text"] + ";"
        )
        lay.addWidget(self.check)

        # -------- кнопки --------
        btns = QHBoxLayout()
        btns.addStretch(1)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("pillBtn")
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("Включить полный доступ")
        self.ok_btn.setObjectName("sendBtn")
        self.ok_btn.setFixedHeight(32)
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accept)
        btns.addWidget(self.ok_btn)

        self.check.toggled.connect(self.ok_btn.setEnabled)
        lay.addLayout(btns)

class InputArea(QWidget):
    submitted = Signal(str)
    attachments_submitted = Signal(list)
    stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._attachments = []
        self._is_busy = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 4, 20, 8)
        lay.setSpacing(6)

        # превью вложений
        self.attach_bar = QWidget()
        self.attach_bar.setVisible(False)
        self.attach_lay = QHBoxLayout(self.attach_bar)
        self.attach_lay.setContentsMargins(4, 0, 4, 6)
        self.attach_lay.setSpacing(8)
        self.attach_lay.addStretch(1)
        lay.addWidget(self.attach_bar)

        # карточка
        wrap = QFrame()
        wrap.setObjectName("inputWrap")
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(16, 12, 16, 10)
        wl.setSpacing(6)

        self.editor = QTextEdit()
        self.editor.setObjectName("chatInput")
        self.editor.setPlaceholderText(
            "Сообщение или задача.  / команды.  @ файлы или сессии")
        self.editor.setFixedHeight(48)
        self.editor.installEventFilter(self)
        wl.addWidget(self.editor)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)

        attach = ibtn("plus", C["text_dim"], 15, "Прикрепить файл", 6)
        attach.clicked.connect(self._attach)
        bottom.addWidget(attach)

        self.perm_btn = QPushButton("  Запись в workspace  " + chr(94))
        self.perm_btn.setObjectName("pillBtn")
        self.perm_btn.setIcon(make_icon("shield", C["text_dim"], 12))
        self.perm_btn.setIconSize(QSize(12, 12))
        self.perm_btn.setCursor(Qt.PointingHandCursor)
        self.perm_btn.setFixedHeight(28)
        self.perm_btn.setToolTip("Права агента на запись файлов")
        self.perm_btn.clicked.connect(self._show_perm_menu)
        self.perm_mode = "workspace_write"
        bottom.addWidget(self.perm_btn)

        bottom.addStretch(1)

        self.model_combo = ModelSelector()
        bottom.addWidget(self.model_combo)

        self.send_btn = QToolButton()
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setIcon(make_icon("send", "#ffffff", 14))
        self.send_btn.setIconSize(QSize(14, 14))
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.setToolTip("Отправить (Enter)")
        self.send_btn.setAutoRaise(False)
        self.send_btn.clicked.connect(self._on_send_clicked)
        bottom.addWidget(self.send_btn)

        self.stop_btn = self.send_btn

        wl.addLayout(bottom)
        lay.addWidget(wrap)

    PERM_OPTIONS = [
        ("read_only", "Только чтение"),
        ("workspace_write", "Запись в workspace"),
        ("full_access", "Полный доступ"),
    ]

    def _show_perm_menu(self):
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        for key, label in self.PERM_OPTIONS:
            act = menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(getattr(self, "perm_mode", "full_access") == key)
            act.triggered.connect(
                lambda _=False, k=key: self._set_perm_mode(k)
            )

        pos = self.perm_btn.mapToGlobal(QPoint(0, 0))
        menu_h = menu.sizeHint().height()
        pos.setY(pos.y() - menu_h - 4)
        menu.exec(pos)

    def _set_perm_mode(self, key):
        # для full_access — сначала подтверждение пользователя
        if key == "full_access":
            ov = getattr(self.window(), "full_access_overlay", None)
            if ov is not None:
                ov.open_for(lambda: self._apply_perm_mode(key))
                return
        self.perm_mode = key
        labels = dict(self.PERM_OPTIONS)
        self.perm_btn.setText("  " + labels.get(key, key) + "  ^")

        color = C["accent"] if key == "full_access" else C["text_dim"]
        try:
            self.perm_btn.setIcon(make_icon("shield", color, 12))
        except Exception:
            pass

        w = self.window()
        if hasattr(w, "_on_perm_changed"):
            try:
                w._on_perm_changed(key)
            except Exception as e:
                print(f"[perm] window handler: {e}", flush=True)

    def show_activity(self, text, icon="sparkle", spinning=False):
        w = self.window()
        if hasattr(w, "chat") and hasattr(w.chat, "show_activity"):
            w.chat.show_activity(text, icon)

    def show_activity_done(self, text="Готово"):
        w = self.window()
        if hasattr(w, "chat") and hasattr(w.chat, "finish_activity"):
            w.chat.finish_activity(text)

    def hide_activity(self):
        w = self.window()
        if hasattr(w, "chat") and hasattr(w.chat, "hide_activity"):
            w.chat.hide_activity()

    def set_busy(self, busy):
        self._is_busy = busy
        if busy:
            self.send_btn.setObjectName("stopActiveBtn")
            self.send_btn.setIcon(make_icon("stop", "#ffffff", 14))
            self.send_btn.setToolTip("Остановить")
        else:
            self.send_btn.setObjectName("sendBtn")
            self.send_btn.setIcon(make_icon("send", "#ffffff", 14))
            self.send_btn.setToolTip("Отправить (Enter)")
        self.send_btn.style().unpolish(self.send_btn)
        self.send_btn.style().polish(self.send_btn)
        self.model_combo.setEnabled(not busy)

    def set_models(self, models, current):
        self.model_combo.set_models(models, current)

    def reload_presets(self):
        pass

    def _attach(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Прикрепить файлы")
        if files:
            for f in files:
                paths = extract_image_paths(f)
                if paths:
                    for p in paths:
                        self._add_attachment(p)
                else:
                    cur = self.editor.toPlainText()
                    pre = "\n" if cur and not cur.endswith("\n") else ""
                    self.editor.setPlainText(cur + pre + f + "\n")

    def eventFilter(self, obj, event):
        if obj is not self.editor:
            return super().eventFilter(obj, event)
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:
                    return False
                self._submit()
                return True
            if (event.key() == Qt.Key_V and
                    event.modifiers() & Qt.ControlModifier):
                if self._try_paste_image():
                    return True
                return False
        if event.type() == QEvent.Drop:
            md = event.mimeData()
            if md.hasImage():
                self._insert_mime_image(md)
                return True
            if md.hasUrls():
                paths = [u.toLocalFile() for u in md.urls()
                          if u.toLocalFile()]
                if paths:
                    self._insert_paths(paths)
                    return True
        if event.type() == QEvent.DragEnter:
            md = event.mimeData()
            if md.hasImage() or md.hasUrls():
                event.acceptProposedAction()
                return True
        return super().eventFilter(obj, event)

    def _try_paste_image(self):
        try:
            p = try_get_image_path()
        except Exception as e:
            print("[paste] ошибка:", e)
            return False
        if not p:
            return False
        self._add_attachment(str(p))
        return True

    def _add_attachment(self, path):
        if path in self._attachments:
            return
        self._attachments.append(path)
        thumb = AttachThumb(path)
        thumb.removed.connect(self._remove_attachment)
        self.attach_lay.insertWidget(self.attach_lay.count() - 1, thumb)
        self.attach_bar.setVisible(True)

    def _remove_attachment(self, path):
        if path in self._attachments:
            self._attachments.remove(path)
        for i in range(self.attach_lay.count()):
            item = self.attach_lay.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, AttachThumb) and w._path == path:
                w.deleteLater()
                break
        if not self._attachments:
            self.attach_bar.setVisible(False)

    def _clear_attachments(self):
        self._attachments.clear()
        for i in reversed(range(self.attach_lay.count())):
            item = self.attach_lay.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, AttachThumb):
                w.deleteLater()
        self.attach_bar.setVisible(False)

    def _insert_mime_image(self, md):
        try:
            img = md.imageData()
            from PySide6.QtGui import QImage
            if not isinstance(img, QImage):
                return
            from .clipboard import _save_qimage
            path = _save_qimage(img)
            self._add_attachment(str(path))
        except Exception as e:
            print("[drop image] ошибка:", e)

    def _insert_paths(self, paths):
        cur = self.editor.toPlainText()
        pre = "\n" if cur and not cur.endswith("\n") else ""
        self.editor.setPlainText(cur + pre + "\n".join(paths) + "\n")
        from PySide6.QtGui import QTextCursor
        c = self.editor.textCursor()
        c.movePosition(QTextCursor.End)
        self.editor.setTextCursor(c)
        self.editor.setFocus()

    def _submit(self):
        text = self.editor.toPlainText().strip()
        if not text and not self._attachments:
            return
        self.editor.clear()
        if self._attachments:
            self.attachments_submitted.emit(list(self._attachments))
        self._clear_attachments()
        self.submitted.emit(text)

    def _on_send_clicked(self):
        if getattr(self, "_is_busy", False):
            self.stopped.emit()
        else:
            self._submit()

# ============================================================
class Welcome(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        w = QVBoxLayout()
        w.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(make_icon("brain", C["accent"], 72).pixmap(72, 72))
        ic.setAlignment(Qt.AlignCenter)
        w.addWidget(ic)
        row = QHBoxLayout()
        row.addStretch(1)
        t = QLabel("Into the Unknown")
        t.setStyleSheet(
            "font-family: " + UI + "; font-size: 26px; "
            "font-weight: 700; color: " + C["text"] + ";")
        row.addWidget(t)
        row.addStretch(1)
        w.addLayout(row)
        h = QLabel("Ctrl+K — палитра  ·  Ctrl+N — новая сессия")
        h.setObjectName("mute")
        h.setAlignment(Qt.AlignCenter)
        w.addWidget(h)
        lay.addLayout(w)
        lay.addStretch(1)

# ============================================================
class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_tab = "account"
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(14)

        head = QHBoxLayout()
        head.setSpacing(8)
        title = QLabel("Настройки")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        head.addWidget(title)
        head.addStretch(1)
        op = QPushButton("  Открыть config")
        op.setObjectName("newSessionBig")
        op.setIcon(make_icon("file", C["text"], 13))
        op.setIconSize(QSize(13, 13))
        op.setCursor(Qt.PointingHandCursor)
        op.setFixedHeight(32)
        op.clicked.connect(lambda: open_in_explorer(CONFIG_FILE))
        head.addWidget(op)
        self.back_btn = ibtn("close", C["text_dim"], 14, "Закрыть", 6)
        head.addWidget(self.back_btn)
        main.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(20)
        tabs = QVBoxLayout()
        tabs.setSpacing(2)
        self._btns = {}
        for key, name, ic in [("account", "Аккаунт", "user"),
                                ("models", "Модели", "sparkles"),
                                ("presets", "Пресеты", "star"),
                                ("storage", "Хранилище", "folder"),
                                ("about", "О программе", "info")]:
            b = QPushButton("   " + name)
            b.setObjectName("sidebarItem")
            b.setIcon(make_icon(ic, C["text_dim"], 15))
            b.setIconSize(QSize(15, 15))
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(36)
            b.setFixedWidth(180)
            b.clicked.connect(lambda _=False, k=key: self.show_tab(k))
            tabs.addWidget(b)
            self._btns[key] = b

        # кнопка получения токена DeepSeek
        self._token_btn = QPushButton("   Получить токен")
        self._token_btn.setObjectName("sidebarItem")
        self._token_btn.setIcon(make_icon("key", C["accent"], 15))
        self._token_btn.setIconSize(QSize(15, 15))
        self._token_btn.setCursor(Qt.PointingHandCursor)
        self._token_btn.setFixedHeight(36)
        self._token_btn.setFixedWidth(180)
        self._token_btn.clicked.connect(self._fetch_token)
        tabs.addWidget(self._token_btn)
        tabs.addStretch(1)
        body.addLayout(tabs)
        self.content = QVBoxLayout()
        body.addLayout(self.content, 1)
        main.addLayout(body, 1)

    def show_tab(self, key):
        self._last_tab = key
        for k, b in self._btns.items():
            if k == key:
                b.setStyleSheet(
                    "background: " + C["card_hover"] +
                    "; color: " + C["text"] + ";")
            else:
                b.setStyleSheet("")
        while self.content.count():
            it = self.content.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        getattr(self, "_tab_" + key)()

    def _card(self):
        f = QFrame()
        f.setObjectName("card")
        l = QVBoxLayout(f)
        l.setContentsMargins(18, 14, 18, 14)
        l.setSpacing(8)
        return f, l

    def _tab_account(self):
        f, l = self._card()
        t = QLabel("API-токен")
        t.setStyleSheet("font-weight: 700; font-size: 14px;")
        l.addWidget(t)
        tok = os.getenv("DEEPSEEK_TOKEN", "")
        s = QLabel("● Установлен" if tok else "● Не задан")
        s.setStyleSheet(
            "color: " + (C["success"] if tok else C["danger"]) + ";")
        l.addWidget(s)
        test = QPushButton("Проверить соединение")
        test.setObjectName("primary")
        test.setCursor(Qt.PointingHandCursor)
        test.clicked.connect(self._test)
        l.addWidget(test)
        self._lbl = QLabel("")
        self._lbl.setObjectName("mute")
        self._lbl.setWordWrap(True)
        l.addWidget(self._lbl)
        self.content.addWidget(f)
        self.content.addStretch(1)

    def _test(self):
        import threading
        cfg = cfgmod.load()
        self._lbl.setText("проверяю...")

        def run():
            try:
                pr = provmod.build(cfg)
                r = pr.chat([Message(Role.USER, "ответь: ok")])
                QTimer.singleShot(0, lambda: self._lbl.setText(
                    "OK: " + r.content[:120]))
            except Exception as e:
                msg = str(e)
                QTimer.singleShot(0, lambda: self._lbl.setText(
                    "Ошибка: " + msg[:200]))
        threading.Thread(target=run, daemon=True).start()

    def _tab_models(self):
        cfg = cfgmod.load()
        f, l = self._card()
        t = QLabel("Провайдеры")
        t.setStyleSheet("font-weight: 700; font-size: 14px;")
        l.addWidget(t)
        self._prov = QComboBox()
        self._prov.setFixedHeight(34)
        for p in cfg["providers"]:
            self._prov.addItem(p["name"], userData=p["id"])
        i = self._prov.findData(cfg.get("active_provider"))
        if i >= 0:
            self._prov.setCurrentIndex(i)
        l.addWidget(self._prov)
        self.content.addWidget(f)
        self.content.addStretch(1)

    def _tab_presets(self):
        f, l = self._card()
        t = QLabel("Пресеты")
        t.setStyleSheet("font-weight: 700; font-size: 14px;")
        l.addWidget(t)
        for p in load_presets():
            nm = QLabel("• " + p.name)
            nm.setObjectName("dim")
            l.addWidget(nm)
        self.content.addWidget(f)
        self.content.addStretch(1)

    def _tab_storage(self):
        f, l = self._card()
        t = QLabel("Хранилище")
        t.setStyleSheet("font-weight: 700; font-size: 14px;")
        l.addWidget(t)
        l.addWidget(QLabel(str(CONFIG_DIR)))
        s = Session.all()
        l.addWidget(QLabel("Сессий: %d" % len(s)))
        self.content.addWidget(f)

        # ---------- Папка сохранения файлов ----------
        f2, l2 = self._card()
        t2 = QLabel("Папка сохранения файлов")
        t2.setStyleSheet("font-weight: 700; font-size: 14px;")
        l2.addWidget(t2)

        hint = QLabel(
            "Если агент сохраняет файл без указания пути — "
            "файл попадает сюда.")
        hint.setObjectName("mute")
        hint.setWordWrap(True)
        l2.addWidget(hint)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._out_dir_edit = QLineEdit()
        self._out_dir_edit.setText(cfgmod.get_output_dir())
        self._out_dir_edit.setReadOnly(True)
        self._out_dir_edit.setFixedHeight(34)
        self._out_dir_edit.setStyleSheet(
            "QLineEdit { background: " + C["card"] + "; "
            "border: 1px solid " + C["border"] + "; "
            "border-radius: 8px; padding: 6px 10px; "
            "color: " + C["text"] + "; font-size: 12px; }")
        row.addWidget(self._out_dir_edit, 1)

        pick = QPushButton("Выбрать…")
        pick.setObjectName("primary")
        pick.setCursor(Qt.PointingHandCursor)
        pick.setFixedHeight(34)
        pick.clicked.connect(self._pick_out_dir)
        row.addWidget(pick)

        openb = QPushButton("Открыть")
        openb.setCursor(Qt.PointingHandCursor)
        openb.setFixedHeight(34)
        openb.clicked.connect(
            lambda: open_in_explorer(self._out_dir_edit.text()))
        row.addWidget(openb)

        l2.addLayout(row)

        # кнопка сброса
        reset = QPushButton("Сбросить (использовать папку проекта)")
        reset.setObjectName("sidebarItem")
        reset.setCursor(Qt.PointingHandCursor)
        reset.setFixedHeight(30)
        reset.clicked.connect(self._reset_out_dir)
        l2.addWidget(reset)

        self.content.addWidget(f2)
        self.content.addStretch(1)

    def _pick_out_dir(self):
        """Открыть диалог выбора папки."""
        from PySide6.QtWidgets import QFileDialog
        current = cfgmod.get_output_dir()
        d = QFileDialog.getExistingDirectory(
            self, "Выбери папку для сохранения файлов",
            current, QFileDialog.ShowDirsOnly)
        if d:
            cfgmod.set_output_dir(d)
            if hasattr(self, "_out_dir_edit"):
                self._out_dir_edit.setText(d)
            print(f"[outdir] выбрана папка: {d}", flush=True)

    def _reset_out_dir(self):
        """Сбросить папку на cwd."""
        cfgmod.set_output_dir("")
        if hasattr(self, "_out_dir_edit"):
            self._out_dir_edit.setText(cfgmod.get_output_dir())
        print("[outdir] сброшено на cwd", flush=True)


    def _tab_about(self):
        f, l = self._card()
        n = QLabel("NeuroCore")
        n.setStyleSheet("font-size: 18px; font-weight: 700;")
        n.setAlignment(Qt.AlignCenter)
        l.addWidget(n)
        v = QLabel("v" + VERSION)
        v.setObjectName("mute")
        v.setAlignment(Qt.AlignCenter)
        l.addWidget(v)
        self.content.addWidget(f)
        self.content.addStretch(1)


    def _fetch_token(self):
        """Открыть Chrome, дождаться логина, забрать userToken."""
        import threading

        self._token_btn.setEnabled(False)
        self._token_btn.setText("   Открываю Chrome...")

        def worker():
            try:
                t = fetch_token_via_browser()
                if t:
                    save_token(t)
                    print(f"[token] сохранён, длина {len(t)}", flush=True)
                    self._token_btn.setText("   Токен получен")
                else:
                    self._token_btn.setText("   Не удалось, повтори")
            except Exception as e:
                print(f"[token] ошибка: {e}", flush=True)
                self._token_btn.setText("   Ошибка, смотри консоль")
            finally:
                self._token_btn.setEnabled(True)

        threading.Thread(target=worker, daemon=True).start()


class SettingsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "SettingsOverlay { background-color: rgba(0, 0, 0, 130); }")
        self.hide()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(80, 60, 80, 60)
        outer.setAlignment(Qt.AlignCenter)
        self.card = QFrame()
        self.card.setObjectName("modal")
        self.card.setMinimumWidth(720)
        self.card.setMaximumWidth(780)
        self.card.setMinimumHeight(500)
        self.card.setMaximumHeight(560)
        outer.addWidget(self.card)
        self.page = SettingsPage(self.card)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(self.page)

# ============================================================
class ImageBubble(QWidget):
    """Картинка в ленте чата. Клик — открывает в системном просмотрщике."""

    def __init__(self, path: str, max_width: int = 480, parent=None):
        super().__init__(parent)
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QLabel, QVBoxLayout

        self._path = path
        pix = QPixmap(path)
        if pix.isNull():
            return
        if pix.width() > max_width:
            pix = pix.scaledToWidth(max_width, Qt.SmoothTransformation)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(4)

        label = QLabel()
        label.setPixmap(pix)
        label.setCursor(Qt.PointingHandCursor)
        label.setStyleSheet(
            "border-radius: 10px; background: rgba(255,255,255,0.03);"
        )
        label.setToolTip(f"{path}\n(клик — открыть)")
        label.mousePressEvent = lambda ev: self._open()
        lay.addWidget(label)

    def _open(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(self._path))

class FullAccessOverlay(QWidget):
    """Overlay внутри главного окна — как SettingsOverlay."""

    accepted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fullAccessOverlay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "QWidget#fullAccessOverlay { background: rgba(0, 0, 0, 160); }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)

        card = QFrame()
        card.setObjectName("modal")
        card.setFixedWidth(440)
        card.setStyleSheet(
            "QFrame#modal { background: " + C["card"] + "; "
            "border: 1px solid " + C["border"] + "; "
            "border-radius: 14px; }")

        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.setSpacing(16)

        # иконка + текст
        head = QHBoxLayout()
        head.setSpacing(12)

        warn = QLabel()
        warn.setFixedSize(16, 16)
        warn.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        warn.setStyleSheet("background: transparent; border: none;")
        try:
            pix = make_icon("alert", C["danger"], 16).pixmap(16, 16)
            warn.setPixmap(pix)
        except Exception:
            # запасной вариант — просто красный восклицательный
            warn.setText("!")
            warn.setStyleSheet(
                "color: " + C["danger"] + "; font-weight: 700; "
                "font-size: 14px; background: transparent; border: none;")
        head.addWidget(warn, 0, Qt.AlignTop)

        body = QLabel(
            "Полный доступ сокращает количество подтверждений и позволяет "
            "агенту выполнять действия напрямую: изменять файлы, "
            "запускать команды, обращаться к сети.\n\n"
            "Используйте только если доверяете текущей задаче."
        )
        body.setWordWrap(True)
        body.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text_dim"] + "; "
            "background: transparent; border: none;")
        head.addWidget(body, 1)

        lay.addLayout(head)

        self.check = QCheckBox("Я понимаю риски и хочу продолжить")
        self.check.setStyleSheet(
            "font-family: " + UI + "; font-size: 13px; "
            "color: " + C["text_dim"] + "; "
            "background: transparent; border: none;")
        lay.addWidget(self.check)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addStretch(1)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("dialogCancelBtn")
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.setMinimumWidth(88)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btns.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("Включить полный доступ")
        self.ok_btn.setObjectName("dialogOkBtn")
        self.ok_btn.setFixedHeight(32)
        self.ok_btn.setMinimumWidth(150)
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self._on_ok)
        btns.addWidget(self.ok_btn)

        self.check.toggled.connect(self.ok_btn.setEnabled)
        lay.addLayout(btns)

        row.addWidget(card, 0)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

        self.hide()

        # следим за размером родителя
        if parent is not None:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Реагируем на resize родителя — растягиваемся."""
        from PySide6.QtCore import QEvent
        if obj is self.window() and event.type() == QEvent.Resize:
            if self.isVisible():
                self.setGeometry(self.window().rect())
        return super().eventFilter(obj, event)

    def open_for(self, on_accept):
        """Показать оверлей."""
        self._on_accept = on_accept
        self.check.setChecked(False)
        self.ok_btn.setEnabled(False)
        # растягиваемся на родителя
        w = self.window()
        if w is not None:
            self.setGeometry(w.rect())
        self.show()
        self.raise_()

    def _on_cancel(self):
        self.hide()
        try:
            del self._on_accept
        except Exception:
            pass

    def _on_ok(self):
        cb = getattr(self, "_on_accept", None)
        self.hide()
        if callable(cb):
            try:
                cb()
            except Exception as e:
                print(f"[fullAccess] {e}", flush=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroCore")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        try:
            self.setWindowIcon(make_icon("brain", C["accent"], 64))
        except Exception:
            pass
        self.setMinimumSize(1000, 640)
        self.resize(1320, 860)

        self.cfg = cfgmod.load()
        self._plugins_info = []
        self.agent = None
        self.current_session = None
        self.worker = None
        self._turns = 0
        self._steps = 0
        self._msg_start = 0.0
        self._model_signal_connected = False
        self._pending_attachments = []

        self.setStyleSheet(QSS)

        # Acrylic blur
        try:
            pass
        except Exception as e:
            print("[glass] ошибка:", e)

        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)

        vlay = QVBoxLayout(central)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # ---------- macOS-кружки ----------
        try:
            from .mac_controls import MacControls
            self.win_controls = MacControls(self)
            self.win_controls.raise_()
        except Exception as e:
            print("[mac_controls] ошибка:", e)

        # inner_vlay = QVBoxLayout(central)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # app_page
        root = QWidget()
        root.setObjectName("root")
        self.app_page = root
        vlay.addWidget(root, 1)

        hl = QHBoxLayout(root)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        # sidebar
        self.sidebar = Sidebar()
        self.sidebar.setAttribute(Qt.WA_StyledBackground, True)
        self.sidebar.setFixedWidth(260)
        self.sidebar.new_session.connect(self.new_session)
        self.sidebar.session_selected.connect(self.load_session)
        self.sidebar.session_menu.connect(self.show_session_menu)
        self.sidebar.open_settings.connect(self.show_settings)
        self.sidebar.open_plugins.connect(self.show_plugins)
        self.sidebar.toggle_palette.connect(self.toggle_palette)
        self.sidebar.add_workspace_requested.connect(self.add_workspace)
        self.sidebar.workspace_selected.connect(self.select_workspace)
        self.sidebar.workspace_menu.connect(self.show_workspace_menu)
        hl.addWidget(self.sidebar)

        # main
        main = QWidget()
        main.setObjectName("main")
        main.setAttribute(Qt.WA_StyledBackground, True)
        main.setStyleSheet(
            "QWidget#main { background-color: #1a1a1a; }")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self.topbar = TopBar()
        self.topbar.tools_btn.clicked.connect(self.toggle_tools)
        ml.addWidget(self.topbar)

        self.tabs_row = TabsRow()
        self.tabs_row.tab_changed.connect(self.set_tab)
        ml.addWidget(self.tabs_row)

        self.main_stack = QStackedWidget()
        ml.addWidget(self.main_stack, 1)

        self.tab_stack = QStackedWidget()
        self.main_stack.addWidget(self.tab_stack)

        self.welcome = Welcome()
        self.tab_stack.addWidget(self.welcome)

        self.chat = ChatArea()
        self.tab_stack.addWidget(self.chat)

        self.trajectory = TrajectoryView()
        self.tab_stack.addWidget(self.trajectory)

        self.input_area = InputArea()
        self.input_area.submitted.connect(self.send)
        self.input_area.attachments_submitted.connect(self.on_attachments)
        self.input_area.stopped.connect(self.stop)
        ml.addWidget(self.input_area)

        self.tools_panel = ToolsPanel()
        # плагины теперь живут в правой панели (tools_panel)
        self.plugins_page = self.tools_panel.plugins
        self.plugins_page.back.connect(self.hide_plugins)
        self.tools_panel.setMinimumWidth(0)
        self.tools_panel.setMaximumWidth(0)
        self.tools_panel.hide()

        hl.addWidget(main, 1)
        hl.addWidget(self.tools_panel)
        self.code_panel = CodePanel(self)
        self.code_panel.hide()
        self._pending_write_path = None
        hl.addWidget(self.code_panel)

        self.settings_overlay = SettingsOverlay(self)
        self.dialog_overlay = DialogOverlay(self)
        self.full_access_overlay = FullAccessOverlay(self)
        self.settings_overlay.page.back_btn.clicked.connect(self.hide_settings)

        self.command_palette = CommandPalette(self)
        self.command_palette.set_commands([
            ("Новая сессия", "Ctrl+N", self.new_session),
            ("Настройки", "Ctrl+,", lambda: self.show_settings("account")),
            ("Плагины", "", self.show_plugins),
            ("Пресеты", "", lambda: self.show_settings("presets")),
            ("Экспорт MD", "Ctrl+S", lambda: self.export_current("md")),
            ("Очистить чат", "", self.clear_current),
            ("Инструменты", "Ctrl+B", self.toggle_tools),
        ])

        QShortcut(QKeySequence("Ctrl+N"), self, self.new_session)
        QShortcut(QKeySequence("Ctrl+K"), self, self.toggle_palette)
        QShortcut(QKeySequence("Ctrl+,"), self,
                  lambda: self.show_settings("account"))
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_tools)
        QShortcut(QKeySequence("Esc"), self, self._hide_overlays)

        self.refresh_models()
        self._current_tab = 0
        self.new_session()

        QApplication.instance().installEventFilter(self)
        self._img_snapshot = set()
        self.workspace_write_enabled = True  # текущее состояние кнопки 'Запись в workspace'
    def refresh_models(self):
        cfg = cfgmod.load()
        self.cfg = cfg
        p = cfgmod.active_provider(cfg)
        self.input_area.set_models(p["models"], cfg.get("active_model"))
        if not self._model_signal_connected:
            try:
                self.input_area.model_combo.changed.connect(
                    self._model_changed)
            except Exception:
                pass
            self._model_signal_connected = True

    def _model_changed(self, txt):
        if not txt:
            return
        cfg = cfgmod.load()
        cfg["active_model"] = txt
        cfgmod.save(cfg)

    def toggle_tools(self):
        from .animations import animate_max_width
        panel = self.tools_panel
        if panel.isVisible() and panel.maximumWidth() > 10:
            animate_max_width(panel, 0, duration=240)
            QTimer.singleShot(260, panel.hide)
        else:
            panel.show()
            panel.go_start()
            panel.setMaximumWidth(0)
            animate_max_width(panel, 420, duration=280)

    def toggle_palette(self):
        if self.command_palette.isVisible():
            self.command_palette.hide()
        else:
            self.command_palette.setGeometry(self.rect())
            self.command_palette.open()

    def _hide_overlays(self):
        self.command_palette.hide()
        self.settings_overlay.hide()

    def _open_code_file(self, path):
        """Открыть реальный файл с диска в панели."""
        try:
            p = Path(path)
            if not p.is_absolute():
                p = Path.cwd() / p
            print(f"[panel] пробую: {p}", flush=True)
            if not p.exists():
                print(f"[panel] НЕ найден", flush=True)
                return
            self.code_panel.open_file(str(p))
            print(f"[panel] OK: {p.name}", flush=True)
        except Exception as e:
            import traceback
            print(f"[panel] FAIL: {e}", flush=True)
            traceback.print_exc()

    def toggle_code_panel(self, checked=None):
        """Показать/скрыть панель кода справа."""
        if self.code_panel.isVisible():
            self.code_panel.hide()
        else:
            self.code_panel.show()

    def show_code_in_panel(self, text, stream=True):
        """Извлечь код из текста и показать в панели."""
        try:
            if not text:
                return
            blocks = extract_code_blocks(text)
            print(f"[code_panel] найдено блоков: {len(blocks)}", flush=True)
            if not blocks:
                return
            if not self.code_panel.isVisible():
                self.code_panel.show()
            # берём последний блок (самый большой/актуальный)
            lang, code = blocks[-1]
            print(f"[code_panel] lang={lang}, длина={len(code)}", flush=True)
            self.code_panel.show_code(code, lang=lang,
                                       stream=stream,
                                       filename=f"code.{lang}")
        except Exception as e:
            import traceback
            print(f"[code_panel] FAIL: {e}", flush=True)
            traceback.print_exc()

    def show_settings(self, tab="account"):
        self.settings_overlay.page.show_tab(tab)
        self.settings_overlay.setGeometry(self.rect())
        self.settings_overlay.show()
        self.settings_overlay.raise_()

    def hide_settings(self):
        self.settings_overlay.hide()

    def show_plugins(self):
        # раскрываем правую панель
        try:
            self.tools_panel.setMinimumWidth(360)
            self.tools_panel.setMaximumWidth(16777215)
            self.tools_panel.show()
        except Exception as e:
            print(f'[show_plugins] {e}', flush=True)
        self.plugins_page.states = load_plugin_states()
        self.plugins_page._populate()
        self.tools_panel.go(4)
    def hide_plugins(self):
        self.tools_panel.go_start()

    def set_tab(self, idx):
        self._current_tab = idx
        self.tabs_row.set_active(idx)
        if self.main_stack.currentWidget() is self.plugins_page:
            self.main_stack.setCurrentWidget(self.tab_stack)
        if idx == 0:
            if self.current_session and self.current_session.messages:
                self.tab_stack.setCurrentWidget(self.chat)
            else:
                self.tab_stack.setCurrentWidget(self.welcome)
        else:
            self.tab_stack.setCurrentWidget(self.trajectory)

    def new_session(self):
        cfg = cfgmod.load()
        active_ws = cfg.get("active_workspace", "По умолчанию")
        self.current_session = Session.new(
            model=cfg.get("active_model", "deepseek-v4-pro"),
            workspace=active_ws)
        self.current_session.save()
        self.agent = None
        self.chat.clear_all()
        self.trajectory.clear()
        self.tab_stack.setCurrentWidget(self.welcome)
        self.topbar.title.setText("Новая сессия")
        self.sidebar.set_active(self.current_session.id)

    def load_session(self, sid):
        try:
            s = Session.load(sid)
        except Exception as e:
            sd_error(self, str(e))
            return
        self.current_session = s
        self.agent = None
        self.chat.clear_all()
        self.trajectory.clear()
        if s.model:
            try:
                self.input_area.model_combo.set_current(s.model)
            except Exception:
                pass
        if not s.messages:
            self.tab_stack.setCurrentWidget(self.welcome)
        else:
            self.tab_stack.setCurrentWidget(self.chat)
            for m in s.messages:
                if m["role"] == "user":
                    content = m["content"]
                    paths = extract_image_paths(content)
                    clean = content
                    for p in paths:
                        clean = clean.replace(p, "")
                    self.chat.add(UserBubble(clean.strip(),
                                              attachments=paths), anim=False, batch=True)
                elif m["role"] == "assistant":
                    self.chat.add(AssistantBlock(m["content"]), anim=False, batch=True)
            QTimer.singleShot(0, self.chat.to_end)
        self.topbar.title.setText(s.title)
        self.sidebar.set_active(sid)

    def show_session_menu(self, sid, pos):
        m = QMenu(self)
        m.addAction("Переименовать", lambda: self._rename(sid))
        m.addAction("Дублировать", lambda: self._dup(sid))
        m.addSeparator()
        m.addAction("Экспорт MD", lambda: self._export(sid, "md"))
        m.addAction("Удалить", lambda: self._del(sid))
        m.exec(pos)

    def _rename(self, sid):
        s = Session.load(sid)
        n, ok = sd_ask_text(self, "Переименовать", "Новое имя:",
                             default=s.title)
        if ok and n.strip():
            s.rename(n.strip())
            self.sidebar._refresh()
            if self.current_session and self.current_session.id == sid:
                self.topbar.title.setText(s.title)

    def _dup(self, sid):
        Session.load(sid).duplicate()
        self.sidebar._refresh()

    def _export(self, sid, fmt):
        s = Session.load(sid)
        p, _ = QFileDialog.getSaveFileName(
            self, "Сохранить",
            s.title.replace(" ", "_") + "." + fmt,
            "Markdown (*.md)" if fmt == "md" else "JSON (*.json)")
        if p:
            c = s.export_markdown() if fmt == "md" else s.export_json()
            Path(p).write_text(c, encoding="utf-8")

    def _del(self, sid):
        if not sd_question(self, "Удалить сессию?"):
            return
        was = self.current_session and self.current_session.id == sid
        Session.delete(sid)
        if was:
            self.new_session()
        else:
            self.sidebar._refresh()

    def clear_current(self):
        if not self.current_session:
            return
        if not sd_question(self, "Очистить чат?"):
            return
        self.current_session.messages = []
        self.current_session.save()
        self.agent = None
        self.chat.clear_all()
        self.trajectory.clear()
        self.tab_stack.setCurrentWidget(self.welcome)

    def export_current(self, fmt):
        if self.current_session:
            self._export(self.current_session.id, fmt)

    def add_workspace(self):
        path = QFileDialog.getExistingDirectory(
            self, "Выберите папку", str(Path.home()))
        if not path:
            return
        name = Path(path).name or path
        cfg = cfgmod.load()
        cfgmod.add_workspace(cfg, name, path)
        cfg["active_workspace"] = name
        cfgmod.save(cfg)
        self.sidebar._rebuild_workspaces()
        self.sidebar._refresh()
        self.new_session()

    def select_workspace(self, name):
        cfg = cfgmod.load()
        cfg["active_workspace"] = name
        cfgmod.save(cfg)
        self.sidebar._rebuild_workspaces()
        self.sidebar._refresh()
        self.new_session()

    def show_workspace_menu(self, name, pos):
        m = QMenu(self)
        m.addAction("Открыть в проводнике",
                    lambda: self._open_workspace(name))
        if name != "По умолчанию":
            m.addAction("Удалить",
                        lambda: self._remove_workspace(name))
        m.exec(pos)

    def _open_workspace(self, name):
        cfg = cfgmod.load()
        ws = next((w for w in cfgmod.get_workspaces(cfg)
                   if w["name"] == name), None)
        if ws:
            open_in_explorer(ws.get("path") or str(Path.home()))

    def _remove_workspace(self, name):
        if not sd_question(self, "Удалить папку " + name + "?"):
            return
        cfg = cfgmod.load()
        cfgmod.remove_workspace(cfg, name)
        self.sidebar._rebuild_workspaces()
        self.sidebar._refresh()

    def on_attachments(self, paths):
        self._pending_attachments = list(paths)

    def _build_agent(self):
        cfg = cfgmod.load()
        provider = provmod.build(cfg)
        reg = ToolRegistry()
        reg.register(ShellTool())
        reg.register(ReadFileTool())
        _out_dir = cfgmod.get_output_dir()
        reg.register(WriteFileTool(base_dir=_out_dir))
        reg.register(ListDirTool())
        reg.register(GenerateImageTool())
        for _T in ALL_DESKTOP_TOOLS:
            reg.register(_T())
        for _T in ALL_BROWSER_TOOLS:
            reg.register(_T())

        reg.register(DeepSeekSearchTool())
        self._plugins_info = load_plugins(reg)
        a = Agent(provider=provider, tools=reg)
        for m in self.current_session.messages:
            if m["role"] == "user":
                a.messages.append(Message(Role.USER, m["content"]))
            elif m["role"] == "assistant":
                a.messages.append(Message(Role.ASSISTANT, m["content"]))
        return a

    def send(self, text):
        if self.worker and self.worker.isRunning():
            return
        attachments = getattr(self, "_pending_attachments", [])
        self._pending_attachments = []
        try:
            if self.agent is None:
                self.agent = self._build_agent()
        except Exception as e:
            sd_error(self, str(e))
            return

        self.current_session.model = self.input_area.model_combo.current()
        session_text = text
        if attachments:
            session_text = text + "\n" + "\n".join(attachments)
        self.current_session.add("user", session_text)

        self.tab_stack.setCurrentWidget(self.chat)
        self.chat.add(UserBubble(text, attachments=attachments))
        self._msg_start = time.time()
        self._turns += 1
        self._steps = 0
        self.input_area.set_busy(True)

        self.worker = AgentWorker(self.agent, text,
                                    attachments=attachments)
        self.worker.event.connect(self._on_event)
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()
        self.sidebar._refresh()

    def stop(self):
        if self.worker:
            self.worker.stop()

    def _on_event(self, ev, data):
        try:
            from .activity import _verb_for_tool
            if ev == "thinking":
                try:
                    self.chat.add(ThinkingBlock(data["iteration"]))
                except Exception as e:
                    print("[thinking] ошибка:", e)
                if data["iteration"] == 1:
                    self.input_area.show_activity("Думает", icon="brain")
            elif ev == "tool_call":
                self._steps += 1
                args = data.get("arguments") or {}
                _wf_name = data.get("name", "")
                if _wf_name in ("write_file", "WriteFileTool"):
                    _wf_path = args.get("path") or args.get("filename")
                    if _wf_path:
                        self._pending_write_path = _wf_path
                        print(f"[panel] write_file -> {_wf_path}", flush=True)
                try:
                    self.chat.tool_call(data["name"], args)
                    self.trajectory.add_step(data["name"], args)
                except Exception:
                    pass
                self._img_snapshot = self._img_snapshot_now()
                self._log(f"[on_event] снимок до tool_call: {len(self._img_snapshot)}")
                verb, icon = _verb_for_tool(data["name"])
                text = verb
                target = (args.get("path") or args.get("command") or
                          args.get("query") or args.get("url") or "")
                if target:
                    text = verb + ": " + str(target).split("\n")[0][:60]
                self.input_area.show_activity(text, icon=icon)
            elif ev == "tool_result":
                # --- хук: если write_file создал файл, открыть его ---
                _tr_n = data.get("name", "")
                if _tr_n in ("write_file", "WriteFileTool"):
                    _p = getattr(self, "_pending_write_path", None)
                    if _p:
                        self._pending_write_path = None
                        from PySide6.QtCore import QTimer as _QT
                        _QT.singleShot(120, lambda pp=_p: self._open_code_file(pp))

                result = data.get("result", "")
                print(f"[_on_event] tool_result: {result[:200]!r}", flush=True)
                try:
                    self.chat.tool_result(result)
                except Exception as e:
                    print(f"[_on_event] chat.tool_result FAIL: {e}", flush=True)
                try:
                    self._show_new_images()
                except Exception as e:
                    import traceback
                    print(f"[_on_event] _maybe_show_image FAIL: {e}", flush=True)
                    traceback.print_exc()
                try:
                    self.trajectory.set_result(result)
                except Exception as e:
                    print(f"[_on_event] trajectory.set_result FAIL: {e}", flush=True)
                self.input_area.show_activity("Обрабатывает результат",
                                                icon="sparkle")
                try:
                    from PySide6.QtCore import QTimer as _QT2
                    _res = data.get("result", "")
                    _QT2.singleShot(0,
                                    lambda r=_res: self.show_code_in_panel(r))
                except Exception as _e:
                    print(f'[code_panel tool hook] {_e}', flush=True)
            elif ev == "parse_error":
                l = QLabel("Ошибка: " + str(data.get("error")))
                l.setStyleSheet("color: " + C["danger"] + ";")
                self.chat.add(l)
        except Exception:
            import traceback
            traceback.print_exc()

    def _on_done(self, answer):
        try:
            from PySide6.QtCore import QTimer as _QT
            _QT.singleShot(0, lambda: self.show_code_in_panel(answer))
        except Exception as _e:
            print(f'[code_panel hook] {_e}', flush=True)
        elapsed = time.time() - self._msg_start
        self.chat.add(AssistantBlock(answer, elapsed=elapsed))
        self.current_session.add("assistant", answer)
        self.sidebar._refresh()
        self.input_area.set_busy(False)
        self.input_area.show_activity_done("Готово")

    def _on_error(self, msg):
        l = QLabel("Ошибка: " + msg)
        l.setStyleSheet("color: " + C["danger"] + ";")
        self.chat.add(l)
        self.input_area.set_busy(False)
        self.input_area.show_activity_done("Ошибка")

    def _on_perm_changed(self, mode):
        """Реакция окна на смену режима доступа."""
        self.perm_mode = mode
        print(f"[perm] режим доступа: {mode}", flush=True)
        labels = {
            "read_only": "Только чтение",
            "workspace_write": "Запись в workspace",
            "full_access": "Полный доступ",
        }
        try:
            self.input_area.show_activity(
                f"Режим: {labels.get(mode, mode)}", icon="shield"
            )
        except Exception:
            pass

    def _apply_dwm_round(self):
        """Скругление углов через DWM API (Windows 11)."""
        try:
            import sys as _sys
            if _sys.platform != "win32":
                return
            import ctypes
            from ctypes import wintypes
            hwnd = int(self.winId())
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33
            # DWMWCP_ROUND = 2 (стандартное), ROUNDSMALL = 3
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(33),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            pass

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtWidgets import QApplication, QPushButton, QToolButton

        if event.type() == QEvent.MouseButtonPress and isinstance(event, QMouseEvent):
            if event.button() == Qt.LeftButton:
                global_pos = event.globalPosition().toPoint()
                local_pos = self.mapFromGlobal(global_pos)
                if 0 <= local_pos.y() <= 45:
                    w = QApplication.widgetAt(global_pos)
                    is_button = False
                    while w is not None:
                        if isinstance(w, (QPushButton, QToolButton)):
                            is_button = True
                            break
                        w = w.parentWidget()
                    if not is_button and self.windowHandle() is not None:
                        self.windowHandle().startSystemMove()
                        return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if hasattr(self, "command_palette") and self.command_palette.isVisible():
                self.command_palette.setGeometry(self.rect())
        except Exception:
            pass
        try:
            if hasattr(self, "settings_overlay") and self.settings_overlay.isVisible():
                self.settings_overlay.setGeometry(self.rect())
        except Exception:
            pass
        try:
            if hasattr(self, "win_controls"):
                self.win_controls.move(16, 12)
        except Exception:
            pass
        # скругление углов окна (DWM — не ломает Qt)
        self._apply_dwm_round()

    def _img_snapshot_now(self):
        from pathlib import Path as _P
        exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.gif", "*.bmp")
        cwd = _P.cwd()
        s = set()
        for pat in exts:
            for f in cwd.glob(pat):
                try:
                    s.add(str(f.resolve()))
                except Exception:
                    pass
        return s

    def _log(self, msg):
        try:
            from pathlib import Path as _P
            import datetime
            line = f"{datetime.datetime.now().isoformat()} {msg}\n"
            with open(_P.cwd() / "neurocore.log", "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
        print(msg, flush=True)

    def _show_new_images(self):
        """Сравнить папку с прошлым снимком, показать новые картинки."""
        try:
            now = self._img_snapshot_now()
            new = now - getattr(self, "_img_snapshot", set())
            self._log(f"[show] было={len(self._img_snapshot)} стало={len(now)} новых={len(new)}")
            for p in sorted(new):
                try:
                    self._log(f"[show] добавляю {p}")
                    b = ImageBubble(p)
                    self._log(f"[show] ImageBubble sizeHint={b.sizeHint()}")
                    self.chat.add(b)
                    self._log(f"[show] OK добавлено в чат")
                except Exception as e:
                    import traceback
                    self._log(f"[show] FAIL {type(e).__name__}: {e}")
                    self._log(traceback.format_exc())
        except Exception as e:
            import traceback
            self._log(f"[show] outer FAIL: {e}")
            self._log(traceback.format_exc())
    def closeEvent(self, event):
        if self.current_session:
            self.current_session.save()
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
        super().closeEvent(event)

# ============================================================
# Имя пользователя системы
# ============================================================
def _get_username() -> str:
    """Имя пользователя Windows."""
    import os
    try:
        name = os.environ.get("USERNAME") or os.environ.get("USER")
        if not name:
            name = getpass.getuser()
        return (name or "User").strip()
    except Exception:
        return "User"

def _get_user_initial() -> str:
    """Первая буква имени."""
    n = _get_username()
    return n[0].upper() if n else "U"

# ============================================================
# Фильтр Qt-сообщений (глушим безобидные warning'и)
# ============================================================
_QT_QUIET = (
    "QPainter::begin",
    "QPainter::end",
    "QPainter::restore",
    "QPainter::save",
    "QPainter::translate",
    "QPainter::worldTransform",
    "QPainter::setOpacity",
    "QPainter::setWorldTransform",
    "QWidgetEffectSourcePrivate::pixmap",
)


def _qt_msg_filter(mode, ctx, msg):
    for pattern in _QT_QUIET:
        if pattern in msg:
            return
    import sys as _s
    _s.stderr.write(msg + "\n")


def main():
    try:
        from PySide6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(_qt_msg_filter)
    except Exception:
        pass
    from PySide6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat()
    fmt.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("NeuroCore")

    w = MainWindow()
    w.show()

    from PySide6.QtCore import QTimer
    QTimer.singleShot(80, w._apply_dwm_round)
    QTimer.singleShot(300, w._apply_dwm_round)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
