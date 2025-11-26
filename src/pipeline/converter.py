from __future__ import annotations

from pathlib import Path
from typing import List

from pdf2image import convert_from_path


def convert_pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    base_name: str | None = None,
    *,
    dpi: int = 300,
    overwrite: bool = False,
) -> List[Path]:
    """Convert *pdf_path* to PNG images and return their paths."""

    output_dir.mkdir(parents=True, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=dpi)
    saved_paths: List[Path] = []

    for index, image in enumerate(images, start=1):
        stem = base_name or pdf_path.stem
        filename = f"{stem}_page_{index:03d}.png"
        image_path = output_dir / filename
        if image_path.exists() and not overwrite:
            saved_paths.append(image_path)
            continue
        image.save(image_path, "PNG")
        saved_paths.append(image_path)

    return saved_paths
