from ir import (
    Cell,
    Document,
    Page,
    ParagraphBlock,
    Run,
    TableBlock,
    document_from_json,
    document_to_json,
)


def test_ir_dataclass_construction() -> None:
    heading = Run(text="Hello", bold=True, font_name="TH Sarabun New", size_pt=14.0)
    para = ParagraphBlock(runs=[heading, Run(text=" world")])
    cell = Cell(runs=[Run(text="Amount"), Run(text=" 100")])
    table = TableBlock(rows=[[cell]])
    page = Page(page_number=1, blocks=[para, table])
    document = Document(pages=[page])

    assert document.pages[0].page_number == 1
    assert isinstance(document.pages[0].blocks[0], ParagraphBlock)
    assert isinstance(document.pages[0].blocks[1], TableBlock)
    assert document.pages[0].blocks[0].runs[0].bold is True


def test_block_and_cell_ids_are_stable_and_unique() -> None:
    para = ParagraphBlock(runs=[Run(text="One")])
    table = TableBlock(rows=[[Cell(runs=[Run(text="Two")])]])

    original_para_id = para.id
    original_table_id = table.id
    original_cell_id = table.rows[0][0].id

    assert original_para_id != original_table_id
    assert original_para_id == para.id
    assert original_table_id == table.id
    assert original_cell_id == table.rows[0][0].id


def test_document_json_round_trip_preserves_structure_and_ids() -> None:
    para = ParagraphBlock(runs=[Run(text="Thai text"), Run(text="English text", italic=True)])
    cell_left = Cell(runs=[Run(text="A1")])
    cell_right = Cell(runs=[Run(text="B1", bold=True)])
    table = TableBlock(rows=[[cell_left, cell_right]])
    source = Document(pages=[Page(page_number=1, blocks=[para, table])])

    payload = document_to_json(source)
    restored = document_from_json(payload)

    assert len(restored.pages) == 1
    assert len(restored.pages[0].blocks) == 2
    restored_para = restored.pages[0].blocks[0]
    restored_table = restored.pages[0].blocks[1]

    assert isinstance(restored_para, ParagraphBlock)
    assert isinstance(restored_table, TableBlock)
    assert restored_para.id == para.id
    assert restored_table.id == table.id
    assert restored_table.rows[0][0].id == cell_left.id
    assert restored_para.runs[1].italic is True
