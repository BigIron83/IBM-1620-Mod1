# IBM 1620 Parts App — Sprint 1

This repository contains Sprint 1 of a local Python desktop application for indexing IBM 1620 reference PDFs and extracting raw parts-catalog evidence.

Sprint 1 focuses on a command-line workflow, not the desktop UI yet.

## Sprint 1 features

- SQLite database initialization
- PDF ingestion with SHA-256 tracking
- Embedded text extraction with PyMuPDF
- Optional page image rendering to PNG
- Rule-based page classification
- Conservative CPU parts-catalog candidate extraction
- Raw CSV export for later Excel review

## Requirements

- Python 3.12+

## Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Commands

```bash
python -m ibm1620_parts.cli init-db --db data/extracted/ibm1620.db
python -m ibm1620_parts.cli ingest-pdf --db data/extracted/ibm1620.db --pdf data/source_pdfs/127-0753-2_IBM_1620_Central_Processing_Unit_Parts_Catalog_May63.pdf --render-pages
python -m ibm1620_parts.cli extract-parts-catalog --db data/extracted/ibm1620.db --document 127-0753-2_IBM_1620_Central_Processing_Unit_Parts_Catalog_May63.pdf
python -m ibm1620_parts.cli export-raw-parts --db data/extracted/ibm1620.db --out data/exports/parts_catalog_raw.csv
pytest
```

## Notes

- Source evidence is preserved for every extracted row.
- Uncertain rows are retained and marked `needs_review`.
- Sprint 1 uses deterministic local rules only. No cloud OCR or external APIs are used.
