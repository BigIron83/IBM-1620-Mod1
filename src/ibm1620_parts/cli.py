from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ibm1620_parts.export.csv_exporter import export_raw_parts_csv, export_reviewed_parts_csv
from ibm1620_parts.extractors.parts_catalog import extract_parts_catalog
from ibm1620_parts.ingest.pdf_indexer import ingest_pdf
from ibm1620_parts.model.repositories import initialize_database
from ibm1620_parts.review_app import launch_review_app


def _require_existing_file(path: Path, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{label} is not a file: {path}")
    return path


def _require_existing_database(path: Path) -> Path:
    return _require_existing_file(path, "Database")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ibm1620_parts.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db", help="Initialize SQLite database")
    init_db.add_argument("--db", required=True)

    ingest = subparsers.add_parser("ingest-pdf", help="Ingest a PDF into the database")
    ingest.add_argument("--db", required=True)
    ingest.add_argument("--pdf", required=True)
    ingest.add_argument("--render-pages", action="store_true")

    extract = subparsers.add_parser("extract-parts-catalog", help="Extract raw parts candidates")
    extract.add_argument("--db", required=True)
    extract.add_argument("--document", required=True)

    export = subparsers.add_parser("export-raw-parts", help="Export raw parts CSV")
    export.add_argument("--db", required=True)
    export.add_argument("--out", required=True)

    export_reviewed = subparsers.add_parser("export-reviewed-parts", help="Export reviewed parts CSV")
    export_reviewed.add_argument("--db", required=True)
    export_reviewed.add_argument("--out", required=True)

    review = subparsers.add_parser("review-db", help="Open desktop review workflow")
    review.add_argument("--db")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "init-db":
            initialize_database(Path(args.db))
            return 0

        if args.command == "ingest-pdf":
            ingest_pdf(Path(args.db), _require_existing_file(Path(args.pdf), "PDF"), render_pages=args.render_pages)
            return 0

        if args.command == "extract-parts-catalog":
            extract_parts_catalog(_require_existing_database(Path(args.db)), args.document)
            return 0

        if args.command == "export-raw-parts":
            export_raw_parts_csv(_require_existing_database(Path(args.db)), Path(args.out))
            return 0

        if args.command == "export-reviewed-parts":
            export_reviewed_parts_csv(_require_existing_database(Path(args.db)), Path(args.out))
            return 0

        if args.command == "review-db":
            launch_review_app(Path(args.db) if args.db else None)
            return 0

        parser.error(f"Unknown command: {args.command}")
        return 2
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
