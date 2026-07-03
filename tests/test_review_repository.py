from ibm1620_parts.model.repositories import (
    fetch_review_candidates,
    get_connection,
    initialize_database,
    update_raw_part_candidate,
)


def test_review_repository_filters_and_updates(tmp_path) -> None:
    db_path = tmp_path / "review.db"
    initialize_database(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO documents (filename, source_path, sha256) VALUES (?, ?, ?)",
            ("doc.pdf", "doc.pdf", "abc"),
        )
        document_id = conn.execute("SELECT document_id FROM documents").fetchone()[0]
        conn.execute(
            "INSERT INTO pages (document_id, pdf_page_number, image_path, page_type) VALUES (?, ?, ?, ?)",
            (document_id, 3, "image.png", "catalog_figure"),
        )
        page_id = conn.execute("SELECT page_id FROM pages").fetchone()[0]
        conn.executemany(
            """
            INSERT INTO raw_part_candidates (
                page_id, document_id, source_document, source_page, figure_number, item_number,
                ibm_part_number, description, quantity, raw_text, confidence, review_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (page_id, document_id, "doc.pdf", 3, "1620-1", None, "123456", None, None, "raw", 0.3, "needs_review", None),
                (page_id, document_id, "doc.pdf", 3, "1620-1", "A", "654321", "BLOCK ASM", None, "raw2", 0.9, "reviewed_ok", None),
            ],
        )
        conn.commit()

        rows = fetch_review_candidates(conn, source_page=3, blank_description_only=True)
        assert len(rows) == 1
        assert rows[0]["ibm_part_number"] == "123456"

        candidate_id = rows[0]["raw_part_candidate_id"]
        update_raw_part_candidate(conn, candidate_id, {"description": "FIXED DESC", "review_status": "corrected"})
        conn.commit()

        updated = fetch_review_candidates(conn, review_status="corrected")
        assert len(updated) == 1
        assert updated[0]["description"] == "FIXED DESC"