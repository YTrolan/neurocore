"""SVG icons (Lucide-style, stroke-based) → QIcon."""
from PySide6.QtCore import QByteArray, Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


SVG = {}


def _svg(body, view_box="0 0 24 24"):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + view_box + '" '
        'fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        + body + '</svg>'
    )


# --- logo: нейронная сеть в круге ---
SVG["logo"] = _svg(
    '<circle cx="12" cy="12" r="9"/>'
    '<circle cx="12" cy="12" r="2.5" fill="currentColor"/>'
    '<circle cx="12" cy="6" r="1.2" fill="currentColor"/>'
    '<circle cx="12" cy="18" r="1.2" fill="currentColor"/>'
    '<circle cx="6" cy="12" r="1.2" fill="currentColor"/>'
    '<circle cx="18" cy="12" r="1.2" fill="currentColor"/>'
    '<circle cx="7.5" cy="7.5" r="1" fill="currentColor"/>'
    '<circle cx="16.5" cy="16.5" r="1" fill="currentColor"/>'
    '<circle cx="16.5" cy="7.5" r="1" fill="currentColor"/>'
    '<circle cx="7.5" cy="16.5" r="1" fill="currentColor"/>'
)

SVG["plus"] = _svg('<path d="M12 5v14M5 12h14"/>')
SVG["search"] = _svg(
    '<circle cx="11" cy="11" r="7"/>'
    '<path d="M21 21l-4.35-4.35"/>'
)
SVG["settings"] = _svg(
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
)
SVG["puzzle"] = _svg(
    '<path d="M15.5 3a2 2 0 0 1 2 2c0 .5-.2 1-.5 1.4.3.4.5.9.5 1.4h3a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 1 0 0 4 2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-3c-.4.3-.9.5-1.4.5a2 2 0 1 1 0-4c.5 0 1 .2 1.4.5v-4.4a2 2 0 0 1-.5.3c-.3.2-.6.3-.9.3a2 2 0 1 1 0-4c.3 0 .6.1.9.3.2.1.4.2.5.3V7a2 2 0 0 1 2-2h2.4c-.3-.4-.4-.9-.4-1.4a2 2 0 1 1 4 0c0 .5-.2 1-.5 1.4h2.4z"/>'
)
SVG["star"] = _svg(
    '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>'
)
SVG["command"] = _svg(
    '<path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 0 0 0-6z"/>'
)
SVG["copy"] = _svg(
    '<rect x="9" y="9" width="13" height="13" rx="2"/>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'
)
SVG["thumbs_up"] = _svg(
    '<path d="M7 10v12M15 5.88L14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>'
)
SVG["thumbs_down"] = _svg(
    '<path d="M17 14V2M9 18.12L10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>'
)
SVG["share"] = _svg(
    '<path d="M7 17L17 7M7 7h10v10"/>'
)
SVG["trash"] = _svg(
    '<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
    '<path d="M10 11v6M14 11v6"/>'
)
SVG["edit"] = _svg(
    '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
    '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'
)
SVG["duplicate"] = _svg(
    '<rect x="8" y="8" width="13" height="13" rx="2"/>'
    '<path d="M4 16V4a2 2 0 0 1 2-2h12"/>'
)
SVG["folder"] = _svg(
    '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
)
SVG["file"] = _svg(
    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
    '<path d="M14 2v6h6"/>'
)
SVG["close"] = _svg('<path d="M18 6L6 18M6 6l12 12"/>')
SVG["chevron_down"] = _svg('<path d="M6 9l6 6 6-6"/>')
SVG["chevron_right"] = _svg('<path d="M9 6l6 6-6 6"/>')
SVG["send"] = _svg(
    '<path d="M12 20V5" stroke-width="2.4" stroke-linecap="round"/>'
    '<path d="M5.5 11.5L12 5l6.5 6.5" stroke-width="2.4" '
    'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
)
SVG["stop"] = _svg(
    '<rect x="6" y="6" width="12" height="12" rx="2" '
    'fill="none" stroke-width="2.4"/>'
)
SVG["attach"] = _svg('<path d="M12 5v14M5 12h14"/>')
SVG["more"] = _svg(
    '<circle cx="12" cy="12" r="1.5" fill="currentColor"/>'
    '<circle cx="19" cy="12" r="1.5" fill="currentColor"/>'
    '<circle cx="5" cy="12" r="1.5" fill="currentColor"/>'
)
SVG["download"] = _svg(
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>'
)
SVG["chat"] = _svg(
    '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
)
SVG["info"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="M12 16v-4M12 8h.01"/>'
)
SVG["user"] = _svg(
    '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
    '<circle cx="12" cy="7" r="4"/>'
)
SVG["check"] = _svg('<path d="M20 6L9 17l-5-5"/>')
SVG["alert"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="M12 8v4M12 16h.01"/>'
)
SVG["wrench"] = _svg(
    '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
)
SVG["brain"] = _svg(
    '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44A2.5 2.5 0 0 1 4 17.5v-1A2.5 2.5 0 0 1 3 14.5V10a2.5 2.5 0 0 1 1-2V6.5A2.5 2.5 0 0 1 6.5 4c.44-1.2 1.5-2 3-2z"/>'
    '<path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44A2.5 2.5 0 0 0 20 17.5v-1a2.5 2.5 0 0 0 1-2V10a2.5 2.5 0 0 0-1-2V6.5A2.5 2.5 0 0 0 17.5 4c-.44-1.2-1.5-2-3-2z"/>'
)
SVG["sparkles"] = _svg(
    '<path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/>'
    '<path d="M19 14l.7 2.1L22 17l-2.3.9L19 20l-.7-2.1L16 17l2.3-.9L19 14z"/>'
)
SVG["power"] = _svg(
    '<path d="M12 2v10"/>'
    '<path d="M18.4 6.6a9 9 0 1 1-12.77 0"/>'
)



SVG["panel_right"] = _svg(
    '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    '<path d="M15 3v18"/>'
)
SVG["terminal"] = _svg(
    '<path d="M4 17l6-6-6-6"/>'
    '<path d="M12 19h8"/>'
)
SVG["globe"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="M2 12h20"/>'
    '<path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20z"/>'
)
SVG["compass"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="none"/>'
)
SVG["arrow_left"] = _svg('<path d="M19 12H5M12 19l-7-7 7-7"/>')
SVG["refresh"] = _svg(
    '<path d="M23 4v6h-6M1 20v-6h6"/>'
    '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'
)
SVG["external"] = _svg(
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<path d="M15 3h6v6"/>'
    '<path d="M10 14L21 3"/>'
)



SVG["sparkle"] = _svg(
    '<path d="M12 3l1.9 4.6L18.5 9.5l-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3z" fill="currentColor" stroke="none"/>'
)
SVG["dots"] = _svg(
    '<circle cx="5" cy="12" r="1.6" fill="currentColor"/>'
    '<circle cx="12" cy="12" r="1.6" fill="currentColor"/>'
    '<circle cx="19" cy="12" r="1.6" fill="currentColor"/>'
)
SVG["activity"] = _svg('<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>')
SVG["zap"] = _svg(
    '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
)
SVG["database"] = _svg(
    '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
    '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
    '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
)
SVG["gauge"] = _svg(
    '<path d="M12 14l4-4"/>'
    '<path d="M3.34 19a10 10 0 1 1 17.32 0"/>'
)
SVG["sliders"] = _svg(
    '<line x1="4" y1="21" x2="4" y2="14"/>'
    '<line x1="4" y1="10" x2="4" y2="3"/>'
    '<line x1="12" y1="21" x2="12" y2="12"/>'
    '<line x1="12" y1="8" x2="12" y2="3"/>'
    '<line x1="20" y1="21" x2="20" y2="16"/>'
    '<line x1="20" y1="12" x2="20" y2="3"/>'
    '<line x1="1" y1="14" x2="7" y2="14"/>'
    '<line x1="9" y1="8" x2="15" y2="8"/>'
    '<line x1="17" y1="16" x2="23" y2="16"/>'
)
SVG["target"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<circle cx="12" cy="12" r="6"/>'
    '<circle cx="12" cy="12" r="2"/>'
)



SVG["users"] = _svg(
    '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
    '<circle cx="9" cy="7" r="4"/>'
    '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
    '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
)
SVG["shield"] = _svg(
    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
)
SVG["clock"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<polyline points="12 6 12 12 16 14"/>'
)
SVG["mic"] = _svg(
    '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>'
    '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
    '<line x1="12" y1="19" x2="12" y2="23"/>'
    '<line x1="8" y1="23" x2="16" y2="23"/>'
)
SVG["layers"] = _svg(
    '<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
    '<polyline points="2 17 12 22 22 17"/>'
    '<polyline points="2 12 12 17 22 12"/>'
)
SVG["loop"] = _svg(
    '<path d="M17 1l4 4-4 4"/>'
    '<path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
    '<path d="M7 23l-4-4 4-4"/>'
    '<path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
)









SVG["win_min"] = _svg(
    '<path d="M4.5 12h15" stroke-width="1.1"/>'
)
SVG["win_max"] = _svg(
    '<rect x="4.5" y="4.5" width="15" height="15" rx="2.5" '
    'stroke-width="1.1" fill="none"/>'
)
SVG["win_restore"] = _svg(
    '<rect x="4.5" y="7.5" width="12" height="12" rx="2.5" '
    'stroke-width="1.1" fill="none"/>'
    '<path d="M8.5 4.5h9a2 2 0 0 1 2 2v9" stroke-width="1.1"/>'
)
SVG["win_close"] = _svg(
    '<path d="M5.5 5.5l13 13M18.5 5.5l-13 13" stroke-width="1.1"/>'
)



SVG["folder_plus"] = _svg(
    '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
    '<path d="M12 11v6M9 14h6"/>'
)
SVG["trash"] = _svg(
    '<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
)



SVG["image"] = _svg(
    '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    '<circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>'
    '<path d="M21 15l-5-5L5 21"/>'
)
SVG["loader"] = _svg(
    '<path d="M21 12a9 9 0 1 1-6.2-8.55" stroke-width="2.2"/>'
)




# --- SVG-иконки для диалогов (кружок + символ) ---
SVG["help"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
    '<line x1="12" y1="17" x2="12.01" y2="17"/>'
)

SVG["alert"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="12" y1="8" x2="12" y2="12"/>'
    '<line x1="12" y1="16" x2="12.01" y2="16"/>'
)

SVG["info"] = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="12" y1="16" x2="12" y2="12"/>'
    '<line x1="12" y1="8" x2="12.01" y2="8"/>'
)

SVG["check_circle"] = _svg(
    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
    '<polyline points="22 4 12 14.01 9 11.01"/>'
)



SVG["chevron_up"] = _svg('<path d="M18 15l-6-6-6 6"/>')

_icon_cache = {}


def make_icon(name: str, color: str = "#ececec", size: int = 20):
    """Кэшированная версия — одинаковые иконки считаются 1 раз."""
    key = (name, color, size)
    if key in _icon_cache:
        return _icon_cache[key]
    icon = _make_icon_raw(name, color, size)
    _icon_cache[key] = icon
    return icon


def _make_icon_raw(name: str, color: str = "#ececec", size: int = 20):
    """Рендерит SVG в QIcon с запасом, antialiasing и 3x для чёткости."""
    import re

    svg = SVG.get(name)
    if not svg:
        return QIcon()
    svg = svg.replace("currentColor", color)

    # Расширяем viewBox на 1 единицу со всех сторон — stroke не обрезается
    def pad_viewbox(m):
        try:
            x, y, w, h = (float(v) for v in m.groups())
        except ValueError:
            return m.group(0)
        return 'viewBox="{} {} {} {}"'.format(x - 2, y - 2, w + 4, h + 4)

    svg = re.sub(
        r'viewBox="([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"',
        pad_viewbox, svg)

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    # Рендерим в 3x для чётких линий при масштабировании
    SCALE = 3
    px = size * SCALE
    pix = QPixmap(px, px)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    renderer.render(painter)
    painter.end()

    # Сообщаем Qt реальный размер — при отображении в size×size будет резко
    pix.setDevicePixelRatio(float(SCALE))

    return QIcon(pix)
