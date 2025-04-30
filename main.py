from icon import build_icon
from optionspluscheck import monitor_options_plus
from dotenv import load_dotenv
load_dotenv()


def main():
    monitor_options_plus()
    tray_icon = build_icon()
    tray_icon.run()

if __name__ == "__main__":
    main()
