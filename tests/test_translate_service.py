from __future__ import annotations

from dataclasses import dataclass

from ir import Cell, Document, Page, ParagraphBlock, Run, TableBlock
from translate.base import RateLimitError, TranslationRequest
from translate.segmenter import merge_translations, segment_document
from translate.service import TranslationProgress, TranslationService


def _sample_document() -> Document:
    para = ParagraphBlock(runs=[Run(text="สวัสดี"), Run(text=" โลก")])
    table = TableBlock(rows=[[Cell(runs=[Run(text="ขอบคุณ")])]])
    return Document(pages=[Page(page_number=1, blocks=[para, table])])


def test_segmenter_stable_ids_and_style_boundary_granularity() -> None:
    doc = _sample_document()
    segments_first = segment_document(doc)
    segments_second = segment_document(doc)

    assert [s.id for s in segments_first] == [s.id for s in segments_second]
    # paragraph has two runs -> two style-boundary segments
    para_ids = [s.id for s in segments_first if s.cell_row is None]
    assert len(para_ids) == 2


def test_merge_translations_by_segment_id() -> None:
    doc = _sample_document()
    segs = segment_document(doc)
    translated = {segs[0].id: "Hello", segs[1].id: " world", segs[2].id: "Thank you"}

    merge_translations(doc, translated)

    para = doc.pages[0].blocks[0]
    table = doc.pages[0].blocks[1]
    assert isinstance(para, ParagraphBlock)
    assert isinstance(table, TableBlock)
    assert para.runs[0].text == "Hello"
    assert para.runs[1].text == " world"
    assert table.rows[0][0].runs[0].text == "Thank you"


@dataclass
class _MockProvider:
    calls: int = 0

    def translate_batch(self, request: TranslationRequest) -> list[str | None]:
        self.calls += 1
        return [f"EN:{txt}" for txt in request.texts]


def test_service_batches_and_translates_document() -> None:
    provider = _MockProvider()
    service = TranslationService(provider, batch_size=2, max_retries=0, requests_per_second=0)
    doc = _sample_document()

    out = service.translate_document(doc, source_lang="TH", target_lang="EN")
    para = out.pages[0].blocks[0]
    assert isinstance(para, ParagraphBlock)
    assert para.runs[0].text.startswith("EN:")
    assert provider.calls == 2  # 3 segments batched by 2


class _FlakyProvider:
    def __init__(self) -> None:
        self.calls = 0

    def translate_batch(self, request: TranslationRequest) -> list[str | None]:
        self.calls += 1
        if self.calls == 1:
            raise RateLimitError("limited")
        if self.calls == 2:
            return [None for _ in request.texts]
        return [f"OK:{t}" for t in request.texts]


def test_service_retries_rate_limit_and_partial_failures() -> None:
    provider = _FlakyProvider()
    service = TranslationService(
        provider,
        batch_size=10,
        max_retries=4,
        base_backoff_s=0,
        requests_per_second=0,
    )
    doc = _sample_document()

    out = service.translate_document(doc, source_lang="TH", target_lang="EN")
    para = out.pages[0].blocks[0]
    table = out.pages[0].blocks[1]
    assert isinstance(para, ParagraphBlock)
    assert isinstance(table, TableBlock)
    assert para.runs[0].text.startswith("OK:")
    assert table.rows[0][0].runs[0].text.startswith("OK:")
    assert provider.calls >= 3


class _CancelAfterFirstCallProvider:
    def translate_batch(self, request: TranslationRequest) -> list[str | None]:
        return [f"EN:{txt}" for txt in request.texts]


def test_service_honors_cancellation_between_batches() -> None:
    provider = _CancelAfterFirstCallProvider()
    service = TranslationService(provider, batch_size=1, max_retries=0, requests_per_second=0)
    doc = _sample_document()
    calls = {"n": 0}

    def should_cancel() -> bool:
        calls["n"] += 1
        return calls["n"] > 2

    out = service.translate_document(
        doc,
        source_lang="TH",
        target_lang="EN",
        should_cancel=should_cancel,
    )
    para = out.pages[0].blocks[0]
    assert isinstance(para, ParagraphBlock)
    assert para.runs[0].text.startswith("EN:")
    assert para.runs[1].text == " โลก"


def test_service_emits_progress_callback() -> None:
    provider = _MockProvider()
    service = TranslationService(provider, batch_size=2, max_retries=0, requests_per_second=0)
    updates: list[TranslationProgress] = []
    doc = _sample_document()

    service.translate_document(
        doc,
        source_lang="TH",
        target_lang="EN",
        progress_callback=updates.append,
    )

    assert updates
    last = updates[-1]
    assert last.translated_segments == last.total_segments == 3
    assert last.translated_chars == last.total_chars
