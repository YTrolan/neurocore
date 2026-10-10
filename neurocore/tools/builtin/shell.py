from shutil import which as shutil_which
import os
import platform
import subprocess

from ..base import Tool


# Поддерживаемые оболочки: key -> argv
WINDOWS_SHELLS = {
    "cmd": ["cmd.exe", "/c"],
    "powershell": ["powershell", "-NoProfile", "-NonInteractive", "-Command"],
    "pwsh": ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command"],
    "git": ["bash.exe", "-lc"],
    "bash": ["bash.exe", "-lc"],
}

UNIX_SHELLS = {
    "sh": ["/bin/sh", "-c"],
    "bash": ["bash", "-lc"],
    "zsh": ["zsh", "-lc"],
}


class ShellTool(Tool):
    name = "shell"
    description = (
        "Выполнить команду в системной оболочке. "
        "На Windows это PowerShell, на Unix — sh. "
        "Возвращает stdout+stderr и код выхода."
    )
    parameters = {"command": "строка — команда для выполнения"}

    def __init__(self, cwd: str | None = None, timeout: int = 60,
                 shell_kind: str = "cmd"):
        self.cwd = cwd or os.getcwd()
        self.timeout = timeout
        self.shell_kind = (shell_kind or "cmd").lower()

    def _shell_argv(self, command: str) -> list[str]:
        """Собрать argv для выбранной оболочки."""
        if platform.system() == "Windows":
            table = WINDOWS_SHELLS
            default = WINDOWS_SHELLS["cmd"]
        else:
            table = UNIX_SHELLS
            default = UNIX_SHELLS["sh"]
        base = table.get(self.shell_kind, default)
        # git/bash может отсутствовать — падаем на дефолт
        if self.shell_kind in ("git", "bash") and platform.system() == "Windows":
            if shutil_which("bash.exe") is None and shutil_which("bash") is None:
                base = WINDOWS_SHELLS["cmd"]
        return list(base) + [command]

    def run(self, command: str) -> str:
        try:
            argv = self._shell_argv(command)
            r = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                timeout=self.timeout,
            )
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            parts = ["[exit=" + str(r.returncode) + "]"]
            if out:
                parts.append(out)
            if err:
                parts.append("[stderr]\n" + err)
            if not out and not err:
                parts.append("(пусто)")
            return "\n".join(parts)
        except subprocess.TimeoutExpired:
            return "[timeout после " + str(self.timeout) + "s]"
        except FileNotFoundError as e:
            return ("[error] оболочка не найдена (" + self.shell_kind +
                    "): " + str(e))
        except Exception as e:
            return "[error] " + type(e).__name__ + ": " + str(e)
