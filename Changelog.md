# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.25.0] - 2024-04-30
### Added
- Initial release of **Logi Battery Tray**
- Reads Logitech MX Master 3S battery level from Logi Options+ SQLite settings DB
- Displays current battery level as a tray icon with refresh interval
- Auto-launches Logi Options+ if not running
- Supports configurable Options+ path and interval via UI
- Persisted config via `config.json`
- MSIX packaging with auto-incremented versioning
- Startup task registration for Windows
- Auto-generated `.msix` packages using `makeappx.exe`

---

## [Unreleased]
- 🔧 Planned: Notification on critical battery level
- 💡 Planned: Option to auto-close Options+ after querying
- 📦 Planned: CI workflow for automatic packaging and release
