import threading
import os


def _run_settings_gui():
    from tkinter import Tk, filedialog, Label, Button
    from config import load_config, save_config

    config = load_config()

    def save_path():
        initial_dir = os.path.dirname(config.get("options_plus_path", "C:\\"))
        folder = filedialog.askdirectory(
            title="Select LogiOptionsPlus Folder", initialdir=initial_dir
        )
        if folder:
            path = os.path.join(folder, "LogiOptionsPlus.exe")
            if os.path.exists(path):
                config["options_plus_path"] = path
                save_config(config)
                label.config(text=f"✅ Saved:\n{path}")
            else:
                label.config(text="❌ LogiOptionsPlus.exe not found in selected folder")

    window = Tk()
    window.title("Logi Battery Tray Settings")
    window.geometry("400x200")

    label = Label(window, text=f"Current: {config.get('options_plus_path')}", pady=10)
    label.pack()

    select_button = Button(window, text="Browse", command=save_path)
    select_button.pack(pady=10)

    close_button = Button(window, text="Close", command=window.destroy)
    close_button.pack()

    window.mainloop()


def open_settings_window():
    if threading.active_count() > 10:
        print("[INFO] Settings window already open.")
        return
    threading.Thread(target=_run_settings_gui, daemon=True).start()
