from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence


@dataclass(slots=True)
class BoundingBox:
    """Quadrilateral bounding box defined by 4 points (x, y)."""

    points: Sequence[Sequence[float]]

    @property
    def center(self) -> tuple[float, float]:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (sum(xs) / 4.0, sum(ys) / 4.0)

    @property
    def top(self) -> float:
        return min(p[1] for p in self.points)

    @property
    def bottom(self) -> float:
        return max(p[1] for p in self.points)


@dataclass(slots=True)
class TextSpan:
    text: str
    confidence: float
    bbox: BoundingBox


@dataclass(slots=True)
class TableCell:
    row: int
    col: int
    text: str


@dataclass(slots=True)
class TableContent:
    rows: int
    cols: int
    cells: List[TableCell] = field(default_factory=list)
    bbox: BoundingBox | None = None


@dataclass(slots=True)
class OCRDocument:
    texts: List[TextSpan] = field(default_factory=list)
    tables: List[TableContent] = field(default_factory=list)

    def all_text(self) -> str:
        return "\n".join(span.text for span in self.texts)


@dataclass(slots=True)
class CaptionResult:
    caption: str
    supporting_sentences: List[str]


@dataclass(slots=True)
class QAResult:
    warnings: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)

    def is_acceptable(self) -> bool:
        return not self.blocking_issues


@dataclass(slots=True)
class ImageArtifact:
    image_path: Path
    parent_pdf: Path
    page_number: int
    split_index: int = 0


@dataclass(slots=True)
class DatasetRecord:
    artifact: ImageArtifact
    ocr: OCRDocument
    caption: CaptionResult
    qa: QAResult

    def to_dict(self) -> dict:
        return {
            "image_path": str(self.artifact.image_path),
            "parent_pdf": str(self.artifact.parent_pdf),
            "page_number": self.artifact.page_number,
            "split_index": self.artifact.split_index,
            "ocr": {
                "texts": [
                    {
                        "text": span.text,
                        "confidence": span.confidence,
                        "bbox": span.bbox.points,
                    }
                    for span in self.ocr.texts
                ],
                "tables": [
                    {
                        "rows": table.rows,
                        "cols": table.cols,
                        "cells": [
                            {
                                "row": cell.row,
                                "col": cell.col,
                                "text": cell.text,
                            }
                            for cell in table.cells
                        ],
                        "bbox": table.bbox.points if table.bbox else None,
                    }
                    for table in self.ocr.tables
                ],
            },
            "caption": {
                "text": self.caption.caption,
                "supporting_sentences": self.caption.supporting_sentences,
            },
            "qa": {
                "warnings": self.qa.warnings,
                "blocking_issues": self.qa.blocking_issues,
                "is_acceptable": self.qa.is_acceptable(),
            },
        }
