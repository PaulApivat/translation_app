"""Main desktop UI window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from export import conversion_capabilities, resolve_docx_body_font
from extract import pdf_page_count

from .settings_dialog import SettingsDialog
from .worker import PipelineWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF → DOCX Translator")
        self.resize(900, 640)

        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

        self._input_pdf = QLineEdit()
        self._output_docx = QLineEdit()
        self._output_docx.setPlaceholderText("Choose output .docx path")

        self._lang_combo = QComboBox()
        self._lang_combo.addItem("Thai → English (TH → EN)", ("TH", "EN"))
        self._lang_combo.addItem("English → Thai (EN → TH)", ("EN", "TH"))

        self._body_font = QLineEdit()
        self._body_font.setPlaceholderText("Optional DOCX body font (blank = profile default)")

        self._column_mode_combos: dict[int, QComboBox] = {}
        self._column_inner = QWidget()
        self._column_layout = QVBoxLayout(self._column_inner)
        self._column_layout.addWidget(
            QLabel("Select a PDF to set per-page column mode (optional).")
        )
        self._column_scroll = QScrollArea()
        self._column_scroll.setWidgetResizable(True)
        self._column_scroll.setWidget(self._column_inner)
        self._column_scroll.setMaximumHeight(200)

        column_group = QGroupBox("Per-page columns (layout override)")
        column_group_layout = QVBoxLayout(column_group)
        column_group_layout.addWidget(self._column_scroll)

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
        form.addWidget(QLabel("Language pair"), 2, 0)
        form.addWidget(self._lang_combo, 2, 1, 1, 2)
        form.addWidget(QLabel("DOCX body font"), 3, 0)
        form.addWidget(self._body_font, 3, 1, 1, 2)
        form.addWidget(column_group, 4, 0, 1, 3)
        form.addWidget(self._also_pdf, 5, 0, 1, 3)

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

    def _snapshot_column_modes(self) -> dict[int, str]:
        out: dict[int, str] = {}
        for page_num, combo in self._column_mode_combos.items():
            data = combo.currentData()
            out[page_num] = str(data) if data is not None else "auto"
        return out

    def _rebuild_column_overrides(self, page_count: int) -> None:
        old = self._snapshot_column_modes()
        while self._column_layout.count():
            item = self._column_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._column_mode_combos.clear()
        if page_count <= 0:
            self._column_layout.addWidget(
                QLabel("Select a PDF to configure per-page column overrides.")
            )
            return
        for p in range(1, page_count + 1):
            mode = old.get(p, "auto")
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(f"Page {p}"))
            cb = QComboBox()
            cb.addItem("Auto", "auto")
            cb.addItem("1 column", "single")
            cb.addItem("2 columns", "two")
            mode_to_idx = {"auto": 0, "single": 1, "two": 2}
            cb.setCurrentIndex(mode_to_idx.get(mode, 0))
            row.addWidget(cb)
            row.addStretch(1)
            self._column_layout.addWidget(row_widget)
            self._column_mode_combos[p] = cb

    def _pick_input_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Input PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        self._input_pdf.setText(path)
        if not self._output_docx.text():
            stem = Path(path).with_suffix("")
            self._output_docx.setText(str(stem) + "_translated.docx")
        try:
            n = pdf_page_count(path)
            self._rebuild_column_overrides(n)
        except OSError as exc:
            self._append_log(f"Could not read PDF page count: {exc}")
            self._rebuild_column_overrides(0)

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

        pair = self._lang_combo.currentData()
        if not isinstance(pair, tuple) or len(pair) != 2:
            source_lang, target_lang = "TH", "EN"
        else:
            source_lang, target_lang = str(pair[0]), str(pair[1])

        font_override = self._body_font.text().strip() or None
        docx_default_font = resolve_docx_body_font(
            source_lang, target_lang, user_override=font_override
        )
        page_modes = self._snapshot_column_modes()

        self._set_running(True)
        self._progress.setValue(0)
        self._log.clear()
        self._append_log("Pipeline started.")

        self._thread = QThread()
        self._worker = PipelineWorker(
            input_pdf=input_pdf,
            output_docx=output_docx,
            source_lang=source_lang,
            target_lang=target_lang,
            also_export_pdf=self._also_pdf.isChecked(),
            page_column_modes=page_modes if page_modes else None,
            docx_default_font=docx_default_font,
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
        self._lang_combo.setEnabled(not running)
        self._body_font.setEnabled(not running)
        for cb in self._column_mode_combos.values():
            cb.setEnabled(not running)

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
