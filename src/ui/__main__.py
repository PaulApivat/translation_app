"""Run desktop UI."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

# PyInstaller runs this file as a script, not as part of package `ui`, so relative
# imports fail. When frozen, use absolute imports (pathex / bundle includes `ui`).
if getattr(sys, "frozen", False):
    from ui.main_window import MainWindow
else:
    from .main_window import MainWindow


def main() -> int:
    from translate.env_loader import load_first_dotenv

    load_first_dotenv()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
