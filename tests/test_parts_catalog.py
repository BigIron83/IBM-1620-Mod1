from ibm1620_parts.extractors.parts_catalog import extract_candidate_rows


def test_parts_extractor_does_not_crash_on_empty_or_noisy_text() -> None:
    assert extract_candidate_rows("", "doc.pdf", 1) == []
    noisy = "@@@@ #### random noise 1620-51 no usable table"
    assert isinstance(extract_candidate_rows(noisy, "doc.pdf", 2), list)


def test_parts_extractor_prefers_rows_with_part_number_and_description() -> None:
    text = """A 587320 BLOCK ASM - 40 POS
1 21636 SCREW - RETAINER
2 287310 RETAINER - BLOCK"""
    rows = extract_candidate_rows(text, "doc.pdf", 3, "catalog_figure")

    assert [row["ibm_part_number"] for row in rows] == ["587320", "21636", "287310"]
    assert rows[0]["item_number"] == "A"
    assert rows[1]["item_number"] == "1"
    assert rows[2]["item_number"] == "2"
    assert rows[0]["description"] == "BLOCK ASM - 40 POS"
    assert rows[1]["description"] == "SCREW - RETAINER"
    assert rows[2]["description"] == "RETAINER - BLOCK"
    assert all(row["confidence"] >= 0.82 for row in rows)


def test_item_number_capture_supports_b1_and_two_digit_values() -> None:
    text = """B1 587319 CONNECTOR ASM - 40 POS
15 205329 JUMPER - BRASS"""
    rows = extract_candidate_rows(text, "doc.pdf", 5, "catalog_figure")

    assert rows[0]["item_number"] == "B1"
    assert rows[0]["ibm_part_number"] == "587319"
    assert rows[1]["item_number"] == "15"
    assert rows[1]["ibm_part_number"] == "205329"


def test_ampersand_description_is_preserved() -> None:
    rows = extract_candidate_rows("587312 SCREW & HOUSING ASM", "doc.pdf", 6, "catalog_figure")
    assert rows[0]["description"] == "SCREW & HOUSING ASM"


def test_description_ocr_cleanup_preserves_raw_text() -> None:
    rows = extract_candidate_rows("587376 CLAMP - CABlE\n595989 COVER - BlOCK", "doc.pdf", 7, "catalog_figure")
    assert rows[0]["description"] == "CLAMP - CABLE"
    assert rows[0]["raw_text"] == "587376 CLAMP - CABlE"
    assert rows[1]["description"] == "COVER - BLOCK"
    assert rows[1]["raw_text"] == "595989 COVER - BlOCK"


def test_no_duplicate_standalone_row_when_described_row_exists() -> None:
    rows = extract_candidate_rows("587320 BLOCK ASM - 40 POS\n587320", "doc.pdf", 8, "catalog_figure")
    assert len(rows) == 1
    assert rows[0]["ibm_part_number"] == "587320"
    assert rows[0]["description"] == "BLOCK ASM - 40 POS"


def test_figure_labels_are_not_treated_as_part_numbers() -> None:
    assert extract_candidate_rows("1620-51", "doc.pdf", 4, "catalog_figure") == []
