# 🧠 NeuroCore

[![Build & Release](https://github.com/YTrolan/neurocore/actions/workflows/build-release.yml/badge.svg)](https://github.com/YTrolan/neurocore/actions/workflows/build-release.yml)
[![Latest Release](https://img.shields.io/github/v/release/YTrolan/neurocore?color=green&label=release)](https://github.com/YTrolan/neurocore/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/YTrolan/neurocore/total?color=blue)](https://github.com/YTrolan/neurocore/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-9cf)](#-установка)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Made with PySide6](https://img.shields.io/badge/UI-PySide6-41cd52)](https://www.qt.io/qt-for-python)

> **NeuroCore** — десктопный клиент для DeepSeek с поддержкой инструментов, генерации изображений и автономного агентного цикла. Работает через неофициальный веб-API через библиотеку [OpenDeep](https://github.com/cmpdchtr/OpenDeep).

---

## ✨ Возможности

- 🤖 **DeepSeek внутри** — полный доступ к моделям `deepseek-v4-pro`, `deepseek-reasoner`, `deepseek-chat`
- 🧠 **DeepThink** — режим пошаговых рассуждений для сложных задач
- 🔧 **Tool-calling** — агент сам вызывает shell, читает/пишет файлы, ходит в интернет
- 🎨 **Генерация изображений** — встроенный тул через Pollinations (бесплатно, без ключа)
- 💬 **Многосессионность** — история чатов, переименование, экспорт
- 🗂 **Workspace** — рабочие папки, привязка проектов к сессиям
- 🖥 **Нативный frameless UI** — Qt/PySide6, тёмная тема, кастомная типографика
- ⚡ **Сборка onefile** — один `.exe` / один бинарь Linux, без зависимостей

---

## 📦 Установка

### Windows

Скачай [`NeuroCore.exe`](https://github.com/YTrolan/neurocore/releases/latest) со страницы релизов и запусти. Ничего дополнительно ставить не нужно.

### Linux

    wget https://github.com/YTrolan/neurocore/releases/latest/download/NeuroCore-linux-x64
    chmod +x NeuroCore-linux-x64
    ./NeuroCore-linux-x64

### Из исходников

    git clone https://github.com/YTrolan/neurocore.git
    cd neurocore
    pip install -e .

Нужен **Python 3.10+**.

---

## 🚀 Быстрый старт

1. Запусти `NeuroCore` (или `python -m neurocore.gui`)
2. Открой `chat.deepseek.com` → F12 → Application → Local Storage → скопируй `userToken`
3. Вставь токен в настройках приложения
4. Начинай чат

**Примеры запросов:**

    › создай файл hello.py с print("hi") и запусти его
    › нарисуй кота в космосе и сохрани в cat.png
    › прочитай все .py в проекте и расскажи что он делает

---

## 🏗 Архитектура

    neurocore/
    ├── core/        # Provider (OpenDeep, официальный API)
    ├── tools/       # Инструменты: shell, files, image, web
    ├── agent/       # Agent loop: think → act → observe
    ├── gui/         # PySide6 интерфейс
    └── cli.py       # CLI-версия

**Ключевая идея:** провайдер отделён от тулов и от UI. Если OpenDeep сломается — подменяешь на официальный API DeepSeek одной строкой.

---

## 🛠 Разработка

    # зависимости
    pip install -e .

    # CLI-версия
    python -m neurocore.cli

    # GUI-версия
    python -m neurocore.gui

    # сборка релиза локально
    python build_full.py

CI/CD: при пуше тега `v*` GitHub Actions собирает Windows `.exe` и Linux бинарь автоматически.

---

## 📄 Лицензия

MIT — используй свободно.

---

<p align="center">
  <sub>Сделано с ❤️ на Python + PySide6 + DeepSeek</sub>
</p>
