import subprocess
import shutil
from pathlib import Path
import argparse
import re

# --- Argument Parsing ---
parser = argparse.ArgumentParser()
parser.add_argument("--release", action="store_true", help="Build and package release")
args, _ = parser.parse_known_args()  # Avoid crashing in environments like Jupyter

# --- Constants ---
PROJECT_DIR = Path(__file__).resolve().parent
PY_SRC_DIR = PROJECT_DIR
MSIX_ROOT_DIR = PROJECT_DIR.parent / "logi-battery-tray-msix"
MSIX_APPFILES_DIR = MSIX_ROOT_DIR / "AppFiles"
ASSETS_SRC_FILE = PROJECT_DIR / "logo.png"
ASSETS_DST_DIR = MSIX_APPFILES_DIR / "Assets"
APPX_MANIFEST_TEMPLATE = MSIX_APPFILES_DIR / "AppxManifest.xml"
APPX_MANIFEST_TARGET = MSIX_APPFILES_DIR / "AppxManifest.xml"
BUILD_NAME = "logi-battery-tray"
DIST_EXE = PY_SRC_DIR / "dist" / f"{BUILD_NAME}.exe"
VERSION_FILE = PROJECT_DIR / "version.txt"
MSIX_OUTPUT = PROJECT_DIR.parent / "logi-battery-tray.msix"


# --- Version Handling ---
def read_and_bump_version():
    if not VERSION_FILE.exists():
        return "1.0.0.0"
    version = VERSION_FILE.read_text().strip()
    parts = version.split(".")
    if len(parts) != 4:
        raise ValueError("Invalid version format, expected Major.Minor.Build.Revision")
    parts[2] = str(int(parts[2]) + 1)
    new_version = ".".join(parts)
    VERSION_FILE.write_text(new_version + "\n")
    print(f"Bumped version: {version} to {new_version}")
    return new_version


# --- PyInstaller Build ---
def run_pyinstaller():
    print("Building with pyinstaller...")
    main_script_path = PY_SRC_DIR / "main.py"
    subprocess.run(
        [
            "pyinstaller",
            "--noconsole",
            "--onefile",
            f"--name={BUILD_NAME}",
            str(main_script_path),
        ],
        check=True,
    )


# --- Copy Executable to MSIX folder ---
def copy_to_msix_folder():
    if not DIST_EXE.exists():
        raise FileNotFoundError(f"Built executable not found: {DIST_EXE}")
    MSIX_APPFILES_DIR.mkdir(parents=True, exist_ok=True)
    target_path = MSIX_APPFILES_DIR / f"{BUILD_NAME}.exe"
    shutil.copy2(DIST_EXE, target_path)
    print(f"Copied to MSIX AppFiles: {target_path}")


# --- Logo Asset ---
def copy_logo_to_assets():
    if not ASSETS_SRC_FILE.exists():
        raise FileNotFoundError(f"Logo not found at: {ASSETS_SRC_FILE}")
    ASSETS_DST_DIR.mkdir(parents=True, exist_ok=True)
    target_path = ASSETS_DST_DIR / "logo.png"
    shutil.copy2(ASSETS_SRC_FILE, target_path)
    print(f"Copied logo to MSIX Assets: {target_path}")


# --- Manifest Version Injection ---
def update_manifest_version(version: str):
    print(f"Updating AppxManifest.xml to version {version}")
    path = APPX_MANIFEST_TEMPLATE

    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    text = path.read_text(encoding="utf-8")
    updated = re.sub(
        r'(<Identity[^>]+Version=")[^"]+"', lambda m: m.group(1) + version + '"', text
    )
    path.write_text(updated, encoding="utf-8")
    print("Manifest version updated.")


# --- MakeAppx Package ---
def run_makeappx():
    print("Creating MSIX package...")

    makeappx_path = shutil.which("makeappx")

    if not makeappx_path:
        sdk_base = Path("C:/Program Files (x86)/Windows Kits/10/bin")
        preferred_versions = [
            "10.0.26100.0",
            "10.0.22621.0",
            "10.0.19041.0",
            "10.0.18362.0",
        ]

        # First: try preferred SDKs in order
        if sdk_base.exists():
            for ver in preferred_versions:
                candidate = sdk_base / ver / "x64" / "makeappx.exe"
                if candidate.exists():
                    makeappx_path = str(candidate)
                    print(f"Using makeappx.exe from: {makeappx_path}")
                    break

        # Fallback: use first found in any SDK version
        if not makeappx_path:
            for subdir in sdk_base.iterdir():
                possible = subdir / "x64" / "makeappx.exe"
                if possible.exists():
                    makeappx_path = str(possible)
                    print(f"Found fallback makeappx.exe at: {makeappx_path}")
                    break

    if not makeappx_path:
        raise FileNotFoundError("makeappx.exe not found.")

    subprocess.run(
        [
            makeappx_path,
            "pack",
            "/d",
            str(MSIX_APPFILES_DIR),
            "/p",
            str(MSIX_OUTPUT),
            "/l",
        ],
        check=True,
    )

    print(f"MSIX created: {MSIX_OUTPUT}")


# --- Main ---
if __name__ == "__main__":
    VERSION = read_and_bump_version() if args.release else "1.0.0.0"
    run_pyinstaller()
    copy_to_msix_folder()
    copy_logo_to_assets()
    update_manifest_version(VERSION)
    if args.release:
        run_makeappx()
