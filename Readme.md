# Logi Battery Tray

A lightweight system tray utility for Windows that monitors your Logitech MX Master 3S battery level by reading data directly from the Logi Options+ SQLite settings database.

## macOS Widget (Sonoma)

This repo now includes a macOS SwiftUI app + WidgetKit widget under `macos-widget-template/`. It reads Logi Options+ battery data from:

`~/Library/Application Support/LogiOptionsPlus/settings.db`

and writes a snapshot into an App Group container for the widget to render.

### Manual allow (unsigned builds)

If you distribute an unsigned build, macOS Gatekeeper will warn. Users can still open it:

1. In Finder, right-click the app, choose **Open**.
2. Click **Open** in the warning dialog.
3. Or go to **System Settings → Privacy & Security** and click **Open Anyway**.

Note: allowing an unsigned app does **not** guarantee Widget/App Group/Launch at Login will work reliably. Those features depend on proper signing + entitlements.

## 🚀 Features

- 🪫 Tray icon with live battery status
- 🧠 Auto-launch Options+ silently (if not running)
- ⚙️ Settings GUI to choose Options+ path
- 🔄 Periodic background polling
- 🧱 Packaged as MSIX with version auto-injection
- ✅ Optional fulltrust autostart on boot

## 🛠️ Requirements

- Python 3.10+
- Windows 10 or later
- Logi Options+ installed
- Windows SDK (for `makeappx.exe`)
- PyInstaller (for `.exe` builds)

## 🔧 Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🏗 Build & Package
```
python buildandcopy.py --release
```
This will:

    Build the .exe via PyInstaller

    Copy it to the MSIX AppFiles folder

    Inject version into AppxManifest.xml

    Run makeappx.exe to generate the .msix package

## 🖼 App Manifest

MSIX manifest supports:

    runFullTrust capability

    windows.startupTask extension

    Assets and logo bundling

## 📁 Folder Structure

```
/logitec-mouse-battery-tray
│   main.py
│   icon.py
│   config.py
│   optionspluscheck.py
│   ...
│   logo.png
│   buildandcopy.py
│   version.txt
│   requirements.txt
│
└── logi-battery-tray-msix/
    └── AppFiles/
        └── AppxManifest.xml
```

## 📄 License

MIT License. Free for personal and commercial use.
