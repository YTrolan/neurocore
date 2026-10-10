"""Превью картинок: в input и в чате."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                                QVBoxLayout, QWidget)

from .theme import C
from .icons import make_icon


MAX_W = 340
MAX_H = 240
THUMB = 72


class AttachThumb(QFrame):
    """Миниатюра вложения в поле ввода — с крестиком для удаления."""
    removed = Signal(str)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._path = path
        self.setObjectName("attachThumb")
        self.setFixedSize(THUMB, THUMB)
        self.setStyleSheet(
            "QFrame#attachThumb { background: transparent; "
            "border: 1px solid " + C["border"] + "; "
            "border-radius: 10px; }")

        pix = QPixmap(path)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(0)

        if not pix.isNull():
            scaled = pix.scaled(THUMB - 8, THUMB - 8,
                                 Qt.KeepAspectRatio,
                                 Qt.SmoothTransformation)
            lbl = QLabel()
            lbl.setPixmap(scaled)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(lbl)

        # крестик в углу
        close = QPushButton(self)
        close.setObjectName("attachClose")
        close.setIcon(make_icon("close", "#ffffff", 8))
        close.setIconSize(QSize(8, 8))
        close.setFixedSize(18, 18)
        close.setCursor(Qt.PointingHandCursor)
        close.setStyleSheet(
            "QPushButton#attachClose {"
            "  background: rgba(0, 0, 0, 180);"
            "  border: none; border-radius: 9px;"
            "  padding: 0;"
            "}"
            "QPushButton#attachClose:hover {"
            "  background: " + C["danger"] + ";"
            "}")
        close.move(THUMB - 20, 2)
        close.clicked.connect(lambda: self.removed.emit(self._path))
        close.raise_()

        # клик по миниатюре — открыть
        def _open(_):
            import sys, subprocess, os
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
            except Exception:
                pass
        self.mousePressEvent = _open
        self.setToolTip(Path(path).name)


class ImagePreview(QFrame):
    """Большое превью в user-bubble."""

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._path = path
        self.setObjectName("imgPreview")
        self.setStyleSheet(
            "QFrame#imgPreview { background: transparent; "
            "border: 1px solid " + C["border_soft"] + "; "
            "border-radius: 12px; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(0)

        pix = QPixmap(path)
        if pix.isNull():
            lbl = QLabel("⚠ картинка не читается")
            lbl.setStyleSheet(
                "color: " + C["danger"] + "; font-size: 11px; "
                "padding: 8px; background: transparent;")
            lay.addWidget(lbl)
            return

        scaled = pix.scaled(
            QSize(MAX_W, MAX_H),
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl = QLabel()
        lbl.setPixmap(scaled)
        lbl.setFixedSize(scaled.size())
        lbl.setStyleSheet("background: transparent;")
        lbl.setCursor(Qt.PointingHandCursor)
        lbl.setToolTip("Клик — открыть в системном просмотрщике")

        def _open(_):
            import sys, subprocess, os
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
            except Exception as e:
                print("[image] не открыть:", e)

        lbl.mousePressEvent = _open
        lay.addWidget(lbl)


def extract_image_paths(text: str) -> list[str]:
    import re
    from pathlib import Path as P
    found = []
    image_exts = (".png", ".jpg", ".jpeg", ".gif", ".webp",
                   ".bmp", ".tif", ".tiff", ".svg", ".ico")
    for line in text.split("\n"):
        s = line.strip().strip('"').strip("'")
        if not s:
            continue
        try:
            p = P(s)
            if p.exists() and p.suffix.lower() in image_exts:
                found.append(str(p))
        except Exception:
            pass
    return found
