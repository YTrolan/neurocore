"""NeuroCore — точка входа для PyInstaller.

ВАЖНО: используем только абсолютные импорты.
Относительные (from . import ...) работают только внутри пакета,
но PyInstaller запускает этот файл как standalone-скрипт.
"""


def _fix_streams():
    """sys.stdout/stderr могут быть None в windowed-сборке .exe."""
    import os
    import sys
    if sys.stdout is None:
        try:
            sys.stdout = open(os.devnull, "w")
        except Exception:
            pass
    if sys.stderr is None:
        try:
            sys.stderr = open(os.devnull, "w")
        except Exception:
            pass


def main():
    _fix_streams()
    from neurocore.gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
