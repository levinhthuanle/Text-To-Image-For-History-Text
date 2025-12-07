from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List

from .caption import CaptionGenerator
from .config import PipelineConfig
from .models import DatasetRecord, ImageArtifact
from .converter import convert_pdf_to_images
from .ocr import OCRService
from .preprocess import ImagePreprocessor
from .qa import QualityAssurance

LOGGER = logging.getLogger(__name__)


class DatasetPipeline:
    """High-level orchestration for dataset creation."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.preprocessor = ImagePreprocessor(config)
        self.ocr_service = OCRService(config)
        self.captioner = CaptionGenerator()
        self.qa = QualityAssurance(config)

    def run(self) -> List[DatasetRecord]:
        records: List[DatasetRecord] = []
        artifacts = self.convert_pdfs()
        if not artifacts:
            LOGGER.warning("No artifacts generated; nothing to process.")
            return records

        derived_artifacts: List[ImageArtifact] = []
        for artifact in artifacts:
            derived_artifacts.extend(self.preprocessor.process(artifact))

        if self.config.num_workers and self.config.num_workers > 1:
            with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
                for record in executor.map(self._process_image, derived_artifacts):
                    records.append(record)
        else:
            for derived in derived_artifacts:
                record = self._process_image(derived)
                records.append(record)
        self._write_annotations(records)
        LOGGER.info("Pipeline completed with %d records", len(records))
        return records

    def convert_pdfs(self) -> List[ImageArtifact]:
        self._ensure_output_dirs()
        pdf_files = sorted(self.config.raw_pdf_dir.glob(self.config.pdf_glob_pattern))

        if self.config.max_pdfs is not None:
            pdf_files = pdf_files[: self.config.max_pdfs]

        if not pdf_files:
            LOGGER.warning(
                "No PDF files matched pattern %s in %s",
                self.config.pdf_glob_pattern,
                self.config.raw_pdf_dir,
            )
            return []

        artifacts: List[ImageArtifact] = []
        for pdf_path in pdf_files:
            LOGGER.info("Converting PDF %s", pdf_path.name)
            artifacts.extend(self._convert_pdf(pdf_path))
        LOGGER.info("Prepared %d page images", len(artifacts))
        return artifacts

    def _ensure_output_dirs(self) -> None:
        self.config.image_output_dir.mkdir(parents=True, exist_ok=True)
        self.config.annotation_output_path.parent.mkdir(parents=True, exist_ok=True)

    def _convert_pdf(self, pdf_path: Path) -> List[ImageArtifact]:
        image_paths = convert_pdf_to_images(
            pdf_path,
            self.config.image_output_dir,
            dpi=self.config.dpi,
            overwrite=self.config.overwrite_images,
            max_pages=self.config.max_pages_per_pdf,
        )
        artifacts: List[ImageArtifact] = []
        for idx, image_path in enumerate(image_paths, start=1):
            LOGGER.debug("Prepared image %s", image_path.name)
            artifacts.append(
                ImageArtifact(
                    image_path=image_path, parent_pdf=pdf_path, page_number=idx
                )
            )
        return artifacts

    def _process_image(self, artifact: ImageArtifact) -> DatasetRecord:
        document = self.ocr_service.extract(artifact.image_path)
        caption = self.captioner.generate(artifact.image_path, document)
        qa_result = self.qa.evaluate(document, caption)
        return DatasetRecord(
            artifact=artifact, ocr=document, caption=caption, qa=qa_result
        )

    def _write_annotations(self, records: Iterable[DatasetRecord]) -> None:
        output = self.config.annotation_output_path
        with output.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
