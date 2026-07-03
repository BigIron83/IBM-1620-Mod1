from __future__ import annotations

from pathlib import Path

import fitz


def render_document_pages(doc: fitz.Document, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered_paths: list[str] = []
    for index, page in enumerate(doc, start=1):
        pix = page.get_pixmap()
        image_path = output_dir / f"page_{index:04d}.png"
        pix.save(image_path)
        rendered_paths.append(str(image_path))
    return rendered_paths
