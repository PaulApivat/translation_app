"""DOCX to PDF conversion helpers."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


class PdfConversionError(RuntimeError):
    """Raised when DOCX to PDF conversion cannot complete."""


def conversion_capabilities() -> tuple[bool, str]:
    """Return whether PDF conversion is available and a user-facing reason."""
    if _has_docx2pdf():
        if sys.platform == "darwin":
            return True, "docx2pdf available (requires Microsoft Word for conversion)."
        return True, "docx2pdf available."
    if shutil.which("soffice"):
        return True, "LibreOffice (soffice) available."
    return False, "Install docx2pdf (and Word on macOS) or LibreOffice (soffice)."


def convert_docx_to_pdf(docx_path: str | Path, pdf_path: str | Path) -> None:
    """Convert DOCX to PDF using docx2pdf, fallback to LibreOffice."""
    src = Path(docx_path)
    dst = Path(pdf_path)
    if not src.is_file():
        raise PdfConversionError(f"DOCX file not found: {src}")

    if _has_docx2pdf():
        try:
            from docx2pdf import convert as docx2pdf_convert

            docx2pdf_convert(str(src), str(dst))
            if not dst.exists():
                raise PdfConversionError("docx2pdf did not create the expected PDF.")
            return
        except Exception as exc:  # noqa: BLE001
            raise PdfConversionError(f"docx2pdf conversion failed: {exc}") from exc

    soffice = shutil.which("soffice")
    if soffice:
        outdir = dst.parent
        cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(src)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise PdfConversionError(
                f"LibreOffice conversion failed ({proc.returncode}): {proc.stderr.strip()}"
            )
        converted = outdir / f"{src.stem}.pdf"
        if not converted.exists():
            raise PdfConversionError("LibreOffice did not create the expected PDF.")
        if converted != dst:
            converted.replace(dst)
        return

    raise PdfConversionError(
        "No converter available. Install docx2pdf (+Word on macOS) or LibreOffice (soffice)."
    )


def _has_docx2pdf() -> bool:
    try:
        import docx2pdf  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True
