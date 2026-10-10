# История версий

Все значимые изменения NeuroCore описаны здесь.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/),
версии следуют [Semantic Versioning](https://semver.org/lang/ru/).

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
