PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    form_number TEXT,
    source_path TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    page_count INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS pages (
    page_id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    pdf_page_number INTEGER NOT NULL,
    printed_page_label TEXT,
    ocr_text TEXT,
    ocr_confidence REAL,
    image_path TEXT,
    page_type TEXT,
    notes TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS extraction_runs (
    extraction_run_id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    source_document_id INTEGER,
    extractor_name TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY(source_document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS raw_part_candidates (
    raw_part_candidate_id INTEGER PRIMARY KEY,
    extraction_run_id INTEGER,
    document_id INTEGER,
    page_id INTEGER,
    source_document TEXT,
    source_page INTEGER,
    figure_number TEXT,
    item_number TEXT,
    ibm_part_number TEXT,
    description TEXT,
    quantity TEXT,
    raw_text TEXT,
    confidence REAL,
    review_status TEXT DEFAULT needs_review,
    notes TEXT,
    FOREIGN KEY(extraction_run_id) REFERENCES extraction_runs(extraction_run_id),
    FOREIGN KEY(document_id) REFERENCES documents(document_id),
    FOREIGN KEY(page_id) REFERENCES pages(page_id)
);
