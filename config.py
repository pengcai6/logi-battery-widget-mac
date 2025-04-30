import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".logi_battery_tray_config.json"


def auto_detect_logi_path():
    guesses = [
        os.path.join(
            os.environ.get("LocalAppData", ""), "LogiOptionsPlus", "LogiOptionsPlus.exe"
        ),
        r"C:\Program Files\LogiOptionsPlus\LogiOptionsPlus.exe",
        r"C:\Program Files (x86)\LogiOptionsPlus\LogiOptionsPlus.exe",
    ]
    for path in guesses:
        if os.path.exists(path):
            return path
    return ""


DEFAULT_CONFIG = {
    "options_plus_path": auto_detect_logi_path(),
    "check_interval_seconds": 1800,
    "auto_launch_enabled": True,
    "refresh_interval_seconds": 600,
}


def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        # Fallback if path saved is no longer valid
        if not os.path.exists(config.get("options_plus_path", "")):
            config["options_plus_path"] = auto_detect_logi_path()
            print("[INFO] Options+ path was invalid, auto-corrected.")

        return config

    except Exception as e:
        print(f"[WARN] Failed to load config: {e}")
        return DEFAULT_CONFIG


def save_config(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)
