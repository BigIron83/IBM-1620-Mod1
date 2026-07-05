from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
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
    QStatusBar,
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
        self.current_row_index: int | None = None
        self._loading_row = False
        self._dirty = False

        central = QWidget()
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        root = QVBoxLayout(central)

        root.addLayout(self._build_top_bar())
        root.addLayout(self._build_filters())
        self.counts_label = QLabel("Visible: 0 | needs_review: 0 | reviewed_ok: 0 | corrected: 0")
        root.addWidget(self.counts_label)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels([label for _, label in TABLE_COLUMNS])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
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

        for widget in (self.item_edit, self.description_edit, self.quantity_edit):
            widget.textEdited.connect(self._mark_dirty)
        self.status_edit.currentTextChanged.connect(self._mark_dirty)
        self.notes_edit.textChanged.connect(self._mark_dirty)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Save row")
        self.save_button.clicked.connect(self._save_current_row)
        self.review_ok_button = QPushButton("Mark reviewed_ok")
        self.review_ok_button.clicked.connect(lambda: self._set_review_status_and_save("reviewed_ok"))
        self.needs_review_button = QPushButton("Mark needs_review")
        self.needs_review_button.clicked.connect(lambda: self._set_review_status_and_save("needs_review"))
        self.corrected_button = QPushButton("Mark corrected")
        self.corrected_button.clicked.connect(lambda: self._set_review_status_and_save("corrected"))
        self.export_button = QPushButton("Export reviewed CSV")
        self.export_button.clicked.connect(self._export_reviewed)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.review_ok_button)
        buttons.addWidget(self.needs_review_button)
        buttons.addWidget(self.corrected_button)
        buttons.addWidget(self.export_button)
        right_layout.addLayout(buttons)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._save_current_row)
        QShortcut(QKeySequence("Ctrl+Down"), self, activated=self._select_next_row)

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
        reset_btn = QPushButton("Reset filters")
        reset_btn.clicked.connect(self._reset_filters)
        layout.addWidget(self.page_filter)
        layout.addWidget(self.figure_filter)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_filter)
        layout.addWidget(QLabel("Max confidence"))
        layout.addWidget(self.confidence_filter)
        layout.addWidget(self.blank_desc_filter)
        layout.addWidget(apply_btn)
        layout.addWidget(reset_btn)
        return layout

    def _reset_filters(self) -> None:
        self.page_filter.clear()
        self.figure_filter.clear()
        self.status_filter.setCurrentIndex(0)
        self.confidence_filter.setValue(1.0)
        self.blank_desc_filter.setChecked(False)
        self.refresh_rows()

    def _mark_dirty(self, *_args) -> None:
        if self._loading_row:
            return
        self._dirty = True
        self.statusBar().showMessage("Unsaved changes", 2000)

    def _confirm_discard_changes(self) -> bool:
        if not self._dirty:
            return True
        response = QMessageBox.question(
            self,
            "Unsaved changes",
            "You have unsaved changes. Discard them?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return response == QMessageBox.Yes

    def _choose_db(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SQLite database",
            str(Path.cwd()),
            "SQLite DB (*.db *.sqlite *.sqlite3)",
        )
        if path:
            if not self._confirm_discard_changes():
                return
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
        self._update_counts()
        if self.rows:
            self.table.selectRow(0)

    def _update_counts(self) -> None:
        visible = len(self.rows)
        needs_review = sum(1 for row in self.rows if row.get("review_status") == "needs_review")
        reviewed_ok = sum(1 for row in self.rows if row.get("review_status") == "reviewed_ok")
        corrected = sum(1 for row in self.rows if row.get("review_status") == "corrected")
        self.counts_label.setText(
            f"Visible: {visible} | needs_review: {needs_review} | reviewed_ok: {reviewed_ok} | corrected: {corrected}"
        )

    def _load_selected_row(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        if not self._confirm_discard_changes():
            self._loading_row = True
            if self.current_row_index is not None and 0 <= self.current_row_index < self.table.rowCount():
                self.table.selectRow(self.current_row_index)
            self._loading_row = False
            return
        row = self.rows[selected[0].row()]
        self.current_row_index = selected[0].row()
        self.current_candidate_id = row["raw_part_candidate_id"]
        self._loading_row = True
        self.item_edit.setText(row.get("item_number") or "")
        self.description_edit.setText(row.get("description") or "")
        self.quantity_edit.setText(row.get("quantity") or "")
        self.status_edit.setCurrentText(row.get("review_status") or "needs_review")
        self.notes_edit.setPlainText(row.get("notes") or "")
        self.raw_text_view.setPlainText(row.get("raw_text") or "")
        self._loading_row = False
        self._dirty = False
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
        self._dirty = False
        self.statusBar().showMessage("Row saved", 3000)
        self.refresh_rows()

    def _set_review_status_and_save(self, status: str) -> None:
        self.status_edit.setCurrentText(status)
        self._save_current_row()

    def _select_next_row(self) -> None:
        if self.table.rowCount() == 0:
            return
        current = self.table.currentRow()
        next_row = min(current + 1, self.table.rowCount() - 1)
        self.table.selectRow(next_row)

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

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._confirm_discard_changes():
            event.accept()
        else:
            event.ignore()


def launch_review_app(db_path: Path | None = None) -> None:
    app = QApplication.instance() or QApplication([])
    window = ReviewWindow(db_path)
    window.show()
    app.exec()