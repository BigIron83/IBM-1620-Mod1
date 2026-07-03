from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ibm1620_parts.export.csv_exporter import export_reviewed_parts_csv
from ibm1620_parts.model.repositories import (
    fetch_review_candidates,
    get_connection,
    update_raw_part_candidate,
)


TABLE_COLUMNS = [
    ("raw_part_candidate_id", "ID"),
    ("source_page", "Page"),
    ("figure_number", "Figure"),
    ("item_number", "Item"),
    ("ibm_part_number", "Part #"),
    ("description", "Description"),
    ("quantity", "Qty"),
    ("confidence", "Confidence"),
    ("review_status", "Status"),
]


class ReviewWindow(QMainWindow):
    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("IBM 1620 Parts Review")
        self.resize(1400, 900)
        self.db_path: Path | None = db_path
        self.rows: list[dict] = []
        self.current_candidate_id: int | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addLayout(self._build_top_bar())
        root.addLayout(self._build_filters())

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels([label for _, label in TABLE_COLUMNS])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selected_row)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        splitter.addWidget(self.table)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        splitter.addWidget(right)

        self.image_label = QLabel("No image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(380)
        right_layout.addWidget(self.image_label)

        form = QFormLayout()
        right_layout.addLayout(form)
        self.item_edit = QLineEdit()
        self.description_edit = QLineEdit()
        self.quantity_edit = QLineEdit()
        self.status_edit = QComboBox()
        self.status_edit.addItems(["needs_review", "auto_extracted", "reviewed_ok", "corrected", "rejected"])
        self.notes_edit = QPlainTextEdit()
        self.raw_text_view = QPlainTextEdit()
        self.raw_text_view.setReadOnly(True)
        form.addRow("Item number", self.item_edit)
        form.addRow("Description", self.description_edit)
        form.addRow("Quantity", self.quantity_edit)
        form.addRow("Review status", self.status_edit)
        form.addRow("Notes", self.notes_edit)
        form.addRow("Raw OCR", self.raw_text_view)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Save row")
        self.save_button.clicked.connect(self._save_current_row)
        self.export_button = QPushButton("Export reviewed CSV")
        self.export_button.clicked.connect(self._export_reviewed)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.export_button)
        right_layout.addLayout(buttons)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        if self.db_path is not None:
            self.db_path_edit.setText(str(self.db_path))
            self.refresh_rows()

    def _build_top_bar(self):
        layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        browse = QPushButton("Open DB")
        browse.clicked.connect(self._choose_db)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_rows)
        layout.addWidget(QLabel("Database"))
        layout.addWidget(self.db_path_edit, 1)
        layout.addWidget(browse)
        layout.addWidget(refresh)
        return layout

    def _build_filters(self):
        layout = QHBoxLayout()
        self.page_filter = QLineEdit()
        self.page_filter.setPlaceholderText("source page")
        self.figure_filter = QLineEdit()
        self.figure_filter.setPlaceholderText("figure number")
        self.status_filter = QComboBox()
        self.status_filter.addItem("", "")
        self.status_filter.addItems(["needs_review", "auto_extracted", "reviewed_ok", "corrected", "rejected"])
        self.confidence_filter = QDoubleSpinBox()
        self.confidence_filter.setRange(0.0, 1.0)
        self.confidence_filter.setSingleStep(0.05)
        self.confidence_filter.setValue(1.0)
        self.blank_desc_filter = QCheckBox("Blank description only")
        apply_btn = QPushButton("Apply filters")
        apply_btn.clicked.connect(self.refresh_rows)
        layout.addWidget(self.page_filter)
        layout.addWidget(self.figure_filter)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_filter)
        layout.addWidget(QLabel("Max confidence"))
        layout.addWidget(self.confidence_filter)
        layout.addWidget(self.blank_desc_filter)
        layout.addWidget(apply_btn)
        return layout

    def _choose_db(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SQLite database",
            str(Path.cwd()),
            "SQLite DB (*.db *.sqlite *.sqlite3)",
        )
        if path:
            self.db_path = Path(path)
            self.db_path_edit.setText(path)
            self.refresh_rows()

    def refresh_rows(self) -> None:
        if self.db_path is None:
            return
        with get_connection(self.db_path) as conn:
            rows = fetch_review_candidates(
                conn,
                source_page=int(self.page_filter.text()) if self.page_filter.text().strip().isdigit() else None,
                figure_number=self.figure_filter.text().strip() or None,
                review_status=self.status_filter.currentText() or None,
                confidence_max=self.confidence_filter.value() if self.confidence_filter.value() < 1.0 else None,
                blank_description_only=self.blank_desc_filter.isChecked(),
            )
        self.rows = [dict(row) for row in rows]
        self.table.setRowCount(len(self.rows))
        for row_idx, row in enumerate(self.rows):
            for col_idx, (field, _) in enumerate(TABLE_COLUMNS):
                item = QTableWidgetItem("" if row[field] is None else str(row[field]))
                self.table.setItem(row_idx, col_idx, item)
        if self.rows:
            self.table.selectRow(0)

    def _load_selected_row(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        row = self.rows[selected[0].row()]
        self.current_candidate_id = row["raw_part_candidate_id"]
        self.item_edit.setText(row.get("item_number") or "")
        self.description_edit.setText(row.get("description") or "")
        self.quantity_edit.setText(row.get("quantity") or "")
        self.status_edit.setCurrentText(row.get("review_status") or "needs_review")
        self.notes_edit.setPlainText(row.get("notes") or "")
        self.raw_text_view.setPlainText(row.get("raw_text") or "")
        self._load_image(row.get("image_path"))

    def _load_image(self, image_path: str | None) -> None:
        if not image_path or not Path(image_path).exists():
            self.image_label.setText("No image")
            self.image_label.setPixmap(QPixmap())
            return
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.image_label.setText("Unable to load image")
            return
        scaled = pixmap.scaled(600, 380, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def _save_current_row(self) -> None:
        if self.db_path is None or self.current_candidate_id is None:
            return
        updates = {
            "item_number": self.item_edit.text().strip() or None,
            "description": self.description_edit.text().strip() or None,
            "quantity": self.quantity_edit.text().strip() or None,
            "review_status": self.status_edit.currentText(),
            "notes": self.notes_edit.toPlainText().strip() or None,
        }
        with get_connection(self.db_path) as conn:
            update_raw_part_candidate(conn, self.current_candidate_id, updates)
            conn.commit()
        self.refresh_rows()

    def _export_reviewed(self) -> None:
        if self.db_path is None:
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export reviewed CSV",
            str(Path.cwd() / "data/exports/reviewed_parts.csv"),
            "CSV (*.csv)",
        )
        if not out_path:
            return
        export_reviewed_parts_csv(self.db_path, Path(out_path))
        QMessageBox.information(self, "Export complete", f"Wrote {out_path}")


def launch_review_app(db_path: Path | None = None) -> None:
    app = QApplication.instance() or QApplication([])
    window = ReviewWindow(db_path)
    window.show()
    app.exec()