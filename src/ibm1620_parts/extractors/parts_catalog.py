from __future__ import annotations

import re
from pathlib import Path

from ibm1620_parts.model.repositories import (
    complete_extraction_run,
    create_extraction_run,
    get_connection,
    get_document_by_filename,
    get_pages_for_document,
    insert_raw_part_candidates,
)

PART_NUMBER_PATTERN = re.compile(r"\b(\d{5,7})\b")
FIGURE_PATTERN = re.compile(r"\b(1620-\d{1,3})\b")
ITEM_PATTERN = re.compile(r"^\s*(\d{1,3}[A-Z]?)\b")
UPPERCASE_DESC_PATTERN = re.compile(r"\b\d{5,7}\b\s+([A-Z][A-Z0-9 ,\-./()]+)")


def extract_candidate_rows(page_text: str, document_name: str, page_number: int) -> list[dict]:
    if not page_text.strip():
        return []

    figure_match = FIGURE_PATTERN.search(page_text)
    figure_number = figure_match.group(1) if figure_match else None
    candidates: list[dict] = []

    for line in page_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        part_match = PART_NUMBER_PATTERN.search(stripped)
        if not part_match:
            continue
        description_match = UPPERCASE_DESC_PATTERN.search(stripped)
        item_match = ITEM_PATTERN.match(stripped)
        description = description_match.group(1).strip() if description_match else None
        confidence = 0.82 if description else 0.55
        candidates.append(
            {
                "source_document": document_name,
                "source_page": page_number,
                "figure_number": figure_number,
                "item_number": item_match.group(1) if item_match else None,
                "ibm_part_number": part_match.group(1),
                "description": description,
                "quantity": None,
                "raw_text": stripped,
                "confidence": confidence,
                "review_status": "auto_extracted" if confidence >= 0.7 else "needs_review",
                "notes": None,
            }
        )
    return candidates


def extract_parts_catalog(db_path: Path, document_filename: str) -> int:
    with get_connection(db_path) as conn:
        document = get_document_by_filename(conn, document_filename)
        if document is None:
            raise ValueError(f"Document not found: {document_filename}")

        run_id = create_extraction_run(
            conn,
            source_document_id=document["document_id"],
            extractor_name="parts_catalog",
        )
        pages = get_pages_for_document(conn, document["document_id"])
        all_candidates = []
        for page in pages:
            page_candidates = extract_candidate_rows(
                page["ocr_text"] or "",
                document["filename"],
                page["pdf_page_number"],
            )
            for candidate in page_candidates:
                candidate["extraction_run_id"] = run_id
                candidate["document_id"] = document["document_id"]
                candidate["page_id"] = page["page_id"]
            all_candidates.extend(page_candidates)

        insert_raw_part_candidates(conn, all_candidates)
        complete_extraction_run(conn, run_id, status="completed")
        conn.commit()
        return len(all_candidates)
