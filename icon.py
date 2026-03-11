from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import time
from battery import get_battery_infos, get_battery_info
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


def _format_title(infos):
    if not infos:
        return "Battery: --%"
    parts = [f"{item['device_name']}: {item['level']}%" for item in infos]
    return " | ".join(parts)

def _format_updated_at(updated_at):
    if not updated_at:
        return "--"
    return updated_at.strftime("%Y-%m-%d %H:%M:%S")


def _build_device_items(infos):
    if not infos:
        return [MenuItem("No devices found", lambda *_: None, enabled=False)]
    items = []
    for item in infos:
        updated = _format_updated_at(item.get("updated_at"))
        label = f"{item['device_name']}: {item['level']}% (Updated: {updated})"
        items.append(MenuItem(label, lambda *_: None, enabled=False))
    return items


def build_icon():
    infos = get_battery_infos()
    battery, _ = get_battery_info()
    icon = Icon("LogiBattery", create_icon_image(battery if battery else 0))
    icon.title = _format_title(infos)

    def refresh(icon_ref):
        new_infos = get_battery_infos()
        new_level, _ = get_battery_info()
        if new_level is not None:
            icon_ref.icon = create_icon_image(new_level)
        icon_ref.title = _format_title(new_infos)
        icon_ref.menu = _build_menu(new_infos)
        if new_level is not None:
            print(f"[INFO] Battery level updated to {new_level}%")

    def loop():
        while True:
            refresh(icon)
            time.sleep(config.get("refresh_interval_seconds", 600))

    def _build_menu(infos_for_menu):
        device_items = _build_device_items(infos_for_menu)
        return Menu(
            *device_items,
            MenuItem("Refresh", lambda icon, item: refresh(icon)),
            MenuItem("Settings", lambda icon, item: open_settings_window()),
            MenuItem("Exit", lambda icon, item: icon.stop()),
        )

    icon.menu = _build_menu(infos)

    threading.Thread(target=loop, daemon=True).start()
    return icon
