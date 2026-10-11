# История версий

Все значимые изменения NeuroCore описаны здесь.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/),
версии следуют [Semantic Versioning](https://semver.org/lang/ru/).

## [1.0.2] - 2026-10-11

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

## [1.0.0] - 2026-10-10

### Добавлено
- Первый публичный релиз
- GUI на PySide6 в стиле DeepSeek Harness
- 36 встроенных инструментов:
  - Файлы — read, write, list, grep, find, mkdir, rm, mv, cp, head, tail, wc
  - Система — shell, system_info, process_list, env_get, env_set, disk_usage
  - Интернет — deepseek_search, http_get, download_file, open_url
  - Данные — base64, hash, json_pretty, uuid, rand
  - Утилиты — calc, sleep, time_now, notify, clipboard
  - Архивы — zip_create, zip_extract
  - Картинки — generate_image (Pollinations, бесплатно)
  - Desktop — screenshot, click, type, hotkey, drag, scroll, windows
  - Браузер — Playwright + Chrome: open, click, type, screenshot, links
- Автополучение токена из Chrome
- Многосессионный чат с сохранением
- Система прав: только чтение / workspace / полный доступ
- Просмотр траектории вызовов
- Палитра команд (Ctrl+K)
- Своя тема оформления

### Исправлено
- Изоляция сессий (у каждой свой контекст)
- Кнопка Стоп работает мгновенно (terminate через 500мс)
- Убраны бесконечные циклы (антиповтор, максимум 6 итераций)
- Защита от повторной генерации картинки

[1.0.0]: https://github.com/YTrolan/neurocore/releases/tag/v1.0.0
