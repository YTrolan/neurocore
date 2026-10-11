"""Инструмент для автоматической игры в Roblox."""
import time
import pyautogui
import pydirectinput
from pathlib import Path
from ..base import Tool

class RobloxAutoPlayTool(Tool):
    name = "roblox_auto_play"
    description = (
        "Автоматически играет в Roblox. Делает скриншот, анализирует его "
        "с помощью vision-модели и выполняет игровые действия. "
        "Используй для автоматизации повторяющихся задач в Roblox."
    )
    parameters = {
        "prompt": "Что нужно делать в игре? Например, 'фарми ресурсы' или 'играй в мини-игру'.",
        "duration_seconds": "Сколько времени играть (по умолчанию 60 секунд).",
        "action_delay": "Пауза между действиями в секундах (по умолчанию 2).",
    }

    def run(self, prompt: str, duration_seconds: int = 60, action_delay: float = 2.0) -> str:
        try:
            from ...token_manager import load_token
            import opendeep
            from opendeep import GenerativeModel
        except ImportError as e:
            return f"[error] Не удалось импортировать модули: {e}"

        token = load_token()
        if not token:
            return "[error] Токен DeepSeek не найден. Настройте токен в Настройках."

        opendeep.configure(api_key=token)
        
        # Попытка использовать vision-модель. Если не поддерживается, будет fallback.
        try:
            vision_model = GenerativeModel("deepseek-v4-flash-vision-exp")
        except Exception:
            return "[error] Vision-модель недоступна. Проверьте доступность `deepseek-v4-flash-vision-exp`."

        start_time = time.time()
        actions_log = []
        
        # Убедимся, что окно Roblox активно (можно уточнить, как именно оно называется)
        try:
            roblox_window = pyautogui.getWindowsWithTitle("Roblox")[0]
            roblox_window.activate()
            time.sleep(1)
        except IndexError:
            return "[error] Окно Roblox не найдено. Убедитесь, что игра запущена."

        while time.time() - start_time < duration_seconds:
            # 1. Делаем скриншот
            screenshot_path = Path("roblox_screen.png")
            try:
                # Делаем скриншот именно области окна Roblox для эффективности
                rect = roblox_window.box
                screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width, rect.height))
                screenshot.save(screenshot_path)
            except Exception as e:
                return f"[error] Не удалось сделать скриншот: {e}"

            # 2. Анализируем через vision-модель
            analysis_prompt = (
                f"Ты — AI-агент, который играет в Roblox. "
                f"Текущая задача: '{prompt}'. "
                f"Посмотри на скриншот и определи, какое ОДНО действие нужно сделать сейчас. "
                f"Ответь строго в формате JSON: {{\"action\": \"название_действия\", \"params\": {{...}}}}. "
                f"Возможные действия: "
                f"'move_forward', 'move_backward', 'move_left', 'move_right', "
                f"'jump', 'click_screen', 'wait', 'chat', 'use_item'. "
                f"Для 'click_screen' укажи 'x' и 'y' в params (координаты в пикселях относительно окна игры). "
                f"Для 'chat' укажи 'message' в params. "
                f"Пример: {{\"action\": \"move_forward\", \"params\": {{}}}}"
            )
            
            try:
                with open(screenshot_path, "rb") as f:
                    img_bytes = f.read()
                
                response = vision_model.generate_content(
                    [analysis_prompt, {"mime_type": "image/png", "data": img_bytes}]
                )
                response_text = getattr(response, "text", "").strip()
            except Exception as e:
                return f"[error] Ошибка vision-модели: {e}"

            # 3. Парсим и выполняем действие
            import json
            try:
                # Ищем JSON в ответе
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    action_data = json.loads(json_match.group())
                else:
                    action_data = {"action": "wait", "params": {}}
            except json.JSONDecodeError:
                action_data = {"action": "wait", "params": {}}

            action = action_data.get("action", "wait")
            params = action_data.get("params", {})

            log_msg = f"Действие: {action} с параметрами {params}"
            actions_log.append(log_msg)
            
            try:
                if action == "move_forward":
                    pydirectinput.keyDown('w')
                    time.sleep(action_delay)
                    pydirectinput.keyUp('w')
                elif action == "move_backward":
                    pydirectinput.keyDown('s')
                    time.sleep(action_delay)
                    pydirectinput.keyUp('s')
                elif action == "move_left":
                    pydirectinput.keyDown('a')
                    time.sleep(action_delay)
                    pydirectinput.keyUp('a')
                elif action == "move_right":
                    pydirectinput.keyDown('d')
                    time.sleep(action_delay)
                    pydirectinput.keyUp('d')
                elif action == "jump":
                    pydirectinput.press('space')
                elif action == "click_screen":
                    x = params.get("x")
                    y = params.get("y")
                    if x is not None and y is not None:
                        # Клик с использованием pydirectinput для DirectX-игр
                        pydirectinput.click(x, y)
                    else:
                        log_msg += " (Ошибка: не указаны x, y)"
                elif action == "chat":
                    msg = params.get("message", "")
                    if msg:
                        pydirectinput.press('t') # Открыть чат
                        time.sleep(0.5)
                        pydirectinput.write(msg)
                        pydirectinput.press('enter')
                elif action == "wait":
                    pass # Просто ждем
                else:
                    log_msg += " (Неизвестное действие)"
            except Exception as e:
                log_msg += f" (Ошибка выполнения: {e})"

            time.sleep(action_delay) # Пауза перед следующим циклом

        # Убираем временный файл
        try:
            screenshot_path.unlink()
        except OSError:
            pass

        # Формируем отчёт
        report = f"Автоматическая игра завершена за {int(time.time() - start_time)} секунд.\n"
        report += f"Выполнено действий: {len(actions_log)}\n"
        report += "Последние 10 действий:\n"
        report += "\n".join(actions_log[-10:])
        return report