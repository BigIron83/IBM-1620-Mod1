# Sprint 1 Notes

## Scope delivered

Sprint 1 delivers a local CLI-first foundation for IBM 1620 PDF ingestion and raw parts-catalog extraction.

## Current limitations

- No PySide6 desktop UI yet.
- No OCR fallback pipeline beyond embedded PDF text.
- Parts extraction is conservative and regex-based.
- Quantity extraction is intentionally not guessed.
- Bounding-box evidence and image overlays are deferred.
- Only the raw CPU parts-catalog workflow is targeted in Sprint 1.

## Next steps

- Add OCR fallback when embedded text is weak or missing.
- Improve figure/index detection and multi-column parsing.
- Add explicit page index export and extraction summaries.
- Add module, parts, and evidence tables for later milestones.
- Begin Sprint 2 review workflow and UI design.
