from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from paddleocr import PaddleOCR

try:
    from paddleocr import PPStructure
except ImportError:  # pragma: no cover - optional dependency
    PPStructure = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional dependency
    BeautifulSoup = None  # type: ignore

from .config import PipelineConfig
from .models import BoundingBox, OCRDocument, TableCell, TableContent, TextSpan

LOGGER = logging.getLogger(__name__)


class OCRService:
    """Runs OCR (and optional table extraction) on images."""

    def __init__(self, config: PipelineConfig, language: str = "vi") -> None:
        self.config = config
        self.ocr_engine = PaddleOCR(use_angle_cls=True, lang=language)
        self.table_engine = None
        if PPStructure is not None:
            try:
                self.table_engine = PPStructure(lang=language, layout=True, table=True)
            except Exception as exc:  # pragma: no cover - PPStructure is optional
                LOGGER.warning("PPStructure unavailable: %s", exc)

    def extract(self, image_path: Path) -> OCRDocument:
        ocr_result = self.ocr_engine.ocr(str(image_path))
        document = OCRDocument()
        entries = ocr_result if ocr_result else []

        # Handle dict-style outputs (Paddlex doc pipeline)
        dict_entries = [e for e in entries if isinstance(e, dict)]
        line_entries = [e for e in entries if not isinstance(e, dict)]

        for entry in dict_entries:
            rec_texts = entry.get("rec_texts", [])
            rec_scores = entry.get("rec_scores", [])
            rec_polys = entry.get("rec_polys", [])
            for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
                bbox = self._normalize_bbox(poly)
                if bbox is None or not text:
                    continue
                document.texts.append(
                    TextSpan(text=text, confidence=float(score), bbox=bbox)
                )

        # Flatten possible nested page lists
        if (
            line_entries
            and isinstance(line_entries[0], list)
            and line_entries[0]
            and isinstance(line_entries[0][0], list)
        ):
            flat_lines = []
            for page in line_entries:
                flat_lines.extend(page or [])
            line_entries = flat_lines

        for line in line_entries:
            if not line:
                continue
            bbox_raw, text_info, *rest = line
            bbox = self._normalize_bbox(bbox_raw)
            if bbox is None:
                continue
            text, confidence = self._parse_text_info(text_info)
            if not text:
                continue
            document.texts.append(TextSpan(text=text, confidence=confidence, bbox=bbox))

        if self.table_engine is not None:
            try:
                tables = self.table_engine(str(image_path))
                document.tables.extend(self._parse_tables(tables))
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.warning("Table extraction failed for %s: %s", image_path, exc)

        return document

    def _parse_tables(self, tables: List[dict]) -> List[TableContent]:
        parsed: List[TableContent] = []
        for table in tables:
            if table.get("type") != "table":
                continue
            bbox = table.get("bbox")
            bbox_obj = BoundingBox(points=bbox) if bbox else None
            res = table.get("res", {})
            html = res.get("html")
            if not html or BeautifulSoup is None:
                continue
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.find_all("tr")
            row_count = len(rows)
            col_count = 0
            cells: List[TableCell] = []
            for r_idx, row in enumerate(rows):
                columns = row.find_all(["td", "th"])  # type: ignore[arg-type]
                col_count = max(col_count, len(columns))
                for c_idx, col in enumerate(columns):
                    text = col.get_text(" ", strip=True)
                    cells.append(TableCell(row=r_idx, col=c_idx, text=text))
            parsed.append(
                TableContent(rows=row_count, cols=col_count, cells=cells, bbox=bbox_obj)
            )
        return parsed

    def _parse_text_info(self, text_info):
        if isinstance(text_info, dict):
            text = text_info.get("text", "")
            confidence = float(text_info.get("confidence", 0.0))
            return text, confidence
        if isinstance(text_info, (list, tuple)):
            if len(text_info) >= 2:
                return text_info[0], float(text_info[1])
            if len(text_info) == 1:
                return text_info[0], 0.0
        return str(text_info), 0.0

    def _normalize_bbox(self, bbox_raw) -> BoundingBox | None:
        # Expect list/tuple/ndarray of 4 points, each point a list/tuple with at least 2 numbers.
        try:
            import numpy as np  # local import to avoid hard dependency at import time
        except ImportError:  # pragma: no cover
            np = None  # type: ignore

        if np is not None and isinstance(bbox_raw, np.ndarray):
            bbox_raw = bbox_raw.tolist()

        if not isinstance(bbox_raw, (list, tuple)):
            return None
        if len(bbox_raw) < 4:
            return None
        points = []
        for pt in bbox_raw:
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                return None
            try:
                x, y = float(pt[0]), float(pt[1])
            except (TypeError, ValueError):
                return None
            points.append([x, y])
        return BoundingBox(points=points)
