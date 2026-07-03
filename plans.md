# IBM 1620 PDF Part-List Desktop Application — Project Plan

## 1. Purpose - 

Build a local desktop application that reviews the IBM 1620 reference PDFs, extracts structured parts information, associates parts with IBM 1620 modules, and exports clean text/CSV files that can be opened in Excel later.

The first useful outcome is not a fully automatic perfect bill of materials. The first useful outcome is a repeatable extraction workflow with page-level evidence, confidence flags, and a human review step so the parts lists can be trusted and corrected over time.

## 2. Working definition of “module”

The application should support more than one module type because the IBM 1620 documentation uses several overlapping structures.

Primary module types:

- **System diagram module**: one logic/system diagram page, such as `01.60.11.1`.
- **Card type module**: one SMS card type, such as `AHK`, `CAB`, `CD`, `DAX`, `MX`, etc.
- **Physical assembly module**: a mechanical/electrical assembly from the parts catalog, such as a card gate, relay gate, power supply, display panel, typewriter subassembly, or memory/test panel.
- **Feature module**: optional feature documentation such as floating point or the 1622 card read-punch feature.

The MVP should start with **card type modules** and **physical assembly modules**, then add system diagram modules once the page-to-card relationships are reliable.

## 3. Source documents in the project knowledge base

Place source PDFs in `data/source_pdfs/` and keep the filenames stable. Suggested initial sources:

| Source | Purpose in app |
|---|---|
| `1620_CE_System_Diagrams_Vol_1_OCR_deskewed.pdf` | Function charts and system diagrams for early diagram ranges. |
| `1620_CE_System_Diagrams_Vol_2_OCR_deskewed.pdf` | System diagrams for middle diagram ranges. |
| `1620_CE_System_Diagrams_Vol_3_OCR_deskewed.pdf` | System diagrams, additional feature charts, and SMS card schematic pages. |
| `227-5631-0_IBM_1620_Customer_Engineering_Instructional_System_Diagrams_1962.pdf` | Combined/alternate instructional system diagrams source. |
| `127-0753-2_IBM_1620_Central_Processing_Unit_Parts_Catalog_May63.pdf` | CPU parts catalog; main source for IBM part numbers, mechanical assemblies, resistors, capacitors, SMS cards, and diodes. |
| `227-5500-3_1620_Model_1_FEMM_Dec63.pdf` | Field Engineering Maintenance Manual; use for machine locations, component locations, gates, connectors, terminal blocks, and service context. |
| `227-5751-1_1620_Model_1_Customer_Engineering_Manual_of_Instruction_Aug63.pdf` | Customer Engineering Manual of Instruction; use for system overview, component descriptions, and bibliography/source cross-checks. |
| `227-5647-0_1620_E_Level_CE_Manual_of_Instruction_1962.pdf` | E-level manual; use for earlier machine-level descriptions and operation references. |
| `227-5630-1_IBM_1620_Floating_Point_Feature_CE_Manual_1962.pdf` | Floating Point Feature; use for feature-specific module extraction. |
| `227-5816-0_1620_Model_1_1622_Card_Read_Punch_Feature_Customer_Engineering_Manual_of_Instruction_Sep63.pdf` | 1622 Card Read-Punch Feature; use for card reader/punch feature-specific module extraction. |
| `Transistor Diode Cross Reference.txt` | Cross-reference and prior extraction notes for transistor/diode equivalents and card-level BOM work. |

## 4. Product goals

### MVP goals

- Load the IBM 1620 PDFs into a local searchable document library.
- Extract page text, page images, page numbers, document names, and OCR confidence metadata.
- Detect tables and catalog rows from the parts catalog.
- Extract candidate part rows with part number, description, figure/module, item number, quantity when present, and source evidence.
- Extract candidate SMS card schematic rows from Volume III and map them to card type modules.
- Create a human-review screen where uncertain rows can be corrected.
- Export:
  - one combined CSV file,
  - one CSV file per module,
  - a plain text report per module,
  - unresolved/needs-review items.

### Later goals

- Link system diagram pages to SMS cards and physical locations.
- Reconstruct module-level BOMs by combining card placement counts with card-type BOMs.
- Add image overlays showing where a row or component was extracted from on the scanned page.
- Add a correction memory so fixes to OCR errors and card-code aliases are reused automatically.
- Add a verification report comparing expected card types, placements, and catalog lookup rows.

## 5. Non-goals for the first version

- No automatic procurement purchasing workflow.
- No assumption that OCR output is authoritative without review.
- No full pin-to-pin backplane netlist in the MVP.
- No destructive editing of source PDFs.
- No dependence on cloud OCR or external services for the first local desktop build.

## 6. Recommended application stack

Use a Python-first desktop stack because the extraction work is PDF/OCR/table-heavy.

### Recommended MVP stack

- **Language**: Python 3.12+
- **Desktop UI**: PySide6 / Qt
- **Database**: SQLite
- **PDF rendering**: PyMuPDF (`fitz`)
- **OCR**: Tesseract via `pytesseract`, optional if OCR text is already embedded
- **Image processing**: OpenCV and Pillow
- **Table/data processing**: pandas
- **CSV export**: Python `csv` module and pandas
- **Packaging**: PyInstaller
- **Testing**: pytest
- **Config**: TOML or YAML

### Optional later stack changes

- Tauri + React frontend with a Python extraction backend.
- DuckDB instead of SQLite if large analytical exports become important.
- A task queue if extraction jobs become slow enough to need background processing.

## 7. Proposed repository structure

```text
ibm1620-parts-app/
├── README.md
├── plans.md
├── pyproject.toml
├── requirements.txt
├── src/
│   └── ibm1620_parts/
│       ├── app.py
│       ├── ui/
│       │   ├── main_window.py
│       │   ├── document_viewer.py
│       │   ├── module_browser.py
│       │   ├── review_grid.py
│       │   └── export_wizard.py
│       ├── ingest/
│       │   ├── pdf_indexer.py
│       │   ├── ocr.py
│       │   ├── page_classifier.py
│       │   └── image_cache.py
│       ├── extractors/
│       │   ├── parts_catalog.py
│       │   ├── system_diagrams.py
│       │   ├── sms_card_schematics.py
│       │   ├── transistor_crossref.py
│       │   └── machine_locations.py
│       ├── normalize/
│       │   ├── part_numbers.py
│       │   ├── card_codes.py
│       │   ├── component_refs.py
│       │   └── text_cleanup.py
│       ├── model/
│       │   ├── schema.sql
│       │   ├── repositories.py
│       │   └── dataclasses.py
│       ├── export/
│       │   ├── csv_exporter.py
│       │   ├── text_exporter.py
│       │   └── excel_ready.py
│       └── qa/
│           ├── validators.py
│           ├── reconciliation.py
│           └── reports.py
├── data/
│   ├── source_pdfs/
│   ├── cache/
│   ├── extracted/
│   └── exports/
├── tests/
│   ├── fixtures/
│   ├── test_parts_catalog.py
│   ├── test_card_code_normalization.py
│   ├── test_exports.py
│   └── test_validators.py
└── docs/
    ├── data_dictionary.md
    ├── extraction_rules.md
    └── review_workflow.md
```

## 8. Core data model

The database should preserve both clean data and source evidence.

### Tables

#### `documents`

- `document_id`
- `filename`
- `title`
- `form_number`
- `source_path`
- `sha256`
- `page_count`
- `notes`

#### `pages`

- `page_id`
- `document_id`
- `pdf_page_number`
- `printed_page_label`
- `ocr_text`
- `ocr_confidence`
- `image_path`
- `page_type`
- `notes`

Suggested `page_type` values:

- `catalog_index`
- `catalog_figure`
- `resistor_chart`
- `capacitor_chart`
- `system_diagram`
- `function_chart`
- `sms_card_schematic`
- `machine_location`
- `manual_text`
- `unknown`

#### `modules`

- `module_id`
- `module_type`
- `module_code`
- `module_name`
- `parent_module_id`
- `source_document_id`
- `source_page_id`
- `notes`

Suggested `module_type` values:

- `card_type`
- `physical_assembly`
- `system_diagram`
- `feature`
- `gate`
- `power_supply`
- `typewriter`
- `memory`
- `io_device`

#### `parts`

- `part_id`
- `ibm_part_number`
- `normalized_part_number`
- `description`
- `part_category`
- `value`
- `rating`
- `commercial_equivalent`
- `notes`

Suggested `part_category` values:

- `sms_card`
- `transistor`
- `diode`
- `resistor`
- `capacitor`
- `inductor`
- `relay`
- `connector`
- `terminal_block`
- `mechanical`
- `power_supply`
- `unknown`

#### `module_parts`

- `module_part_id`
- `module_id`
- `part_id`
- `quantity`
- `reference_designator`
- `item_number`
- `figure_number`
- `source_page_id`
- `extraction_confidence`
- `review_status`
- `notes`

Suggested `review_status` values:

- `auto_extracted`
- `needs_review`
- `reviewed_ok`
- `corrected`
- `rejected`

#### `evidence`

- `evidence_id`
- `entity_type`
- `entity_id`
- `document_id`
- `page_id`
- `bbox_x0`
- `bbox_y0`
- `bbox_x1`
- `bbox_y1`
- `raw_text`
- `image_clip_path`
- `extractor_name`
- `extractor_version`

#### `normalization_aliases`

- `alias_id`
- `alias_type`
- `raw_value`
- `normalized_value`
- `reason`
- `created_by`

Examples:

- card-code OCR aliases: `CAH -> CAB`, `CLYB -> CEYB`
- punctuation cleanup: `01,60.11.1 -> 01.60.11.1`
- part-number cleanup: remove spaces inside numeric part numbers

#### `extraction_runs`

- `run_id`
- `started_at`
- `completed_at`
- `source_document_ids`
- `extractor_versions`
- `status`
- `notes`

## 9. CSV export formats

### `modules.csv`

```csv
module_id,module_type,module_code,module_name,parent_module_code,source_document,source_page,notes
```

### `module_parts.csv`

```csv
module_code,module_name,module_type,ibm_part_number,description,part_category,value,rating,quantity,reference_designator,item_number,figure_number,source_document,source_page,confidence,review_status,notes
```

### `parts_catalog.csv`

```csv
ibm_part_number,description,part_category,value,rating,figure_number,item_number,source_document,source_page,raw_text,confidence,review_status
```

### `card_type_bom.csv`

```csv
card_type,ibm_part_number,description,part_category,value,rating,quantity,reference_designator,commercial_equivalent,source_document,source_page,confidence,review_status
```

### `unresolved_items.csv`

```csv
source_document,source_page,raw_text,issue_type,suspected_value,suggested_fix,notes
```

### `evidence.csv`

```csv
entity_type,entity_id,source_document,source_page,bbox_x0,bbox_y0,bbox_x1,bbox_y1,raw_text,extractor_name,extractor_version
```

## 10. Extraction pipeline

### Stage 1: Document ingestion

- Hash each source file.
- Record filename, form number, title, page count, and source path.
- Render each page to an image cache.
- Extract embedded OCR text.
- If embedded OCR is missing or very low quality, run OCR on the rendered page.
- Store raw page text and page image paths.

### Stage 2: Page classification

Classify pages into broad page types.

Rules to start with:

- Page contains `CONTENTS` and `Logic Page Number` -> likely system diagram index/contents page.
- Page contains figure numbers like `1620-51`, `1620-52`, `1620-53`, or `1620-54` -> likely resistor/capacitor/SMS card catalog chart.
- Page contains diagram number pattern like `01.60.11.1` -> likely system diagram page.
- Page contains card schematic page pattern like `C.00.03.1` -> likely SMS card schematic page.
- Page contains `Machine Locations`, `Terminal Blocks`, `Diode Boards`, or connector-terminal notes -> machine location/reference page.

### Stage 3: Parts catalog extraction

Target documents:

- `127-0753-2_IBM_1620_Central_Processing_Unit_Parts_Catalog_May63.pdf`

Initial extraction tasks:

- Extract index rows mapping figures to assembly names.
- Extract figure rows with item numbers, IBM part numbers, and descriptions.
- Identify figure/module boundaries.
- Detect subassembly headings and nested assembly blocks.
- Mark rows without clear quantity or part number as `needs_review`.

Important catalog figure groups:

- `1620-1` through `1620-50`: CPU frame, covers, power supplies, gates, memory/test panel, power sequence panel, typewriter assemblies, magnet unit, control contacts.
- `1620-51` through `1620-54`: SMS cards, diodes, resistors, and capacitors.

### Stage 4: SMS card schematic extraction

Target documents:

- `1620_CE_System_Diagrams_Vol_3_OCR_deskewed.pdf`
- `227-5631-0_IBM_1620_Customer_Engineering_Instructional_System_Diagrams_1962.pdf`

Initial extraction tasks:

- Identify card schematic pages using `C.00.xx.1` page patterns.
- Extract card type code, card function, transistor references, diode references, resistor references, capacitor references, and any IBM part numbers present.
- Normalize component references such as `R1`, `C1`, `D1`, `Q1`, etc.
- Tie each extracted row to a card type module.
- Link transistor and diode rows to `Transistor Diode Cross Reference.txt` when possible.

### Stage 5: System diagram extraction

Target documents:

- Volume I, Volume II, Volume III, and the combined instructional system diagrams PDF.

Initial extraction tasks:

- Extract logic page number, logic title/function, and page number from contents/index pages.
- Detect card blocks and card references on logic pages.
- Extract candidate signal names and cross-sheet references.
- Associate a system diagram module with candidate card types and page evidence.
- Do not treat these as verified wiring until reviewed.

### Stage 6: Machine location extraction

Target documents:

- `227-5500-3_1620_Model_1_FEMM_Dec63.pdf`
- `227-5500-2_1620_Customer_Engineering_Reference_Manual_Jun61.pdf`

Initial extraction tasks:

- Extract gate, connector, terminal-block, diode-board, and power-supply location references.
- Map physical assemblies to location modules.
- Add location notes to module reports.

### Stage 7: Normalization and reconciliation

Normalize:

- IBM part numbers.
- Figure numbers.
- Printed page labels.
- Card type codes.
- Logic page numbers.
- Resistor values.
- Capacitor values.
- Diode/transistor type numbers.
- Common OCR confusions.

Reconcile:

- Catalog part rows against card schematic rows.
- Card schematic parts against transistor/diode cross-reference rows.
- Physical assembly rows against machine-location pages.
- System diagram modules against card schematic pages.

### Stage 8: Human review

The application should never silently discard ambiguous extraction results.

Review UI should allow:

- selecting an extraction run,
- filtering by `needs_review`,
- viewing the source page image next to the extracted row,
- editing fields,
- marking rows as reviewed or rejected,
- adding aliases or normalization rules from a correction,
- re-exporting after corrections.

### Stage 9: Export

Export options:

- all modules in one CSV,
- one CSV per module,
- one text report per module,
- unresolved items CSV,
- evidence CSV,
- extraction summary report.

CSV files should be Excel-friendly:

- UTF-8 with BOM option.
- Quote all fields.
- Normalize newlines inside cells.
- Avoid formulas or leading `=` in exported values unless escaped.
- Preserve part numbers as text.

## 11. Desktop UI plan

### Main screens

#### Document Library

- List source PDFs.
- Show title, form number, page count, OCR status, and extraction status.
- Buttons: `Add PDF`, `Index`, `Re-OCR`, `Open`.

#### Extraction Runs

- Show completed and failed runs.
- Show extractor versions and summary counts.
- Button: `Run Extraction`.

#### Module Browser

- Tree view by module type.
- Filters: card type, physical assembly, feature, system diagram, needs review.
- Summary: part count, unresolved count, last reviewed date.

#### Module Detail

- Parts grid for selected module.
- Fields: part number, description, category, value, rating, quantity, reference, figure, source, confidence, review status.
- Buttons: `Open Evidence`, `Mark Reviewed`, `Reject Row`, `Export Module`.

#### Evidence Viewer

- Rendered PDF page image.
- Highlight bounding boxes where possible.
- Show raw OCR text and cleaned value.

#### Export Wizard

- Choose export target folder.
- Choose combined vs per-module outputs.
- Choose CSV dialect and Excel compatibility options.
- Generate export report.

## 12. Milestones

### M0 — Repository and source setup

- [ ] Create Git repository.
- [ ] Add `plans.md`.
- [ ] Add `README.md` with project purpose.
- [ ] Add `.gitignore` for cache, database, rendered images, exports, and virtual environment.
- [ ] Add `data/source_pdfs/README.md` explaining that source PDFs are local and may not be committed.
- [ ] Add Python environment and dependency management.

### M1 — PDF ingestion and indexing

- [ ] Load PDF metadata.
- [ ] Extract embedded text.
- [ ] Render page images.
- [ ] Create SQLite schema.
- [ ] Store documents and pages.
- [ ] Add command-line ingestion script.
- [ ] Add tests using 2-3 sample pages.

### M2 — Parts catalog extractor

- [ ] Detect parts catalog index pages.
- [ ] Extract figure/module names.
- [ ] Extract part rows from catalog pages.
- [ ] Extract resistor/capacitor/SMS card chart candidates.
- [ ] Store evidence text and page number.
- [ ] Export first `parts_catalog.csv`.

### M3 — SMS card schematic extractor

- [ ] Detect SMS card schematic pages.
- [ ] Extract card type code and card function.
- [ ] Extract component rows.
- [ ] Link transistor/diode equivalents where possible.
- [ ] Export first `card_type_bom.csv`.

### M4 — Module BOM builder

- [ ] Create card type modules.
- [ ] Create physical assembly modules.
- [ ] Link extracted part rows to modules.
- [ ] Add confidence scoring.
- [ ] Add unresolved item reporting.

### M5 — Review UI

- [ ] Build basic PySide6 window.
- [ ] Add document list.
- [ ] Add module browser.
- [ ] Add editable parts grid.
- [ ] Add evidence viewer.
- [ ] Persist review status and corrections.

### M6 — Export UI

- [ ] Add export wizard.
- [ ] Export all module parts.
- [ ] Export one CSV per module.
- [ ] Export text reports.
- [ ] Export unresolved and evidence reports.

### M7 — Quality checks and reconciliation

- [ ] Add validators for part numbers, figure numbers, and card codes.
- [ ] Add duplicate detection.
- [ ] Add catalog-vs-card cross-check report.
- [ ] Add review completeness report.
- [ ] Add regression tests for known pages and known parts.

### M8 — Packaged desktop release

- [ ] Add app icon and version number.
- [ ] Package with PyInstaller.
- [ ] Test on Windows.
- [ ] Create release notes.
- [ ] Create sample export folder.

## 13. Extraction confidence rules

Start with simple confidence scoring.

High confidence:

- Part number matches expected IBM part-number pattern.
- Row contains a clear description.
- Row is located inside a detected catalog table or card schematic table.
- Figure number or card type is known.

Medium confidence:

- Part number is clear but quantity or category is missing.
- Description is clear but OCR produced minor punctuation errors.
- Card type is inferred from nearby page header.

Low confidence:

- OCR produced ambiguous characters in the part number.
- Row crosses page columns incorrectly.
- Component reference is detected but no part number is nearby.
- The row appears in a diagram rather than a structured parts list.

Default action:

- High confidence -> `auto_extracted`.
- Medium confidence -> `needs_review`.
- Low confidence -> `needs_review` and include in `unresolved_items.csv`.

## 14. Normalization rules to implement early

### Card codes

- Trim whitespace.
- Uppercase.
- Remove OCR punctuation.
- Maintain alias table rather than hard-coding all fixes.

Examples to support:

- `CAH` may be reviewed as `CAB` when evidence supports it.
- `CLYB` or `CECYB` may be reviewed as `CEYB` when evidence supports it.
- `YJR` may be reviewed as `YJB` when evidence supports it.

### Logic page numbers

Normalize OCR variants into:

```text
NN.NN.NN.N
```

Examples:

- `01,60.11.1` -> `01.60.11.1`
- `OLlO.05.1` -> `01.10.05.1`, only when reviewed or strongly supported by context

### Part numbers

- Strip spaces inside numeric strings.
- Preserve leading zeros if any are present.
- Store both raw and normalized forms.

### Component values

- Normalize capacitor values to a canonical string while preserving raw OCR.
- Normalize resistor ohm symbols and common OCR errors.
- Preserve original IBM descriptions exactly in `raw_text` evidence.

## 15. Validation checks

- Every `module_parts` row must link to a module and source page.
- Every exported row must include source document and source page.
- Part-number-only rows must be flagged if description is missing.
- Duplicate part rows within a module should be detected and shown in review.
- Any alias-created normalization should record the alias rule used.
- OCR-only rows without visual evidence should be flagged.
- Exports should be reproducible from a stored extraction run and correction database.

## 16. Suggested first issue list

Create these GitHub/Git issues first:

1. `Initialize repository structure`
2. `Add SQLite schema for documents, pages, modules, parts, evidence, and extraction runs`
3. `Implement PDF document ingestion with PyMuPDF`
4. `Implement page rendering cache`
5. `Implement parts catalog index-page detector`
6. `Extract first parts catalog table into CSV`
7. `Build basic module_parts.csv exporter`
8. `Add card-code normalization alias table`
9. `Detect SMS card schematic pages in Volume III`
10. `Create first PySide6 document library window`
11. `Create module browser and editable review grid`
12. `Add evidence viewer with page image preview`
13. `Package initial Windows build`

## 17. Risks and mitigations

| Risk | Mitigation |
|---|---|
| OCR errors in old scanned diagrams | Store raw evidence, confidence scores, page images, and review status. |
| Tables split across columns | Use page image layout and table-area detection, not text extraction alone. |
| Ambiguous card-code OCR | Use alias table and require review before normalizing uncertain codes. |
| Missing quantities | Export blank quantity and flag `needs_review` rather than guessing. |
| System diagrams are not complete BOMs | Treat system diagram extraction as evidence/cross-reference, not as the sole BOM source. |
| Similar form numbers and revised manuals | Store document filename, form number, and page number on every row. |
| Excel corrupting part numbers | Quote all fields and optionally write UTF-8 BOM; keep part numbers as text. |

## 18. Definition of done for MVP

The MVP is done when:

- A user can add the source PDFs.
- The app indexes pages and stores source evidence.
- The app extracts candidate parts from the CPU parts catalog.
- The app extracts candidate SMS card parts from card schematic pages.
- The app creates modules for card types and physical assemblies.
- The user can review/correct extracted rows.
- The app exports `module_parts.csv`, `parts_catalog.csv`, `card_type_bom.csv`, and `unresolved_items.csv`.
- Every exported row includes source document and page reference.

## 19. Sample exported row

```csv
module_code,module_name,module_type,ibm_part_number,description,part_category,value,rating,quantity,reference_designator,item_number,figure_number,source_document,source_page,confidence,review_status,notes
CAB,Ctrl-Inverters N Type Unlo Col,card_type,2123456,"RESISTOR - 4.7K",resistor,4.7K,,1,R3,,C.00.xx.1,1620_CE_System_Diagrams_Vol_3_OCR_deskewed.pdf,123,0.72,needs_review,"OCR value needs visual confirmation"
```

## 20. Open questions

- Should “module” default to card type, physical assembly, or system diagram page in the UI?
- Should source PDFs be committed to Git or kept outside the repo because of size/copyright?
- Should the app support existing XLS/XLSX card-placement data as a source in addition to PDFs?
- Should the first release target Windows only?
- Should exports include one file per card type by default, or one combined file with filters?
- Should reviewed corrections be stored in the same SQLite database or exported as separate project files?

## 21. Immediate next steps

- Create the repository and commit this `plans.md`.
- Add source PDF filenames to `data/source_pdfs/README.md`.
- Implement `documents`, `pages`, and `extraction_runs` tables.
- Build a command-line prototype that extracts text and renders page images.
- Run the prototype on the CPU parts catalog first.
- Export the first raw `parts_catalog.csv` before building the desktop UI.
