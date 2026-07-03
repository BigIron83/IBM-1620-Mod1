from __future__ import annotations

import hashlib
import re
from pathlib import Path

import fitz

from ibm1620_parts.ingest.image_cache import render_document_pages
from ibm1620_parts.model.repositories import (
    get_connection,
    initialize_database,
    replace_pages_for_document,
    upsert_document,
)
from ibm1620_parts.normalize.text_cleanup import normalize_multiline_text

PART_NUMBER_PATTERN = re.compile(r"\b\d{5,7}\b")


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_page_text(text: str) -> str:
    normalized = (text or "").upper()
    if "RESISTORS" in normalized:
        return "resistor_chart"
    if "CAPACITORS" in normalized:
        return "capacitor_chart"
    if "1620-" in normalized and len(PART_NUMBER_PATTERN.findall(normalized)) >= 2:
        return "catalog_figure"
    if "PARTS CATALOG" in normalized:
        return "catalog_index"
    if "IBM 1620 CENTRAL PROCESSING" in normalized:
        return "manual_text"
    return "unknown"


def _extract_form_number(filename: str) -> str | None:
    match = re.match(r"^(\d{3}-\d{4}-\d)", filename)
    return match.group(1) if match else None


def ingest_pdf(db_path: Path, pdf_path: Path, render_pages: bool = False) -> int:
    initialize_database(db_path)
    sha256 = compute_sha256(pdf_path)

    with fitz.open(pdf_path) as doc:
        title = doc.metadata.get("title") or pdf_path.stem
        document_data = {
            "filename": pdf_path.name,
            "title": title,
            "form_number": _extract_form_number(pdf_path.name),
            "source_path": str(pdf_path),
            "sha256": sha256,
            "page_count": doc.page_count,
            "notes": None,
        }

        rendered_paths: list[str] = []
        if render_pages:
            cache_dir = Path("data/cache/page_images") / sha256
            rendered_paths = render_document_pages(doc, cache_dir)

        page_rows = []
        for idx, page in enumerate(doc, start=1):
            raw_text = page.get_text("text") or ""
            page_rows.append(
                {
                    "pdf_page_number": idx,
                    "printed_page_label": page.get_label() or None,
                    "ocr_text": normalize_multiline_text(raw_text),
                    "ocr_confidence": None,
                    "image_path": rendered_paths[idx - 1] if rendered_paths else None,
                    "page_type": classify_page_text(raw_text),
                    "notes": None,
                }
            )

    with get_connection(db_path) as conn:
        document_id = upsert_document(conn, document_data)
        replace_pages_for_document(conn, document_id, page_rows)
        conn.commit()
    return document_id
