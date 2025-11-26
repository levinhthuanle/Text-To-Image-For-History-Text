from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from pipeline import DatasetPipeline, PipelineConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PDFs to PNG images")
    parser.add_argument("--raw-dir", type=Path, help="Directory containing PDF files")
    parser.add_argument("--image-dir", type=Path, help="Directory to store generated PNG files")
    parser.add_argument("--pattern", type=str, help="Glob pattern to match PDF filenames")
    parser.add_argument("--dpi", type=int, help="Resolution for PDF to image conversion")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PNG files when converting",
    )
    return parser.parse_args()


def resolve_config(args: argparse.Namespace) -> PipelineConfig:
    config = PipelineConfig()
    updates: dict = {}

    if args.raw_dir:
        updates["raw_pdf_dir"] = args.raw_dir
    if args.image_dir:
        updates["image_output_dir"] = args.image_dir
    if args.pattern:
        updates["pdf_glob_pattern"] = args.pattern
    if args.dpi:
        updates["dpi"] = args.dpi
    if args.overwrite:
        updates["overwrite_images"] = True

    if updates:
        config = replace(config, **updates)

    project_root = Path(__file__).resolve().parents[1]
    return config.resolve(project_root)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    config = resolve_config(args)
    pipeline = DatasetPipeline(config)
    artifacts = pipeline.convert_pdfs()
    if not artifacts:
        logging.warning(
            "No PDF files matched pattern %s in %s",
            config.pdf_glob_pattern,
            config.raw_pdf_dir,
        )
        return

    pages = len(artifacts)
    logging.info(
        "Converted %d page images from PDFs in %s into %s",
        pages,
        config.raw_pdf_dir,
        config.image_output_dir,
    )


if __name__ == "__main__":
    main()