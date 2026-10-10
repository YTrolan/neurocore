# Установка

## Требования

- **Python 3.10+** — [скачать](https://python.org/downloads)
- **Windows 10/11** (macOS и Linux работают, но не тестировались)
- **Google Chrome** — для работы браузерных инструментов
- **Аккаунт DeepSeek** — бесплатно, [chat.deepseek.com](https://chat.deepseek.com)

## Быстрый старт

Открой cmd или PowerShell:

    git clone https://github.com/YTrolan/neurocore.git
    cd neurocore

    python -m venv .venv
    .venv\Scripts\activate

    pip install -e .

    REM Опционально — для полного набора инструментов
    pip install pyautogui pillow pygetwindow pyperclip
    pip install playwright

## Настройка токена

NeuroCore нужен твой `userToken` от DeepSeek. Три способа:

### Способ 1 — Автоматически из Chrome (рекомендую)

1. Войди на [chat.deepseek.com](https://chat.deepseek.com) в Chrome
2. Закрой Chrome (все окна)
3. Запусти:

       python -m neurocore.token_manager

Скрипт скопирует профиль Chrome во временную папку, откроет его в Playwright
и заберёт токен в `~/.neurocore/token.txt`.

### Способ 2 — Переменная окружения

    set DEEPSEEK_TOKEN=твой_токен

Найти токен вручную:
- Chrome → F12 → **Application** → **Local Storage** → `https://chat.deepseek.com`
- Скопируй значение `userToken`

### Способ 3 — Вручную в файл

    mkdir "%USERPROFILE%\.neurocore"
    echo ТВОЙ_ТОКЕН > "%USERPROFILE%\.neurocore\token.txt"

## Запуск

GUI:

    python -m neurocore.gui

CLI:

    python -m neurocore.cli

## Решение проблем

**`ImportError: No module named 'PySide6'`**
    pip install PySide6

**`playwright._impl._errors.Error: Executable doesn't exist`**
    Установи Chrome или используй Edge. Playwright запустит их автоматически.

**Токен не работает**
    Проверь `~/.neurocore/token.txt`. Залогинься заново на chat.deepseek.com.
    Убедись что с VPN или мобильного интернета — РФ IP иногда блокируются.

**`SSL: CERTIFICATE_VERIFY_FAILED`**
    Уже обработано в коде (`verify=False`). Если всё равно — обнови `requests`.
