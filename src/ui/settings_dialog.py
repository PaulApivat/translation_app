"""Settings dialog for API credentials."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from .settings_store import read_deepl_api_key, write_deepl_api_key


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self._api_key_input.setText(read_deepl_api_key())

        form = QFormLayout()
        form.addRow("DeepL API Key", self._api_key_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _save(self) -> None:
        write_deepl_api_key(self._api_key_input.text().strip())
        QMessageBox.information(self, "Saved", "Settings saved to .env")
        self.accept()
