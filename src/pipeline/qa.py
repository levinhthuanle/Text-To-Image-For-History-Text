from __future__ import annotations

from typing import List

from .config import PipelineConfig
from .models import CaptionResult, OCRDocument, QAResult


class QualityAssurance:
    """Rule-based QA checks for generated annotations."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def evaluate(self, document: OCRDocument, caption: CaptionResult) -> QAResult:
        warnings: List[str] = []
        blocking: List[str] = []

        caption_text = caption.caption.lower()

        for span in document.texts:
            if span.confidence < self.config.min_ocr_confidence:
                warnings.append(f"Đoạn chữ '{span.text}' có độ tin cậy thấp ({span.confidence:.2f}).")
                continue
            normalized = span.text.strip().lower()
            if normalized and normalized not in caption_text:
                blocking.append(f"Caption chưa nhắc đến đoạn chữ: '{span.text}'.")

        if document.tables and "bảng" not in caption_text:
            blocking.append("Caption chưa mô tả bảng biểu trong ảnh.")

        return QAResult(warnings=warnings, blocking_issues=blocking)
