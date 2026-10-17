"""Работа с буфером: картинки, файлы, текст."""
import hashlib
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QImage

TEMP_DIR = Path.home() / ".neurocore" / "paste"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _save_qimage(img: QImage) -> Path:
    """Сохраняет QImage в PNG, возвращает путь."""
    if img is None or img.isNull():
        raise ValueError("empty QImage")
    buf = img.bits().tobytes() if hasattr(img.bits(), "tobytes") \
        else bytes(img.bits())
    digest = hashlib.md5(buf).hexdigest()[:12]
    fname = "paste_" + digest + ".png"
    path = TEMP_DIR / fname
    if not path.exists():
        img.save(str(path), "PNG")
    return path


def try_get_image_path() -> Path | None:
    """Если в буфере картинка — сохраняет и возвращает путь. Иначе None."""
    cb = QGuiApplication.clipboard()
    md = cb.mimeData()
    if md is None:
        return None

    # 1) QImage напрямую
    if md.hasImage():
        img = cb.image()
        if not img.isNull():
            return _save_qimage(img)

    # 2) Файл-картинка из буфера файлов
    if md.hasUrls():
        for url in md.urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif",
                                     ".webp", ".bmp", ".tif", ".tiff",
                                     ".svg", ".ico"):
                return p

    # 3) Сырые mime-данные (копирование из браузера)
    for fmt in md.formats():
        if fmt.startswith("image/"):
            data = md.data(fmt)
            if not data.isEmpty():
                img = QImage()
                if img.loadFromData(data):
                    return _save_qimage(img)

    return None


def is_image_in_clipboard() -> bool:
    cb = QGuiApplication.clipboard()
    md = cb.mimeData()
    if md is None:
        return False
    if md.hasImage():
        return True
    if md.hasUrls():
        for url in md.urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif",
                                     ".webp", ".bmp", ".svg"):
                return True
    for fmt in md.formats():
        if fmt.startswith("image/"):
            return True
    return False
