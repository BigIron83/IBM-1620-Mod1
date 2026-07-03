import csv

from ibm1620_parts.export.csv_exporter import RAW_PART_COLUMNS, export_raw_parts_csv
from ibm1620_parts.model.repositories import get_connection, initialize_database


def test_csv_exporter_writes_expected_columns(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    initialize_database(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO raw_part_candidates (
                source_document, source_page, figure_number, item_number, ibm_part_number,
                description, quantity, raw_text, confidence, review_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("doc.pdf", 1, "1620-1", "1", "123456", "PART", None, "raw", 0.8, "needs_review", None),
        )
        conn.commit()

    out_path = tmp_path / "out.csv"
    export_raw_parts_csv(db_path, out_path)

    with out_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == RAW_PART_COLUMNS
