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
ITEM_PATTERN = re.compile(r"^\s*([A-Z]\d{0,2}|\d{1,3}[A-Z]?|[A-Z])\b")
INLINE_WS_PATTERN = re.compile(r"\s+")
DESC_START_PATTERN = re.compile(r"[A-Z][A-Za-z0-9&][A-Za-z0-9& ,\-./()]*")
WORD_WITH_LOWER_L_PATTERN = re.compile(r"\b[A-Z]*l[A-Z]+\b")


def _normalize_line(text: str) -> str:
    return INLINE_WS_PATTERN.sub(" ", text).strip()


def _looks_like_description(text: str) -> bool:
    if not text:
        return False
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    uppercase_letters = [char for char in letters if char.isupper()]
    return len(uppercase_letters) / len(letters) >= 0.7


def _normalize_description(text: str) -> str:
    normalized = text.strip(" ,")

    def fix_lower_l(match: re.Match[str]) -> str:
        return match.group(0).replace("l", "L")

    normalized = WORD_WITH_LOWER_L_PATTERN.sub(fix_lower_l, normalized)
    return normalized


def _build_candidate(
    raw_text: str,
    document_name: str,
    page_number: int,
    figure_number: str | None,
    allow_number_only: bool,
) -> dict | None:
    stripped = _normalize_line(raw_text)
    if not stripped or FIGURE_PATTERN.fullmatch(stripped):
        return None

    part_match = PART_NUMBER_PATTERN.search(stripped)
    if not part_match:
        return None

    item_match = ITEM_PATTERN.match(stripped)
    remainder = stripped[part_match.end():].strip(" -:")
    description_match = DESC_START_PATTERN.search(remainder) if remainder else None
    description = (
        _normalize_description(description_match.group(0))
        if description_match and _looks_like_description(description_match.group(0))
        else None
    )

    if description:
        confidence = 0.9 if item_match else 0.82
        review_status = "auto_extracted"
    elif allow_number_only:
        confidence = 0.3
        review_status = "needs_review"
    else:
        return None

    return {
        "source_document": document_name,
        "source_page": page_number,
        "figure_number": figure_number,
        "item_number": item_match.group(1) if item_match else None,
        "ibm_part_number": part_match.group(1),
        "description": description,
        "quantity": None,
        "raw_text": stripped,
        "confidence": confidence,
        "review_status": review_status,
        "notes": None,
    }


def extract_candidate_rows(
    page_text: str,
    document_name: str,
    page_number: int,
    page_type: str | None = None,
) -> list[dict]:
    if not page_text.strip():
        return []

    figure_match = FIGURE_PATTERN.search(page_text)
    figure_number = figure_match.group(1) if figure_match else None
    context_page_types = {"catalog_figure", "resistor_chart", "capacitor_chart"}
    allow_number_only = page_type in context_page_types or figure_number is not None
    candidates: list[dict] = []
    seen: set[tuple[str, str]] = set()
    described_part_numbers: set[str] = set()
    lines = [_normalize_line(line) for line in page_text.splitlines()]
    lines = [line for line in lines if line]

    for index, line in enumerate(lines):
        attempts = [line]
        if index + 1 < len(lines):
            next_line = lines[index + 1]
            if PART_NUMBER_PATTERN.search(line) and not PART_NUMBER_PATTERN.search(next_line):
                attempts.insert(0, f"{line} {next_line}")

        for attempt in attempts:
            candidate = _build_candidate(
                attempt,
                document_name,
                page_number,
                figure_number,
                allow_number_only=allow_number_only and attempt == line,
            )
            if candidate is None:
                continue
            key = (candidate["ibm_part_number"], candidate["raw_text"])
            if key in seen:
                continue
            if candidate["description"] is None and candidate["ibm_part_number"] in described_part_numbers:
                continue
            seen.add(key)
            if candidate["description"]:
                described_part_numbers.add(candidate["ibm_part_number"])
            candidates.append(candidate)
            break

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
                page["page_type"],
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
