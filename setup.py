from setuptools import setup

setup(
    name="logi_battery_tray",
    version="0.1.0",
    description="Tray app to monitor Logitech mouse battery level using Options+ data",
    author="Fabio Romariz",
    py_modules=["battery", "icon", "main", "optionspluscheck", "config", "settings"],
    install_requires=[
        "pystray==0.19.5",
        "Pillow==10.2.0",
        "psutil==5.9.8",
        "python-dotenv==1.0.1",
    ],
    entry_points={"console_scripts": ["logi-battery-tray=main:main"]},
    python_requires=">=3.7",
)
