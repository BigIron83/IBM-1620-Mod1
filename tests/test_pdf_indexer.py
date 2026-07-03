from pathlib import Path

import fitz

from ibm1620_parts.ingest.pdf_indexer import classify_page_text, compute_sha256, ingest_pdf
from ibm1620_parts.model.repositories import get_connection


def test_sha256_hashing_is_stable(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("abc123", encoding="utf-8")
    assert compute_sha256(file_path) == compute_sha256(file_path)


def test_page_classifier_sample_strings() -> None:
    assert classify_page_text("IBM 1620 CENTRAL PROCESSING UNIT") == "manual_text"
    assert classify_page_text("PARTS CATALOG INDEX") == "catalog_index"
    assert classify_page_text("1620-51 123456 234567 SOME PART") == "catalog_figure"
    assert classify_page_text("RESISTORS") == "resistor_chart"
    assert classify_page_text("CAPACITORS") == "capacitor_chart"
    assert classify_page_text("random text") == "unknown"


def test_ingest_pdf_stores_document_and_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PARTS CATALOG")
    doc.save(pdf_path)
    doc.close()

    db_path = tmp_path / "test.db"
    ingest_pdf(db_path, pdf_path, render_pages=False)

    with get_connection(db_path) as conn:
        document_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        page_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]

    assert document_count == 1
    assert page_count == 1
