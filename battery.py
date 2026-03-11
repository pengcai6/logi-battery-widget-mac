import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def _get_db_path():
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/LogiOptionsPlus/settings.db"
    if sys.platform.startswith("win"):
        return Path.home() / "AppData/Local/LogiOptionsPlus/settings.db"
    return None


def _format_device_name(device_id: str) -> str:
    parts = device_id.split("-")
    if parts and len(parts[-1]) == 5 and all(c in "0123456789abcdef" for c in parts[-1].lower()):
        parts = parts[:-1]
    return " ".join(parts).title()


def _parse_timestamp(timestamp_raw):
    if not timestamp_raw:
        return None
    try:
        timestamp = int(timestamp_raw)
        return datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError):
        return None


def get_battery_infos():
    db_path = _get_db_path()
    if not db_path or not db_path.exists():
        print("[WARN] Logi Options+ DB not found")
        return []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file FROM data LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            print("[WARN] No data in settings.db")
            return []

        data = json.loads(row[0])
        results = []
        for key, value in data.items():
            if not key.startswith("battery/") or not key.endswith("/warning_notification"):
                continue
            if not isinstance(value, dict):
                continue
            level = value.get("batteryLevel")
            if level is None:
                continue
            device_id = key.split("/")[1]
            results.append(
                {
                    "device_id": device_id,
                    "device_name": _format_device_name(device_id),
                    "level": level,
                    "updated_at": _parse_timestamp(value.get("time")),
                }
            )
        return results

    except Exception as e:
        print(f"[ERROR] Failed to read battery info from DB: {e}")
        return []


def get_battery_info():
    infos = get_battery_infos()
    if not infos:
        return None, None
    primary = min(infos, key=lambda item: item.get("level", 0))
    return primary.get("level"), primary.get("updated_at")
