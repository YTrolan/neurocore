"""Release-сборка .exe (без консоли)."""
from pathlib import Path
import subprocess
import shutil
import sys

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"

for p in (DIST, BUILD):
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
print("[ok] очищено")

subprocess.run(["taskkill", "/IM", "NeuroCore.exe", "/F"], capture_output=True)
print("[ok] процессы убиты")

import wasmtime
wt_dll = Path(wasmtime.__file__).parent / "win32-x86_64" / "_wasmtime.dll"
print(f"[ok] wasmtime: {wt_dll.name}")

icon_arg = ["--icon", str(ROOT / "icon.ico")] if (ROOT / "icon.ico").exists() else []

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

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "NeuroCore",
    "--windowed",
    "--onefile",
    "--noconfirm",
    "--clean",
    "--log-level", "ERROR",
    str(ROOT / "run.py"),
    "--collect-all", "opendeep",
    "--collect-all", "curl_cffi",
    "--collect-all", "wasmtime",
    "--collect-all", "numpy",
    "--collect-all", "pyautogui",
    "--collect-all", "pygetwindow",
    "--collect-all", "pyperclip",
    "--collect-all", "PIL",
    "--collect-all", "pyte",
    "--collect-all", "winpty",
    "--collect-all", "playwright",
    "--hidden-import", "wasmtime",
    "--hidden-import", "_wasmtime",
    "--hidden-import", "numpy",
    "--hidden-import", "_cffi_backend",
    "--hidden-import", "cffi",
    "--hidden-import", "PySide6.QtSvg",
    "--hidden-import", "PySide6.QtSvgWidgets",
    "--hidden-import", "PySide6.QtNetwork",
    "--hidden-import", "PySide6.QtPrintSupport",
    "--hidden-import", "PySide6.QtOpenGL",
    "--hidden-import", "PySide6.QtOpenGLWidgets",
    "--add-binary", f"{wt_dll};wasmtime/win32-x86_64",
]

cmd.extend(icon_arg)
for mod in EXCLUDE:
    cmd.extend(["--exclude-module", mod])

print()
print("Собираю release (5-7 минут)...")
print()

r = subprocess.run(cmd, cwd=str(ROOT))
if r.returncode != 0:
    print(f"[!] код {r.returncode}")
    sys.exit(1)

exe = DIST / "NeuroCore.exe"
mb = exe.stat().st_size / 1024 / 1024
print()
print("=" * 55)
print(f"ГОТОВО: {exe}")
print(f"Размер: {mb:.1f} MB")
print("=" * 55)
