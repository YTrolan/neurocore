"""Сверхплавные анимации — 60-120 fps ощущение."""
from PySide6.QtCore import (QEasingCurve, QParallelAnimationGroup, QPoint,
                             QPropertyAnimation, QTimer, Qt, QVariantAnimation)
from PySide6.QtWidgets import (QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                                QStackedWidget, QWidget)


# Easing-константы для разных сценариев
EASE_SMOOTH = QEasingCurve.OutSine       # супер-плавное торможение
EASE_SOFT = QEasingCurve.InOutSine       # идеально симметричное
EASE_SNAP = QEasingCurve.OutQuad         # быстрое с мягкой остановкой
EASE_INOUT = QEasingCurve.InOutSine      # идеально плавный вход-выход


def _ensure_opacity_effect(widget):
    eff = widget.graphicsEffect()
    if not isinstance(eff, QGraphicsOpacityEffect):
        eff = QGraphicsOpacityEffect(widget)
        eff.setOpacity(1.0)
        widget.setGraphicsEffect(eff)
    return eff


def _prep_anim(anim):
    """Одна тонкая настройка для всех анимаций."""
    anim.setEasingCurve(EASE_SMOOTH)
    return anim


def fade_in(w, duration=260):
    """no-op."""
    return None


def fade_out(widget, duration=280, on_finished=None, easing=QEasingCurve.InQuad):
    eff = _ensure_opacity_effect(widget)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(eff.opacity())
    anim.setEndValue(0.0)
    anim.setEasingCurve(easing)
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._fade_anim = anim
    return anim


def cross_fade(stack, new_widget, duration=420):
    """Плавный переход между страницами — синхронно."""
    old = stack.currentWidget()
    if old is new_widget:
        return None
    if old is None:
        stack.setCurrentWidget(new_widget)
        return fade_in(new_widget, duration)
    # одновременно: старое гаснет, новое появляется
    stack.setCurrentWidget(new_widget)
    fade_in(new_widget, duration)
    fade_out(old, int(duration * 0.5))


def pop_in(widget, duration=440):
    eff = _ensure_opacity_effect(widget)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutBack)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._pop_anim = anim
    return anim


def slide_fade_in(widget, duration=460, offset=8):
    target = widget.pos()
    widget.move(target.x(), target.y() + offset)
    eff = _ensure_opacity_effect(widget)
    eff.setOpacity(0.0)

    fade = QPropertyAnimation(eff, b"opacity", widget)
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(EASE_SMOOTH)

    slide = QPropertyAnimation(widget, b"pos", widget)
    slide.setDuration(duration)
    slide.setStartValue(widget.pos())
    slide.setEndValue(target)
    slide.setEasingCurve(EASE_SMOOTH)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(fade)
    group.addAnimation(slide)
    group.start(QParallelAnimationGroup.DeleteWhenStopped)
    widget._anim_group = group
    return group


def smooth_scroll(scroll_area, target_value, duration=560):
    sb = scroll_area.verticalScrollBar()
    if sb is None:
        return None
    anim = QPropertyAnimation(sb, b"value", scroll_area)
    anim.setDuration(duration)
    anim.setStartValue(sb.value())
    anim.setEndValue(int(target_value))
    anim.setEasingCurve(EASE_SMOOTH)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    scroll_area._scroll_anim = anim
    return anim


def animate_height(widget, target_height, duration=360,
                    collapse=None, on_finished=None):
    start = widget.maximumHeight()
    if start > 1000000 or start <= 0:
        start = widget.height()
    widget.setMaximumHeight(start)

    anim = QPropertyAnimation(widget, b"maximumHeight", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(target_height)
    anim.setEasingCurve(EASE_INOUT if collapse else EASE_SMOOTH)
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._height_anim = anim
    return anim


def slide_in_x(widget, from_x=None, duration=620, easing=EASE_SMOOTH):
    target = widget.pos()
    start_x = from_x if from_x is not None else target.x() - 40
    widget.move(start_x, target.y())
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(duration)
    anim.setStartValue(QPoint(start_x, target.y()))
    anim.setEndValue(target)
    anim.setEasingCurve(easing)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._slide_x_anim = anim
    return anim


def slide_in_y(widget, from_y=None, duration=620, easing=EASE_SMOOTH):
    target = widget.pos()
    start_y = from_y if from_y is not None else target.y() + 30
    widget.move(target.x(), start_y)
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(duration)
    anim.setStartValue(QPoint(target.x(), start_y))
    anim.setEndValue(target)
    anim.setEasingCurve(easing)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._slide_y_anim = anim
    return anim


def fade_and_slide_y(widget, duration=560, offset=28):
    eff = _ensure_opacity_effect(widget)
    eff.setOpacity(0.0)
    target = widget.pos()
    widget.move(target.x(), target.y() + offset)

    fade = QPropertyAnimation(eff, b"opacity", widget)
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(EASE_SMOOTH)

    slide = QPropertyAnimation(widget, b"pos", widget)
    slide.setDuration(duration)
    slide.setStartValue(QPoint(target.x(), target.y() + offset))
    slide.setEndValue(target)
    slide.setEasingCurve(EASE_SMOOTH)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(fade)
    group.addAnimation(slide)
    group.start(QParallelAnimationGroup.DeleteWhenStopped)
    widget._anim_group = group
    return group


def fade_and_scale(widget, duration=480, offset=60, delta=14):
    eff = _ensure_opacity_effect(widget)
    eff.setOpacity(0.0)
    target = widget.pos()
    widget.move(target.x(), target.y() - delta)

    fade = QPropertyAnimation(eff, b"opacity", widget)
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(EASE_SMOOTH)

    slide = QPropertyAnimation(widget, b"pos", widget)
    slide.setDuration(duration)
    slide.setStartValue(QPoint(target.x(), target.y() - delta))
    slide.setEndValue(target)
    slide.setEasingCurve(EASE_SMOOTH)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(fade)
    group.addAnimation(slide)
    group.start(QParallelAnimationGroup.DeleteWhenStopped)
    widget._fade_scale_anim = group
    return group


def pulse_scale(widget, duration=380):
    target = widget.geometry()
    anim = QPropertyAnimation(widget, b"geometry", widget)
    anim.setDuration(duration)
    anim.setStartValue(target)
    mid = target.adjusted(-2, -1, 2, 1)
    anim.setKeyValueAt(0.5, mid)
    anim.setEndValue(target)
    anim.setEasingCurve(QEasingCurve.OutQuad)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._pulse_anim = anim
    return anim


def animate_max_width(widget, target, duration=440, easing=EASE_SMOOTH):
    start = widget.maximumWidth()
    if start > 1_000_000:
        start = widget.width()
    widget.setMaximumWidth(start)
    anim = QPropertyAnimation(widget, b"maximumWidth", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(target)
    anim.setEasingCurve(easing)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._mw_anim = anim
    return anim


def animate_splitter(splitter, target_index, from_size, to_size,
                      duration=440, easing=EASE_SMOOTH, on_finished=None):
    anim = QVariantAnimation(splitter)
    anim.setDuration(duration)
    anim.setStartValue(float(from_size))
    anim.setEndValue(float(to_size))
    anim.setEasingCurve(easing)
    other_index = 1 - target_index
    total = splitter.width()

    def _on_value(v):
        try:
            v = int(v)
            other = max(1, total - v)
            sizes = [0, 0]
            sizes[target_index] = v
            sizes[other_index] = other
            splitter.setSizes(sizes)
        except Exception:
            pass

    anim.valueChanged.connect(_on_value)
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start(QVariantAnimation.DeleteWhenStopped)
    splitter._anim = anim
    return anim


def slide_panel(widget, from_x_offset, duration=580, easing=EASE_SMOOTH):
    target = widget.pos()
    widget.move(target.x() + from_x_offset, target.y())
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(duration)
    anim.setStartValue(QPoint(target.x() + from_x_offset, target.y()))
    anim.setEndValue(target)
    anim.setEasingCurve(easing)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._panel_anim = anim
    return anim


class PulsingDots(QWidget):
    """Три точки, пульсируют волной. Обновляются на ~20 fps."""

    def __init__(self, parent=None, color="#a8a8a8"):
        super().__init__(parent)
        self.setFixedSize(24, 12)
        self.color = color

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)

        self.dots = []
        for _ in range(3):
            d = QLabel(".")
            d.setFixedSize(6, 12)
            d.setAlignment(Qt.AlignCenter)
            d.setStyleSheet(
                "color: " + color + "; font-size: 12px; "
                "background: transparent;")
            eff = QGraphicsOpacityEffect(d)
            eff.setOpacity(0.3)
            d.setGraphicsEffect(eff)
            lay.addWidget(d)
            self.dots.append(d)

        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(480)  # очень мягкая пульсация

    def _tick(self):
        for i, d in enumerate(self.dots):
            eff = d.graphicsEffect()
            anim = QPropertyAnimation(eff, b"opacity", d)
            anim.setDuration(680)
            active = (self._phase % 3) == i
            anim.setStartValue(eff.opacity())
            anim.setEndValue(1.0 if active else 0.3)
            anim.setEasingCurve(QEasingCurve.InOutSine)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            d._anim = anim
        self._phase += 1

    def stop(self):
        self._timer.stop()
