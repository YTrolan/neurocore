"""macOS-стиль кнопок окна — три цветных кружка слева."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class TrafficLight(QPushButton):
    """Один кружок светофора."""

    def __init__(self, color, symbol, tooltip, parent=None):
        super().__init__(parent)
        self.color = color
        self.symbol = symbol
        self.setFixedSize(12, 12)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setStyleSheet(
            "QPushButton {"
            "  background-color: " + color + ";"
            "  border: none;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "  background-color: " + color + ";"
            "}")
        self._hover = False
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        # сначала рисуем кружок через QSS
        super().paintEvent(event)
        # потом символ при hover
        if not self._hover:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor(0, 0, 0, 160))
        pen.setWidthF(1.4)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        # центр
        cx, cy, r = 6, 6, 3
        if self.symbol == "x":
            p.drawLine(cx - r, cy - r, cx + r, cy + r)
            p.drawLine(cx + r, cy - r, cx - r, cy + r)
        elif self.symbol == "-":
            p.drawLine(cx - r, cy, cx + r, cy)
        elif self.symbol == "+":
            p.drawLine(cx - r, cy, cx + r, cy)
            p.drawLine(cx, cy - r, cx, cy + r)
        p.end()


class MacControls(QWidget):
    """Группа из трёх кружков: закрыть / свернуть / развернуть."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("macControls")
        self.setStyleSheet("QWidget#macControls { background: transparent; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.close_btn = TrafficLight("#ff5f57", "x", "Закрыть")
        self.close_btn.clicked.connect(self._on_close)
        lay.addWidget(self.close_btn)

        self.min_btn = TrafficLight("#febc2e", "-", "Свернуть")
        self.min_btn.clicked.connect(self._on_min)
        lay.addWidget(self.min_btn)

        self.max_btn = TrafficLight("#28c840", "+", "Развернуть")
        self.max_btn.clicked.connect(self._on_max)
        lay.addWidget(self.max_btn)

    def _on_close(self):
        self.window().close()

    def _on_min(self):
        self.window().showMinimized()

    def _on_max(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()
