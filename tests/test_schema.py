from pathlib import Path
import sqlite3

from ibm1620_parts.model.repositories import initialize_database


def test_schema_creates_fresh_database(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    initialize_database(db_path)

    conn = sqlite3.connect(db_path)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert {"documents", "pages", "extraction_runs", "raw_part_candidates"}.issubset(tables)
