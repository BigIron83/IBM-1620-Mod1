from __future__ import annotations

import csv
from pathlib import Path

from ibm1620_parts.model.repositories import fetch_raw_part_candidates, get_connection

RAW_PART_COLUMNS = [
    "source_document",
    "source_page",
    "figure_number",
    "item_number",
    "ibm_part_number",
    "description",
    "quantity",
    "confidence",
    "review_status",
    "raw_text",
    "notes",
]


def export_raw_parts_csv(db_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as conn:
        rows = fetch_raw_part_candidates(conn)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_PART_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in RAW_PART_COLUMNS})
