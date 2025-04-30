import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "AppData/Local/LogiOptionsPlus/settings.db"


def get_battery_info():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file FROM data LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            print("[WARN] No data in settings.db")
            return None, None

        data = json.loads(row[0])
        battery = data.get("battery/mx-master-3s-2b034/warning_notification", {})
        level = battery.get("batteryLevel")
        timestamp_raw = battery.get("time")

        if level is not None and timestamp_raw:
            # Handle string or int timestamp
            try:
                timestamp = int(timestamp_raw)
                updated_at = datetime.fromtimestamp(timestamp)
            except ValueError:
                updated_at = None
            return level, updated_at

    except Exception as e:
        print(f"[ERROR] Failed to read battery info from DB: {e}")
        return None, None
