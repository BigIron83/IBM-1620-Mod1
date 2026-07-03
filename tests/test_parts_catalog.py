from ibm1620_parts.extractors.parts_catalog import extract_candidate_rows


def test_parts_extractor_does_not_crash_on_empty_or_noisy_text() -> None:
    assert extract_candidate_rows("", "doc.pdf", 1) == []
    noisy = "@@@@ #### random noise 1620-51 no usable table"
    assert isinstance(extract_candidate_rows(noisy, "doc.pdf", 2), list)
