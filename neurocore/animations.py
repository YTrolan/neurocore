"""NeuroCore анимации — плавные и заметные, без QGraphicsEffect."""
import math
from PySide6.QtCore import (QPropertyAnimation, QEasingCurve, QPoint,
                             QParallelAnimationGroup, QSequentialAnimationGroup,
                             QTimer, Qt, QSize, QAbstractAnimation, QRect)
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsOpacityEffect


# ============================================================
# БАЗОВЫЕ
# ============================================================
def _ensure_visible(w):
    try:
        if not w.isVisible():
            w.setVisible(True)
    except Exception:
        pass


def animate_pos(w, target, duration=320, easing=None, delay=0):
    if easing is None:
        easing = QEasingCurve.OutCubic
    a = QPropertyAnimation(w, b"pos", w)
    a.setDuration(duration)
    a.setStartValue(w.pos())
    a.setEndValue(target)
    a.setEasingCurve(easing)
    if delay > 0:
        QTimer.singleShot(delay, lambda: a.start(QAbstractAnimation.DeleteWhenStopped))
    else:
        a.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_pos = a
    return a


def animate_size(w, target, duration=320, easing=None):
    if easing is None:
        easing = QEasingCurve.OutBack
    a = QPropertyAnimation(w, b"size", w)
    a.setDuration(duration)
    a.setStartValue(w.size())
    a.setEndValue(target)
    a.setEasingCurve(easing)
    a.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_sz = a
    return a


def animate_height(w, target, duration=320, easing=None):
    if easing is None:
        easing = QEasingCurve.OutCubic
    a = QPropertyAnimation(w, b"maximumHeight", w)
    a.setDuration(duration)
    a.setStartValue(w.maximumHeight())
    a.setEndValue(target)
    a.setEasingCurve(easing)
    a.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_h = a
    return a


def animate_width(w, target, duration=320, easing=None):
    if easing is None:
        easing = QEasingCurve.OutCubic
    a = QPropertyAnimation(w, b"maximumWidth", w)
    a.setDuration(duration)
    a.setStartValue(w.maximumWidth())
    a.setEndValue(target)
    a.setEasingCurve(easing)
    a.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_w = a
    return a


def animate_max_width(w, target, duration=320):
    return animate_width(w, target, duration)


def animate_max_height(w, target, duration=320):
    return animate_height(w, target, duration)


# ============================================================
# SLIDE — выезды
# ============================================================
def slide_in(w, direction="right", distance=30, duration=320, delay=0):
    """direction: left | right | up | down"""
    _ensure_visible(w)
    target = w.pos()
    dx, dy = 0, 0
    if direction == "right":
        dx = distance
    elif direction == "left":
        dx = -distance
    elif direction == "up":
        dy = -distance
    elif direction == "down":
        dy = distance

    w.move(target + QPoint(dx, dy))
    return animate_pos(w, target, duration, QEasingCurve.OutBack, delay)


def slide_in_x(w, distance=20, duration=320, delay=0):
    return slide_in(w, "right", distance, duration, delay)


def slide_in_y(w, distance=15, duration=320, delay=0):
    return slide_in(w, "down", distance, duration, delay)


def slide_from_left(w, distance=30, duration=340, delay=0):
    return slide_in(w, "left", distance, duration, delay)


def slide_from_bottom(w, distance=25, duration=340, delay=0):
    return slide_in(w, "down", distance, duration, delay)


def slide_fade_in(w, duration=300, delay=0):
    return slide_in_y(w, 12, duration, delay)


def slide_panel(w, target_width, duration=340):
    return animate_width(w, target_width, duration)


# ============================================================
# PULSE — привлекающие внимание
# ============================================================
def pulse_size(w, scale=1.06, duration=280):
    """Пульс — увеличение и возврат."""
    _ensure_visible(w)
    start = w.size()
    peak = QSize(int(start.width() * scale), int(start.height() * scale))
    seq = QSequentialAnimationGroup(w)

    up = QPropertyAnimation(w, b"size", w)
    up.setDuration(duration // 2)
    up.setStartValue(start)
    up.setEndValue(peak)
    up.setEasingCurve(QEasingCurve.OutQuad)

    down = QPropertyAnimation(w, b"size", w)
    down.setDuration(duration // 2)
    down.setStartValue(peak)
    down.setEndValue(start)
    down.setEasingCurve(QEasingCurve.OutBack)

    seq.addAnimation(up)
    seq.addAnimation(down)
    seq.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_p = seq
    return seq


def pulse_window_opacity(w, low=0.85, high=1.0, duration=1200):
    """Бесконечный пульс прозрачности окна (безопасно)."""
    try:
        a = QPropertyAnimation(w, b"windowOpacity", w)
        a.setDuration(duration)
        a.setStartValue(high)
        a.setKeyValueAt(0.5, low)
        a.setEndValue(high)
        a.setLoopCount(-1)
        a.setEasingCurve(QEasingCurve.InOutSine)
        a.start(QAbstractAnimation.DeleteWhenStopped)
        w._anim_op = a
        return a
    except Exception:
        return None


def bounce(w, height=8, duration=420):
    """Подпрыгивание."""
    _ensure_visible(w)
    start = w.pos()
    peak = start - QPoint(0, height)
    seq = QSequentialAnimationGroup(w)

    up = QPropertyAnimation(w, b"pos", w)
    up.setDuration(duration * 2 // 5)
    up.setStartValue(start)
    up.setEndValue(peak)
    up.setEasingCurve(QEasingCurve.OutQuad)

    down = QPropertyAnimation(w, b"pos", w)
    down.setDuration(duration * 3 // 5)
    down.setStartValue(peak)
    down.setEndValue(start)
    down.setEasingCurve(QEasingCurve.OutBounce)

    seq.addAnimation(up)
    seq.addAnimation(down)
    seq.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_b = seq
    return seq


def shake(w, amplitude=6, duration=460):
    """Дрожание по X."""
    _ensure_visible(w)
    start = w.pos()
    a = QPropertyAnimation(w, b"pos", w)
    a.setDuration(duration)
    steps = 12
    for i in range(steps + 1):
        t = i / steps
        offset = int(amplitude * math.sin(t * math.pi * 8) * (1 - t))
        a.setKeyValueAt(t, start + QPoint(offset, 0))
    a.setEndValue(start)
    a.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_shk = a
    return a


def swing(w, angle_deg=6, duration=500):
    """Покачивание через поворот rotation (через styleSheet)."""
    # простое — через движок pos
    _ensure_visible(w)
    start = w.pos()
    radius = 4
    a = QPropertyAnimation(w, b"pos", w)
    a.setDuration(duration)
    for i in range(9):
        t = i / 8
        angle = math.sin(t * math.pi * 2) * (1 - t) * math.radians(angle_deg)
        dx = int(math.sin(angle) * radius * 8)
        a.setKeyValueAt(t, start + QPoint(dx, 0))
    a.setEndValue(start)
    a.start(QAbstractAnimation.DeleteWhenStopped)
    w._anim_sw = a
    return a


def grow_in(w, duration=340, delay=0):
    """Появление через рост высоты."""
    _ensure_visible(w)
    target = w.maximumHeight() if w.maximumHeight() < 100000 else w.sizeHint().height()
    if target <= 0:
        target = w.sizeHint().height() or 40
    w.setMaximumHeight(0)
    if delay > 0:
        QTimer.singleShot(delay, lambda: animate_height(w, target, duration))
    else:
        animate_height(w, target, duration)


# ============================================================
# ЦВЕТ — без эффектов, через stylesheet
# ============================================================
def flash_stylesheet(w, color="#7ec8ff", duration=500):
    """Подсветка — короткий цветной фон."""
    try:
        orig = w.styleSheet()
        w.setStyleSheet(orig + f"\nbackground-color: {color};")
        QTimer.singleShot(duration, lambda: w.setStyleSheet(orig))
    except Exception:
        pass


# ============================================================
# СТАРЫЕ ИМЕНА — для совместимости
# ============================================================
def flash(w, *a, **k):
    return flash_stylesheet(w)


def fade_in(w, duration=300, delay=0):
    _ensure_visible(w)
    return slide_in_y(w, 10, duration, delay)


def fade_out(w, duration=220, on_done=None):
    _ensure_visible(w)
    start = w.pos()
    end = start + QPoint(0, -10)
    a = animate_pos(w, end, duration, QEasingCurve.InCubic)
    QTimer.singleShot(duration, lambda: w.setVisible(False))
    if on_done:
        QTimer.singleShot(duration + 10, on_done)
    return a


def fade_and_slide_y(w, duration=280, offset=10):
    return slide_in_y(w, offset, duration)


def cross_fade(old, new, duration=260):
    try:
        old.setVisible(False)
        _ensure_visible(new)
        slide_in_y(new, 10, duration)
    except Exception:
        pass


def pop_in(w, duration=280):
    return pulse_size(w, 1.06, duration)


def fade_and_scale(w, duration=280, scale=1.05):
    return pulse_size(w, scale, duration)


def pulse_scale(w, duration=2000, scale=1.02):
    return pulse_size(w, scale, duration)


def glow(w, *a, **k):
    return flash_stylesheet(w, "#7ec8ff", 600)


def ripple(w, *a, **k):
    return pulse_size(w, 1.05, 220)


def pop(w, scale=1.04, duration=240):
    return pulse_size(w, scale, duration)


def spin_icon(label, *a, **k):
    return None


def rotate_forever(label, *a, **k):
    return None


def stop_rotate(label):
    pass


def smooth_scroll(scroll_area, target, duration=340):
    sb = scroll_area.verticalScrollBar()
    a = QPropertyAnimation(sb, b"value", sb)
    a.setDuration(duration)
    a.setStartValue(sb.value())
    a.setEndValue(target)
    a.setEasingCurve(QEasingCurve.OutCubic)
    a.start(QAbstractAnimation.DeleteWhenStopped)
    return a


# ============================================================
# КАСКАД — список элементов по очереди
# ============================================================
def stagger_slide_in(widgets, distance=20, duration=280, gap=45):
    """Плавно выезжает список виджетов по очереди."""
    for i, w in enumerate(widgets):
        _ensure_visible(w)
        target = w.pos()
        w.move(target + QPoint(-distance, 0))
        animate_pos(w, target, duration, QEasingCurve.OutCubic, i * gap)


def stagger_pulse(widgets, gap=60, scale=1.04):
    for i, w in enumerate(widgets):
        QTimer.singleShot(i * gap, lambda x=w: pulse_size(x, scale, 260))


# ============================================================
# PulsingDots — три мигающие точки
# ============================================================
class PulsingDots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from .theme import C
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        self._lbls = []
        for _ in range(3):
            l = QLabel("●")
            l.setStyleSheet(f"color: {C['text_mute']}; font-size: 8px;")
            lay.addWidget(l)
            self._lbls.append(l)

        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(280)
        self._timer.start()

    def _tick(self):
        from .theme import C
        for i, l in enumerate(self._lbls):
            color = C["accent"] if i == self._phase % 3 else C["text_mute"]
            l.setStyleSheet(f"color: {color}; font-size: 8px;")
        self._phase += 1

    def stop(self):
        self._timer.stop()


def make_pulse_dots(parent=None):
    return PulsingDots(parent)
