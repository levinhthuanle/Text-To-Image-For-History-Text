from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image

from .models import CaptionResult, OCRDocument, TableContent, TextSpan


class CaptionGenerator:
    """Creates heuristic Vietnamese captions based on OCR output."""

    def generate(self, image_path: Path, document: OCRDocument) -> CaptionResult:
        image = Image.open(image_path)
        width, height = image.size
        sentences: List[str] = []

        if not document.texts and not document.tables:
            sentences.append("Ảnh trang tài liệu không có chữ rõ ràng được nhận diện.")
            return CaptionResult(caption=" ".join(sentences), supporting_sentences=sentences)

        sentences.append(
            "Ảnh tài liệu với bố cục dọc, nền giấy sáng và nội dung tiếng Việt."  # baseline context
        )

        top_spans = sorted(document.texts, key=lambda span: span.bbox.top)[:3]
        for span in top_spans:
            position = self._describe_position(span, width, height)
            sentences.append(f"{position} có đoạn chữ: \"{span.text}\".")

        for table in document.tables:
            sentences.append(self._describe_table(table))

        missing = len(document.texts) - len(top_spans)
        if missing > 0:
            sentences.append(f"Ngoài ra còn {missing} đoạn chữ khác xuất hiện ở các vị trí phía dưới.")

        caption = " ".join(sentences)
        return CaptionResult(caption=caption, supporting_sentences=sentences)

    def _describe_position(self, span: TextSpan, width: int, height: int) -> str:
        cx, cy = span.bbox.center
        horizontal = "bên trái" if cx < width * 0.33 else "bên phải" if cx > width * 0.66 else "chính giữa"
        vertical = "phần trên" if cy < height * 0.33 else "phần dưới" if cy > height * 0.66 else "khoảng giữa"
        return f"Ở {vertical} {horizontal}".strip()

    def _describe_table(self, table: TableContent) -> str:
        header = f"Ảnh có một bảng gồm {table.rows} dòng và {table.cols} cột."
        if not table.cells:
            return header
        preview = []
        for cell in table.cells[: min(4, len(table.cells))]:
            preview.append(f"(dòng {cell.row + 1}, cột {cell.col + 1}): \"{cell.text}\"")
        preview_text = "; ".join(preview)
        return f"{header} Một số ô nội dung gồm {preview_text}."
