"""Собирает NeuroCore.exe со ВСЕМИ библиотеками внутри."""
from pathlib import Path
import subprocess
import shutil
import sys

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"

# ============================================================
# 1. Проверяем и ставим все пакеты
# ============================================================
NEEDED_PACKAGES = [
    "python-docx", "pypdf", "openpyxl", "pyyaml",
    "psutil", "pillow", "markdown", "xmltodict",
    "croniter", "tomli-w", "pydirectinput", "opencv-python",
    "pyte", "winpty", "pygetwindow", "pyperclip", "playwright",
    "wasmtime", "numpy", "requests", "curl_cffi",
    "opendeep", "PySide6",
]

print("=" * 60)
print("ШАГ 1. Проверка зависимостей")
print("=" * 60)

for pkg in NEEDED_PACKAGES:
    r = subprocess.run(
        [sys.executable, "-m", "pip", "show", pkg],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"[+] Ставлю {pkg}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            check=False,
        )
    else:
        print(f"[ok] {pkg}")

# ============================================================
# 2. Чистим старые сборки
# ============================================================
print()
print("=" * 60)
print("ШАГ 2. Очистка старых сборок")
print("=" * 60)

for p in (DIST, BUILD):
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
        print(f"[ok] удалено: {p.name}/")

# Убиваем запущенный .exe
subprocess.run(["taskkill", "/IM", "NeuroCore.exe", "/F"],
               capture_output=True)
print("[ok] процессы убиты")

# ============================================================
# 3. Пути к wasmtime
# ============================================================
import wasmtime
wt_dll = Path(wasmtime.__file__).parent / "win32-x86_64" / "_wasmtime.dll"
print(f"[ok] wasmtime: {wt_dll.name}")

# ============================================================
# 4. Исключения Qt (не нужны — экономят 130 MB)
# ============================================================
EXCLUDE = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
    "PySide6.Qt3DExtras", "PySide6.Qt3DInput", "PySide6.Qt3DLogic",
    "PySide6.QtBluetooth", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtDBus",
    "PySide6.QtDesigner", "PySide6.QtGraphs", "PySide6.QtGraphsWidgets",
    "PySide6.QtHelp", "PySide6.QtHttpServer", "PySide6.QtLocation",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth", "PySide6.QtNfc", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtPositioning",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
    "PySide6.QtSerialBus", "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio", "PySide6.QtSql",
    "PySide6.QtStateMachine", "PySide6.QtTest",
    "PySide6.QtTextToSpeech", "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets", "PySide6.QtWebSockets",
    "PySide6.QtWebView", "PySide6.QtXml",
    "PySide6.QtAxContainer", "PySide6.QtConcurrent",
    "tkinter", "matplotlib", "scipy", "pandas",
    "IPython", "jupyter", "notebook", "PyQt5", "PyQt6",
]

# ============================================================
# 5. Команда сборки
# ============================================================
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "NeuroCore",
    "--windowed",
    "--onefile",
    "--noconfirm",
    "--clean",
    "--log-level", "ERROR",
    str(ROOT / "run.py"),

    # ---- Основные библиотеки ----
    "--collect-all", "opendeep",
    "--collect-all", "curl_cffi",
    "--collect-all", "wasmtime",
    "--collect-all", "numpy",
    "--collect-all", "pyautogui",
    "--collect-all", "pygetwindow",
    "--collect-all", "pyperclip",
    "--collect-all", "pydirectinput",
    "--collect-all", "cv2",           # opencv
    "--collect-all", "PIL",
    "--collect-all", "docx",
    "--collect-all", "pypdf",
    "--collect-all", "openpyxl",
    "--collect-all", "yaml",
    "--collect-all", "psutil",
    "--collect-all", "markdown",
    "--collect-all", "xmltodict",
    "--collect-all", "croniter",
    "--collect-all", "tomli_w",
    "--collect-all", "tomli",
    "--collect-all", "pyte",
    "--collect-all", "winpty",
    "--collect-all", "playwright",

    # ---- Скрытые импорты ----
    "--hidden-import", "wasmtime",
    "--hidden-import", "_wasmtime",
    "--hidden-import", "numpy",
    "--hidden-import", "_cffi_backend",
    "--hidden-import", "cffi",
    "--hidden-import", "pydirectinput",
    "--hidden-import", "cv2",
    "--hidden-import", "docx",
    "--hidden-import", "pypdf",
    "--hidden-import", "openpyxl",
    "--hidden-import", "yaml",
    "--hidden-import", "psutil",
    "--hidden-import", "markdown",
    "--hidden-import", "xmltodict",
    "--hidden-import", "croniter",
    "--hidden-import", "tomli_w",
    "--hidden-import", "tomli",
    "--hidden-import", "xml.etree.ElementTree",
    "--hidden-import", "sqlite3",
    "--hidden-import", "configparser",
    "--hidden-import", "plistlib",
    "--hidden-import", "ipaddress",
    "--hidden-import", "hmac",
    "--hidden-import", "secrets",
    "--hidden-import", "unicodedata",
    "--hidden-import", "PySide6.QtSvg",
    "--hidden-import", "PySide6.QtSvgWidgets",
    "--hidden-import", "PySide6.QtNetwork",
    "--hidden-import", "PySide6.QtPrintSupport",
    "--hidden-import", "PySide6.QtOpenGL",
    "--hidden-import", "PySide6.QtOpenGLWidgets",

    # ---- wasmtime.dll ----
    "--add-binary", f"{wt_dll};wasmtime/win32-x86_64",
]

# Иконка
if (ROOT / "icon.ico").exists():
    cmd += ["--icon", str(ROOT / "icon.ico")]
    print("[ok] иконка")

# Исключения
for mod in EXCLUDE:
    cmd += ["--exclude-module", mod]

# ============================================================
# 6. Запуск
# ============================================================
print()
print("=" * 60)
print(f"ШАГ 3. Сборка (5-10 минут, {len(EXCLUDE)} исключений)")
print("=" * 60)
print()

r = subprocess.run(cmd, cwd=str(ROOT))
if r.returncode != 0:
    print(f"[!] PyInstaller упал: код {r.returncode}")
    sys.exit(1)

exe = DIST / "NeuroCore.exe"
if not exe.exists():
    print("[!] NeuroCore.exe не создан")
    sys.exit(1)

mb = exe.stat().st_size / 1024 / 1024
print()
print("=" * 60)
print(f"ГОТОВО: {exe}")
print(f"Размер: {mb:.1f} MB")
print("=" * 60)
print()
print("Что теперь работает БЕЗ дополнительных установок:")
print("  • Файлы: read_docx, read_pdf, read_xlsx")
print("  • Картинки: resize, convert, watermark")
print("  • Данные: csv ↔ json ↔ yaml ↔ xml")
print("  • SQLite: query, import CSV")
print("  • Система: reg, services, tasks, admin")
print("  • Dev: git, pip, pytest, compile")
print("  • Roblox: автоплей через pydirectinput")
print("  • Текст: slug, extract, normalize")
print("  • Math, Crypto, Time — всё работает")
print()
print("Проверь:")
print(f"  {exe}")