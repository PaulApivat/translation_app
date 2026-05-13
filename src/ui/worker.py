"""Background worker for extract -> translate -> export pipeline."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from export import PdfConversionError, convert_docx_to_pdf, export_docx
from extract import extract_document
from translate import DeepLProvider, TranslationProgress, TranslationService


class PipelineWorker(QObject):
    progress_changed = Signal(int)
    log_message = Signal(str)
    finished = Signal(str, str)  # docx_path, pdf_path_or_empty
    failed = Signal(str)
    cancelled = Signal()

    def __init__(
        self,
        *,
        input_pdf: str,
        output_docx: str,
        source_lang: str = "TH",
        target_lang: str = "EN",
        also_export_pdf: bool = False,
        page_column_modes: dict[int, str] | None = None,
        docx_default_font: str | None = None,
    ) -> None:
        super().__init__()
        self._input_pdf = input_pdf
        self._output_docx = output_docx
        self._source_lang = source_lang
        self._target_lang = target_lang
        self._also_export_pdf = also_export_pdf
        self._page_column_modes = page_column_modes
        self._docx_default_font = docx_default_font
        self._cancel_requested = False

    @Slot()
    def run(self) -> None:
        try:
            self.progress_changed.emit(1)
            self.log_message.emit("Starting extraction...")
            document = extract_document(
                self._input_pdf,
                page_column_modes=self._page_column_modes,
            )
            if self._is_cancelled():
                return
            self.progress_changed.emit(20)
            self.log_message.emit(f"Extracted {len(document.pages)} page(s).")
            for notice in document.layout_warnings:
                self.log_message.emit(f"Layout notice: {notice}")

            self.log_message.emit(
                f"Starting translation ({self._source_lang} -> {self._target_lang})..."
            )
            provider = DeepLProvider()
            service = TranslationService(provider)
            document = service.translate_document(
                document,
                source_lang=self._source_lang,
                target_lang=self._target_lang,
                progress_callback=self._on_translate_progress,
                should_cancel=self._is_cancelled,
            )
            if self._is_cancelled():
                return
            self.progress_changed.emit(85)
            self.log_message.emit("Translation stage finished.")

            self.log_message.emit(f"Exporting DOCX: {self._output_docx}")
            export_docx(
                document,
                self._output_docx,
                include_page_breaks=True,
                default_font=self._docx_default_font,
            )
            if self._is_cancelled():
                return
            self.progress_changed.emit(92)

            pdf_path = ""
            if self._also_export_pdf:
                out_pdf = str(Path(self._output_docx).with_suffix(".pdf"))
                self.log_message.emit(f"Converting DOCX -> PDF: {out_pdf}")
                convert_docx_to_pdf(self._output_docx, out_pdf)
                pdf_path = out_pdf
                self.progress_changed.emit(98)

            self.progress_changed.emit(100)
            self.log_message.emit("Pipeline complete.")
            self.finished.emit(self._output_docx, pdf_path)
        except PdfConversionError as exc:
            self.failed.emit(
                f"PDF conversion failed: {exc}\nDOCX was still produced at: {self._output_docx}"
            )
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    def request_cancel(self) -> None:
        self._cancel_requested = True
        self.log_message.emit("Cancellation requested...")

    def _is_cancelled(self) -> bool:
        if self._cancel_requested:
            self.cancelled.emit()
            return True
        return False

    def _on_translate_progress(self, progress: TranslationProgress) -> None:
        # Map translate phase into progress bar range [20, 85].
        pct = 0.0 if progress.total_chars == 0 else progress.translated_chars / progress.total_chars
        bar = 20 + int(65 * pct)
        self.progress_changed.emit(max(20, min(85, bar)))
        self.log_message.emit(
            (
                f"Translated {progress.translated_chars}/{progress.total_chars} chars "
                f"({progress.translated_segments}/{progress.total_segments} segments)"
            )
        )
