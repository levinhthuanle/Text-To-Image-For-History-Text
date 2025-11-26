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
        self.ocr = PaddleOCR(use_angle_cls=True, lang=language)
        self.table_engine = None
        if PPStructure is not None:
            try:
                self.table_engine = PPStructure(lang=language, layout=True, table=True)
            except Exception as exc:  # pragma: no cover - PPStructure is optional
                LOGGER.warning("PPStructure unavailable: %s", exc)

    def extract(self, image_path: Path) -> OCRDocument:
        ocr_result = self.ocr.ocr(str(image_path), cls=True)
        document = OCRDocument()
        for line in ocr_result:
            if not line:
                continue
            bbox_raw, text_info = line
            text, confidence = text_info
            bbox = BoundingBox(points=bbox_raw)
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
            parsed.append(TableContent(rows=row_count, cols=col_count, cells=cells, bbox=bbox_obj))
        return parsed
