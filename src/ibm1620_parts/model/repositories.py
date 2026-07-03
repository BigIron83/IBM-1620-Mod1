from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path: Path) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    schema_sql = schema_path.read_text(encoding="utf-8")
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def upsert_document(conn: sqlite3.Connection, document: dict) -> int:
    existing = conn.execute(
        "SELECT document_id FROM documents WHERE sha256 = ?",
        (document["sha256"],),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE documents
            SET filename = ?, title = ?, form_number = ?, source_path = ?, page_count = ?, notes = ?
            WHERE document_id = ?
            """,
            (
                document["filename"],
                document["title"],
                document["form_number"],
                document["source_path"],
                document["page_count"],
                document["notes"],
                existing["document_id"],
            ),
        )
        return int(existing["document_id"])

    cursor = conn.execute(
        """
        INSERT INTO documents (filename, title, form_number, source_path, sha256, page_count, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document["filename"],
            document["title"],
            document["form_number"],
            document["source_path"],
            document["sha256"],
            document["page_count"],
            document["notes"],
        ),
    )
    return int(cursor.lastrowid)


def replace_pages_for_document(conn: sqlite3.Connection, document_id: int, pages: list[dict]) -> None:
    conn.execute("DELETE FROM pages WHERE document_id = ?", (document_id,))
    conn.executemany(
        """
        INSERT INTO pages (
            document_id, pdf_page_number, printed_page_label, ocr_text,
            ocr_confidence, image_path, page_type, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                document_id,
                page["pdf_page_number"],
                page["printed_page_label"],
                page["ocr_text"],
                page["ocr_confidence"],
                page["image_path"],
                page["page_type"],
                page["notes"],
            )
            for page in pages
        ],
    )


def create_extraction_run(
    conn: sqlite3.Connection,
    *,
    source_document_id: int | None,
    extractor_name: str,
    status: str = "running",
    notes: str | None = None,
) -> int:
    started_at = datetime.now(UTC).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO extraction_runs (started_at, completed_at, status, source_document_id, extractor_name, notes)
        VALUES (?, NULL, ?, ?, ?, ?)
        """,
        (started_at, status, source_document_id, extractor_name, notes),
    )
    return int(cursor.lastrowid)


def complete_extraction_run(conn: sqlite3.Connection, run_id: int, status: str) -> None:
    completed_at = datetime.now(UTC).isoformat()
    conn.execute(
        "UPDATE extraction_runs SET completed_at = ?, status = ? WHERE extraction_run_id = ?",
        (completed_at, status, run_id),
    )


def get_document_by_filename(conn: sqlite3.Connection, filename: str):
    return conn.execute("SELECT * FROM documents WHERE filename = ?", (filename,)).fetchone()


def get_pages_for_document(conn: sqlite3.Connection, document_id: int):
    return conn.execute(
        "SELECT * FROM pages WHERE document_id = ? ORDER BY pdf_page_number",
        (document_id,),
    ).fetchall()


def insert_raw_part_candidates(conn: sqlite3.Connection, candidates: list[dict]) -> None:
    if not candidates:
        return
    conn.executemany(
        """
        INSERT INTO raw_part_candidates (
            extraction_run_id, document_id, page_id, source_document, source_page,
            figure_number, item_number, ibm_part_number, description, quantity,
            raw_text, confidence, review_status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                c["extraction_run_id"],
                c["document_id"],
                c["page_id"],
                c["source_document"],
                c["source_page"],
                c["figure_number"],
                c["item_number"],
                c["ibm_part_number"],
                c["description"],
                c["quantity"],
                c["raw_text"],
                c["confidence"],
                c["review_status"],
                c["notes"],
            )
            for c in candidates
        ],
    )


def fetch_raw_part_candidates(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT source_document, source_page, figure_number, item_number, ibm_part_number,
               description, quantity, confidence, review_status, raw_text, notes
        FROM raw_part_candidates
        ORDER BY source_document, source_page, raw_part_candidate_id
        """
    ).fetchall()


def fetch_review_candidates(
    conn: sqlite3.Connection,
    *,
    source_page: int | None = None,
    figure_number: str | None = None,
    review_status: str | None = None,
    confidence_max: float | None = None,
    blank_description_only: bool = False,
):
    query = """
        SELECT rpc.raw_part_candidate_id, rpc.source_document, rpc.source_page, rpc.figure_number,
               rpc.item_number, rpc.ibm_part_number, rpc.description, rpc.quantity,
               rpc.confidence, rpc.review_status, rpc.raw_text, rpc.notes,
               p.image_path, p.page_type
        FROM raw_part_candidates rpc
        LEFT JOIN pages p ON p.page_id = rpc.page_id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if source_page is not None:
        query += " AND rpc.source_page = ?"
        params.append(source_page)
    if figure_number:
        query += " AND rpc.figure_number = ?"
        params.append(figure_number)
    if review_status:
        query += " AND rpc.review_status = ?"
        params.append(review_status)
    if confidence_max is not None:
        query += " AND rpc.confidence <= ?"
        params.append(confidence_max)
    if blank_description_only:
        query += " AND (rpc.description IS NULL OR trim(rpc.description) = '')"

    query += " ORDER BY rpc.source_page, rpc.figure_number, rpc.raw_part_candidate_id"
    return conn.execute(query, params).fetchall()


def update_raw_part_candidate(conn: sqlite3.Connection, candidate_id: int, updates: dict[str, Any]) -> None:
    allowed_fields = {"item_number", "description", "quantity", "review_status", "notes"}
    update_items = [(field, value) for field, value in updates.items() if field in allowed_fields]
    if not update_items:
        return

    assignments = ", ".join(f"{field} = ?" for field, _ in update_items)
    values = [value for _, value in update_items]
    values.append(candidate_id)
    conn.execute(f"UPDATE raw_part_candidates SET {assignments} WHERE raw_part_candidate_id = ?", values)


def fetch_reviewed_part_candidates(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT source_document, source_page, figure_number, item_number, ibm_part_number,
               description, quantity, confidence, review_status, raw_text, notes
        FROM raw_part_candidates
        WHERE review_status IN ('reviewed_ok', 'corrected')
        ORDER BY source_document, source_page, raw_part_candidate_id
        """
    ).fetchall()
