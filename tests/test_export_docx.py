from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from export import DocxExporter
from ir import Cell, Document, Page, ParagraphBlock, Run, TableBlock


def _doc_xml(docx_path: Path) -> str:
    with ZipFile(docx_path) as zf:
        return zf.read("word/document.xml").decode("utf-8")


def test_docx_contains_paragraph_runs_with_styles(tmp_path: Path) -> None:
    doc = Document(
        pages=[
            Page(
                page_number=1,
                blocks=[
                    ParagraphBlock(
                        runs=[
                            Run(
                                text="Hello",
                                bold=True,
                                font_name="TimesNewRomanPSMT",
                                size_pt=12.0,
                            ),
                            Run(text=" world", italic=True, font_name="Helvetica", size_pt=11.0),
                        ]
                    )
                ],
            )
        ]
    )
    out = tmp_path / "styled.docx"
    DocxExporter().export(doc, out)
    xml = _doc_xml(out)

    assert "<w:t>Hello</w:t>" in xml
    assert '<w:t xml:space="preserve"> world</w:t>' in xml
    assert "<w:b/>" in xml
    assert "<w:i/>" in xml
    # 12pt => 24 half-points, 11pt => 22 half-points
    assert 'w:val="24"' in xml
    assert 'w:val="22"' in xml


def test_docx_contains_table_structure_and_cell_text(tmp_path: Path) -> None:
    table = TableBlock(
        rows=[
            [Cell(runs=[Run(text="A1")]), Cell(runs=[Run(text="B1")])],
            [Cell(runs=[Run(text="A2")]), Cell(runs=[Run(text="B2")])],
        ]
    )
    doc = Document(pages=[Page(page_number=1, blocks=[table])])
    out = tmp_path / "table.docx"
    DocxExporter().export(doc, out)
    xml = _doc_xml(out)

    assert "<w:tbl>" in xml
    assert "<w:t>A1</w:t>" in xml
    assert "<w:t>B2</w:t>" in xml
    assert 'w:val="TableGrid"' in xml


def test_docx_page_break_written_between_pages(tmp_path: Path) -> None:
    doc = Document(
        pages=[
            Page(page_number=1, blocks=[ParagraphBlock(runs=[Run(text="Page1")])]),
            Page(page_number=2, blocks=[ParagraphBlock(runs=[Run(text="Page2")])]),
        ]
    )
    out = tmp_path / "pagebreak.docx"
    DocxExporter(include_page_breaks=True).export(doc, out)
    xml = _doc_xml(out)

    assert xml.count("<w:sectPr") >= 2
    assert "<w:t>Page1</w:t>" in xml
    assert "<w:t>Page2</w:t>" in xml


def test_font_mapping_fallback_defaults_to_calibri(tmp_path: Path) -> None:
    doc = Document(
        pages=[
            Page(
                page_number=1,
                blocks=[ParagraphBlock(runs=[Run(text="X", font_name="UnknownFont")])],
            )
        ]
    )
    out = tmp_path / "font.docx"
    DocxExporter().export(doc, out)
    xml = _doc_xml(out)

    assert 'w:ascii="Calibri"' in xml


def test_landscape_orientation_written_for_landscape_page(tmp_path: Path) -> None:
    doc = Document(
        pages=[
            Page(
                page_number=1,
                width_pt=792.0,
                height_pt=612.0,
                blocks=[ParagraphBlock(runs=[Run(text="Landscape")])],
            )
        ]
    )
    out = tmp_path / "landscape.docx"
    DocxExporter().export(doc, out)
    xml = _doc_xml(out)

    assert 'w:orient="landscape"' in xml
    assert 'w:w="15840"' in xml
    assert 'w:h="12240"' in xml
