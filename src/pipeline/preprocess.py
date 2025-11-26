from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, List

import numpy as np
from PIL import Image, ImageOps

from .config import PipelineConfig
from .models import ImageArtifact


class ImagePreprocessor:
    """Performs light image cleanup and optional page splitting."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def process(self, artifact: ImageArtifact) -> List[ImageArtifact]:
        image = Image.open(artifact.image_path)
        image = image.convert("RGB")
        image = self._autocrop(image)
        image.save(artifact.image_path)

        if self._needs_split(image):
            return self._split_image(image, artifact)

        return [artifact]

    def _autocrop(self, image: Image.Image) -> Image.Image:
        gray = image.convert("L")
        np_image = np.array(gray)
        mask = np_image < 245
        if not mask.any():
            return image
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        top, bottom = rows[[0, -1]]
        left, right = cols[[0, -1]]
        cropped = image.crop((left, top, right + 1, bottom + 1))
        return ImageOps.expand(cropped, border=5, fill="white")

    def _needs_split(self, image: Image.Image) -> bool:
        if image.width == 0:
            return False
        ratio = image.height / image.width
        return ratio > self.config.split_height_ratio

    def _split_image(self, image: Image.Image, artifact: ImageArtifact) -> List[ImageArtifact]:
        ratio = image.height / max(image.width, 1)
        max_ratio = max(self.config.split_height_ratio, 1.0)
        pieces = max(2, math.ceil(ratio / max_ratio))
        slice_height = math.ceil(image.height / pieces)

        artifacts: List[ImageArtifact] = []
        base = artifact.image_path.stem
        parent = artifact.image_path.parent

        for idx in range(pieces):
            top = max(0, idx * slice_height - (self.config.split_overlap if idx > 0 else 0))
            bottom = min(
                image.height,
                (idx + 1) * slice_height + (self.config.split_overlap if idx < pieces - 1 else 0),
            )
            part = image.crop((0, top, image.width, bottom))
            new_path = parent / f"{base}_split_{idx + 1}.png"
            part.save(new_path)
            artifacts.append(
                ImageArtifact(
                    image_path=new_path,
                    parent_pdf=artifact.parent_pdf,
                    page_number=artifact.page_number,
                    split_index=idx + 1,
                )
            )
        artifact.image_path.unlink(missing_ok=True)
        return artifacts
