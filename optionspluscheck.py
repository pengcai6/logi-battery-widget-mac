import subprocess
import psutil
import threading
import time
import os
from config import load_config

config = load_config()


def is_options_running():
    for proc in psutil.process_iter(["name"]):
        if proc.info.get("name", "").lower() == "logioptionsplus.exe":
            return True
    return False


def launch_options_plus():
    subprocess.Popen(
        [config["options_plus_path"]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def monitor_options_plus():
    def _loop():
        while True:
            if config.get("auto_launch_enabled", True) and not is_options_running():
                print("[INFO] Logi Options+ not running. Launching silently...")
                launch_options_plus()
            else:
                print("[INFO] Logi Options+ is running.")
            time.sleep(config.get("check_interval_seconds", 1800))

    threading.Thread(target=_loop, daemon=True).start()
