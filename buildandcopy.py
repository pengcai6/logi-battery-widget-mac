import subprocess
from pathlib import Path
import argparse
import hashlib

parser = argparse.ArgumentParser()
parser.add_argument("--release", action="store_true", help="Build release")
args = parser.parse_args()

# --- Constants ---
PROJECT_DIR = Path(__file__).resolve().parent
PY_SRC_DIR = PROJECT_DIR
BUILD_NAME = "logi-battery-tray"
DIST_EXE = PY_SRC_DIR / "dist" / f"{BUILD_NAME}.exe"
VERSION_FILE = PROJECT_DIR / "version.txt"


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


def print_sha256(filepath: Path):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    print(f"SHA256: {sha256.hexdigest()}")


if __name__ == "__main__":
    VERSION = read_and_bump_version() if args.release else "1.0.0.0"
    run_pyinstaller()
    if DIST_EXE.exists():
        print(f"Built executable: {DIST_EXE}")
        print_sha256(DIST_EXE)
    else:
        print("Build failed: executable not found")
