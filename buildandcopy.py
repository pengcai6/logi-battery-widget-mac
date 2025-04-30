import subprocess
import shutil
import re
from pathlib import Path
import argparse
import os

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--release", action="store_true", help="Build and package release")
args = parser.parse_args()

# Paths
PROJECT_DIR = Path(__file__).resolve().parent
MSIX_ROOT_DIR = PROJECT_DIR.parent / "logi-battery-tray-msix"
MSIX_APPFILES_DIR = MSIX_ROOT_DIR / "AppFiles"
ASSETS_SRC_FILE = PROJECT_DIR / "logo.png"
ASSETS_DST_DIR = MSIX_APPFILES_DIR / "Assets"
MANIFEST_TEMPLATE = PROJECT_DIR / "AppxManifest.xml.template"
MANIFEST_TARGET = MSIX_APPFILES_DIR / "AppxManifest.xml"
VERSION_FILE = PROJECT_DIR / "version.txt"
DIST_EXE = PROJECT_DIR / "dist" / "logi-battery-tray.exe"
MSIX_OUTPUT = PROJECT_DIR.parent / "logi-battery-tray.msix"


# Version bumping
def read_and_bump_version():
    if not VERSION_FILE.exists():
        return "1.0.0.0"
    version = VERSION_FILE.read_text().strip()
    parts = version.split(".")
    parts[2] = str(int(parts[2]) + 1)
    new_version = ".".join(parts)
    VERSION_FILE.write_text(new_version + "\n")
    print(f"Bumped version: {version} -> {new_version}")
    return new_version


# PyInstaller


def run_pyinstaller():
    print("Building with pyinstaller...")
    subprocess.run(
        [
            "pyinstaller",
            "--noconsole",
            "--onefile",
            "--name=logi-battery-tray",
            "main.py",
        ],
        check=True,
    )


# Copy build output


def copy_to_msix_folder():
    if not DIST_EXE.exists():
        raise FileNotFoundError(f"Built executable not found: {DIST_EXE}")
    MSIX_APPFILES_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DIST_EXE, MSIX_APPFILES_DIR / "logi-battery-tray.exe")
    print(f"Copied to MSIX AppFiles: {MSIX_APPFILES_DIR / 'logi-battery-tray.exe'}")


# Copy logo


def copy_logo_to_assets():
    if not ASSETS_SRC_FILE.exists():
        raise FileNotFoundError(f"Logo not found: {ASSETS_SRC_FILE}")
    ASSETS_DST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS_SRC_FILE, ASSETS_DST_DIR / "logo.png")
    print(f"Copied logo to MSIX Assets: {ASSETS_DST_DIR / 'logo.png'}")


# Inject version into manifest


def update_manifest_version(version):
    path = MANIFEST_TEMPLATE
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    text = path.read_text(encoding="utf-8")
    updated = re.sub(
        r'(<Identity[^>]+Version=")[^"]+"',
        lambda m: f'{m.group(1)}{version}"',
        text,
    )
    MANIFEST_TARGET.write_text(updated, encoding="utf-8")
    print(f"Updated AppxManifest.xml to version {version}")


# MSIX Packaging


def run_makeappx():
    print("Creating MSIX package...")
    makeappx_path = shutil.which("makeappx")
    if not makeappx_path:
        sdk_base = Path("C:/Program Files (x86)/Windows Kits/10/bin")
        for subdir in sdk_base.glob("*/x64/makeappx.exe"):
            if subdir.exists():
                makeappx_path = str(subdir)
                break
    if not makeappx_path:
        raise FileNotFoundError("makeappx.exe not found")

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


# Main
if __name__ == "__main__":
    VERSION = read_and_bump_version() if args.release else "1.0.0.0"
    run_pyinstaller()
    copy_to_msix_folder()
    copy_logo_to_assets()
    update_manifest_version(VERSION)
    if args.release:
        run_makeappx()
