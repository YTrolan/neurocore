# Справочник инструментов

NeuroCore содержит **36 инструментов**. Агент выбирает их сам.

## Файлы

| Инструмент | Что делает |
|---|---|
| `read_file` | Прочитать файл |
| `write_file` | Записать (перезаписывает) |
| `list_dir` | Содержимое папки |
| `grep` | Поиск по файлам |
| `find` | Найти файлы по маске |
| `mkdir` | Создать папку |
| `rm` | Удалить файл/папку |
| `mv` | Переместить/переименовать |
| `cp` | Скопировать |
| `head` | Первые N строк |
| `tail` | Последние N строк |
| `wc` | Строки / слова / символы |

## Система

| Инструмент | Что делает |
|---|---|
| `shell` | Команда в cmd/powershell/bash |
| `system_info` | ОС, CPU, RAM |
| `process_list` | Список процессов |
| `env_get` | Прочитать переменную |
| `env_set` | Установить переменную |
| `disk_usage` | Свободное место |

## Интернет

| Инструмент | Что делает |
|---|---|
| `deepseek_search` | Поиск через Flash (быстро, точно) |
| `web_search` | Wikipedia / Bing (резерв) |
| `web_fetch` | Скачать URL + извлечь текст |
| `web_text` | Только читаемый текст |
| `http_get` | Сырой GET |
| `download_file` | Скачать в файл |
| `open_url` | Открыть в браузере |

## Desktop (pyautogui)

| Инструмент | Что делает |
|---|---|
| `desktop_screenshot` | Скриншот экрана |
| `desktop_click` | Клик в (x, y) |
| `desktop_double_click` | Двойной клик |
| `desktop_right_click` | ПКМ |
| `desktop_move` | Двигать курсор |
| `desktop_drag` | Тащить из A в B |
| `desktop_scroll` | Колесо |
| `desktop_type` | Печатать текст |
| `desktop_hotkey` | Комбинация (ctrl+c) |
| `desktop_press` | Одна клавиша |
| `desktop_windows` | Список окон |
| `desktop_focus_window` | Активировать окно |
| `desktop_active_window` | Текущее окно |
| `desktop_screen_size` | Размер экрана |
| `desktop_cursor_pos` | Позиция курсора |
| `desktop_wait` | Пауза |
| `desktop_open_url` | Открыть URL |
| `desktop_read_clipboard` | Буфер обмена |
| `desktop_copy_all` | Ctrl+A, Ctrl+C |
| `desktop_find_in_page` | Ctrl+F |
| `desktop_cleanup_screenshots` | Удалить временные PNG |

## Браузер (Playwright + Chrome)

| Инструмент | Что делает |
|---|---|
| `browser_open` | Открыть URL, вернуть текст + кнопки + ссылки |
| `browser_click` | Клик по тексту или CSS |
| `browser_type` | Ввод в поле + Enter |
| `browser_screenshot` | Скриншот страницы |
| `browser_back` | Назад |
| `browser_links` | Список ссылок |
| `browser_get_text` | Текст страницы |
| `browser_close` | Закрыть браузер |

## Данные

| Инструмент | Что делает |
|---|---|
| `base64` | Кодировать / декодировать |
| `hash` | MD5 / SHA256 |
| `json_pretty` | Форматировать JSON |
| `uuid` | Сгенерировать UUID4 |
| `rand` | Случайное число |

## Утилиты

| Инструмент | Что делает |
|---|---|
| `calc` | Математическое выражение |
| `sleep` | Подождать |
| `time_now` | Текущее время |
| `notify` | Уведомление Windows |
| `clipboard_get` / `clipboard_set` | Буфер |

## Картинки

| Инструмент | Что делает |
|---|---|
| `generate_image` | Генерация через Pollinations (бесплатно) |

## Архивы

| Инструмент | Что делает |
|---|---|
| `zip_create` | Заархивировать |
| `zip_extract` | Распаковать |

## Свой инструмент

Создай файл `neurocore/tools/builtin/my_tool.py`:

    from ..base import Tool


    class MyTool(Tool):
        name = "my_tool"
        description = "Что делает"
        parameters = {"arg1": "описание"}

        def run(self, arg1: str) -> str:
            return f"результат: {arg1}"

Затем зарегистрируй в `neurocore/tools/builtin/__init__.py`.

Подробнее в [CONTRIBUTING.md](../CONTRIBUTING.md).
