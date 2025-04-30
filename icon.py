from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import time
from battery import get_battery_info
from settings import open_settings_window
from config import load_config

config = load_config()


def create_icon_image(level: int) -> Image.Image:
    img = Image.new("RGB", (64, 64), color="black")
    draw = ImageDraw.Draw(img)
    fill_color = "green" if level >= 30 else "red"
    draw.rectangle((16, 24, 48, 40), fill=fill_color)
    draw.text((20, 45), f"{level}%", fill="white")
    return img


def build_icon():
    battery, updated = get_battery_info()
    icon = Icon("LogiBattery", create_icon_image(battery if battery else 0))
    icon.title = f"Battery: {battery}%" if battery is not None else "Battery: --%"

    def refresh(icon_ref):
        new_level, _ = get_battery_info()
        if new_level is not None:
            icon_ref.icon = create_icon_image(new_level)
            icon_ref.title = f"Battery: {new_level}%"
            print(f"[INFO] Battery level updated to {new_level}%")

    def loop():
        while True:
            refresh(icon)
            time.sleep(config.get("refresh_interval_seconds", 600))

    icon.menu = Menu(
        MenuItem("Refresh", lambda icon, item: refresh(icon)),
        MenuItem("Settings", lambda icon, item: open_settings_window()),
        MenuItem("Exit", lambda icon, item: icon.stop()),
    )

    threading.Thread(target=loop, daemon=True).start()
    return icon
