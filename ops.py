import subprocess
import time
import threading
from PIL import Image, ImageDraw, ImageFont
import pystray
import sys

class OllamaTrayApp:
    def __init__(self):
        self.icon = None
        self.running = True

        try:
            self.font = ImageFont.truetype("arial.ttf", 50)
        except Exception:
            self.font = ImageFont.load_default()

    def get_ollama_ps(self):
        try:
            result = subprocess.run(
                ["ollama", "ps"],
                capture_output=True, text=True, shell=True
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def create_icon_with_number(self, number):
        img = Image.new('RGBA', (64, 64), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, 64, 64), fill=(0, 0, 0, 255))

        text = str(number)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=self.font)
        text_width = right - left
        text_height = bottom - top

        x = (64 - text_width) / 2
        y = (64 - text_height) / 2

        draw.text((x, y), text, font=self.font, fill=(255, 255, 255, 255))
        return img

    def parse_models_info(self, ps_output):
        if ps_output.startswith("Error:"):
            return []

        models = []
        for line in ps_output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                model_name = parts[0]
                memory = parts[2]
                cpu = parts[4]
                models.append(f"{model_name} (Mem: {memory}, CPU: {cpu})")
            else:
                # В случае необычного формата добавляем всю строку
                models.append(line)
        return models

    def update_tray(self):
        while self.running:
            ps_output = self.get_ollama_ps()
            models = self.parse_models_info(ps_output)
            models_count = len(models)

            # Логируем для отладки (можно раскомментировать)
            # print(f"[update_tray] Models count: {models_count-1}")

            icon_image = self.create_icon_with_number(models_count-1)
            if self.icon:
                # Обновление иконки каждый цикл с актуальным числом
                self.icon.icon = icon_image
                self.icon.title = f"Model(s) loaded: {models_count-1}"

            time.sleep(1)

    def show_balloon(self, icon, item):
        ps_output = self.get_ollama_ps()
        models = self.parse_models_info(ps_output)

        if models:
            balloon_msg = "\n".join(models)
            if len(balloon_msg) > 1000:
                balloon_msg = balloon_msg[:1000] + "\n..."
        else:
            balloon_msg = "Model(s) not found or error."

        icon.notify(balloon_msg, title="Ollama models(s)")

    def quit_app(self, icon, item):
        self.running = False
        self.icon.stop()

    def run(self):
        initial_icon = self.create_icon_with_number(0)
        menu = pystray.Menu(
            pystray.MenuItem("Показать модели", self.show_balloon),
            pystray.MenuItem("Выход", self.quit_app)
        )

        self.icon = pystray.Icon("OllamaPS", initial_icon, "Loading...", menu)

        updater_thread = threading.Thread(target=self.update_tray, daemon=True)
        updater_thread.start()

        self.icon.run()

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Windows only.")
        sys.exit(1)
    app = OllamaTrayApp()
    app.run()
