"""Обновляет лицензию и документацию под v1.0.2."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent

# ============================================================
# 1. НОВАЯ ЛИЦЕНЗИЯ — мягче, но с запретами
# ============================================================
NEW_LICENSE = """NeuroCore — Custom Source-Available License
Copyright (c) 2026 YTrolan
============================================================

Простая лицензия для проекта NeuroCore. Читай внимательно —
она короче и понятнее, чем юридический жаргон.


✅ РАЗРЕШЕНО
─────────────────────────────────────────────

1. ИСПОЛЬЗОВАТЬ
   Запускать NeuroCore на своём компьютере, для личных
   и рабочих задач, без ограничений.

2. ИЗУЧАТЬ
   Читать исходный код, разбираться в архитектуре,
   учиться на нём.

3. МОДЕРНИЗИРОВАТЬ
   Изменять код, добавлять функции, улучшать —
   для себя и в своём форке (см. пункт "Форки" ниже).

4. ДЕЛИТЬСЯ ИДЕЯМИ
   Писать статьи, снимать видео, показывать друзьям
   со ссылкой на официальный репозиторий.


❌ ЗАПРЕЩЕНО
─────────────────────────────────────────────

1. ПРОДАВАТЬ
   Нельзя продавать NeuroCore или любую его часть,
   использовать в коммерческих продуктах и сервисах,
   монетизировать напрямую или через рекламу.

2. ПУБЛИКОВАТЬ ЗАНОВО
   Нельзя заливать копию репозитория на GitHub (или
   другие платформы) под своим именем как оригинал.

3. ВЫДАВАТЬ ЗА СВОЁ
   Нельзя менять информацию об авторе в коде,
   документации или интерфейсе.


📦 ФОРКИ
─────────────────────────────────────────────

Форки разрешены ТОЛЬКО для личного использования
и модернизации. Публичный форк на GitHub допустим
при условиях:
  • В README указан оригинал (ссылка на YTrolan/neurocore)
  • Не продаётся и не используется коммерчески
  • Не переименован под другим брендом


💼 КОММЕРЧЕСКОЕ ИСПОЛЬЗОВАНИЕ
─────────────────────────────────────────────

Хочешь использовать NeuroCore в компании, встроить
в свой продукт или сервис? Нужно письменное
разрешение. Свяжись через GitHub Issues.


⚠️ БЕЗ ГАРАНТИЙ
─────────────────────────────────────────────

NeuroCore предоставляется "как есть". Автор не несёт
ответственности за возможный ущерб, потерю данных
или другие последствия использования.


📅 СРОК ДЕЙСТВИЯ
─────────────────────────────────────────────

Лицензия действует бессрочно. При нарушении условий
права автоматически прекращаются.


📬 КОНТАКТ
─────────────────────────────────────────────

GitHub:  https://github.com/YTrolan/neurocore
Issues:  https://github.com/YTrolan/neurocore/issues
Почта:   см. профиль GitHub


============================================================
Оригинал: https://github.com/YTrolan/neurocore
Год: 2026
============================================================
"""

(ROOT / "LICENSE").write_text(NEW_LICENSE, encoding="utf-8")
print("[+] LICENSE — новая мягкая версия")

# ============================================================
# 2. ОБНОВИТЬ README
# ============================================================
R = ROOT / "README.md"
if R.exists():
    shutil.copy2(R, R.with_suffix(".md.bak_v102"))
    rtext = R.read_text(encoding="utf-8")

    # Бейджи
    rtext = rtext.replace(
        "[![Tools](https://img.shields.io/badge/tools-36-orange.svg)](docs/tools.md)",
        "[![Tools](https://img.shields.io/badge/tools-129-orange.svg)](docs/tools.md)",
    )
    rtext = rtext.replace(
        "36 инструментов. Нативный GUI.",
        "129 инструментов. Нативный GUI.",
    )
    rtext = rtext.replace(
        "- 🛠️ **36 инструментов** — файлы, shell, интернет, GUI-контроль, браузер",
        "- 🛠️ **129 инструментов** — файлы, shell, интернет, GUI-контроль, браузер, БД, данные",
    )

    # Добавим новые фичи в возможности (если ещё нет)
    if "Roblox" not in rtext:
        rtext = rtext.replace(
            "- ⌨️ **Палитра команд** — Ctrl+K",
            "- 🤖 **Roblox автоплей** — агент играет сам\n"
            "- 📊 **SQLite, CSV, JSON, YAML, XML** — работа с данными\n"
            "- 📄 **Word, PDF, Excel** — чтение документов\n"
            "- 🔐 **Криптография** — хеши, HMAC, пароли\n"
            "- 🪟 **Система Windows** — реестр, службы, задачи\n"
            "- ⌨️ **Палитра команд** — Ctrl+K",
        )

    # Обновим счёт тулов в таблице
    rtext = rtext.replace("## 🛠️ Инструменты (36)", "## 🛠️ Инструменты (129)")
    rtext = rtext.replace("36 встроенных инструментов:", "129 встроенных инструментов:")

    R.write_text(rtext, encoding="utf-8")
    print("[+] README.md обновлён (129 тулов)")

# ============================================================
# 3. ОБНОВИТЬ CHANGELOG
# ============================================================
C = ROOT / "CHANGELOG.md"
if C.exists():
    shutil.copy2(C, C.with_suffix(".md.bak_v102"))
    ctext = C.read_text(encoding="utf-8")

    NEW_VERSION = """## [1.0.2] - 2026-10-11

### Добавлено
- **93 новых инструмента** (было 36, стало 129):
  - Windows System (10): реестр, службы, задачи, firewall, users
  - Dev Tools (15): git, pip, pytest, flake8, venv, AST-анализ
  - Data / Format (13): TOML, INI, XML, SQLite, MD→HTML, pickle
  - Web / API (12): POST, HEAD, DNS, SSL, URL-parse, JWT-decode
  - Text Advanced (14): slug, transliterate, extract emails/IP/urls/dates
  - Encoding / Crypto (9): hex, base32/85, HMAC, password-gen
  - Math / Random (10): math_eval, stats, prime, fibonacci, dice
  - Time / Date (10): timestamps, cron, timezone, calendar
- **Roblox автоплей** — агент играет через `pydirectinput` + vision-модель

### Исправлено
- **Длинные чаты** — сообщения больше не пропадают при 50+ сообщениях
- **Кодировка** — русские буквы в выводе Windows-команд (cp866)
- **Пути к файлам** — тулы ищут файл в cwd / Downloads / output_dir
- **CSV → SQLite** — параметр `csv` больше не перекрывает модуль
- **`.exe` без консоли** — защита от `sys.stderr = None`
- **Логи краха** — пишутся в `neurocore_crash.log`

### Изменено
- **Лицензия** — с MIT на Custom Source-Available
  (можно модернизировать, нельзя продавать и публиковать заново)

"""
    # Вставим перед [1.0.0]
    if "[1.0.0]" in ctext:
        ctext = ctext.replace("## [1.0.0]", NEW_VERSION + "## [1.0.0]", 1)
    else:
        ctext = NEW_VERSION + ctext

    C.write_text(ctext, encoding="utf-8")
    print("[+] CHANGELOG.md обновлён (v1.0.2)")

# ============================================================
# 4. ОБНОВИТЬ pyproject.toml — версия
# ============================================================
P = ROOT / "pyproject.toml"
if P.exists():
    shutil.copy2(P, P.with_suffix(".toml.bak_v102"))
    ptext = P.read_text(encoding="utf-8")

    import re
    ptext = re.sub(r'version\s*=\s*"1\.0\.0"', 'version = "1.0.2"', ptext)
    ptext = re.sub(r'version\s*=\s*"1\.0\.1"', 'version = "1.0.2"', ptext)

    P.write_text(ptext, encoding="utf-8")
    print("[+] pyproject.toml — version 1.0.2")

# ============================================================
# 5. ОБНОВИТЬ CONTRIBUTING
# ============================================================
CO = ROOT / "CONTRIBUTING.md"
if CO.exists():
    shutil.copy2(CO, CO.with_suffix(".md.bak_v102"))
    ctext = CO.read_text(encoding="utf-8")

    ctext = ctext.replace(
        "## Лицензия\n\nПроект распространяется под проприетарной лицензией.\nОтправляя Pull Request, ты передаёшь все права на изменения Автору проекта.",
        "## Лицензия\n\nПроект распространяется под Custom Source-Available License.\nМожно модернизировать для личного использования, нельзя продавать\nи публиковать заново. См. [LICENSE](LICENSE).\n\nОтправляя Pull Request, ты передаёшь права на изменения Автору проекта."
    )
    CO.write_text(ctext, encoding="utf-8")
    print("[+] CONTRIBUTING.md обновлён")

print()
print("=" * 60)
print("ГОТОВО")
print("=" * 60)
print()
print("Что изменилось:")
print("  • LICENSE — мягкая Source-Available (модернизация ОК)")
print("  • README — 129 тулов, Roblox, новые фичи")
print("  • CHANGELOG — полный список v1.0.2")
print("  • pyproject.toml — version 1.0.2")
print("  • CONTRIBUTING — новая лицензия")
print()
print("Дальше — коммит и релиз:")
print("  git add -A")
print("  git commit -m \"Release v1.0.2: 93 new tools + Roblox + license update\"")
print("  git push")