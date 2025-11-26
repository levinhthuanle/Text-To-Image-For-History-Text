from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PipelineConfig:
    """Static configuration for the dataset pipeline."""

    raw_pdf_dir: Path = Path("../raw")
    pdf_glob_pattern: str = "*.pdf"
    image_output_dir: Path = Path("../dataset/image")
    annotation_output_path: Path = Path("../dataset/annotations.jsonl")
    dpi: int = 300
    min_ocr_confidence: float = 0.5
    split_height_ratio: float = 1.6
    split_overlap: int = 32
    overwrite_images: bool = False

    def resolve(self, anchor: Path) -> "PipelineConfig":
        """Return a new config with paths resolved against *anchor*."""
        return PipelineConfig(
            raw_pdf_dir=(anchor / self.raw_pdf_dir).resolve(),
            pdf_glob_pattern=self.pdf_glob_pattern,
            image_output_dir=(anchor / self.image_output_dir).resolve(),
            annotation_output_path=(anchor / self.annotation_output_path).resolve(),
            dpi=self.dpi,
            min_ocr_confidence=self.min_ocr_confidence,
            split_height_ratio=self.split_height_ratio,
            split_overlap=self.split_overlap,
            overwrite_images=self.overwrite_images,
        )
