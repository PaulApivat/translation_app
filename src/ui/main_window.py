"""Main desktop UI window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from export import conversion_capabilities

from .settings_dialog import SettingsDialog
from .worker import PipelineWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Thai PDF -> English DOCX Translator")
        self.resize(840, 560)

        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

        self._input_pdf = QLineEdit()
        self._output_docx = QLineEdit()
        self._output_docx.setPlaceholderText("Choose output .docx path")
        self._lang_label = QLabel("Language Pair: TH -> EN (fixed in v1)")
        self._also_pdf = QCheckBox("Also export PDF")
        self._progress = QProgressBar()
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)

        self._btn_pick_input = QPushButton("Browse PDF")
        self._btn_pick_output = QPushButton("Browse DOCX")
        self._btn_settings = QPushButton("Settings")
        self._btn_start = QPushButton("Translate")
        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setEnabled(False)

        self._btn_pick_input.clicked.connect(self._pick_input_pdf)
        self._btn_pick_output.clicked.connect(self._pick_output_docx)
        self._btn_settings.clicked.connect(self._open_settings)
        self._btn_start.clicked.connect(self._start_pipeline)
        self._btn_cancel.clicked.connect(self._cancel_pipeline)
        self._also_pdf.toggled.connect(self._on_pdf_toggle)

        form = QGridLayout()
        form.addWidget(QLabel("Input PDF"), 0, 0)
        form.addWidget(self._input_pdf, 0, 1)
        form.addWidget(self._btn_pick_input, 0, 2)
        form.addWidget(QLabel("Output DOCX"), 1, 0)
        form.addWidget(self._output_docx, 1, 1)
        form.addWidget(self._btn_pick_output, 1, 2)
        form.addWidget(self._lang_label, 2, 0, 1, 3)
        form.addWidget(self._also_pdf, 3, 0, 1, 3)

        buttons = QHBoxLayout()
        buttons.addWidget(self._btn_settings)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_start)
        buttons.addWidget(self._btn_cancel)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addLayout(buttons)
        root.addWidget(self._progress)
        root.addWidget(QLabel("Log"))
        root.addWidget(self._log)

        w = QWidget()
        w.setLayout(root)
        self.setCentralWidget(w)
        self._on_pdf_toggle(self._also_pdf.isChecked())

    def _pick_input_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Input PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        self._input_pdf.setText(path)
        if not self._output_docx.text():
            stem = Path(path).with_suffix("")
            self._output_docx.setText(str(stem) + "_translated.docx")

    def _pick_output_docx(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select Output DOCX", "", "DOCX Files (*.docx)")
        if not path:
            return
        if not path.lower().endswith(".docx"):
            path += ".docx"
        self._output_docx.setText(path)

    def _open_settings(self) -> None:
        SettingsDialog(self).exec()

    def _start_pipeline(self) -> None:
        input_pdf = self._input_pdf.text().strip()
        output_docx = self._output_docx.text().strip()
        if not input_pdf:
            QMessageBox.warning(self, "Missing input", "Please select an input PDF.")
            return
        if not output_docx:
            QMessageBox.warning(self, "Missing output", "Please select an output DOCX path.")
            return
        if not Path(input_pdf).is_file():
            QMessageBox.warning(self, "Missing file", f"Input PDF not found:\n{input_pdf}")
            return

        self._set_running(True)
        self._progress.setValue(0)
        self._log.clear()
        self._append_log("Pipeline started.")

        self._thread = QThread()
        self._worker = PipelineWorker(
            input_pdf=input_pdf,
            output_docx=output_docx,
            source_lang="TH",
            target_lang="EN",
            also_export_pdf=self._also_pdf.isChecked(),
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self._progress.setValue)
        self._worker.log_message.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.cancelled.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()

    def _cancel_pipeline(self) -> None:
        if self._worker is not None:
            self._worker.request_cancel()
        self._btn_cancel.setEnabled(False)

    def _on_finished(self, docx_path: str, pdf_path: str) -> None:
        if pdf_path:
            self._append_log(f"Finished. DOCX: {docx_path}\nPDF: {pdf_path}")
        else:
            self._append_log(f"Finished. DOCX: {docx_path}")
        QMessageBox.information(self, "Done", "Translation pipeline completed.")

    def _on_failed(self, message: str) -> None:
        self._append_log(f"ERROR: {message}")
        QMessageBox.critical(self, "Pipeline failed", message)

    def _on_cancelled(self) -> None:
        self._append_log("Pipeline cancelled.")
        QMessageBox.information(self, "Cancelled", "Pipeline cancelled.")

    def _cleanup_thread(self) -> None:
        self._set_running(False)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None

    def _set_running(self, running: bool) -> None:
        self._btn_start.setEnabled(not running)
        self._btn_cancel.setEnabled(running)
        self._btn_pick_input.setEnabled(not running)
        self._btn_pick_output.setEnabled(not running)
        self._btn_settings.setEnabled(not running)
        self._also_pdf.setEnabled(not running)

    def _append_log(self, text: str) -> None:
        self._log.appendPlainText(text)

    def _on_pdf_toggle(self, checked: bool) -> None:
        if not checked:
            return
        available, reason = conversion_capabilities()
        self._append_log(f"PDF conversion check: {reason}")
        if not available:
            QMessageBox.warning(
                self,
                "PDF conversion unavailable",
                (
                    "PDF conversion dependency not detected.\n"
                    "You can still run DOCX-only output.\n\n"
                    f"Details: {reason}"
                ),
            )
