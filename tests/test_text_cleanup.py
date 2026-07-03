from ibm1620_parts.normalize.text_cleanup import normalize_multiline_text, normalize_whitespace


def test_normalize_whitespace_preserves_ascii_text() -> None:
    assert normalize_whitespace("IBM   1620 PARTS\tCATALOG") == "IBM 1620 PARTS CATALOG"


def test_normalize_multiline_text_preserves_lines() -> None:
    assert normalize_multiline_text("A   B\nC\tD") == "A B\nC D"
